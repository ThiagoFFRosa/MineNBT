"""Regression tests for official registry evidence and overlap-aware projections."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_minecraft_registry import ComplexityAnalyzer, ModelGraph, IMPORTANT, project_coverage
from minecraft_classfile import ClassFile, descriptor_types, instructions
from minecraft_registry_source import RegistryInspector, ITEMS, BLOCK_ITEM
from sync_minecraft_assets import PROJECT_ROOT, read_json


class TraversalTests(unittest.TestCase):
    def setUp(self):
        self.models = {"minecraft:item/test": {"path": "assets/minecraft/models/item/test.json",
                                              "data": {"parent": "builtin/generated", "textures": {"layer0": "item/test"}}}}
        self.textures = {"minecraft:item/test": {"path": "assets/minecraft/textures/item/test.png"}}
        self.item = {"id": "minecraft:test", "definition": "assets/minecraft/items/test.json", "iconStatus": "complex_model"}

    def analyze(self, model, depth=64):
        return ComplexityAnalyzer(self.models, self.textures, {}, depth).analyze(self.item, {"model": model})

    def test_model_parent_cycle(self):
        self.models["minecraft:item/test"]["data"]["parent"] = "item/test"
        result = self.analyze({"type": "model", "model": "item/test"})
        self.assertTrue(any("model_cycle" in issue for issue in result["diagnostics"]))

    def test_definition_cycle(self):
        node = {"type": "condition", "on_false": {"type": "empty"}}
        node["on_true"] = node
        result = self.analyze(node)
        self.assertTrue(any("definition_cycle" in issue for issue in result["diagnostics"]))

    def test_texture_alias_cycle(self):
        self.models["minecraft:item/test"]["data"]["textures"] = {"layer0": "#a", "a": "#layer0"}
        self.assertTrue(self.analyze({"type": "model", "model": "item/test"})["diagnostics"])

    def test_depth_limit_with_and_without_cached_parent(self):
        models = {f"minecraft:item/{n}": {"data": {"parent": f"item/{n + 1}"}, "path": str(n)} for n in range(8)}
        graph = ModelGraph(models, 3)
        self.assertTrue(graph.resolve("item/0")["errors"])
        node = {"type": "empty"}
        for _ in range(8): node = {"type": "composite", "models": [node]}
        self.assertTrue(any("depth_limit" in issue for issue in self.analyze(node, 3)["diagnostics"]))

    def test_nested_tint_not_confused_with_definition_node(self):
        node = {"type": "select", "fallback": {"type": "model", "model": "item/test", "tints": [{"type": "dye"}]}}
        result = self.analyze(node)
        self.assertIn("tinted", result["reasons"])
        self.assertEqual(result["tintTypes"], ["minecraft:dye"])
        self.assertNotIn("minecraft:dye", result["definitionNodeTypes"])

    def test_block_texture_animation(self):
        self.models["minecraft:item/test"]["data"] = {"elements": [{"faces": {"north": {"texture": "all"}}}],
                                                       "textures": {"all": "item/test"}}
        self.textures["minecraft:item/test"]["animated"] = True
        result = self.analyze({"type": "model", "model": "item/test"})
        self.assertIn("texture_animation", result["requiredFeatures"])
        self.assertEqual(result["diagnostics"], [])

    def test_missing_model_and_texture_are_diagnosed(self):
        result = self.analyze({"type": "model", "model": "item/nonexistent"})
        self.assertIn("repair_references", result["requiredFeatures"])
        self.textures.clear()
        self.assertTrue(any("broken_texture" in d for d in self.analyze({"type": "model", "model": "item/test"})["diagnostics"]))

    def test_generated_atlas_sprite_is_not_a_missing_file(self):
        result = ComplexityAnalyzer(self.models, {}, {"minecraft:item/test": {"atlas": "assets/minecraft/atlases/items.json"}}).analyze(
            self.item, {"model": {"type": "model", "model": "item/test"}})
        self.assertIn("atlas_sprites", result["requiredFeatures"])
        self.assertEqual(result["diagnostics"], [])


class ProjectionTests(unittest.TestCase):
    def fixture(self):
        rows = [{"id": k, "selectable": True, "icon": {"status": "direct" if k == "a" else "complex_model"}}
                for k in ("a", "b", "c", "d")]
        analyses = {"a": {"requiredFeatures": []}, "b": {"requiredFeatures": ["model_geometry"]},
                    "c": {"requiredFeatures": ["model_geometry", "tints"]},
                    "d": {"requiredFeatures": ["tints", "texture_layers"]}}
        return rows, analyses

    def test_dependencies_not_double_counted(self):
        result = project_coverage(*self.fixture())
        self.assertEqual(result["currentlyResolvable"], 1)
        first = result["incrementalPlan"][0]
        self.assertEqual(first["featuresAdded"], ["model_geometry"])
        self.assertEqual(first["newItemsResolved"], 1)
        ids = [i for step in result["incrementalPlan"] for i in step["itemIds"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(result["incrementalPlan"][-1]["coverageAfter"], 4)

    def test_zero_gain_requires_bundle(self):
        rows, analyses = self.fixture()
        result = project_coverage([rows[-1]], {"d": analyses["d"]})
        self.assertEqual(result["incrementalPlan"][0]["featuresAdded"], ["texture_layers", "tints"])
        self.assertTrue(all(r["newItemsResolved"] == 0 for r in result["potentialFeatures"]))

    def test_unknowns_not_projected_as_supported(self):
        rows, analyses = self.fixture()
        analyses["d"]["requiredFeatures"] = ["unknown_semantics"]
        self.assertEqual(project_coverage(rows, analyses)["unprojectedItems"], ["d"])

    def test_nonselectable_excluded_from_denominator(self):
        rows, analyses = self.fixture()
        rows[-1]["selectable"] = False
        result = project_coverage(rows, analyses)
        self.assertEqual(result["selectableItems"], 3)
        self.assertNotIn("d", [i for row in result["potentialFeatures"] for i in row["itemIds"]])


class OfficialRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = PROJECT_ROOT / "minecraft-assets/26.2"
        cls.catalog = cls.root / "catalog"
        cls.registry = read_json(cls.catalog / "registry.json")
        cls.by_id = {r["id"]: r for r in cls.registry}
        cls.visual = read_json(cls.catalog / "items.json")
        cls.breakdown = read_json(cls.catalog / "complex-model-breakdown.json")
        cls.coverage = read_json(cls.catalog / "renderer-coverage.json")
        with zipfile.ZipFile(cls.root / "raw/client.jar") as archive:
            cls.inspector = RegistryInspector(archive)
            cls.registered, cls.provenance = cls.inspector.inspect()

    def test_valid_unique_namespaced_registry(self):
        self.assertIsInstance(self.registry, list)
        self.assertEqual(len(self.registry), len(self.by_id))
        for row in self.registry:
            self.assertRegex(row["id"], r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")

    def test_selectable_evidence_and_definitions(self):
        for row in self.registry:
            if row["selectable"]:
                self.assertIn(row["id"], self.registered)
                self.assertTrue((self.root / row["definition"]).is_file())
                self.assertIn("registry-provenance.json", row["source"])

    def test_air_is_registered_but_not_selectable(self):
        self.assertTrue(self.by_id["minecraft:air"]["registered"])
        self.assertFalse(self.by_id["minecraft:air"]["selectable"])
        self.assertEqual(self.registered["minecraft:air"]["class"], "net/minecraft/world/item/AirItem")

    def test_no_silent_loss_or_nonselectable_overlap(self):
        self.assertEqual(set(self.by_id), {r["id"] for r in self.visual})
        self.assertEqual(set(self.by_id), set(self.registered))
        rejected = read_json(self.catalog / "non-selectable-definitions.json")
        self.assertEqual({r["id"] for r in rejected}, {r["id"] for r in self.registry if not r["selectable"]})

    def test_block_kind_uses_constructor_hierarchy(self):
        for row in self.registry:
            source = self.registered[row["id"]]
            self.assertEqual(row["isBlockItem"], BLOCK_ITEM in source["classHierarchy"])
        self.assertTrue(self.by_id["minecraft:player_head"]["isBlockItem"])
        self.assertFalse(self.by_id["minecraft:air"]["isBlockItem"])

    def test_collections_expanded_and_block_aliases_not_extra_items(self):
        for name in ("white_shulker_box", "purple_shulker_box", "waxed_oxidized_copper", "red_bundle"):
            self.assertIn("minecraft:" + name, self.registered)
        aliases = [r for r in self.registered.values() if r.get("blockAliases")]
        self.assertGreater(len(aliases), 0)

    def test_breakdown_totals_and_every_complex_has_reason(self):
        original = {r["id"] for r in self.visual if r["iconStatus"] == "complex_model"}
        self.assertEqual(original, {r["id"] for r in self.breakdown["items"]})
        self.assertEqual(self.breakdown["total"], len(original))
        self.assertEqual(sum(self.breakdown["primaryReasons"].values()), len(original))
        for row in self.breakdown["items"]:
            self.assertTrue(row["reasons"])
            self.assertTrue(row["requiredFeatures"])
        for category, group in self.breakdown["categories"].items():
            expected = {r["id"] for r in self.breakdown["items"] if category in r["reasons"]}
            self.assertEqual(set(group["items"]), expected)
            self.assertEqual(group["count"], len(expected))

    def test_no_new_missing_or_diagnostics(self):
        for row in self.registry:
            self.assertNotEqual(row["icon"]["status"], "missing")
        self.assertEqual(self.breakdown["diagnostics"], [])
        old = {r["id"]: r["iconStatus"] for r in self.visual}
        self.assertEqual(old, {r["id"]: r["icon"]["status"] for r in self.registry})

    def test_all_fourteen_required_items(self):
        checks = read_json(self.catalog / "important-item-checks.json")
        self.assertEqual({r["id"] for r in checks}, {"minecraft:" + n for n in IMPORTANT})
        for row in checks:
            self.assertTrue(row["registered"])
            self.assertTrue(row["selectable"])
            self.assertGreater(len(row["mainReferenceChain"]), 1)

    def test_real_projection_never_double_counts(self):
        seen = set()
        total = self.coverage["currentlyResolvable"]
        for step in self.coverage["incrementalPlan"]:
            self.assertFalse(seen & set(step["itemIds"]))
            seen.update(step["itemIds"])
            total += step["newItemsResolved"]
            self.assertEqual(step["coverageAfter"], total)
        self.assertEqual(total + len(self.coverage["unprojectedItems"]), self.coverage["selectableItems"])

    def test_provenance_matches_reinspection(self):
        saved = read_json(self.catalog / "registry-provenance.json")
        self.assertEqual(saved["registryEntries"], self.registered)
        self.assertEqual(saved["classSha256"], self.provenance["classSha256"])
        self.assertEqual(saved["methodCodeSha256"], self.provenance["methodCodeSha256"])


class BytecodeTests(unittest.TestCase):
    def test_bad_magic_and_descriptor(self):
        with self.assertRaises(ValueError): ClassFile(b"wrong")
        self.assertEqual(descriptor_types("(Ljava/lang/String;[IJD)Ljava/lang/Object;"),
                         (["Ljava/lang/String;", "[I", "J", "D"], "Ljava/lang/Object;"))

    def test_unsupported_opcode_fails_closed(self):
        class Fixture:
            methods = {("test", "()V"): {"access": 8, "code": b"\xff\xb1", "exceptions": []}}
        inspector = RegistryInspector(None)
        inspector.classes["fixture"] = Fixture()
        with self.assertRaisesRegex(ValueError, "Unsupported JVM opcode"):
            inspector.evaluate("fixture", "test", "()V", [])

    def test_registry_depth_limit(self):
        with zipfile.ZipFile(PROJECT_ROOT / "minecraft-assets/26.2/raw/client.jar") as archive:
            with self.assertRaisesRegex(ValueError, "cycle/depth"):
                RegistryInspector(archive, max_depth=1).inspect()


if __name__ == "__main__": unittest.main()
