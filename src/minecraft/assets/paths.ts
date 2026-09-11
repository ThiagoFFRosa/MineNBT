import { assetBaseUrl } from '../version';
const resource=/^(?:[a-z0-9_.-]+:)?[a-z0-9_./-]+$/;
export function safeAssetPath(relative:string) { if(!relative||relative.includes('..')||relative.startsWith('/')||!resource.test(relative)) throw new Error(`Unsafe asset path: ${relative}`); return `${assetBaseUrl}/${relative}`; }
export function resourceParts(id:string,kind:'models'|'textures') { if(id.includes('..')||id.startsWith('/')) throw new Error(`Unsafe resource id: ${id}`); const [namespace,value]=id.includes(':')?id.split(':',2):['minecraft',id]; if(!/^[a-z0-9_.-]+$/.test(namespace)||!resource.test(value)) throw new Error(`Invalid resource id: ${id}`); return {namespace,value,path:`assets/${namespace}/${kind}/${value}.${kind==='models'?'json':'png'}`}; }
export const assetUrl=(path:string)=>safeAssetPath(path);
