export type ResourceLocation = `${string}:${string}`;
export type NbtPrimitive = string | number | boolean | null;
export type NbtValue = NbtPrimitive | NbtValue[] | Record<string, unknown>;

export interface TextComponent {
  text: string;
  color?: string;
  bold?: boolean;
  italic?: boolean;
  underlined?: boolean;
  strikethrough?: boolean;
  obfuscated?: boolean;
  extra?: TextComponent[];
}

export interface ContainerEntry { slot: number; item: EditableItem }
export interface ItemComponents { [id: string]: NbtValue | ContainerEntry[] }
export interface EditableItem { id: ResourceLocation; count: number; components: ItemComponents }
export interface NBTGenProject {
  version: 1;
  target: '26.2';
  rootType: 'item';
  rootObject: EditableItem;
  metadata: { name: string; createdAt: string; updatedAt: string };
}

export const createItem = (id: string, count = 1): EditableItem => ({
  id: (id.includes(':') ? id : `minecraft:${id}`) as ResourceLocation,
  count,
  components: {},
});

export const createProject = (item: EditableItem, name = 'Projeto sem título'): NBTGenProject => {
  const now = new Date().toISOString();
  return { version: 1, target: '26.2', rootType: 'item', rootObject: item, metadata: { name, createdAt: now, updatedAt: now } };
};

export function isEditableItem(value: unknown): value is EditableItem {
  if (!value || typeof value !== 'object') return false;
  const item = value as Record<string, unknown>;
  return typeof item.id === 'string' && item.id.includes(':') && Number.isFinite(item.count) && !!item.components && typeof item.components === 'object' && !Array.isArray(item.components);
}

export const containerEntries = (item: EditableItem): ContainerEntry[] =>
  (Array.isArray(item.components['minecraft:container']) ? item.components['minecraft:container'] : []) as ContainerEntry[];

export function setContainerSlot(item: EditableItem, slot: number, child?: EditableItem): EditableItem {
  const entries = containerEntries(item).filter(entry => entry.slot !== slot);
  if (child) entries.push({ slot, item: child });
  entries.sort((a, b) => a.slot - b.slot);
  const components = { ...item.components };
  if (entries.length) components['minecraft:container'] = entries;
  else delete components['minecraft:container'];
  return { ...item, components };
}

export function treeMetrics(root: EditableItem) {
  let totalItems = 0, maxDepth = 0;
  const visit = (item: EditableItem, depth: number) => {
    totalItems++; maxDepth = Math.max(maxDepth, depth);
    for (const entry of containerEntries(item)) visit(entry.item, depth + 1);
  };
  visit(root, 0);
  return { totalItems, maxDepth, estimatedBytes: new TextEncoder().encode(JSON.stringify(root)).length };
}
