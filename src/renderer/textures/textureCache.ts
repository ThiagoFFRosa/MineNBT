import * as THREE from 'three';
import { assetUrl } from '../../minecraft/assets/paths';
export class TextureCache {
 private loader=new THREE.TextureLoader(); private entries=new Map<string,Promise<THREE.Texture>>();
 load(path:string){let found=this.entries.get(path);if(!found){found=this.loader.loadAsync(assetUrl(path)).then(texture=>{texture.magFilter=THREE.NearestFilter;texture.minFilter=THREE.NearestFilter;texture.colorSpace=THREE.SRGBColorSpace;texture.flipY=false;return texture});this.entries.set(path,found);found.catch(()=>this.entries.delete(path));}return found}
 get size(){return this.entries.size}
 dispose(){for(const promise of this.entries.values())promise.then(t=>t.dispose());this.entries.clear()}
}
