import type { EditableItem } from '../item/model';import { stringifySnbt } from './snbt';
export function itemCommand(item:EditableItem,target='@p'){const componentEntries=Object.entries(item.components);const components=componentEntries.length?`[${componentEntries.map(([id,value])=>`${id}=${stringifySnbt(value)}`).join(',')}]`:'';return `/give ${target} ${item.id}${components} ${item.count}`}
