#!/usr/bin/env python3
"""Download official release assets and conservatively catalogue inventory icons.

Python 3.10+, standard library only. All paths in catalogues are relative to
minecraft-assets/<version>. No renderer, game execution or registry guessing.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import struct
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import zipfile
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
OBJECT_BASE_URL = "https://resources.download.minecraft.net"
STATUSES = ("direct", "model_resolved", "complex_model", "missing")
LOG = logging.getLogger("minecraft-assets")


class SyncError(Exception):
    """An actionable failure; the CLI prints it without a traceback."""


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as exc:
        raise SyncError(f"JSON invalido ou inacessivel: {path}: {exc}") from exc


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha1(path: Path, expected: str, size: int | None = None) -> bool:
    return (path.is_file() and (size is None or path.stat().st_size == size)
            and sha1_file(path) == expected.lower())


def official_url(url: str) -> str:
    from urllib.parse import urlsplit
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in {
        "piston-meta.mojang.com", "piston-data.mojang.com",
        "launchermeta.mojang.com", "launcher.mojang.com",
        "resources.download.minecraft.net",
    } or parsed.username or parsed.password):
        raise SyncError(f"URL fora das origens oficiais permitidas: {url}")
    return url


def download(url: str, destination: Path, expected: str | None = None,
             size: int | None = None, force: bool = False) -> dict:
    """Stream to a sibling temporary file; replace only after hash validation."""
    official_url(url)
    if expected and not re.fullmatch(r"[0-9a-fA-F]{40}", expected):
        raise SyncError(f"SHA-1 invalido para {destination.name}")
    if not force and expected and verify_sha1(destination, expected, size):
        LOG.info("Cache validado: %s", destination.name)
        return {"cached": True, "sha1": expected.lower(), "size": destination.stat().st_size}
    destination.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        temp_path = None
        try:
            request = Request(url, headers={"User-Agent": "MinecraftAssetSync/1.0"})
            with urlopen(request, timeout=60) as response:
                official_url(response.url)
                with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as target:
                    temp_path = Path(target.name)
                    shutil.copyfileobj(response, target, length=1024 * 1024)
            actual = sha1_file(temp_path)
            actual_size = temp_path.stat().st_size
            if expected and actual != expected.lower():
                raise SyncError(f"SHA-1 incorreto em {destination.name}: esperado {expected}, obtido {actual}")
            if size is not None and actual_size != size:
                raise SyncError(f"Tamanho incorreto em {destination.name}: {actual_size}, esperado {size}")
            temp_path.replace(destination)
            LOG.info("Download validado: %s (%s bytes)", destination.name, actual_size)
            return {"cached": False, "sha1": actual, "size": actual_size}
        except (URLError, TimeoutError, OSError) as exc:
            if attempt == 2 or isinstance(exc, HTTPError) and exc.code < 500 and exc.code != 429:
                raise SyncError(f"Falha ao baixar {url}: {exc}") from exc
            LOG.warning("Falha de rede; nova tentativa: %s", exc)
            time.sleep(attempt + 1)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
    raise SyncError(f"Download incompleto: {url}")


def get_version_manifest(destination: Path) -> dict:
    # Always refresh: a local metadata file cannot establish release availability.
    download(MANIFEST_URL, destination, force=True)
    return read_json(destination)


def resolve_version(manifest: dict, version: str) -> dict:
    entry = next((v for v in manifest.get("versions", []) if v.get("id") == version), None)
    if entry is None or entry.get("type") != "release":
        raise SyncError(f"Minecraft Java {version} nao foi encontrado como release oficial. "
                        "Snapshots, pre-releases e release candidates nao sao permitidos.")
    return entry


def download_version_metadata(entry: dict, destination: Path, force=False) -> dict:
    download(entry["url"], destination, entry.get("sha1"), force=force)
    data = read_json(destination)
    if data.get("id") != entry["id"] or data.get("type") != "release":
        raise SyncError("O metadata da versao nao corresponde a release solicitada.")
    return data


def download_client(metadata: dict, destination: Path, force=False) -> dict:
    client = metadata.get("downloads", {}).get("client")
    if not client or not client.get("sha1"):
        raise SyncError("Metadata oficial sem client ou SHA-1; download abortado.")
    result = download(client["url"], destination, client["sha1"], client.get("size"), force)
    return {**result, "expected": client["sha1"], "status": "OK", "url": client["url"]}


def safe_child(root: Path, relative: str) -> Path:
    """Reject traversal, Windows drives/ADS, ambiguous names and symlink escapes."""
    if not relative or "\\" in relative or ":" in relative or "\x00" in relative:
        raise SyncError(f"Caminho inseguro: {relative!r}")
    path = PurePosixPath(relative)
    if path.is_absolute() or any(p in {"..", "."} for p in relative.split("/")):
        raise SyncError(f"Caminho inseguro: {relative!r}")
    for part in path.parts:
        if (part.endswith((" ", ".")) or any(c in part for c in '<>"|?*')
                or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part)):
            raise SyncError(f"Nome de arquivo inseguro: {relative!r}")
    target = root.joinpath(*path.parts)
    if not target.resolve().is_relative_to(root.resolve()) or target.resolve() == root.resolve():
        raise SyncError(f"Caminho escapa do destino: {relative!r}")
    return target


def ensure_no_links(root: Path):
    """Do not clean or write through symlinks/junctions, including Windows reparse points."""
    candidates = [root, *root.parents]
    if root.exists():
        candidates.extend(root.rglob("*"))
    for path in candidates:
        if path.is_symlink() or (path.exists() and
                getattr(path.lstat(), "st_file_attributes", 0) & 0x400):
            raise SyncError(f"Symlink/junction nao permitido no destino: {path}")


def version_directory(project: Path, version: str) -> Path:
    if not re.fullmatch(r"[0-9][A-Za-z0-9._-]*", version) or ".." in version or version.endswith("."):
        raise SyncError(f"ID de versao inseguro: {version!r}")
    root = project / "minecraft-assets"
    target = safe_child(root, version)
    ensure_no_links(target)
    if target.resolve().parent != root.resolve():
        raise SyncError("O destino deve ser filho direto de minecraft-assets.")
    return target


def clean_version(project: Path, version: str):
    target = version_directory(project, version)
    if target.exists():
        LOG.info("Removendo somente %s", target.resolve())
        shutil.rmtree(target)


@contextmanager
def temporary_workspace(root: Path):
    # TemporaryDirectory uses mode 0700 on recent Python/Windows, whose ACL
    # survives directory moves. Inherit the project's normal ACL instead.
    staging = safe_child(root, ".sync-" + uuid4().hex)
    staging.mkdir()
    try:
        yield staging
    finally:
        ensure_no_links(staging)
        if staging.exists():
            shutil.rmtree(staging)


def extract_assets(jar: Path, destination: Path) -> dict:
    counts = Counter()
    with zipfile.ZipFile(jar) as archive:
        selected = []
        seen = set()
        for info in archive.infolist():
            # Validate every entry, even those not selected for extraction.
            target = safe_child(destination, info.filename.rstrip("/"))
            if stat.S_ISLNK(info.external_attr >> 16):
                raise SyncError(f"Link simbolico no JAR: {info.filename}")
            if not info.filename.startswith("assets/") or info.is_dir():
                continue
            key = str(target).casefold()
            if key in seen:
                raise SyncError(f"Caminho duplicado no JAR: {info.filename}")
            seen.add(key)
            selected.append((info, target))
        for info, target in selected:
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            parts = PurePosixPath(info.filename).parts
            counts["/".join(parts[:3])] += 1
        if "version.json" in archive.namelist():
            write_json(destination / "metadata/client-version.json", json.loads(archive.read("version.json")))
    LOG.info("Assets extraidos: %s arquivos", sum(counts.values()))
    return dict(sorted(counts.items()))


def sync_languages(metadata: dict, destination: Path, force=False, cache: Path | None = None) -> list:
    """pt_br normally lives in the official content-addressed asset store, not the JAR."""
    index_info = metadata.get("assetIndex")
    if not index_info:
        LOG.warning("Versao sem assetIndex; idiomas limitados ao JAR.")
        return []
    index_path = destination / "metadata/asset-index.json"
    download(index_info["url"], index_path, index_info.get("sha1"), index_info.get("size"), force)
    objects = read_json(index_path).get("objects", {})
    sources = []
    for lang in ("en_us", "pt_br"):
        name = f"minecraft/lang/{lang}.json"
        path = safe_child(destination, f"assets/{name}")
        if path.exists():
            sources.append({"language": lang, "path": f"assets/{name}", "source": "client.jar"})
        elif name in objects:
            obj = objects[name]
            digest = obj["hash"]
            if not re.fullmatch(r"[0-9a-f]{40}", digest):
                raise SyncError(f"Hash de idioma invalido: {name}")
            url = f"{OBJECT_BASE_URL}/{digest[:2]}/{digest}"
            old = cache / f"assets/{name}" if cache else None
            if not force and old and verify_sha1(old, digest, obj.get("size")):
                path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(old, path)
            download(url, path, digest, obj.get("size"), force)
            sources.append({"language": lang, "path": f"assets/{name}", "source": url, "sha1": digest})
        else:
            LOG.warning("Idioma oficial nao encontrado: %s", lang)
            sources.append({"language": lang, "path": None, "source": None})
    return sources


def resource_id(value: str) -> str:
    return value if ":" in value else f"minecraft:{value}"


def asset_files(destination: Path, kind: str, suffix: str):
    for namespace in sorted((destination / "assets").iterdir()):
        folder = namespace / kind
        if folder.is_dir():
            for path in sorted(folder.rglob(f"*{suffix}")):
                yield f"{namespace.name}:{path.relative_to(folder).as_posix()[:-len(suffix)]}", path


def index_textures(destination: Path) -> dict:
    result = {}
    for identifier, path in asset_files(destination, "textures", ".png"):
        with path.open("rb") as stream:
            header = stream.read(24)
        if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            raise SyncError(f"Cabecalho PNG invalido: {path}")
        width, height = struct.unpack(">II", header[16:24])
        item = {"path": path.relative_to(destination).as_posix(), "width": width, "height": height}
        mcmeta = path.with_suffix(".png.mcmeta")
        if mcmeta.exists():
            item["metadata"] = mcmeta.relative_to(destination).as_posix()
            item["animated"] = "animation" in read_json(mcmeta)
        result[identifier] = item
    return result


def index_models(destination: Path) -> dict:
    return {identifier: {"path": path.relative_to(destination).as_posix(), "data": read_json(path)}
            for identifier, path in asset_files(destination, "models", ".json")}


def index_atlas_sprites(destination: Path, textures: dict) -> dict:
    """Record generated sprites without pretending they are physical PNGs."""
    result = {}
    for _, path in asset_files(destination, "atlases", ".json"):
        for source in read_json(path).get("sources", []):
            kind = resource_id(source.get("type", ""))
            sprites = []
            if kind == "minecraft:paletted_permutations":
                separator = source.get("separator", "_")
                sprites = [resource_id(t) + separator + key for t in source.get("textures", [])
                           for key in source.get("permutations", {})]
            elif kind == "minecraft:single":
                sprites = [resource_id(source.get("sprite", source["resource"]))]
            elif kind == "minecraft:unstitch":
                sprites = [resource_id(r["sprite"]) for r in source.get("regions", [])]
            for sprite in sprites:
                if sprite not in textures:
                    result[sprite] = {"atlas": path.relative_to(destination).as_posix(), "source": source}
    return result


class ModelResolver:
    def __init__(self, models: dict, textures: dict, sprites: dict):
        self.models, self.textures, self.sprites = models, textures, sprites
        self.cache = {}

    def inherit(self, identifier: str, chain=()) -> dict:
        identifier = resource_id(identifier)
        if identifier in chain:
            return {"errors": [f"model parent cycle: {' -> '.join((*chain, identifier))}"], "chain": [identifier]}
        if identifier in self.cache:
            return self.cache[identifier]
        if identifier.startswith("minecraft:builtin/"):
            return {"builtin": identifier, "chain": [identifier], "errors": []}
        if identifier not in self.models:
            return {"errors": [f"model not found: {identifier}"], "chain": [identifier]}
        own = self.models[identifier]["data"]
        parent = self.inherit(own["parent"], (*chain, identifier)) if own.get("parent") else {}
        result = {**parent, **own,
                  "textures": {**parent.get("textures", {}), **own.get("textures", {})},
                  "display": {**parent.get("display", {}), **own.get("display", {})},
                  "chain": [identifier, *parent.get("chain", [])],
                  "errors": list(parent.get("errors", []))}
        self.cache[identifier] = result
        return result

    def texture(self, value, mapping: dict) -> tuple[str | None, str | None]:
        seen = set()
        while True:
            # Modern clients also encode material options alongside a sprite.
            if isinstance(value, dict):
                value = value.get("sprite")
            if not isinstance(value, str):
                return None, "unsupported texture value (expected string or sprite object)"
            if not value.startswith("#"):
                break
            key = value[1:]
            if key in seen or key not in mapping:
                return None, f"texture alias missing/cyclic: {value}"
            seen.add(key)
            value = mapping[key]
        identifier = resource_id(value)
        if identifier in self.textures or identifier in self.sprites or identifier == "minecraft:missingno":
            return identifier, None
        return identifier, f"texture not found: {identifier}"

    def analyze(self, name: str, definition: dict) -> dict:
        reasons, issues, refs, found = set(), set(), set(), set()
        node_types = set()
        model_ids = set()

        def walk(value):
            if isinstance(value, list):
                for child in value:
                    walk(child)
            elif isinstance(value, dict):
                if isinstance(value.get("type"), str):
                    node_types.add(resource_id(value["type"]))
                for key, child in value.items():
                    if key in {"model", "base"} and isinstance(child, str):
                        model_ids.add(resource_id(child))
                    if key == "texture" and isinstance(child, str):
                        refs.add("special_texture:" + resource_id(child))
                    walk(child)

        walk(definition.get("model", {}))
        root = definition.get("model")
        if not isinstance(root, dict):
            return {"iconStatus": "missing", "directTexture": None, "resolvedTextures": [],
                    "reasons": ["item definition has no model object"], "references": [], "resourceIssues": []}
        for kind in node_types - {"minecraft:model"}:
            reasons.add("definition node: " + kind)
        if not root.get("type"):
            reasons.add("unknown definition node without type")
        if root.get("tints"):
            reasons.add("tint")
        if set(root) - {"type", "model", "tints"} and root.get("type") in {"model", "minecraft:model"}:
            reasons.add("additional model properties")
        if set(definition) - {"model", "swap_animation_scale", "hand_animation_on_swap"}:
            reasons.add("unknown item definition properties")

        simple_layer = None
        model_errors = set()
        for model_id in sorted(model_ids):
            model = self.inherit(model_id)
            refs.update("model:" + ref for ref in model["chain"])
            issues.update(model.get("errors", []))
            model_errors.update(model.get("errors", []))
            mapping = model.get("textures", {})
            if any(isinstance(v, dict) and set(v) - {"sprite"} for v in mapping.values()):
                reasons.add("texture material options (e.g. force_translucent)")
            resolved = {}
            for key, value in mapping.items():
                texture, error = self.texture(value, mapping)
                if texture:
                    refs.add("texture:" + texture)
                    resolved[key] = texture
                    if texture in self.textures:
                        found.add(self.textures[texture]["path"])
                    elif texture in self.sprites:
                        reasons.add("atlas-generated sprite")
                        refs.add(self.sprites[texture]["atlas"])
                # Particle-only metadata does not make an inventory icon missing.
                if error and key != "particle":
                    issues.add(error)
            if model.get("elements"):
                reasons.add("3D/block geometry")
            if model.get("builtin") != "minecraft:builtin/generated":
                reasons.add("special, empty or non-generated model")
            if model.get("overrides"):
                reasons.add("legacy dynamic overrides")
            if model.get("builtin") == "minecraft:builtin/generated" and model.get("gui_light", "front") != "front":
                reasons.add("non-front GUI lighting")
            known = {"parent", "textures", "elements", "display", "gui_light", "ambientocclusion",
                     "overrides", "builtin", "chain", "errors"}
            if set(model) - known:
                reasons.add("unknown model properties")
            gui = model.get("display", {}).get("gui", {})
            if any(gui.get(key, default) != default for key, default in
                   (("rotation", [0, 0, 0]), ("translation", [0, 0, 0]), ("scale", [1, 1, 1]))):
                reasons.add("GUI model transformation")
            layers = sorted(k for k in mapping if re.fullmatch(r"layer\d+", k))
            if len(layers) > 1:
                reasons.add("multiple texture layers")
            if model.get("builtin") == "minecraft:builtin/generated" and not layers:
                issues.add("generated model without texture layer")
            for key in layers:
                texture = resolved.get(key)
                if texture == "minecraft:missingno":
                    reasons.add("built-in missingno sprite")
                if self.textures.get(texture, {}).get("animated"):
                    reasons.add("animated texture")
            if layers == ["layer0"] and resolved.get("layer0") in self.textures:
                simple_layer = self.textures[resolved["layer0"]]["path"]

        if not model_ids and not reasons:
            issues.add("no model reference")
        if model_errors and node_types <= {"minecraft:model"}:
            status = "missing"
        elif issues and not reasons:
            status = "missing"
        elif reasons:
            # Recognized complex definitions retain all evidence, even if their
            # sprites are generated by an atlas or hardcoded special renderer.
            status = "complex_model"
        elif simple_layer and len(model_ids) == 1:
            namespace, item = name.split(":", 1)
            expected = f"assets/{namespace}/textures/item/{item}.png"
            status = "direct" if simple_layer == expected else "model_resolved"
        else:
            status = "missing"
            issues.add("no simple texture resolved")
        if issues:
            reasons.update(issues)
        return {"iconStatus": status, "directTexture": simple_layer if status in STATUSES[:2] else None,
                "resolvedTextures": sorted(found), "reasons": sorted(reasons),
                "references": sorted(refs), "resourceIssues": sorted(issues)}


def build_item_catalog(destination: Path, textures: dict, models: dict, sprites: dict) -> list:
    languages = {}
    for language in ("en_us", "pt_br"):
        path = destination / f"assets/minecraft/lang/{language}.json"
        languages[language] = read_json(path) if path.exists() else {}
    resolver = ModelResolver(models, textures, sprites)
    items = []
    for identifier, path in asset_files(destination, "items", ".json"):
        namespace, name = identifier.split(":", 1)
        keys = [f"{kind}.{namespace}.{name.replace('/', '.')}" for kind in ("item", "block")]
        names = {lang: next(((key, values[key]) for key in keys if key in values), (None, None))
                 for lang, values in languages.items()}
        items.append({"id": identifier, "name": name,
                      "displayName": names["en_us"][1], "displayNamePtBr": names["pt_br"][1],
                      "translationKeys": {lang: value[0] for lang, value in names.items()},
                      "definition": path.relative_to(destination).as_posix(),
                      **resolver.analyze(identifier, read_json(path))})
    if not items:
        raise SyncError("Nenhuma definicao em assets/*/items. Esta estrutura de versao "
                        "nao e suportada; nenhum ID sera inventado a partir de texturas.")
    return items


def generate_report(destination: Path, metadata: dict, client: dict, extraction: dict,
                    languages: list, items: list, textures: dict, models: dict, sprites: dict) -> dict:
    counts = Counter(item["iconStatus"] for item in items)
    return {"version": metadata["id"], "type": metadata["type"],
            "itemDefinitions": len(items), "itemsCatalogued": len(items),
            "catalogSource": "assets/*/items/**/*.json (visual definitions, not a runtime item registry)",
            "textures": len(textures), "itemTextures": sum(":item/" in t for t in textures),
            "blockTextures": sum(":block/" in t for t in textures), "models": len(models),
            "atlasGeneratedSprites": len(sprites),
            "modelTextureValueTypes": dict(Counter(type(v).__name__ for m in models.values()
                                                   for v in m["data"].get("textures", {}).values())),
            "icons": {status: counts[status] for status in STATUSES},
            "missingItems": [i["id"] for i in items if i["iconStatus"] == "missing"],
            "itemsWithResourceIssues": [{"id": i["id"], "issues": i["resourceIssues"]}
                                        for i in items if i["resourceIssues"]],
            "missingTranslations": {lang: [i["id"] for i in items if i[field] is None]
                                    for lang, field in (("en_us", "displayName"), ("pt_br", "displayNamePtBr"))},
            "download": {"client.jar": client}, "languages": languages,
            "extractedFiles": sum(extraction.values()), "extractedDirectories": extraction,
            "output": str(destination.resolve()),
            "limitations": [
                "Item definitions identify visual resources; they are not an authoritative runtime item registry.",
                "Only static single-layer generated models without tint, animation or GUI transform get a simple icon.",
                "No special/3D/dynamic models, palette permutations or component overrides are rendered.",
                "Special texture identifiers are preserved without guessing renderer-specific texture paths.",
                "All JAR assets are preserved; external asset-index downloads are limited to en_us/pt_br.",
                "Custom names, glint, profiles, item_model and other stack components require future rendering.",
            ]}


def write_readme(destination: Path, version: str):
    (destination / "README.md").write_text(f"""# Minecraft Java {version}: assets vanilla

