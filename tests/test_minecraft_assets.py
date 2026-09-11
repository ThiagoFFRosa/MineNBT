"""Offline regression tests for dangerous paths, downloads and icon semantics."""
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import sync_minecraft_assets as sync
from audit_asset_examples import SnbtReader, audit


class IconTests(unittest.TestCase):
    def setUp(self):
        self.models = {
            "minecraft:item/generated": {"data": {"parent": "builtin/generated"}},
            "minecraft:item/handheld": {"data": {"parent": "item/generated"}},
            "minecraft:item/test": {"data": {"parent": "item/handheld", "textures": {"layer0": "item/test"}}},
        }
        self.textures = {
            "minecraft:item/test": {"path": "assets/minecraft/textures/item/test.png"},
            "minecraft:block/other": {"path": "assets/minecraft/textures/block/other.png"},
        }
        self.definition = {"model": {"type": "minecraft:model", "model": "minecraft:item/test"}}

    def result(self):
        return sync.ModelResolver(self.models, self.textures, {}).analyze("minecraft:test", self.definition)

    def test_flat_handheld_direct(self):
        self.assertEqual(self.result()["iconStatus"], "direct")

    def test_different_texture_name_and_alias(self):
        self.models["minecraft:item/test"]["data"]["textures"] = {"layer0": "#shared", "shared": "block/other"}
        result = self.result()
        self.assertEqual(result["iconStatus"], "model_resolved")
        self.assertTrue(result["directTexture"].endswith("block/other.png"))

    def test_tint_overrides_same_name_texture(self):
        self.definition["model"]["tints"] = [{"type": "minecraft:potion"}]
        self.assertEqual(self.result()["iconStatus"], "complex_model")
        self.assertIsNone(self.result()["directTexture"])

    def test_conditions_never_pick_arbitrary_fallback(self):
        self.definition = {"model": {"type": "minecraft:condition", "on_false": self.definition["model"],
                                     "on_true": {"type": "minecraft:empty"}}}
        self.assertEqual(self.result()["iconStatus"], "complex_model")

    def test_multilayer_requires_renderer(self):
        self.models["minecraft:item/test"]["data"]["textures"]["layer1"] = "block/other"
        self.assertEqual(self.result()["iconStatus"], "complex_model")

    def test_block_geometry_not_missing(self):
        self.models["minecraft:item/test"]["data"] = {"elements": [{"from": [0, 0, 0], "to": [16, 16, 16]}],
                                                       "textures": {"all": "block/other"}}
        self.assertEqual(self.result()["iconStatus"], "complex_model")

    def test_special_shulker(self):
        self.definition = {"model": {"type": "minecraft:special", "base": "item/test",
                                     "model": {"type": "minecraft:shulker_box", "texture": "minecraft:shulker_purple"}}}
        result = self.result()
        self.assertEqual(result["iconStatus"], "complex_model")
        self.assertIn("special_texture:minecraft:shulker_purple", result["references"])

    def test_texture_material_object_26_2(self):
        self.models["minecraft:item/test"]["data"]["textures"]["layer0"] = {"sprite": "item/test", "force_translucent": True}
        result = self.result()
        self.assertEqual(result["iconStatus"], "complex_model")
        self.assertEqual(result["resourceIssues"], [])
        self.assertIn(self.textures["minecraft:item/test"]["path"], result["resolvedTextures"])

    def test_sprite_only_object_resolves(self):
        self.models["minecraft:item/test"]["data"]["textures"]["layer0"] = {"sprite": "item/test"}
        self.assertEqual(self.result()["iconStatus"], "direct")

    def test_animation_and_gui_transform_require_renderer(self):
        self.textures["minecraft:item/test"]["animated"] = True
        self.assertEqual(self.result()["iconStatus"], "complex_model")
        self.textures["minecraft:item/test"].pop("animated")
        self.models["minecraft:item/test"]["data"]["display"] = {"gui": {"rotation": [30, 45, 0]}}
        self.assertEqual(self.result()["iconStatus"], "complex_model")

    def test_missing_model_and_parent_cycle(self):
        self.models.pop("minecraft:item/test")
        self.assertEqual(self.result()["iconStatus"], "missing")
        self.models["minecraft:item/test"] = {"data": {"parent": "item/test"}}
        self.assertEqual(self.result()["iconStatus"], "missing")

    def test_missing_texture_and_alias_cycle(self):
        self.textures.clear()
        self.assertEqual(self.result()["iconStatus"], "missing")
        self.models["minecraft:item/test"]["data"]["textures"] = {"layer0": "#loop", "loop": "#layer0"}
        self.assertEqual(self.result()["iconStatus"], "missing")

    def test_empty_air_is_not_a_lost_definition(self):
        self.models["minecraft:item/test"]["data"] = {"textures": {"particle": "minecraft:missingno"}}
        self.assertEqual(self.result()["iconStatus"], "complex_model")

    def test_atlas_sprite_is_not_missing_png(self):
        self.textures.clear()
        resolver = sync.ModelResolver(self.models, {}, {"minecraft:item/test": {"atlas": "assets/minecraft/atlases/items.json"}})
        self.assertEqual(resolver.analyze("minecraft:test", self.definition)["iconStatus"], "complex_model")

    def test_future_node_kept_complex(self):
        self.definition = {"model": {"type": "minecraft:future_node"}}
        self.assertEqual(self.result()["iconStatus"], "complex_model")


