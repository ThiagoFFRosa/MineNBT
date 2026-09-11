import {describe,expect,it} from 'vitest';
import {ItemModelEvaluator} from './evaluator';
import {defaultRenderContext,visualContextKey} from './context';
import {resolveSpecialTexture} from './special';
const evaluator=new ItemModelEvaluator();const model=(name:string)=>({type:'minecraft:model',model:name});
describe('ItemModelEvaluator',()=>{
 it('uses deterministic vanilla defaults for condition and select',()=>{
  expect(evaluator.evaluate({type:'minecraft:condition',property:'minecraft:using_item',on_true:model('pulling'),on_false:model('bow')},defaultRenderContext('minecraft:bow')).nodes[0]).toMatchObject({model:'bow'});
  expect(evaluator.evaluate({type:'minecraft:select',property:'minecraft:display_context',cases:[{when:'gui',model:model('bundle')}],fallback:model('other')},defaultRenderContext('minecraft:bundle')).nodes[0]).toMatchObject({model:'bundle'});
 });
 it('selects range entries at inclusive boundaries',()=>{const node={type:'minecraft:range_dispatch',property:'power',fallback:model('zero'),entries:[{threshold:.5,model:model('half')},{threshold:1,model:model('full')}]};expect(evaluator.evaluate(node,{itemId:'x',state:{power:.5}}).nodes[0]).toMatchObject({model:'half'});expect(evaluator.evaluate(node,{itemId:'x',state:{power:1}}).nodes[0]).toMatchObject({model:'full'});});
 it('flattens composites without inventing bundle contents',()=>expect(evaluator.evaluate({type:'minecraft:composite',models:[model('back'),{type:'minecraft:bundle/selected_item'},model('front')]},{itemId:'x'}).nodes.map(x=>x.kind)).toEqual(['model','bundle-item','model']));
 it('separates cache keys by visual state independent of key order',()=>{const a=visualContextKey({itemId:'x',state:{using:true,pull:1}});expect(a).toBe(visualContextKey({itemId:'x',state:{pull:1,using:true}}));expect(a).not.toBe(visualContextKey({itemId:'x',state:{pull:0,using:true}}));});
 it('resolves every shulker color through one special family',()=>expect(resolveSpecialTexture({type:'minecraft:shulker_box',texture:'minecraft:shulker_cyan'})).toMatchObject({type:'shulker_box',textureUrl:expect.stringContaining('shulker_cyan.png')}));
});
