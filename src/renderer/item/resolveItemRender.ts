import type { RegistryItem, RenderPlan, RenderLayer } from '../../types/minecraft';
import { assetUrl, safeAssetPath } from '../../minecraft/assets/paths';
import { defaultRenderContext, type ItemRenderContext } from '../item-model/context';
import { ItemModelEvaluator } from '../item-model/evaluator';
import { resolveSpecialTexture } from '../item-model/special';
import { resolveTint } from '../item-model/tints';
import { ModelResolver, fetchJson, resolveTexture, type JsonLoader } from '../models/modelResolver';

export class ItemRenderResolver {
  readonly models:ModelResolver; readonly evaluator=new ItemModelEvaluator();
  constructor(private load:JsonLoader=fetchJson){this.models=new ModelResolver(load);}
  async resolve(item:RegistryItem,provided?:Partial<ItemRenderContext>):Promise<RenderPlan>{
    const context={...defaultRenderContext(item.id),...provided,itemId:item.id};
    try {
      if(item.icon.status==='direct'&&item.icon.path)return {type:'direct',textureUrl:assetUrl(item.icon.path),label:'Direct'};
      if(item.icon.status==='model_resolved'&&item.icon.path)return {type:'model_resolved',textureUrl:assetUrl(item.icon.path),label:'Resolved texture'};
      const definition=await this.load(item.definition) as {model?:Record<string,unknown>};
      if(!definition.model)throw new Error('Item definition has no model node');
      const graph=this.evaluator.evaluate(definition.model,context);
      const renderable=graph.nodes.filter(node=>node.kind!=='bundle-item');
      if(!renderable.length)throw new Error('Resolved graph contains no renderable nodes');
      if(renderable.length===1&&renderable[0].kind==='special'){
        const special=resolveSpecialTexture(renderable[0].special);return {type:'special',textureUrl:special.textureUrl,specialType:special.type,label:`Special · ${special.type}`};
      }
      const layers:RenderLayer[]=[];
      for(const node of renderable){
        if(node.kind==='special')throw new Error('Composite special models are not yet supported');
        const model=await this.models.resolve(node.model);
        if(model.elements?.length&&renderable.length===1)return {type:'geometry',model,label:'Geometry'};
        for(let index=0;;index++){
          const ref=model.textures[`layer${index}`];if(!ref)break;
          layers.push({textureUrl:safeAssetPath(resolveTexture(ref,model.textures)),tint:node.tints[index]?resolveTint(node.tints[index],context):undefined});
        }
      }
      if(layers.length===1&&!layers[0].tint)return {type:'model_resolved',textureUrl:layers[0].textureUrl,label:'Resolved texture'};
      if(layers.length)return {type:'layers',layers,label:'Layered item model'};
      throw new Error('Resolved model has neither geometry nor texture layers');
    } catch(error){
      if((import.meta as ImportMeta&{env?:{DEV?:boolean}}).env?.DEV)console.warn(`Could not resolve ${item.id}`,error);
      return {type:'unsupported',reason:'render_error',label:'Render error',diagnostic:error instanceof Error?error.message:String(error)};
    }
  }
}
export const itemRenderResolver=new ItemRenderResolver();
