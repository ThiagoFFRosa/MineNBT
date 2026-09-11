export type IconStatus = 'direct' | 'model_resolved' | 'complex_model';
export interface RegistryItem { id:string; name:string; selectable:boolean; kind:'item'|'block_item'; isBlockItem:boolean; displayName:string; displayNamePtBr:string; definition:string; icon:{status:IconStatus;path:string|null;primaryReason:string|null;reasons:string[]} }
export type Vec3=[number,number,number];
export interface ModelTransform { rotation?:Vec3;translation?:Vec3;scale?:Vec3 }
export interface ModelFace { uv?:[number,number,number,number]; texture:string; rotation?:number; tintindex?:number }
export interface ModelElement { from:Vec3; to:Vec3; rotation?:{origin:Vec3;axis:'x'|'y'|'z';angle:number;rescale?:boolean}; shade?:boolean; faces:Partial<Record<'down'|'up'|'north'|'south'|'west'|'east',ModelFace>> }
export interface VanillaModel { parent?:string; textures?:Record<string,string>; elements?:ModelElement[]; ambientocclusion?:boolean; display?:Record<string,ModelTransform> }
export interface ResolvedModel extends VanillaModel { textures:Record<string,string>; elements?:ModelElement[]; chain:string[] }
export type RenderPlan = {type:'direct'|'model_resolved';textureUrl:string;label:string}|{type:'geometry';model:ResolvedModel;label:string}|{type:'unsupported';reason:string;label:string;diagnostic?:string};