Release oficial confirmada pelo [manifest da Mojang]({MANIFEST_URL}).
O client JAR, metadata e asset index sao validados pelos SHA-1 oficiais.
Os idiomas en_us/pt_br ausentes no JAR sao obtidos do armazenamento oficial
resources.download.minecraft.net, com hash e tamanho do asset index.

## Executar / atualizar (na raiz do projeto, Python 3.10+)

```powershell
python tools/sync_minecraft_assets.py --version {version}
python tools/sync_minecraft_assets.py --version {version} --force
python tools/sync_minecraft_assets.py --version {version} --clean
```

Troque `--version` por outra release oficial. Snapshots/pre-releases/RC sao recusados.
`--force` baixa novamente os arquivos oficiais; normalmente o cache e validado.
`--clean` remove SOMENTE minecraft-assets/{version}/ e refaz a sincronizacao.
O manifest e consultado e a release validada antes de qualquer limpeza.
Os assets e catalogos sao reconstruidos em staging; uma falha preserva a ultima
geracao concluida (exceto quando --clean foi solicitado explicitamente).

## Estrutura

- metadata/: manifest, entrada, version.json, client-version.json, asset-index.json, build-info.json.
- raw/client.jar: client oficial com SHA-1 validado, sem copias duplicadas.
- assets/: estrutura integral original do JAR, incluindo models, textures,
  items, blockstates, atlases, equipment, shaders, fontes e arquivos .mcmeta.
