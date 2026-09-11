#!/usr/bin/env python3
"""Offline coverage audit matching the frontend's generic resolution contract."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; VERSION='26.2'; VR=ROOT/'minecraft-assets'/VERSION
registry=json.loads((VR/'catalog/registry.json').read_text(encoding='utf8')); cache={}
def model(mid, seen=frozenset()):
    if mid in seen: raise ValueError('model parent cycle')
    ns,value=(mid.split(':',1) if ':' in mid else ('minecraft',mid))
    if '..' in value or value.startswith('/'): raise ValueError('unsafe model path')
    key=f'{ns}:{value}'
    if key in cache:return cache[key]
    own=json.loads((VR/'assets'/ns/'models'/f'{value}.json').read_text(encoding='utf8')); parent={}
    if own.get('parent') and not own['parent'].startswith('minecraft:builtin/'):parent=model(own['parent'],seen|{mid})
    merged={**parent,**own,'textures':{**parent.get('textures',{}),**own.get('textures',{})}}
    if 'elements' not in own and 'elements' in parent:merged['elements']=parent['elements']
    cache[key]=merged;return merged
def classify(item):
    status=item['icon']['status']
    if status in ('direct','model_resolved'):return status
    node=json.loads((VR/item['definition']).read_text(encoding='utf8')).get('model',{})
    if node.get('type')!='minecraft:model' or not node.get('model'):
        reason=item['icon'].get('primaryReason') or node.get('type','unsupported').removeprefix('minecraft:')
        if reason=='select' and 'special_model' in item['icon'].get('reasons',[]):reason='special_model'
        return 'unsupported',reason
    if node.get('tints'):return 'unsupported','tint'
    try: resolved=model(node['model'])
    except Exception:return 'unsupported','invalid_asset'
    if resolved.get('elements'):return 'geometry'
    if resolved.get('textures',{}).get('layer0'):return 'model_resolved'
    return 'unsupported','empty_model'
selectable=[x for x in registry if x['selectable']];counts=Counter();reasons=Counter();plans={}
for item in selectable:
    value=classify(item);kind,reason=(value if isinstance(value,tuple) else (value,None));counts[kind]+=1;plans[item['id']]={'renderer':kind,'status':reason or 'renderable'}
    if reason:reasons[reason]+=1
renderable=sum(counts[x] for x in ('direct','model_resolved','geometry'));golden=['minecraft:diamond_sword','minecraft:netherite_sword','minecraft:furnace','minecraft:spawner','minecraft:chest','minecraft:purple_shulker_box','minecraft:potion','minecraft:splash_potion','minecraft:bow','minecraft:crossbow','minecraft:bundle','minecraft:player_head','minecraft:written_book','minecraft:firework_rocket']
result={'minecraftVersion':VERSION,'generatedAt':datetime.now(timezone.utc).isoformat(),'totalSelectable':len(selectable),'structurallyRenderable':renderable,'unsupported':counts['unsupported'],'structuralCoveragePercent':round(renderable/len(selectable)*100,2),'runtimeVisualValidation':{'tested':0,'passed':0,'failed':0,'note':'Run /renderer-test in development; no whole-catalog visual rate is inferred.'},'breakdown':dict(counts),'unsupportedBreakdown':dict(reasons.most_common()),'goldenTests':{i:plans[i] for i in golden},'method':'Structural audit only: every selectable definition and complete model parent chain was parsed; geometry requires non-empty vanilla elements.'}
(ROOT/'frontend-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
