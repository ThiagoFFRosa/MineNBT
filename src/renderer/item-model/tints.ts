import type { ItemRenderContext } from './context';
export function resolveTint(definition:Record<string,unknown>,context:ItemRenderContext):number {
  const type=String(definition.type??'');
  if(type==='minecraft:constant')return Number(definition.value)>>>0;
  if(type==='minecraft:potion'){const contents=context.components?.['minecraft:potion_contents'] as Record<string,unknown>|undefined;return Number(contents?.custom_color??definition.default)>>>0;}
  if(type==='minecraft:dye')return Number((context.components?.['minecraft:dyed_color'] as Record<string,unknown>|undefined)?.rgb??context.components?.['minecraft:dyed_color']??definition.default)>>>0;
  return Number(definition.default??0xffffff)>>>0;
}
