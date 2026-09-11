import { treeMetrics, type EditableItem } from './model';
export interface ValidationMessage { level:'warning'|'error'; message:string }
const known=new Set(['minecraft:custom_name','minecraft:item_name','minecraft:lore','minecraft:enchantments','minecraft:attribute_modifiers','minecraft:unbreakable','minecraft:damage','minecraft:max_damage','minecraft:max_stack_size','minecraft:repair_cost','minecraft:rarity','minecraft:enchantment_glint_override','minecraft:tooltip_display','minecraft:custom_data','minecraft:container','minecraft:trim','minecraft:potion_contents','minecraft:fireworks','minecraft:written_book_content','minecraft:writable_book_content','minecraft:entity_data','minecraft:profile','minecraft:charged_projectiles','minecraft:bundle_contents']);
export function validateItem(item:EditableItem):ValidationMessage[]{
 const messages:ValidationMessage[]=[];
 if(!item.id.includes(':'))messages.push({level:'error',message:'O ID precisa de namespace.'});
 if(item.count<1||item.count>64)messages.push({level:'warning',message:'Count fora dos limites normais do vanilla.'});
 for(const id of Object.keys(item.components))if(!known.has(id))messages.push({level:'warning',message:`Componente desconhecido preservado: ${id}`});
 const metrics=treeMetrics(item);if(metrics.maxDepth>8)messages.push({level:'warning',message:`Estrutura profunda (${metrics.maxDepth} níveis).`});
 if(metrics.totalItems>500)messages.push({level:'warning',message:`Estrutura grande (${metrics.totalItems} itens); nós são abertos sob demanda.`});
 return messages;
}