class FileSafetyTests(unittest.TestCase):
    def test_zip_traversal_windows_ads_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for bad in ("../escape", "/absolute", "assets/../../../escape", "C:/escape", "assets\\escape",
                        "assets/file:stream", "assets/NUL.json", "assets/trailing."):
                with self.subTest(bad=bad), self.assertRaises(sync.SyncError):
                    sync.safe_child(root, bad)
            for filename, mode in (("assets/../../escape", 0), ("assets/link", stat.S_IFLNK | 0o777)):
                jar = root / "bad.jar"
                with zipfile.ZipFile(jar, "w") as archive:
                    archive.writestr("assets/minecraft/valid.json", "{}")
                    info = zipfile.ZipInfo(filename)
                    info.external_attr = mode << 16
                    archive.writestr(info, "outside")
                with self.assertRaises(sync.SyncError):
                    sync.extract_assets(jar, root / "out")
                self.assertFalse((root / "out/assets/minecraft/valid.json").exists())
            self.assertFalse((root / "escape").exists())

    def test_clean_is_scoped_to_exact_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "minecraft-assets/26.2"
            sibling = root / "minecraft-assets/26.3"
            for folder in (target, sibling, root / "exemplos"):
                folder.mkdir(parents=True)
                (folder / "keep.txt").write_text("keep")
            for bad in ("../exemplos", "26.2/../../exemplos", "C:\\", "..", "26.2:ads"):
                with self.assertRaises(sync.SyncError):
                    sync.clean_version(root, bad)
            sync.clean_version(root, "26.2")
            self.assertFalse(target.exists())
            self.assertTrue((sibling / "keep.txt").exists())
            self.assertTrue((root / "exemplos/keep.txt").exists())

    def test_reject_nonrelease_or_wrong_id(self):
        for entries in ([], [{"id": "26.2", "type": "snapshot"}], [{"id": "26.2-rc1", "type": "release"}]):
            with self.assertRaises(sync.SyncError):
                sync.resolve_version({"versions": entries}, "26.2")
        entry = {"id": "26.3", "type": "release"}
        self.assertEqual(sync.resolve_version({"versions": [entry]}, "26.3"), entry)

    def test_invalid_release_does_not_clean_existing_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "minecraft-assets/26.2"
            target.mkdir(parents=True)
            sentinel = target / "keep.txt"
            sentinel.write_text("keep")
            with patch.object(sync, "get_version_manifest", return_value={"versions": []}):
                with self.assertRaises(sync.SyncError):
                    sync.sync(root, "26.2", clean=True)
            self.assertEqual(sentinel.read_text(), "keep")

    def test_cache_force_corruption_and_hash_failure(self):
        payload = b"official bytes"
        expected = hashlib.sha1(payload).hexdigest()
        url = "https://piston-data.mojang.com/test"
        def response(*args, **kwargs):
            stream = io.BytesIO(payload)
            stream.url = url
            return stream
        with tempfile.TemporaryDirectory() as temporary, patch.object(sync, "urlopen", side_effect=response) as opener:
            target = Path(temporary) / "client.jar"
            self.assertFalse(sync.download(url, target, expected)["cached"])
            self.assertTrue(sync.download(url, target, expected)["cached"])
            self.assertEqual(opener.call_count, 1)
            sync.download(url, target, expected, force=True)
            self.assertEqual(opener.call_count, 2)
            target.write_bytes(b"corrupt")
            sync.download(url, target, expected)
            self.assertEqual(opener.call_count, 3)
            self.assertEqual(target.read_bytes(), payload)
            with self.assertRaises(sync.SyncError):
                sync.download(url, target, "0" * 40, force=True)
            self.assertEqual(target.read_bytes(), payload)
            self.assertEqual(list(target.parent.iterdir()), [target])


