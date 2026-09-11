#!/usr/bin/env python3
"""Audit the local official registry and project renderer coverage, offline.

Python 3.10+, standard library only. Does not modify assets, items.json or SNBT.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import logging
from pathlib import Path
import re
import time
import zipfile

from minecraft_registry_source import RegistryInspector
from sync_minecraft_assets import (PROJECT_ROOT, SyncError, read_json, write_json,
                                   resource_id, verify_sha1, version_directory)

LOG = logging.getLogger("registry-audit")
IMPORTANT = ("diamond_sword", "netherite_sword", "bow", "crossbow", "potion", "splash_potion",
             "chest", "furnace", "spawner", "purple_shulker_box", "bundle", "player_head",
             "written_book", "firework_rocket")
FEATURES = {
    "model_geometry": "Modelos item/block: heranca, cubos/faces/UV, GUI, luz e materiais",
    "special_models": "Renderizadores especiais vanilla, suas texturas, transforms e dados especificos",
    "state_dispatch": "Avaliar condition/select/range_dispatch e propriedades dinamicas em todos os ramos",
    "tints": "Fontes de tint constantes e dinamicas e aplicacao por camada/face",
    "texture_layers": "Compor multiplas camadas generated com transparencia",
    "atlas_sprites": "Gerar sprites dos atlas, incluindo paletted_permutations",
    "composite_models": "Compor submodelos na ordem definida",
    "bundle_contents": "Renderizar ItemStack selecionado dentro de bundles (requer suporte ao item contido)",
    "texture_animation": "Ler animacao e frames dos arquivos .png.mcmeta",
    "empty_model": "Representar intencionalmente um modelo sem geometria/icone",
    "unknown_semantics": "Investigar campos/tipos nao reconhecidos antes de estimar suporte",
    "repair_references": "Resolver diagnosticos de referencias antes de renderizar",
}


class ModelGraph:
    def __init__(self, models, max_depth=64):
        self.models, self.max_depth, self.cache = models, max_depth, {}

    def resolve(self, identifier, active=()):
        identifier = resource_id(identifier)
        if identifier in active:
            return {"chain": [identifier], "errors": ["model_cycle:" + identifier]}
        if len(active) >= self.max_depth:
            return {"chain": [identifier], "errors": ["model_depth_limit:" + identifier]}
        if identifier in self.cache:
            cached = self.cache[identifier]
            if len(active) + len(cached["chain"]) > self.max_depth:
                return {"chain": [identifier], "errors": ["model_depth_limit:" + identifier]}
            return cached
        if identifier.startswith("minecraft:builtin/"):
            return {"chain": [identifier], "builtin": identifier, "errors": []}
        if identifier not in self.models:
            return {"chain": [identifier], "errors": ["broken_model_reference:" + identifier]}
        own = self.models[identifier]["data"]
        parent = self.resolve(own["parent"], (*active, identifier)) if own.get("parent") else {}
        result = {**parent, **own, "chain": [identifier, *parent.get("chain", [])],
                  "textures": {**parent.get("textures", {}), **own.get("textures", {})},
                  "display": {**parent.get("display", {}), **own.get("display", {})},
                  "errors": parent.get("errors", [])}
        if not result["errors"]: self.cache[identifier] = result
        return result


class ComplexityAnalyzer:
    def __init__(self, models, textures, sprites, max_depth=64):
        self.graph = ModelGraph(models, max_depth)
        self.models, self.textures, self.sprites = models, textures, sprites
        self.max_depth = max_depth

    def analyze(self, item, definition):
        categories, required, references = set(), set(), {item["definition"]}
        evidence, chains, diagnostics = [], [], []
        node_types, special_types, tint_types, properties = set(), set(), set(), set()
        visited, active = set(), set()

        def reason(category, source, feature=None):
            categories.add(category)
            if feature: required.add(feature)
            row = {"category": category, "source": source}
            if row not in evidence: evidence.append(row)

        def texture(value, mapping, source):
            aliases = set()
            for _ in range(self.max_depth):
                if isinstance(value, dict): value = value.get("sprite")
                if not isinstance(value, str):
                    diagnostics.append("invalid_texture_value:" + source)
                    return None
                if not value.startswith("#"): return resource_id(value)
                key = value[1:]
                if key in aliases or key not in mapping:
                    diagnostics.append("texture_alias_cycle_or_missing:" + source + ":" + value)
                    return None
                aliases.add(key)
                value = mapping[key]
            diagnostics.append("texture_depth_limit:" + source)
            return None

        def model(identifier, source, branch, special_base=False):
            data = self.graph.resolve(identifier)
            diagnostics.extend(data["errors"])
            paths = [self.models[ref]["path"] if ref in self.models else ref for ref in data["chain"]]
            references.update(paths)
            chain = [*branch, *paths]
            mapping = data.get("textures", {})
            layers = [key for key in mapping if re.fullmatch(r"layer\d+", key)]
            if not special_base:
                if any(":block/" in ref for ref in data["chain"]): reason("block_model", source, "model_geometry")
                if data.get("elements"): reason("geometry", source, "model_geometry")
                if len(layers) > 1: reason("multiple_layers", source, "texture_layers")
                if not data.get("elements") and data.get("builtin") != "minecraft:builtin/generated" and not data["errors"]:
                    reason("empty_model", source, "empty_model")
            gui = data.get("display", {}).get("gui", {})
            if any(gui.get(k, default) != default for k, default in
                   (("rotation", [0, 0, 0]), ("translation", [0, 0, 0]), ("scale", [1, 1, 1]))):
                reason("gui_transform", source, None if special_base else "model_geometry")
            if data.get("overrides"): reason("legacy_overrides", source, "state_dispatch")
            for key, value in mapping.items():
                # Particle slots are evidence only; they are not inventory requirements.
                if isinstance(value, dict) and set(value) - {"sprite"} and key != "particle":
                    reason("material_options", source, None if special_base else "model_geometry")
                before = len(diagnostics)
                sprite = texture(value, mapping, source + "/textures/" + key)
                if key == "particle":
                    del diagnostics[before:]
                    continue
                if not sprite: continue
                if sprite in self.textures:
                    path = self.textures[sprite]["path"]
                    references.add(path)
                    chain.append(path)
                    if self.textures[sprite].get("animated"):
                        reason("animated_texture", source, "texture_animation")
                elif sprite in self.sprites:
                    references.add(self.sprites[sprite]["atlas"])
                    references.add("sprite:" + sprite)
                    reason("generated_sprite", source, "atlas_sprites")
                elif sprite != "minecraft:missingno":
                    diagnostics.append("broken_texture_reference:" + sprite)
            # Face texture strings are slot names, with optional #. This is
            # confirmed by official TextureSlots.getMaterial(String) bytecode.
            for element in data.get("elements", []):
                for face in element.get("faces", {}).values():
                    slot = face.get("texture", "").lstrip("#")
                    if slot and slot not in mapping:
                        diagnostics.append("broken_face_slot:" + source + ":" + slot)
                    if face.get("tintindex", -1) >= 0:
                        reason("tinted_faces", source, None if special_base else "tints")
            if set(data) - {"parent", "textures", "elements", "display", "gui_light", "ambientocclusion",
                            "overrides", "texture_size", "builtin", "chain", "errors"}:
                reason("unknown_model_fields", source, "unknown_semantics")
            if data.get("builtin") == "minecraft:builtin/generated" and data.get("gui_light", "front") != "front":
                reason("gui_lighting", source, "model_geometry")
            chains.append(chain)

        def walk(node, source, branch, depth=0):
            if depth >= self.max_depth:
                diagnostics.append("definition_depth_limit:" + source)
                return
            if not isinstance(node, dict):
                diagnostics.append("invalid_definition_node:" + source)
                return
            if id(node) in active:
                diagnostics.append("definition_cycle:" + source)
                return
            if id(node) in visited: return
            visited.add(id(node)); active.add(id(node))
            kind = resource_id(node.get("type", "unknown"))
            node_types.add(kind)
            branch = [*branch, source + " [" + kind + "]"]
            if node.get("property"): properties.add(resource_id(node["property"]))
            if kind == "minecraft:model":
                if node.get("tints"):
                    reason("tinted", source, "tints")
                    tint_types.update(resource_id(t.get("type", "unknown")) for t in node["tints"])
                if isinstance(node.get("model"), str): model(node["model"], source, branch)
                else: diagnostics.append("missing_model_id:" + source)
            elif kind == "minecraft:special":
                reason("special_model", source, "special_models")
                subtype = resource_id(node.get("model", {}).get("type", "unknown"))
                special_types.add(subtype)
                references.add("special_renderer:" + subtype)
                if node.get("model", {}).get("texture"):
                    references.add("special_texture:" + resource_id(node["model"]["texture"]))
                if node.get("base"): model(node["base"], source + "/base", branch, True)
                else: diagnostics.append("missing_special_base:" + source)
            elif kind in ("minecraft:condition", "minecraft:select", "minecraft:range_dispatch"):
                reason(kind.split(":", 1)[1], source, "state_dispatch")
                if kind == "minecraft:condition":
                    for key in ("on_false", "on_true"):
                        if key in node: walk(node[key], source + "/" + key, branch, depth + 1)
                        else: diagnostics.append("missing_branch:" + source + "/" + key)
                else:
                    if "fallback" in node: walk(node["fallback"], source + "/fallback", branch, depth + 1)
                    for key in ("cases", "entries"):
                        for index, entry in enumerate(node.get(key, [])):
                            walk(entry.get("model"), f"{source}/{key}/{index}/model", branch, depth + 1)
            elif kind == "minecraft:composite":
                reason("composite", source, "composite_models")
                for index, child in enumerate(node.get("models", [])):
                    walk(child, f"{source}/models/{index}", branch, depth + 1)
            elif kind == "minecraft:bundle/selected_item": reason("bundle_selected_item", source, "bundle_contents")
            elif kind == "minecraft:empty": reason("empty_model", source, "empty_model")
            else: reason("unknown_definition_node", source, "unknown_semantics")
            active.remove(id(node))

        walk(definition.get("model"), item["definition"] + "#/model", [item["definition"]])
        if diagnostics: required.add("repair_references"); reason("reference_diagnostic", item["definition"])
        if item["iconStatus"] == "complex_model" and not categories:
            reason("unexplained_previous_classification", item["definition"], "unknown_semantics")
        # The legacy status remains compatible. Only audited complex definitions
        # enter coverage projections; simple items require no new capabilities.
        if item["iconStatus"] in ("direct", "model_resolved") and required:
            diagnostics.append("legacy_simple_status_has_additional_requirements")
        priority = ("special_model", "block_model", "geometry", "bundle_selected_item", "select", "condition",
                    "range_dispatch", "composite", "tinted", "multiple_layers", "gui_transform", "empty_model")
        primary = next((category for category in priority if category in categories), next(iter(sorted(categories)), None))
        return {"id": item["id"], "primaryReason": primary, "reasons": sorted(categories),
                "requiredFeatures": sorted(required), "definition": item["definition"],
                "references": sorted(references), "mainReferenceChain": chains[0] if chains else [item["definition"]],
                "referenceChains": chains, "evidence": evidence, "diagnostics": sorted(set(diagnostics)),
                "definitionNodeTypes": sorted(node_types), "specialRendererTypes": sorted(special_types),
                "tintTypes": sorted(tint_types), "dynamicProperties": sorted(properties)}


def project_coverage(registry, analyses):
    selected = {r["id"] for r in registry if r["selectable"]}
    currently = {r["id"] for r in registry if r["selectable"] and r["icon"]["status"] in ("direct", "model_resolved")
                 and not analyses[r["id"]]["requiredFeatures"]}
    required = {i: set(analyses[i]["requiredFeatures"]) for i in selected - currently}
    blocked = {i for i, features in required.items() if features & {"unknown_semantics", "repair_references"}}
    features = sorted(set().union(*required.values()) - {"unknown_semantics", "repair_references"})
    single = [{"feature": f, "newItemsResolved": sum(req <= {f} and bool(req) for req in required.values()),
               "affectedItems": sum(f in req for req in required.values()),
               "itemIds": sorted(i for i, req in required.items() if req and req <= {f})}
              for f in features]
    single.sort(key=lambda row: (-row["newItemsResolved"], -row["affectedItems"], row["feature"]))
    enabled, covered, steps = set(), set(currently), []
    while len(covered | blocked) < len(selected):
        # Prefer the single capability with the highest marginal gain. Only
        # when none unlocks an item do we propose a necessary dependency bundle.
        candidates = {frozenset({f}) for f in features if f not in enabled}
        if not any(req and req <= enabled | addition for i, req in required.items()
                   if i not in covered | blocked for addition in candidates):
            candidates = {frozenset(req - enabled) for i, req in required.items() if i not in covered | blocked}
            candidates.discard(frozenset())
        if not candidates: break
        options = []
        for additions in candidates:
            new = {i for i, req in required.items() if i not in covered | blocked and req <= enabled | additions}
            options.append((additions, new))
        additions, new = sorted(options, key=lambda pair: (-len(pair[1]), len(pair[0]), sorted(pair[0])))[0]
        if not new: break
        enabled.update(additions); covered.update(new)
        steps.append({"featuresAdded": sorted(additions), "newItemsResolved": len(new), "itemIds": sorted(new),
                      "coverageAfter": len(covered), "coveragePercentAfter": round(100 * len(covered) / len(selected), 2)})
    return {"selectableItems": len(selected), "currentlyResolvable": len(currently),
            "currentCoveragePercent": round(100 * len(currently) / len(selected), 2) if selected else 0,
            "potentialFeatures": single, "incrementalPlan": steps,
            "unprojectedItems": sorted(selected - covered),
            "method": "Every branch must be supported. Greedy highest single-feature marginal gain; when all single gains are zero, highest-gain required dependency bundle (ties: fewer capabilities, then lexical order). Independent gains are separate; no double counting.",
            "scope": "Vanilla definition-level capability estimate, not rendered-image verification, effort estimate or arbitrary component/resource-pack coverage. Special renderers include base GUI/material handling. Bundle contents require support for the contained item."}


def human_report(version, registry, nonselectable, breakdown, coverage, checks, provenance):
    selected = [r for r in registry if r["selectable"]]
    icons = Counter(r["icon"]["status"] for r in selected)
    lines = [f"# Minecraft {version} Registry Audit", "", "## Registry", "",
             f"- Raw visual definitions: {len(registry)}",
             f"- Official registered items: {provenance['registeredItems']}",
             f"- Selectable items: {len(selected)}",
             f"- Block items selectable: {sum(r['isBlockItem'] for r in selected)}",
             f"- Normal items selectable: {sum(not r['isBlockItem'] for r in selected)}",
             f"- Non-selectable definitions: {len(nonselectable)}", "",
             "Fonte: client.jar oficial local, conferido com SHA-1 do metadata da release. "
             "Inspecao estatica de Items.<clinit>, helpers de registro, ItemIds/BlockItemIds, "
             "colecoes de cores/cobre, factories/lambdas e superclasses de Item. Nenhuma lista manual de IDs.", "",
             "`selectable` significa Item registrado que pode representar um stack nao vazio; inclui "
             "itens acessiveis por comandos, como spawner. Nao significa disponibilidade em survival "
             "nem presenca em abas creative. AIR e excluido porque ItemStack.isEmpty o trata como vazio. "
             "isBlockItem vem da hierarquia real da classe construida, nao do nome/textura.", "",
             f"Definicoes com registro confirmado: {sum(r['registered'] for r in registry)}; sem registro: "
             f"{sum(not r['registered'] for r in registry)}. IDs excluidos: {', '.join(r['id'] for r in nonselectable) or 'nenhum'}. "
             "Colecoes geram IDs reais; aliases de blocos "
             "em Item.BY_BLOCK nao criam novos IDs de item.", "",
             "## Icon coverage", "", *[f"- {k}: {icons[k]}" for k in ("direct", "model_resolved", "complex_model", "missing")],
             f"- Current usable icons: {coverage['currentlyResolvable']} / {coverage['selectableItems']} "
             f"({coverage['currentCoveragePercent']:.2f}%)", "",
             "## Complex model breakdown", "",
             f"Total bruto: {breakdown['total']}; selecionaveis: {breakdown['selectableTotal']}. "
             "Categorias se sobrepoem; NAO somar suas contagens. A tabela primaryReasons e exclusiva.", "",
             "| Categoria | Todas as definicoes | Selecionaveis |", "|---|---:|---:|",
             *[f"| {k} | {v['count']} | {v['selectableCount']} |" for k, v in breakdown["categories"].items()],
             "", "### Motivo principal (exclusivo)", "",
             *[f"- {k}: {v}" for k, v in breakdown["primaryReasons"].items()],
             "", "## Renderer opportunities", "", "Ganhos independentes em relacao aos icones atuais:", "",
             *[f"- {row['feature']}: +{row['newItemsResolved']} itens; afeta {row['affectedItems']} ao incluir dependencias."
               for row in coverage["potentialFeatures"]], "", "Plano incremental, sem contar itens duas vezes:", "",
             *[f"{n}. {' + '.join(row['featuresAdded'])}: +{row['newItemsResolved']}; total {row['coverageAfter']} "
               f"({row['coveragePercentAfter']}%)." for n, row in enumerate(coverage["incrementalPlan"], 1)], "",
             coverage["method"], "", coverage["scope"], "",
             "## Important item checks", "",
             "| ID | Registrado | Selectable | Kind | Status | Motivos |", "|---|---|---|---|---|---|",
             *[f"| {r['id']} | {r['registered']} | {r['selectable']} | {r['kind']} | {r['iconStatus']} | {', '.join(r['reasons']) or 'simples'} |" for r in checks], ""]
    for row in checks:
        lines.extend([f"### {row['id']}", "", " → ".join(f"`{ref}`" for ref in row["mainReferenceChain"]), ""])
    lines.extend(["## Findings", "",
        "- O catalogo anterior era visual e permaneceu intacto. AIR era corretamente complexo como modelo vazio, mas nao deve ser selecionavel.",
        "- Os motivos anteriores misturavam tipos de nos, tipos de tint e tipos de renderizadores. Esta auditoria os separa por contexto e detecta tint dentro de todos os ramos.",
        "- Animacao tambem e verificada em texturas de faces/blocos, nao apenas nas camadas generated verificadas anteriormente. Isso detalha dependencias sem mudar os iconStatus existentes.",
        "- heavy_core usa texture_size como metadata e faces com slots sem #; TextureSlots.getMaterial aceita nomes de slot com ou sem #. Nao e referencia quebrada.",
        "- 117 model_resolved sao texturas simples resolvidas por modelo, NAO 117 modelos multicamada suportados.",
        "- Modelos especiais usam base para contexto/GUI; sua geometria e tratada pelo renderer especial, evitando exigir dois renderizadores desnecessariamente na projecao.",
        "- Select/condition/range_dispatch sao analisados em todos os ramos. Nenhuma variante e escolhida arbitrariamente.",
        "- Nao houve rede, novo download/extracao, alteracao de exemplos, frontend ou renderer.",
        "- registry-provenance.json registra hashes das classes/metodos e a evidencia por ID; registry.json apenas referencia essa origem.",
        "- O adaptador de bytecode e deliberadamente limitado: estruturas futuras nao reconhecidas abortam. Nao e uma JVM, nem executa o jogo ou valida disponibilidade por feature flags.", ""])
    return "\n".join(lines)


def audit(version="26.2", project=PROJECT_ROOT):
    started = time.perf_counter()
    root = version_directory(project, version)
    catalog = root / "catalog"
    metadata = read_json(root / "metadata/version.json")
    if metadata.get("id") != version or metadata.get("type") != "release": raise SyncError("Metadata nao corresponde a release")
    if not verify_sha1(root / "raw/client.jar", metadata["downloads"]["client"]["sha1"]): raise SyncError("SHA-1 do client local invalido")
    LOG.info("Loading item definitions, models and textures...")
    items = read_json(catalog / "items.json")
    if len({r['id'] for r in items}) != len(items): raise SyncError("IDs visuais duplicados")
    definitions = {row["id"]: read_json(root / row["definition"]) for row in items}
    models, textures, sprites = (read_json(catalog / (name + ".json")) for name in ("models", "textures", "atlas-sprites"))
    LOG.info("Resolving official item registry from local class files...")
    with zipfile.ZipFile(root / "raw/client.jar") as archive:
        # Reject stale or edited base indices instead of attributing them to
        # the validated official JAR. Nothing is extracted or copied again.
        jar_definitions = {n for n in archive.namelist() if n.startswith("assets/") and "/items/" in n and n.endswith(".json")}
        if jar_definitions != {row["definition"] for row in items}:
            raise SyncError("O catalogo visual nao cobre exatamente as definicoes do JAR")
        for row in items:
            if json.loads(archive.read(row["definition"])) != definitions[row["id"]]:
                raise SyncError("Definicao local difere do JAR: " + row["id"])
        for model in models.values():
            if json.loads(archive.read(model["path"])) != model["data"]:
                raise SyncError("Indice de modelos difere do JAR: " + model["path"])
        registered, provenance = RegistryInspector(archive).inspect()
    provenance.update(version=version, clientSha1=metadata["downloads"]["client"]["sha1"],
                      registryEntries=registered, source="raw/client.jar")
    if registered.keys() - definitions.keys():
        raise SyncError("Registered IDs without visual definitions: " + ", ".join(sorted(registered.keys() - definitions.keys())))
    LOG.info("Analyzing %d definitions recursively...", len(items))
    analyzer = ComplexityAnalyzer(models, textures, sprites)
    analyses = {row["id"]: analyzer.analyze(row, definitions[row["id"]]) for row in items}
    registry, nonselectable = [], []
    for item in items:
        identifier = item["id"]
        source = registered.get(identifier)
        analysis = analyses[identifier]
        selectable = bool(source and source["selectable"])
        is_block = source["isBlockItem"] if source else False
        reason = source["selectableReason"] if source else "visual_definition_without_registration"
        row = {"id": identifier, "name": item["name"], "registered": source is not None,
               "selectable": selectable, "selectableReason": reason,
               "kind": ("block_item" if is_block else "item") if source else "visual_definition",
               "isBlockItem": is_block, "displayName": item["displayName"], "displayNamePtBr": item["displayNamePtBr"],
               "definition": item["definition"],
               "source": ("catalog/registry-provenance.json#/registryEntries/" + identifier.replace("~", "~0").replace("/", "~1")) if source else item["definition"],
               "icon": {"status": item["iconStatus"], "path": item["directTexture"],
                        "primaryReason": analysis["primaryReason"], "reasons": analysis["reasons"]}}
        registry.append(row)
        if not selectable:
            nonselectable.append({"id": identifier, "reason": reason, "registered": source is not None,
                                  "source": row["source"], "definition": item["definition"],
                                  "references": analysis["references"]})
    selected = {row["id"] for row in registry if row["selectable"]}
    complex_rows = [analyses[row["id"]] for row in items if row["iconStatus"] == "complex_model"]
    category_names = sorted({c for row in complex_rows for c in row["reasons"]})
    categories = {c: {"count": sum(c in row["reasons"] for row in complex_rows),
                      "selectableCount": sum(c in row["reasons"] and row["id"] in selected for row in complex_rows),
                      "items": [row["id"] for row in complex_rows if c in row["reasons"]]} for c in category_names}
    breakdown = {"total": len(complex_rows), "selectableTotal": sum(r["id"] in selected for r in complex_rows),
                 "categoriesOverlap": True, "categories": categories,
                 "primaryReasonPolicy": "Exclusive display priority: special, block, geometry, bundle, select, condition, range, composite, tint, layers, GUI, empty; otherwise lexical. Requirements retain every reason.",
                 "primaryReasons": dict(sorted(Counter(r["primaryReason"] for r in complex_rows).items())),
                 "items": complex_rows,
                 "diagnostics": [{"id": i, "diagnostics": a["diagnostics"]} for i, a in analyses.items() if a["diagnostics"]]}
    coverage = project_coverage(registry, analyses)
    requirements = {"scope": coverage["scope"], "features": [
        {"feature": status, "description": "Static single-layer texture lookup; no renderer implemented",
         "affectedItems": sum(r["selectable"] and r["icon"]["status"] == status for r in registry), "alreadySupported": True}
        for status in ("direct", "model_resolved")] + [
        {"feature": f, "description": FEATURES[f], "affectedItems": sum(f in analyses[i]["requiredFeatures"] for i in selected),
         "alreadySupported": False, "itemIds": sorted(i for i in selected if f in analyses[i]["requiredFeatures"])}
        for f in sorted({f for i in selected for f in analyses[i]["requiredFeatures"]})],
        "specialRendererTypes": sorted({t for i in selected for t in analyses[i]["specialRendererTypes"]}),
        "tintTypes": sorted({t for i in selected for t in analyses[i]["tintTypes"]}),
        "dynamicProperties": sorted({t for i in selected for t in analyses[i]["dynamicProperties"]})}
    by_id = {row["id"]: row for row in registry}
    checks = []
    for name in IMPORTANT:
        identifier = "minecraft:" + name
        if identifier not in by_id: raise SyncError("Required validation item missing: " + identifier)
        row, analysis = by_id[identifier], analyses[identifier]
        checks.append({"id": identifier, "registered": row["registered"], "selectable": row["selectable"],
                       "kind": row["kind"], "iconStatus": row["icon"]["status"],
                       "reasons": analysis["reasons"], "mainReferenceChain": analysis["mainReferenceChain"]})
    LOG.info("Generating reports...")
    outputs = {"registry": registry, "registry-provenance": provenance,
               "non-selectable-definitions": nonselectable, "complex-model-breakdown": breakdown,
               "renderer-requirements": requirements, "renderer-coverage": coverage, "important-item-checks": checks}
    for name, value in outputs.items(): write_json(catalog / (name + ".json"), value)
    (catalog / "AUDIT.md").write_text(human_report(version, registry, nonselectable, breakdown, coverage, checks, provenance), encoding="utf-8")
    LOG.info("Completed in %.2fs: %d definitions; %d selectable; %d block items; %d non-selectable",
             time.perf_counter() - started, len(items), len(selected), sum(r['isBlockItem'] for r in registry if r['selectable']), len(nonselectable))
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="26.2")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    LOG.info("Minecraft Java %s Registry Audit", args.version)
    try:
        audit(args.version)
    except (SyncError, OSError, ValueError, KeyError, TypeError, IndexError, RecursionError, zipfile.BadZipFile) as exc:
        LOG.error("Audit aborted: %s", exc, exc_info=args.verbose)
        return 1
    return 0


if __name__ == "__main__": raise SystemExit(main())
