"""Offline symbolic inspection of the official, named Minecraft registration code.

Straight-line JVM data flow and forward enum switches are inspected as Python data. No game code,
Java process, class constructor, native method or network request is executed.
Registry-sensitive operations reject unresolved values and unsupported control flow.
"""
from dataclasses import dataclass, field
import hashlib
import re
import struct

from minecraft_classfile import ClassFile, descriptor_types, instructions

ITEMS = "net/minecraft/world/item/Items"
ITEM = "net/minecraft/world/item/Item"
BLOCK_ITEM = "net/minecraft/world/item/BlockItem"
BLOCK_ID = "net/minecraft/references/BlockItemId"
KEY = "net/minecraft/resources/ResourceKey"
IDENTIFIER = "net/minecraft/resources/Identifier"
COLLECTIONS = {"net/minecraft/world/level/block/ColorCollection",
               "net/minecraft/world/level/block/WeatheringCopperCollection",
               "net/minecraft/world/level/block/WeatheringCopperCollection$ByState"}
KEY_SOURCES = {"net/minecraft/references/ItemIds", "net/minecraft/references/BlockItemIds",
               "net/minecraft/world/entity/EntityTypeIds",
               "net/minecraft/world/level/block/entity/DecoratedPotPatterns",
               "net/minecraft/world/item/JukeboxSongs", "net/minecraft/world/item/equipment/trim/TrimPatterns"}
DYE = "net/minecraft/world/item/DyeColor"


@dataclass
class Value:
    kind: str
    fields: dict = field(default_factory=dict)
    args: list = field(default_factory=list)


