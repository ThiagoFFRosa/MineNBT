import type { ResolvedModel,VanillaModel } from '../../types/minecraft';
import { resourceParts,safeAssetPath } from '../../minecraft/assets/paths';
import { AsyncCache } from '../core/cache';
export type JsonLoader=(path:string)=>Promise<unknown>;
export const fetchJson:JsonLoader=async path=>{const response=await fetch(safeAssetPath(path));if(!response.ok)throw new Error(`${response.status} loading ${path}`);return response.json()};
export class ModelResolver {
 private raw:AsyncCache<VanillaModel>; private resolved=new Map<string,Promise<ResolvedModel>>();
 constructor(private load:JsonLoader=fetchJson){this.raw=new AsyncCache(async id=>this.load(resourceParts(id,'models').path) as Promise<VanillaModel>)}
 resolve(id:string){let found=this.resolved.get(id);if(!found){found=this.walk(id,new Set());this.resolved.set(id,found);found.catch(()=>this.resolved.delete(id));}return found}
 private async walk(id:string,visited:Set<string>):Promise<ResolvedModel>{if(visited.has(id))throw new Error(`Model parent cycle: ${[...visited,id].join(' -> ')}`);const next=new Set(visited).add(id);const own=await this.raw.get(id);let parent:ResolvedModel|undefined;if(own.parent&&!own.parent.startsWith('minecraft:builtin/'))parent=await this.walk(own.parent,next);return {...parent,...own,textures:{...(parent?.textures??{}),...(own.textures??{})},display:{...(parent?.display??{}),...(own.display??{})},elements:own.elements??parent?.elements,chain:[...(parent?.chain??[]),id]}}
 get cacheSize(){return this.raw.size}
}
export function resolveTexture(ref:string,textures:Record<string,string>){const seen=new Set<string>();let value=ref;while(value.startsWith('#')){const key=value.slice(1);if(seen.has(key))throw new Error(`Texture reference cycle: ${key}`);seen.add(key);value=textures[key];if(!value)throw new Error(`Missing texture variable #${key}`)}return resourceParts(value,'textures').path}
