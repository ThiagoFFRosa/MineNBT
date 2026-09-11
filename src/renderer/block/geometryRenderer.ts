import * as THREE from 'three';
import type { ModelElement,ResolvedModel } from '../../types/minecraft';
import { resolveTexture } from '../models/modelResolver';
import { TextureCache } from '../textures/textureCache';

const materialOrder=['east','west','up','down','south','north'] as const;
export class GeometryPreviewRenderer {
 private renderer:THREE.WebGLRenderer|null=null; private textures=new TextureCache(); private cache=new Map<string,Promise<string>>();
 render(id:string,model:ResolvedModel,size=256){const key=`${id}@${size}`;let result=this.cache.get(key);if(!result){result=this.renderModel(model,size);this.cache.set(key,result);result.catch(()=>this.cache.delete(key));}return result}
 private async renderModel(model:ResolvedModel,size:number){
  if(!this.renderer)this.renderer=new THREE.WebGLRenderer({alpha:true,antialias:false,preserveDrawingBuffer:true,powerPreference:'low-power'});
  const renderer=this.renderer;renderer.setSize(size,size,false);renderer.setClearColor(0,0);renderer.outputColorSpace=THREE.SRGBColorSpace;
  const scene=new THREE.Scene(),root=new THREE.Group();scene.add(root);
  for(const element of model.elements??[])root.add(await this.elementMesh(element,model));
  root.position.set(-8,-8,-8);const gui=model.display?.gui;if(gui){const r=gui.rotation??[0,0,0];root.rotation.set(...r.map(THREE.MathUtils.degToRad) as [number,number,number]);const s=gui.scale??[1,1,1];root.scale.set(...s);const t=gui.translation??[0,0,0];root.position.add(new THREE.Vector3(...t));}else root.rotation.set(THREE.MathUtils.degToRad(30),THREE.MathUtils.degToRad(225),0);
  scene.add(new THREE.HemisphereLight(0xffffff,0x48516a,2.3));const light=new THREE.DirectionalLight(0xffffff,2.4);light.position.set(-20,30,40);scene.add(light);
  const camera=new THREE.OrthographicCamera(-12,12,12,-12,-100,100);camera.position.set(0,0,35);camera.lookAt(0,0,0);renderer.render(scene,camera);const url=renderer.domElement.toDataURL('image/png');
  scene.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();const materials=Array.isArray(o.material)?o.material:[o.material];for(const material of materials){if(material instanceof THREE.MeshLambertMaterial||material instanceof THREE.MeshBasicMaterial)material.map?.dispose();material.dispose()}}});return url;
 }
 private async elementMesh(element:ModelElement,model:ResolvedModel){const size=new THREE.Vector3(element.to[0]-element.from[0],element.to[1]-element.from[1],element.to[2]-element.from[2]);const geometry=new THREE.BoxGeometry(size.x,size.y,size.z);const materials=await Promise.all(materialOrder.map(async side=>{const face=element.faces[side];if(!face)return new THREE.MeshBasicMaterial({transparent:true,opacity:0});const texture=(await this.textures.load(resolveTexture(face.texture,model.textures))).clone();texture.needsUpdate=true;texture.wrapS=texture.wrapT=THREE.RepeatWrapping;if(face.uv){const [u1,v1,u2,v2]=face.uv;texture.repeat.set((u2-u1)/16,(v2-v1)/16);texture.offset.set(u1/16,v1/16)}if(face.rotation)texture.rotation=-THREE.MathUtils.degToRad(face.rotation);return new THREE.MeshLambertMaterial({map:texture,transparent:true,alphaTest:.05,side:THREE.DoubleSide,color:element.shade===false?0xffffff:0xf4f4f4})}));const mesh=new THREE.Mesh(geometry,materials);mesh.position.set((element.from[0]+element.to[0])/2,(element.from[1]+element.to[1])/2,(element.from[2]+element.to[2])/2);if(element.rotation){const {axis,angle,origin}=element.rotation;mesh.position.sub(new THREE.Vector3(...origin));mesh.rotation[axis]=THREE.MathUtils.degToRad(angle);mesh.position.add(new THREE.Vector3(...origin));}return mesh}
 get contextCount(){return this.renderer?1:0} get cachedPreviews(){return this.cache.size}
}
export const geometryPreviewRenderer=new GeometryPreviewRenderer();
