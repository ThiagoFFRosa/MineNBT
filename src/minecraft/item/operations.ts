import type { EditableItem, NbtValue } from './model';
export type BulkOperation =
  | { type:'SET_COUNT'; count:number }
  | { type:'SET_COMPONENT'; id:string; value:NbtValue }
  | { type:'REMOVE_COMPONENT'; id:string };
export function applyOperation(item:EditableItem, operation:BulkOperation):EditableItem {
  if(operation.type==='SET_COUNT') return {...item,count:operation.count};
  const components={...item.components};
  if(operation.type==='SET_COMPONENT') components[operation.id]=operation.value;
  else delete components[operation.id];
  return {...item,components};
}
export const applyBulk=(items:EditableItem[],operation:BulkOperation)=>items.map(item=>applyOperation(item,operation));
