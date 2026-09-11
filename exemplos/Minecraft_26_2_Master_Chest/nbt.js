'use strict';

const fs = require('fs');
const zlib = require('zlib');

const TYPE = Symbol('nbtType');

const TAG = Object.freeze({
  end: 0,
  byte: 1,
  short: 2,
  int: 3,
  long: 4,
  float: 5,
  double: 6,
  byteArray: 7,
  string: 8,
  list: 9,
  compound: 10,
  intArray: 11,
  longArray: 12,
});

function typed(type, value) {
  return Object.freeze({ [TYPE]: type, value });
}

const byte = (value) => typed('byte', Number(value));
const short = (value) => typed('short', Number(value));
const int = (value) => typed('int', Number(value));
const long = (value) => typed('long', BigInt(value));
const float = (value) => typed('float', Number(value));
const double = (value) => typed('double', Number(value));

function typeOf(value) {
  if (value && typeof value === 'object' && value[TYPE]) {
    return TAG[value[TYPE]];
  }
  if (typeof value === 'string') return TAG.string;
  if (Array.isArray(value)) return TAG.list;
  if (value && typeof value === 'object') return TAG.compound;
  throw new TypeError(`Unsupported NBT value: ${String(value)}`);
}

function encodeString(value) {
  const data = Buffer.from(value, 'utf8');
  if (data.length > 65535) throw new RangeError('NBT string exceeds 65535 UTF-8 bytes');
  const length = Buffer.allocUnsafe(2);
  length.writeUInt16BE(data.length, 0);
  return Buffer.concat([length, data]);
}

function writePayload(value, tagType = typeOf(value)) {
  let buffer;
  switch (tagType) {
    case TAG.byte:
      buffer = Buffer.allocUnsafe(1);
      buffer.writeInt8(value.value, 0);
      return buffer;
    case TAG.short:
      buffer = Buffer.allocUnsafe(2);
      buffer.writeInt16BE(value.value, 0);
      return buffer;
    case TAG.int:
      buffer = Buffer.allocUnsafe(4);
      buffer.writeInt32BE(value.value, 0);
      return buffer;
    case TAG.long:
      buffer = Buffer.allocUnsafe(8);
      buffer.writeBigInt64BE(value.value, 0);
      return buffer;
    case TAG.float:
      buffer = Buffer.allocUnsafe(4);
      buffer.writeFloatBE(value.value, 0);
      return buffer;
    case TAG.double:
      buffer = Buffer.allocUnsafe(8);
      buffer.writeDoubleBE(value.value, 0);
      return buffer;
    case TAG.string:
      return encodeString(value);
    case TAG.list: {
      if (value.length === 0) {
        throw new Error('Empty lists need an explicit element type; this generator emits no empty lists');
      }
      const elementType = typeOf(value[0]);
      const header = Buffer.allocUnsafe(5);
      header.writeUInt8(elementType, 0);
      header.writeInt32BE(value.length, 1);
      const parts = [header];
      for (const entry of value) {
        if (typeOf(entry) !== elementType) throw new TypeError('NBT list contains mixed tag types');
        parts.push(writePayload(entry, elementType));
      }
      return Buffer.concat(parts);
    }
    case TAG.compound: {
      const parts = [];
      for (const [name, entry] of Object.entries(value)) {
        const entryType = typeOf(entry);
        parts.push(Buffer.from([entryType]), encodeString(name), writePayload(entry, entryType));
      }
      parts.push(Buffer.from([TAG.end]));
      return Buffer.concat(parts);
    }
    default:
      throw new Error(`NBT tag type ${tagType} is not implemented by the writer`);
  }
}

function encodeNbt(root, rootName = '') {
  if (typeOf(root) !== TAG.compound) throw new TypeError('The NBT root must be a compound');
  return Buffer.concat([Buffer.from([TAG.compound]), encodeString(rootName), writePayload(root, TAG.compound)]);
}

function writeGzipNbt(path, root, rootName = '') {
  const raw = encodeNbt(root, rootName);
  fs.writeFileSync(path, zlib.gzipSync(raw, { level: 9, mtime: 0 }));
}

