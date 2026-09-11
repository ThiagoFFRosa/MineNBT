"""Minimal read-only JVM class-file inspection for official registry evidence.

Not a Java VM or decompiler. Unsupported instructions fail closed.
"""
import struct


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, size):
        value = self.data[self.pos:self.pos + size]
        if len(value) != size:
            raise ValueError("Truncated class file")
        self.pos += size
        return value

    def u1(self): return self.take(1)[0]
    def u2(self): return struct.unpack(">H", self.take(2))[0]
    def u4(self): return struct.unpack(">I", self.take(4))[0]


class ClassFile:
    def __init__(self, data):
        r = Reader(data)
        if r.u4() != 0xCAFEBABE:
            raise ValueError("Invalid class magic")
        self.minor, self.major = r.u2(), r.u2()
        self.pool = [None] * r.u2()
        index = 1
        while index < len(self.pool):
            tag = r.u1()
            if tag == 1:
                value = r.take(r.u2()).decode("utf-8", errors="replace")
            elif tag in (7, 8, 16, 19, 20):
                value = r.u2()
            elif tag in (9, 10, 11, 12, 17, 18):
                value = (r.u2(), r.u2())
            elif tag == 15:
                value = (r.u1(), r.u2())
            elif tag in (3, 4):
                value = struct.unpack(">i" if tag == 3 else ">f", r.take(4))[0]
            elif tag in (5, 6):
                value = struct.unpack(">q" if tag == 5 else ">d", r.take(8))[0]
            else:
                raise ValueError(f"Unsupported constant pool tag {tag}")
            self.pool[index] = (tag, value)
            index += 2 if tag in (5, 6) else 1
        self.access = r.u2()
        self.name, self.parent = self.constant(r.u2()), self.constant(r.u2())
        self.interfaces = [self.constant(r.u2()) for _ in range(r.u2())]
        self.fields = self.members(r)
        self.methods = self.members(r)
        self.attributes = self.attributes_at(r)
        self.bootstraps = []
        if "BootstrapMethods" in self.attributes:
            b = Reader(self.attributes["BootstrapMethods"])
            for _ in range(b.u2()):
                handle = b.u2()
                self.bootstraps.append((handle, [b.u2() for _ in range(b.u2())]))

    def constant(self, index):
        if index == 0:
            return None
        tag, value = self.pool[index]
        if tag in (7, 8, 16):
            return self.constant(value)
        if tag in (9, 10, 11):
            owner, pair = value
            name, descriptor = self.pool[pair][1]
            return (self.constant(owner), self.constant(name), self.constant(descriptor))
        if tag in (17, 18):
            bootstrap, pair = value
            name, descriptor = self.pool[pair][1]
            return (bootstrap, self.constant(name), self.constant(descriptor))
        if tag == 15:
            return (value[0], self.constant(value[1]))
        return value

    def attributes_at(self, r):
        result = {}
        for _ in range(r.u2()):
            name = self.constant(r.u2())
            result[name] = r.take(r.u4())
        return result

    def members(self, r):
        result = {}
        for _ in range(r.u2()):
            access, name, descriptor = r.u2(), self.constant(r.u2()), self.constant(r.u2())
            attrs = self.attributes_at(r)
            entry = {"access": access, "name": name, "descriptor": descriptor, "attributes": attrs}
            if "Code" in attrs:
                c = Reader(attrs["Code"])
                entry["maxStack"], entry["maxLocals"] = c.u2(), c.u2()
                entry["code"] = c.take(c.u4())
                entry["exceptions"] = [c.take(8) for _ in range(c.u2())]
            result[name, descriptor] = entry
        return result


def instructions(code):
    """Decode instruction boundaries; variable-length switch/wide are supported."""
    sizes = {**{op: 1 for op in [0x10, 0x12, *range(0x15, 0x1a), *range(0x36, 0x3b), 0xa9, 0xbc]},
             **{op: 2 for op in [0x11, 0x13, 0x14, 0x84, *range(0x99, 0xa9),
                                 *range(0xb2, 0xb9), 0xbb, 0xbd, 0xc0, 0xc1, 0xc6, 0xc7]},
             0xb9: 4, 0xba: 4, 0xc5: 3, 0xc8: 4, 0xc9: 4}
    offset = 0
    while offset < len(code):
        start, op = offset, code[offset]
        offset += 1
        if op in (0xaa, 0xab):
            offset += (-offset) % 4
            if op == 0xaa:
                _, low, high = struct.unpack(">iii", code[offset:offset + 12])
                size = 12 + 4 * (high - low + 1)
            else:
                _, pairs = struct.unpack(">ii", code[offset:offset + 8])
                size = 8 + 8 * pairs
        elif op == 0xc4:
            size = 5 if code[offset] == 0x84 else 3
        else:
            size = sizes.get(op, 0)
        operand = code[offset:offset + size]
        if len(operand) != size:
            raise ValueError("Truncated JVM instruction")
        yield start, op, operand
        offset += size


def descriptor_types(descriptor):
    args, offset = [], 1
    while descriptor[offset] != ")":
        start = offset
        while descriptor[offset] == "[":
            offset += 1
        if descriptor[offset] == "L":
            offset = descriptor.index(";", offset) + 1
        else:
            offset += 1
        args.append(descriptor[start:offset])
    return args, descriptor[offset + 1:]
