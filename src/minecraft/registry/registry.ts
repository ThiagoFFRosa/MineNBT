import rawRegistry from '../../../minecraft-assets/26.2/catalog/registry.json';
import type { RegistryItem } from '../../types/minecraft';

export const registry = (rawRegistry as RegistryItem[]).filter(item => item.selectable);
if ((import.meta as ImportMeta & {env?:{DEV?:boolean}}).env?.DEV && registry.length !== 1536) console.error(`Registry inválido: esperado 1536, encontrado ${registry.length}`);
export type ItemFilter='all'|'item'|'block_item';
export const normalizeSearch=(text:string)=>text.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase();
export function filterRegistry(items:RegistryItem[], query:string, filter:ItemFilter) {
 const needle=normalizeSearch(query.trim());
 return items.filter(i=>(filter==='all'||(filter==='item'?!i.isBlockItem:i.isBlockItem))&&(!needle||normalizeSearch(`${i.id} ${i.displayName} ${i.displayNamePtBr}`).includes(needle)));
}
