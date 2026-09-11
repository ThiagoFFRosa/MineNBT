import type { RegistryItem,RenderPlan } from '../../types/minecraft';
import { assetUrl,safeAssetPath } from '../../minecraft/assets/paths';
import { ModelResolver,fetchJson,resolveTexture,type JsonLoader } from '../models/modelResolver';
export class ItemRenderResolver{
 readonly models:ModelResolver; constructor(private load:JsonLoader=fetchJson){this.models=new ModelResolver(load)}
 async resolve(item:RegistryItem):Promise<RenderPlan>{try{
  if(item.icon.status==='direct'&&item.icon.path)return {type:'direct',textureUrl:assetUrl(item.icon.path),label:'Direct'};
  if(item.icon.status==='model_resolved'&&item.icon.path)return {type:'model_resolved',textureUrl:assetUrl(item.icon.path),label:'Resolved texture'};
  const definition=await this.load(item.definition) as {model?:{type?:string;model?:string;tints?:unknown[]}};const node=definition.model;
  if(node?.type!=='minecraft:model'||!node.model)return this.unsupported(item,node?.type);
  if(node.tints?.length)return {type:'unsupported',reason:'tint',label:'Unsupported · tint'};
  const model=await this.models.resolve(node.model);
  if(model.elements?.length)return {type:'geometry',model,label:'Geometry'};
  const layer=model.textures.layer0;if(layer)return {type:'model_resolved',textureUrl:safeAssetPath(resolveTexture(layer,model.textures)),label:'Resolved texture'};
  return {type:'unsupported',reason:'empty_model',label:'Unsupported · empty_model'};
 }catch(error){if((import.meta as ImportMeta & {env?:{DEV?:boolean}}).env?.DEV)console.warn(`Could not resolve ${item.id}`,error);return {type:'unsupported',reason:'invalid_asset',label:'Unsupported · invalid_asset',diagnostic:error instanceof Error?error.message:String(error)}}
 private unsupported(item:RegistryItem,type?:string):RenderPlan {let reason=item.icon.primaryReason??type?.replace('minecraft:','')??'unsupported_model';if(reason==='select'&&item.icon.reasons.includes('special_model'))reason='special_model';return {type:'unsupported',reason,label:`Unsupported · ${reason}`}}
}
export const itemRenderResolver=new ItemRenderResolver();