- catalog/items.json: uma entrada por definicao, nomes oficiais, fontes e analise do icone.
- catalog/textures.json: PNGs fisicos, dimensoes e metadados de animacao.
- catalog/models.json: caminho e JSON completo de cada modelo no campo data.
- catalog/atlas-sprites.json: sprites gerados por atlas, separados dos PNGs fisicos.
- catalog/unresolved-items.json: itens complexos/ausentes, motivos e referencias.
- catalog/report.json: contagens, proveniencia, hashes, traducao e limitacoes.

Todos os caminhos de assets nos catalogos sao relativos a esta pasta.

## Status dos icones

- direct: layer0 aponta para textures/item/<nome>.png, apos validar a cadeia;
  uma textura de mesmo nome, sozinha, nunca sobrepoe uma definicao complexa.
- model_resolved: modelo generated de camada unica resolvido para outra textura.
- complex_model: requer geometria, tint, camadas, animacao, transformacao de GUI,
  conditions/select/range_dispatch/composite, atlas ou renderizador especial.
  Nao geramos PNG nem escolhemos arbitrariamente uma variante.
- missing: definicao/modelo/textura necessarios nao resolvidos para um icone simples.

`directTexture` so e preenchido nos dois primeiros estados. `resolvedTextures`
pode incluir texturas auxiliares/particle e NAO representa um icone pronto.
`references` preserva cadeias e identificadores especiais; `resourceIssues`
registra referencias nao encontradas. Air e outros modelos vazios sao complexos,
nao itens perdidos. Modelos especiais podem resolver texturas em codigo do jogo.

