#!/usr/bin/env python3
"""Read-only asset coverage audit of the project's SNBT examples (not an NBT editor)."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re

from sync_minecraft_assets import PROJECT_ROOT, SyncError, read_json, resource_id, version_directory, write_json


class SnbtReader:
    """Small structural reader for the supplied examples; no commands are executed.

    Scalars stay strings, preserving suffixes. Not a general Minecraft validator.
    Structural parsing avoids counting entity/effect IDs or IDs inside book text.
    """
    def __init__(self, text: str):
        self.text, self.pos = text, 0

    def peek(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1
        return self.text[self.pos:self.pos + 1]

    def take(self, expected):
        if self.peek() != expected:
            raise ValueError(f"Expected {expected!r} at character {self.pos}")
        self.pos += 1

    def scalar(self, key=False):
        char = self.peek()
        if char in ('"', "'"):
            quote = char
            self.pos += 1
            chars = []
            while self.pos < len(self.text):
                char = self.text[self.pos]
                self.pos += 1
                if char == quote:
                    return "".join(chars)
                if char == "\\":
                    if self.pos >= len(self.text):
                        break
                    char = self.text[self.pos]
                    self.pos += 1
                    char = {"n": "\n", "r": "\r", "t": "\t"}.get(char, char)
                chars.append(char)
            raise ValueError("Unterminated string")
        start = self.pos
        stops = "{}[],;" + (":" if key else "")
        while self.pos < len(self.text) and not self.text[self.pos].isspace() and self.text[self.pos] not in stops:
            self.pos += 1
        if self.pos == start:
            raise ValueError(f"Expected scalar at character {self.pos}")
        return self.text[start:self.pos]

    def value(self):
        char = self.peek()
        if char == "{":
            self.take("{")
            result = {}
            while self.peek() != "}":
                key = self.scalar(key=True)
                self.take(":")
                if key in result:
                    raise ValueError(f"Duplicate key {key!r}")
                result[key] = self.value()
                if self.peek() != ",":
                    break
                self.take(",")
            self.take("}")
            return result
        if char == "[":
            self.take("[")
            self.peek()
            prefix = re.match(r"[BILbil]\s*;", self.text[self.pos:])
            if prefix:
                self.pos += len(prefix.group())
            result = []
            while self.peek() != "]":
                result.append(self.value())
                if self.peek() != ",":
                    break
                self.take(",")
            self.take("]")
            return result
        return self.scalar()

    def read(self):
        result = self.value()
        if self.peek():
            raise ValueError(f"Trailing content at character {self.pos}")
        return result


def inspect_stacks(value, stacks: Counter, models: Counter, components: Counter, depth=0) -> int:
    deepest = depth
    if isinstance(value, dict):
        is_stack = isinstance(value.get("id"), str) and ("count" in value or "Count" in value)
        if is_stack:
            stacks[resource_id(value["id"])] += 1
            own = value.get("components", {})
            if isinstance(own, dict):
                components.update(own.keys())
                override = own.get("minecraft:item_model")
                if isinstance(override, str):
                    models[resource_id(override)] += 1
            depth += 1
            deepest = depth
        for child in value.values():
            deepest = max(deepest, inspect_stacks(child, stacks, models, components, depth))
    elif isinstance(value, list):
        for child in value:
            deepest = max(deepest, inspect_stacks(child, stacks, models, components, depth))
    return deepest


def audit(examples: Path, catalog: list) -> dict:
    by_id = {item["id"]: item for item in catalog}
    stacks, overrides, components = Counter(), Counter(), Counter()
    files, failures = [], []
    max_depth = 0
    for path in sorted(examples.rglob("*.snbt")):
        local_stacks, local_models, local_components = Counter(), Counter(), Counter()
        try:
            root = SnbtReader(path.read_text(encoding="utf-8-sig")).read()
            depth = inspect_stacks(root, local_stacks, local_models, local_components)
            max_depth = max(max_depth, depth)
        except (ValueError, RecursionError) as exc:
            failures.append({"file": str(path.relative_to(examples)), "error": str(exc)})
            continue
        stacks.update(local_stacks)
        overrides.update(local_models)
        components.update(local_components)
        files.append({"file": path.relative_to(examples).as_posix(),
                      "itemStacks": sum(local_stacks.values()), "ids": sorted(local_stacks),
                      "itemModelOverrides": sorted(local_models), "stackNestingDepth": depth})
    def coverage(ids):
        return [{"id": identifier, "occurrences": count,
                 "iconStatus": by_id.get(identifier, {}).get("iconStatus", "not_catalogued"),
                 "definition": by_id.get(identifier, {}).get("definition")}
                for identifier, count in sorted(ids.items())]
    return {"source": str(examples.resolve()), "filesRead": len(files), "parseFailures": failures,
            "itemStacks": sum(stacks.values()), "uniqueItemIds": len(stacks),
            "maxStackNestingDepth": max_depth, "items": coverage(stacks),
            "itemModelOverrides": coverage(overrides), "componentsObserved": dict(sorted(components.items())),
            "notCatalogued": sorted((stacks.keys() | overrides.keys()) - by_id.keys()),
            "files": files,
            "limitations": ["Read-only SNBT structural coverage; binary .nbt uses its supplied .snbt counterpart.",
                            "Does not validate gameplay, component legality, commands or actual rendering."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="26.2")
    args = parser.parse_args()
    try:
        destination = version_directory(PROJECT_ROOT, args.version)
        report = audit(PROJECT_ROOT / "exemplos", read_json(destination / "catalog/items.json"))
        output = destination / "catalog/example-coverage.json"
        write_json(output, report)
        # Refresh total size after adding this optional audit.
        summary_path = destination / "catalog/report.json"
        summary = read_json(summary_path)
        for _ in range(4):
            size = sum(p.stat().st_size for p in destination.rglob("*") if p.is_file())
            if summary.get("totalBytes") == size:
                break
            summary["totalBytes"] = size
            write_json(summary_path, summary)
        print(f"SNBT files: {report['filesRead']}; stacks: {report['itemStacks']}; unique IDs: {report['uniqueItemIds']}")
        print(f"Missing: {report['notCatalogued']}; parse failures: {report['parseFailures']}")
        print(f"Report: {output}")
        return int(bool(report["notCatalogued"] or report["parseFailures"] or not report["filesRead"]))
    except (SyncError, OSError) as exc:
        print(f"Audit failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