class RegistryInspector:
    def __init__(self, archive, max_depth=96):
        self.archive, self.max_depth = archive, max_depth
        self.classes, self.statics, self.initialized = {}, {}, set()
        self.active, self.records, self.method_evidence = [], {}, {}
        self.item_objects = {}
        self.site = None

    def cls(self, owner):
        if owner not in self.classes:
            self.classes[owner] = ClassFile(self.archive.read(owner + ".class"))
        return self.classes[owner]

    def initialize(self, owner):
        if owner not in self.initialized:
            self.initialized.add(owner)
            c = self.cls(owner)
            if ("<clinit>", "()V") in c.methods:
                self.evaluate(owner, "<clinit>", "()V", [])

    def static(self, owner, name, descriptor):
        key = owner, name
        if owner in KEY_SOURCES | COLLECTIONS | {DYE, ITEMS, "net/minecraft/world/level/block/ColorCollection$1"}:
            self.initialize(owner)
            if key not in self.statics:
                raise ValueError(f"Unresolved/cyclic static field: {owner}.{name}")
            return self.statics[key]
        return Value("field", {"reference": f"{owner}.{name}", "descriptor": descriptor})

    def remember(self, owner, name, descriptor):
        method = self.cls(owner).methods[name, descriptor]
        self.method_evidence[f"{owner}.{name}{descriptor}"] = hashlib.sha256(method.get("code", b"")).hexdigest()
        return method

    def evaluate(self, owner, name, descriptor, args, receiver=None):
        key = (owner, name, descriptor)
        if len(self.active) >= self.max_depth or key in self.active:
            raise ValueError(f"Registry call cycle/depth limit: {key}")
        self.active.append(key)
        previous_site = self.site
        try:
            method = self.remember(*key)
            if method.get("exceptions") and not owner.endswith("ColorCollection$1"):
                raise ValueError(f"Exception handlers unsupported in registry path: {key}")
            types, _ = descriptor_types(descriptor)
            locals_ = {} if method["access"] & 8 else {0: receiver}
            slot = len(locals_)
            for typ, value in zip(types, args):
                locals_[slot] = value
                slot += 2 if typ in ("J", "D") else 1
            stack = []
            c = self.cls(owner)
            jump_target = -1
            for offset, op, operand in instructions(method["code"]):
                if offset < jump_target: continue
                self.site = f"{owner}.{name}{descriptor}@{offset}"
                index = int.from_bytes(operand[:2], "big")
                if op == 0x00: pass
                elif op == 0x01: stack.append(None)
                elif 0x02 <= op <= 0x08: stack.append(op - 3)
                elif 0x09 <= op <= 0x0f: stack.append({9: 0, 10: 1, 11: 0., 12: 1., 13: 2., 14: 0., 15: 1.}[op])
                elif op in (0x10, 0x11): stack.append(int.from_bytes(operand, "big", signed=True))
                elif op in (0x12, 0x13, 0x14): stack.append(c.constant(index))
                elif 0x15 <= op <= 0x19: stack.append(locals_[index])
                elif 0x1a <= op <= 0x2d: stack.append(locals_[(op - 0x1a) % 4])
                elif 0x36 <= op <= 0x3a: locals_[index] = stack.pop()
                elif 0x3b <= op <= 0x4e: locals_[(op - 0x3b) % 4] = stack.pop()
                elif op == 0x57: stack.pop()
                elif op == 0x59: stack.append(stack[-1])
                elif op == 0xbb: stack.append(Value(c.constant(index)))
                elif op in (0xbc, 0xbd): stack.append([0 if op == 0xbc else None] * stack.pop())
                elif op in (0x4f, 0x53):
                    value, pos, array = stack.pop(), stack.pop(), stack.pop()
                    array[pos] = value
                elif op in (0x2e, 0x32):
                    pos, array = stack.pop(), stack.pop()
                    stack.append(array[pos])
                elif op == 0xbe: stack.append(len(stack.pop()))
                elif op == 0xb2:
                    stack.append(self.static(*c.constant(index)))
                elif op == 0xb3:
                    field_owner, field_name, _ = c.constant(index)
                    self.statics[field_owner, field_name] = stack.pop()
                elif op == 0xb4:
                    _, field_name, _ = c.constant(index)
                    value = stack.pop()
                    if value.kind == "field":
                        stack.append(Value("field", {"reference": value.fields["reference"] + "." + field_name}))
                    else:
                        stack.append(value.fields[field_name])
                elif op == 0xb5:
                    _, field_name, _ = c.constant(index)
                    value, obj = stack.pop(), stack.pop()
                    obj.fields[field_name] = value
                elif op in (0xb6, 0xb7, 0xb8, 0xb9, 0xba):
                    target, method_name, desc = c.constant(index)
                    arg_types, returns = descriptor_types(desc)
                    call_args = [stack.pop() for _ in arg_types][::-1]
                    obj = None if op in (0xb8, 0xba) else stack.pop()
                    if op == 0xba:
                        bootstrap, constants = c.bootstraps[target]
                        bootstrap_ref = c.constant(bootstrap)[1]
                        if bootstrap_ref[0] == "java/lang/invoke/LambdaMetafactory":
                            result = Value("lambda", {"handle": c.constant(constants[1]), "captured": call_args})
                        elif bootstrap_ref[0] == "java/lang/invoke/StringConcatFactory":
                            recipe = c.constant(constants[0])
                            parts = iter(call_args)
                            result = "".join(str(next(parts)) if ch == "\x01" else ch for ch in recipe)
                        else:
                            result = Value("opaque", {"bootstrap": bootstrap_ref})
                    else:
                        result = self.invoke(target, method_name, desc, call_args, obj)
                    if returns != "V": stack.append(result)
                elif op == 0xc0: pass  # checkcast preserves the symbolic value
                elif op == 0xa7:
                    jump_target = offset + int.from_bytes(operand, "big", signed=True)
                    if jump_target <= offset: raise ValueError("Backward branch unsupported in registry evidence")
                elif op == 0xaa:
                    default, low, high = struct.unpack(">iii", operand[:12])
                    selector = stack.pop()
                    delta = struct.unpack_from(">i", operand, 12 + 4 * (selector - low))[0] if low <= selector <= high else default
                    jump_target = offset + delta
                    if jump_target <= offset: raise ValueError("Backward switch unsupported")
                elif op in (0xac, 0xad, 0xae, 0xaf, 0xb0): return stack.pop()
                elif op == 0xb1:
                    if stack: raise ValueError(f"Nonempty stack at return: {self.site}")
                    return None
                else:
                    raise ValueError(f"Unsupported JVM opcode 0x{op:02x} at {self.site}; no registry guessed")
            raise ValueError(f"Missing method return: {key}")
        finally:
            self.active.pop()
            self.site = previous_site

    def apply(self, function, args):
        if not isinstance(function, Value) or function.kind != "lambda":
            raise ValueError("Unresolved registry factory")
        kind, (owner, name, desc) = function.fields["handle"]
        values = [*function.fields["captured"], *args]
        if kind == 8:
            obj = Value(owner)
            self.invoke(owner, name, desc, values, obj)
            return obj
        if kind in (5, 7, 9):
            return self.invoke(owner, name, desc, values[1:], values[0])
        if kind == 6:
            return self.invoke(owner, name, desc, values)
        raise ValueError(f"Unsupported method handle kind: {kind}")

    def invoke(self, owner, name, descriptor, args, receiver=None):
        if owner == "java/lang/Enum" and name == "<init>":
            receiver.fields.update(enumName=args[0], enumOrdinal=args[1])
            return None
        if owner == DYE and name == "ordinal": return receiver.fields["enumOrdinal"]
        if name == "clone" and isinstance(receiver, list): return list(receiver)
        if name == "apply" and isinstance(receiver, Value) and receiver.kind == "lambda":
            return self.apply(receiver, args)
        if owner == IDENTIFIER:
            self.remember(owner, name, descriptor)
            if name == "withDefaultNamespace": return "minecraft:" + args[0]
            if name in ("getPath", "path"): return receiver.split(":", 1)[1]
        if owner == KEY:
            self.remember(owner, name, descriptor)
            if name == "create": return args[1]
            if name in ("identifier", "location"): return receiver
            if name == "dependent":
                if not isinstance(receiver, str): raise ValueError("Unresolved resource key")
                suffix = args[1]
                if isinstance(suffix, str): return receiver + suffix
                namespace, path = receiver.split(":", 1)
                return namespace + ":" + self.apply(suffix, [path])
        if owner == ITEMS and name == "registerItem" and descriptor.startswith(
                "(Lnet/minecraft/resources/ResourceKey;Ljava/util/function/Function;Lnet/minecraft/world/item/Item$Properties;"):
            method = self.remember(owner, name, descriptor)
            calls = [self.cls(owner).constant(int.from_bytes(a[:2], "big"))
                     for _, op, a in instructions(method["code"]) if op == 0xb8]
            if not any(c[:2] == ("net/minecraft/core/Registry", "register") for c in calls):
                raise ValueError("Official registration terminal changed")
            identifier, factory, props = args
            if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9_.-]+:[a-z0-9_./-]+", identifier):
                raise ValueError(f"Unresolved item ID at {self.site}")
            obj = self.apply(factory, [props])
            if obj.kind == "opaque": raise ValueError(f"Unresolved factory for {identifier}: {obj.fields}")
            hierarchy = self.hierarchy(obj.kind)
            if ITEM not in hierarchy:
                raise ValueError(f"Factory is not an Item: {obj.kind}")
            if identifier in self.records:
                raise ValueError(f"Duplicate registration: {identifier}")
            self.records[identifier] = {"id": identifier, "class": obj.kind,
                                        "isBlockItem": BLOCK_ITEM in hierarchy,
                                        "classHierarchy": hierarchy,
                                        "registrationSite": self.site,
                                        "registrationChain": [f"{o}.{n}{d}" for o, n, d in self.active],
                                        "blockReferences": self.block_references(obj)}
            self.item_objects[id(obj)] = identifier
            return obj
        if owner == ITEMS and name == "registerBlock" and "[Lnet/minecraft/world/level/block/Block;" in descriptor:
            # The bytecode registers one item, then adds aliases to Item.BY_BLOCK.
            self.remember(owner, name, descriptor)
            result = self.invoke(owner, name, "(Lnet/minecraft/references/BlockItemId;Lnet/minecraft/world/level/block/Block;)Lnet/minecraft/world/item/Item;", args[:2])
            identifier = args[0].fields["item"]
            self.records[identifier]["blockAliases"] = [v.fields["reference"] for v in args[2]]
            return result
        if owner in KEY_SOURCES | COLLECTIONS | {BLOCK_ID, ITEMS, DYE}:
            return self.evaluate(owner, name, descriptor, args, receiver)
        returns = descriptor_types(descriptor)[1]
        if receiver is None and returns.startswith("Lnet/minecraft/world/item/") and name.startswith("create"):
            if ITEM in self.hierarchy(returns[1:-1]):
                return self.evaluate(owner, name, descriptor, args)
        # Item constructors/properties are opaque data, never game execution.
        # The actual constructor class, validated through its superclasses, is
        # enough to distinguish BlockItem from Item (including AirItem).
        if name == "<init>":
            if owner not in {"java/lang/Object", "java/lang/Record", "java/lang/Enum"}:
                receiver.args = args
            return None
        if receiver is not None and descriptor_types(descriptor)[1] == "L" + owner + ";":
            return receiver
        if owner.startswith("java/lang/") and name == "valueOf": return args[0]
        return Value("opaque", {"call": f"{owner}.{name}{descriptor}"}, args)

    def hierarchy(self, owner):
        result = []
        while owner and not owner.startswith("java/"):
            if owner in result or len(result) >= self.max_depth:
                raise ValueError("Class inheritance cycle/depth limit")
            result.append(owner)
            owner = self.cls(owner).parent
        return result

    def block_references(self, obj):
        result, visited = set(), set()
        def walk(value):
            if id(value) in visited: return
            visited.add(id(value))
            if isinstance(value, Value):
                ref = value.fields.get("reference", "")
                if ref.startswith("net/minecraft/world/level/block/Blocks."): result.add(ref)
                for v in [*value.fields.values(), *value.args]: walk(v)
            elif isinstance(value, (tuple, list)):
                for v in value: walk(v)
        walk(obj)
        return sorted(result)

    def inspect(self):
        self.initialize(ITEMS)
        # Verify the reason for excluding AIR from the main selector directly.
        c = self.cls("net/minecraft/world/item/ItemStack")
        method = self.remember(c.name, "isEmpty", "()Z")
        air_refs = [c.constant(int.from_bytes(a, "big")) for _, op, a in instructions(method["code"]) if op == 0xb2]
        if (ITEMS, "AIR", "Lnet/minecraft/world/item/Item;") not in air_refs:
            raise ValueError("ItemStack empty sentinel changed; selectable policy needs review")
        air = self.statics[ITEMS, "AIR"]
        empty_ids = [self.item_objects[id(air)]] if id(air) in self.item_objects else []
        if len(empty_ids) != 1:
            raise ValueError("Ambiguous empty ItemStack sentinel")
        for identifier, row in self.records.items():
            row["selectable"] = identifier not in empty_ids
            row["selectableReason"] = "registered_nonempty_item" if row["selectable"] else "ItemStack.isEmpty: AIR sentinel"
        return self.records, {
            "method": "static symbolic inspection of official named class files; no runtime execution",
            "classSha256": {name + ".class": hashlib.sha256(self.archive.read(name + ".class")).hexdigest()
                            for name in sorted(self.classes)},
            "methodCodeSha256": dict(sorted(self.method_evidence.items())),
            "registeredItems": len(self.records), "emptyItemIds": empty_ids,
            "selectablePolicy": "Registered Item other than the verified AIR/empty sentinel; includes command-only items. Not creative-tab membership.",
            "limitations": ["Version adapters cover the inspected named code structure; unsupported paths abort.",
                            "Properties and non-registry helper calls remain opaque; creative tabs and feature-flag availability are not evaluated."]}