O catalogo e baseado em definicoes VISUAIS, nao em um registry executado do jogo.
Podem existir variantes visuais e entradas sem item registravel ou nome proprio.
As traducoes usam apenas chaves item.<namespace>.<id> ou block.<namespace>.<id>;
ausencias ficam null, sem inventar traducao. Leia report.json para os casos reais.
Os exemplos NBT/SNBT do projeto sao referencias de cobertura; componentes que
trocam aparencia ou nome nao alteram este catalogo vanilla. O auditor separado
tools/audit_asset_examples.py confere ItemStacks e minecraft:item_model dos SNBT.

## Propriedade

Os assets pertencem ao Minecraft/Mojang/Microsoft. Este projeto apenas os utiliza
para integracao com Minecraft e nao concede direitos de redistribuicao dos assets.
Nenhum site, editor NBT ou renderizador foi criado nesta etapa.

## Estruturas observadas

O parser suporta texturas como string, aliases #layer e objetos com `sprite`.
Opcoes de material como `force_translucent` sao preservadas e exigem renderer.
As contagens reais dos tipos de valor ficam em report.json/modelTextureValueTypes.
Os atlas podem criar sprites por `paletted_permutations`; o indice separado
preserva a receita original, sem fabricar arquivos PNG.
""", encoding="utf-8")


def sync(project: Path, version: str, force=False, clean=False) -> dict:
    destination = version_directory(project, version)
    asset_root = project / "minecraft-assets"
    asset_root.mkdir(parents=True, exist_ok=True)
    with temporary_workspace(asset_root) as staging:
        manifest_path = staging / "metadata/version_manifest.json"
        entry = resolve_version(get_version_manifest(manifest_path), version)
        LOG.info("Release oficial confirmada: %s (%s)", entry["id"], entry["type"])
        metadata = download_version_metadata(entry, staging / "metadata/version.json", force)
        if clean:
            clean_version(project, version)
        destination.mkdir(parents=True, exist_ok=True)
        client = download_client(metadata, destination / "raw/client.jar", force)
        write_json(staging / "metadata/version_manifest_entry.json", entry)
        extraction = extract_assets(destination / "raw/client.jar", staging)
        # Reuse supplemental language/index cache by hash, without copying the JAR.
        index_info = metadata.get("assetIndex", {})
        old_index = destination / "metadata/asset-index.json"
        if not force and index_info.get("sha1") and verify_sha1(old_index, index_info["sha1"]):
            shutil.copyfile(old_index, staging / "metadata/asset-index.json")
        languages = sync_languages(metadata, staging, force, destination)
        textures = index_textures(staging)
        models = index_models(staging)
        sprites = index_atlas_sprites(staging, textures)
        items = build_item_catalog(staging, textures, models, sprites)
        unresolved = [{"id": item["id"], "iconStatus": item["iconStatus"],
                       "reason": "; ".join(item["reasons"]), "definition": item["definition"],
                       "references": item["references"], "resourceIssues": item["resourceIssues"]}
                      for item in items if item["iconStatus"] in STATUSES[2:]]
        for filename, value in (("items", items), ("textures", textures), ("models", models),
                                ("atlas-sprites", sprites), ("unresolved-items", unresolved)):
            write_json(staging / f"catalog/{filename}.json", value)
        report = generate_report(destination, metadata, client, extraction, languages, items, textures, models, sprites)
        write_json(staging / "catalog/report.json", report)
        write_json(staging / "metadata/build-info.json", {
            "schemaVersion": 1, "tool": "tools/sync_minecraft_assets.py",
            "generatedAt": datetime.now(timezone.utc).isoformat(), "version": version, "type": "release",
            "manifestUrl": MANIFEST_URL, "metadataUrl": entry["url"], "metadataSha1": entry.get("sha1"),
            "client": client, "languages": languages,
        })
        write_readme(staging, version)
        # Commit generated folders only after successful parsing/catalogue generation.
        ensure_no_links(destination)
        for name in ("metadata", "assets", "catalog", "README.md"):
            target = safe_child(destination, name)
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink(missing_ok=True)
            (staging / name).replace(target)
    # Include the report's own size, allowing its numeric field to settle.
    for _ in range(4):
        total = sum(p.stat().st_size for p in destination.rglob("*") if p.is_file())
        if report.get("totalBytes") == total:
            break
        report["totalBytes"] = total
        write_json(destination / "catalog/report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="26.2", help="ID exato de uma release oficial (padrao: 26.2)")
    parser.add_argument("--force", action="store_true", help="Forcar novos downloads")
    parser.add_argument("--clean", action="store_true", help="Remover somente a pasta da versao e refazer")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        report = sync(PROJECT_ROOT, args.version, args.force, args.clean)
    except (SyncError, OSError, ValueError, KeyError, TypeError, RecursionError, zipfile.BadZipFile) as exc:
        LOG.error("Sincronizacao abortada: %s", exc)
        return 1
    client = report["download"]["client.jar"]
    print(f"\nMinecraft Java {report['version']} Asset Sync\nType: {report['type']}")
    print(f"Item definitions / catalogued: {report['itemsCatalogued']}")
    print(f"Textures: {report['textures']} (item: {report['itemTextures']}, block: {report['blockTextures']})")
    print(f"Models: {report['models']}\nIcons:")
    for status, count in report["icons"].items():
        print(f"  {status}: {count}")
    print(f"client.jar: {client['size'] / 1024**2:.2f} MiB; cache: {client['cached']}")
    print(f"SHA-1 expected:   {client['expected']}\nSHA-1 calculated: {client['sha1']}\nStatus: {client['status']}")
    print(f"Total: {report['totalBytes'] / 1024**2:.2f} MiB\nOutput: {report['output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