function decodeNbt(input) {
  const buffer = input[0] === 0x1f && input[1] === 0x8b ? zlib.gunzipSync(input) : input;
  let offset = 0;

  function ensure(length) {
    if (offset + length > buffer.length) throw new Error('Unexpected end of NBT stream');
  }

  function readString() {
    ensure(2);
    const length = buffer.readUInt16BE(offset);
    offset += 2;
    ensure(length);
    const value = buffer.toString('utf8', offset, offset + length);
    offset += length;
    return value;
  }

  function readPayload(tagType) {
    let value;
    switch (tagType) {
      case TAG.byte:
        ensure(1);
        value = byte(buffer.readInt8(offset));
        offset += 1;
        return value;
      case TAG.short:
        ensure(2);
        value = short(buffer.readInt16BE(offset));
        offset += 2;
        return value;
      case TAG.int:
        ensure(4);
        value = int(buffer.readInt32BE(offset));
        offset += 4;
        return value;
      case TAG.long:
        ensure(8);
        value = long(buffer.readBigInt64BE(offset));
        offset += 8;
        return value;
      case TAG.float:
        ensure(4);
        value = float(buffer.readFloatBE(offset));
        offset += 4;
        return value;
      case TAG.double:
        ensure(8);
        value = double(buffer.readDoubleBE(offset));
        offset += 8;
        return value;
      case TAG.string:
        return readString();
      case TAG.list: {
        ensure(5);
        const elementType = buffer.readUInt8(offset);
        const length = buffer.readInt32BE(offset + 1);
        offset += 5;
        if (length < 0) throw new Error('Negative NBT list length');
        const list = [];
        for (let index = 0; index < length; index += 1) list.push(readPayload(elementType));
        return list;
      }
      case TAG.compound: {
        const compound = {};
        while (true) {
          ensure(1);
          const entryType = buffer.readUInt8(offset);
          offset += 1;
          if (entryType === TAG.end) break;
          const name = readString();
          compound[name] = readPayload(entryType);
        }
        return compound;
      }
      default:
        throw new Error(`NBT tag type ${tagType} is not implemented by the reader`);
    }
  }

  ensure(1);
  const rootType = buffer.readUInt8(offset);
  offset += 1;
  if (rootType !== TAG.compound) throw new Error(`Expected TAG_Compound root, found ${rootType}`);
  const rootName = readString();
  const root = readPayload(rootType);
  if (offset !== buffer.length) throw new Error(`Trailing bytes after NBT root: ${buffer.length - offset}`);
  return { root, rootName, compressed: input !== buffer };
}

function quote(value) {
  return JSON.stringify(value);
}

function formatDecimal(value) {
  if (!Number.isFinite(value)) throw new RangeError(`Non-finite NBT number: ${value}`);
  const rendered = String(value);
  return /[.eE]/.test(rendered) ? rendered : `${rendered}.0`;
}

function numericValue(value) {
  if (!value || typeof value !== 'object' || !value[TYPE]) {
    throw new TypeError('Expected a typed NBT numeric value');
  }
  return value.value;
}

function toSnbt(value, indent = 0) {
  if (value && typeof value === 'object' && value[TYPE]) {
    switch (value[TYPE]) {
      case 'byte': return `${value.value}b`;
      case 'short': return `${value.value}s`;
      case 'int': return `${value.value}`;
      case 'long': return `${value.value}L`;
      case 'float': return `${formatDecimal(value.value)}f`;
      case 'double': return `${formatDecimal(value.value)}d`;
      default: throw new Error(`Unsupported typed SNBT value: ${value[TYPE]}`);
    }
  }
  if (typeof value === 'string') return quote(value);
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]';
    const childIndent = ' '.repeat(indent + 4);
    const ownIndent = ' '.repeat(indent);
    return `[\n${value.map((entry) => `${childIndent}${toSnbt(entry, indent + 4)}`).join(',\n')}\n${ownIndent}]`;
  }
  if (value && typeof value === 'object') {
    const entries = Object.entries(value);
    if (entries.length === 0) return '{}';
    const childIndent = ' '.repeat(indent + 4);
    const ownIndent = ' '.repeat(indent);
    return `{\n${entries.map(([name, entry]) => `${childIndent}${quote(name)}: ${toSnbt(entry, indent + 4)}`).join(',\n')}\n${ownIndent}}`;
  }
  throw new TypeError(`Unsupported SNBT value: ${String(value)}`);
}

function numericValue(value) {
  if (!value || typeof value !== 'object' || !value[TYPE]) throw new TypeError('Expected typed NBT number');
  return value.value;
}

module.exports = {
  TAG,
  TYPE,
  byte,
  short,
  int,
  long,
  float,
  double,
  encodeNbt,
  writeGzipNbt,
  decodeNbt,
  toSnbt,
  numericValue,
};
