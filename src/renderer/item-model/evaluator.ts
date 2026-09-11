import type { ItemRenderContext } from './context';
import { propertyValue } from './properties';

export type ItemModelNode=Record<string,unknown>;
export type ResolvedItemNode={kind:'model';model:string;tints:Record<string,unknown>[]} | {kind:'special';base:string;special:ItemModelNode} | {kind:'bundle-item'};
export interface EvaluationResult {nodes:ResolvedItemNode[];trace:string[]}
export class ItemModelEvaluator {
  evaluate(node:ItemModelNode,context:ItemRenderContext):EvaluationResult {return this.walk(node,context,[]);}
  private walk(node:ItemModelNode,context:ItemRenderContext,trace:string[]):EvaluationResult {
    const type=String(node.type??''); const next=[...trace,type||'<missing>'];
    if(type==='minecraft:model')return {nodes:[{kind:'model',model:String(node.model),tints:(node.tints as Record<string,unknown>[]|undefined)??[]}],trace:next};
    if(type==='minecraft:special')return {nodes:[{kind:'special',base:String(node.base),special:(node.model as ItemModelNode)??{}}],trace:next};
    if(type==='minecraft:bundle/selected_item')return {nodes:[{kind:'bundle-item'}],trace:next};
    if(type==='minecraft:composite')return (node.models as ItemModelNode[]??[]).reduce<EvaluationResult>((out,child)=>{const result=this.walk(child,context,next);return {nodes:[...out.nodes,...result.nodes],trace:[...out.trace,...result.trace]};},{nodes:[],trace:next});
    if(type==='minecraft:condition'){const value=Boolean(propertyValue(String(node.property),node,context));return this.walk((value?node.on_true:node.on_false) as ItemModelNode,context,next);}
    if(type==='minecraft:select'){
      const value=propertyValue(String(node.property),node,context);const match=(node.cases as ItemModelNode[]??[]).find(entry=>(Array.isArray(entry.when)?entry.when:[entry.when]).includes(value));
      return this.walk(((match?.model??node.fallback) as ItemModelNode),context,next);
    }
    if(type==='minecraft:range_dispatch'){
      const raw=Number(propertyValue(String(node.property),node,context)??0)*Number(node.scale??1);let selected=node.fallback as ItemModelNode;
      for(const entry of (node.entries as ItemModelNode[]??[]))if(raw>=Number(entry.threshold))selected=entry.model as ItemModelNode;
      return this.walk(selected,context,next);
    }
    throw new Error(`Unsupported item model node ${type||'<missing>'}`);
  }
}
