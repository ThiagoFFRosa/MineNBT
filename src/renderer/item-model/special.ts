import { assetUrl } from '../../minecraft/assets/paths';
type SpecialResult={type:string;textureUrl:string};
export function resolveSpecialTexture(special:Record<string,unknown>):SpecialResult {
  const type=String(special.type).replace('minecraft:',''); const texture=String(special.texture??'');
  if(type==='shulker_box')return {type,textureUrl:assetUrl(`assets/minecraft/textures/entity/shulker/${texture.replace('minecraft:','')}.png`)};
  if(type==='chest')return {type,textureUrl:assetUrl(`assets/minecraft/textures/entity/chest/${texture.replace('minecraft:','')}.png`)};
  if(type==='player_head')return {type,textureUrl:assetUrl('assets/minecraft/textures/entity/player/wide/steve.png')};
  const heads:Record<string,string>={zombie:'zombie/zombie',creeper:'creeper/creeper',skeleton:'skeleton/skeleton',wither_skeleton:'skeleton/wither_skeleton',piglin:'piglin/piglin',dragon:'enderdragon/dragon'};
  if(type==='head'&&heads[String(special.kind)])return {type,textureUrl:assetUrl(`assets/minecraft/textures/entity/${heads[String(special.kind)]}.png`)};
  throw new Error(`Special renderer not available for minecraft:${type}`);
}
