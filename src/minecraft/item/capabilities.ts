import type { EditableItem } from './model';
export type ItemCapability = 'container'|'bundle'|'potion'|'book'|'firework'|'entity'|'profile'|'projectiles'|'trim'|'combat';
const shulker = /^minecraft:(?:\w+_)?shulker_box$/;
export function resolveCapabilities(item: Pick<EditableItem,'id'|'components'>): ItemCapability[] {
  const id=item.id, result=new Set<ItemCapability>();
  if (['minecraft:chest','minecraft:trapped_chest','minecraft:barrel'].includes(id)||shulker.test(id)||'minecraft:container' in item.components) result.add('container');
  if(id==='minecraft:bundle'||id.endsWith('_bundle')) result.add('bundle');
  if(/(?:potion|tipped_arrow)$/.test(id)) result.add('potion');
  if(id==='minecraft:written_book'||id==='minecraft:writable_book') result.add('book');
  if(id==='minecraft:firework_rocket'||id==='minecraft:firework_star') result.add('firework');
  if(id.endsWith('_spawn_egg')) result.add('entity');
  if(id==='minecraft:player_head') result.add('profile');
  if(id==='minecraft:crossbow') result.add('projectiles');
  if(/(?:helmet|chestplate|leggings|boots)$/.test(id)) result.add('trim');
  if(/(?:sword|axe|mace|bow|crossbow|trident)$/.test(id)) result.add('combat');
  return [...result];
}
