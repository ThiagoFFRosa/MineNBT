import type { ItemRenderContext } from './context';

const get=(object:Record<string,unknown>|undefined,key:string)=>object?.[key]??object?.[key.replace('minecraft:','')];
export function propertyValue(property:string,node:Record<string,unknown>,context:ItemRenderContext):unknown {
  const explicit=get(context.state,property); if(explicit!==undefined)return explicit;
  const component=get(context.components,property); if(component!==undefined)return component;
  switch(property){
    case 'minecraft:display_context': return context.displayContext??'gui';
    case 'minecraft:local_time': {const date=new Date(context.time??'2000-01-01T12:00:00.000Z');const pattern=node.pattern==='MM-dd';return pattern?`${String(date.getUTCMonth()+1).padStart(2,'0')}-${String(date.getUTCDate()).padStart(2,'0')}`:date.toISOString();}
    case 'minecraft:bundle/has_selected_item': return false;
    case 'minecraft:using_item': case 'minecraft:fishing_rod/cast': case 'minecraft:broken': return false;
    case 'minecraft:charge_type': case 'minecraft:trim_material': case 'minecraft:block_state': return undefined;
    case 'minecraft:use_duration': case 'minecraft:use_cycle': case 'minecraft:crossbow/pull': case 'minecraft:compass': case 'minecraft:time': return 0;
    case 'minecraft:has_component': return get(context.components,String(node.component))!==undefined;
    default:return undefined;
  }
}