class ExampleTests(unittest.TestCase):
    def test_nested_stacks_override_and_entity_id_discrimination(self):
        text = '''{id:"minecraft:chest",count:1,components:{"minecraft:container":[
          {slot:0,item:{id:"minecraft:stick",count:1,components:{
            "minecraft:item_model":"minecraft:end_portal_frame",
            "minecraft:entity_data":{id:"minecraft:wolf"},
            "minecraft:lore":["id: minecraft:fake count: 1"],
            "test:array":[I;1,2,3],"test:number":1b}}}]}}'''
        self.assertIsInstance(SnbtReader(text).read(), dict)
        catalog = [{"id": "minecraft:" + name, "iconStatus": "complex_model", "definition": name}
                   for name in ("chest", "stick", "end_portal_frame")]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "sample.snbt").write_text(text)
            result = audit(root, catalog)
        self.assertEqual(result["uniqueItemIds"], 2)
        self.assertEqual(result["maxStackNestingDepth"], 2)
        self.assertEqual(result["notCatalogued"], [])
        self.assertEqual(result["itemModelOverrides"][0]["id"], "minecraft:end_portal_frame")

    def test_real_examples_are_all_read_and_covered(self):
        path = sync.PROJECT_ROOT / "minecraft-assets/26.2/catalog/items.json"
        if not path.exists():
            self.skipTest("Run the real 26.2 sync first")
        result = audit(sync.PROJECT_ROOT / "exemplos", sync.read_json(path))
        self.assertGreater(result["filesRead"], 0)
        self.assertEqual(result["parseFailures"], [])
        self.assertEqual(result["notCatalogued"], [])


class RealCatalogTests(unittest.TestCase):
    def test_real_catalog_completeness_hash_and_requested_items(self):
        root = sync.PROJECT_ROOT / "minecraft-assets/26.2"
        if not (root / "catalog/items.json").exists():
            self.skipTest("Run the real 26.2 sync first")
        items = sync.read_json(root / "catalog/items.json")
        catalog = {item["id"]: item for item in items}
        with zipfile.ZipFile(root / "raw/client.jar") as archive:
            definitions = {n for n in archive.namelist() if n.startswith("assets/minecraft/items/") and n.endswith(".json")}
            self.assertEqual(definitions, {item["definition"] for item in items})
            # Exact bytes: all vanilla assets, including mcmeta/equipment/atlases.
            for name in archive.namelist():
                if name.startswith("assets/") and not name.endswith("/"):
                    self.assertEqual((root / name).read_bytes(), archive.read(name), name)
        metadata = sync.read_json(root / "metadata/version.json")
        self.assertTrue(sync.verify_sha1(root / "raw/client.jar", metadata["downloads"]["client"]["sha1"]))
        for name in ("diamond_sword", "netherite_sword"):
            self.assertEqual(catalog["minecraft:" + name]["iconStatus"], "direct")
        for name in ("bow", "potion", "chest", "furnace", "spawner", "purple_shulker_box"):
            self.assertEqual(catalog["minecraft:" + name]["iconStatus"], "complex_model", name)
        for item in items:
            if item["iconStatus"] in ("direct", "model_resolved"):
                self.assertTrue((root / item["directTexture"]).is_file())
            else:
                self.assertIsNone(item["directTexture"])
        report = sync.read_json(root / "catalog/report.json")
        self.assertEqual(sum(report["icons"].values()), len(items))
        self.assertEqual(len(catalog), len(items))
        unresolved = sync.read_json(root / "catalog/unresolved-items.json")
        self.assertEqual({i["id"] for i in unresolved}, {i["id"] for i in items if i["iconStatus"] in ("complex_model", "missing")})


if __name__ == "__main__":
    unittest.main()
