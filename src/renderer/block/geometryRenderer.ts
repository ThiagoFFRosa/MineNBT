import * as THREE from 'three';
import type { ModelElement, ResolvedModel } from '../../types/minecraft';
import { resolveTexture } from '../models/modelResolver';
import { TextureCache } from '../textures/textureCache';
import { applyGuiTransform, calculateBounds, calculateOrthographicFrame, createElementPivot } from './framing';

// BoxGeometry groups are +X, -X, +Y, -Y, +Z, -Z respectively.
const materialOrder = ['east', 'west', 'up', 'down', 'south', 'north'] as const;
export const GEOMETRY_PREVIEW_SIZE = 256;

export interface PixelDiagnostics {
  visibleBounds: { xMin:number; xMax:number; yMin:number; yMax:number } | null;
  occupancy: { widthPercent:number; heightPercent:number };
  minimumEdgePercent: number;
  empty: boolean;
  touchingEdge: boolean;
  tooSmall: boolean;
  status: 'OK'|'TOO SMALL'|'TOUCHING EDGE'|'EMPTY';
}

export function analyzePixels(data: Uint8ClampedArray, width:number, height:number, alphaThreshold=8):PixelDiagnostics {
  let xMin=width,yMin=height,xMax=-1,yMax=-1;
  for(let y=0;y<height;y++)for(let x=0;x<width;x++)if(data[(y*width+x)*4+3]>alphaThreshold){xMin=Math.min(xMin,x);xMax=Math.max(xMax,x);yMin=Math.min(yMin,y);yMax=Math.max(yMax,y)}
  const empty=xMax<0;
  const visibleBounds=empty?null:{xMin,xMax,yMin,yMax};
  const widthPercent=empty?0:(xMax-xMin+1)/width*100;
  const heightPercent=empty?0:(yMax-yMin+1)/height*100;
  const minimumEdgePercent=empty?0:Math.min(xMin,yMin,width-1-xMax,height-1-yMax)/Math.min(width,height)*100;
  const touchingEdge=!empty&&minimumEdgePercent<1;
  const tooSmall=!empty&&Math.max(widthPercent,heightPercent)<35;
  return {visibleBounds,occupancy:{widthPercent,heightPercent},minimumEdgePercent,empty,touchingEdge,tooSmall,status:empty?'EMPTY':touchingEdge?'TOUCHING EDGE':tooSmall?'TOO SMALL':'OK'};
}

export class GeometryPreviewRenderer {
  private renderer:THREE.WebGLRenderer|null=null;
  private textures=new TextureCache();
  private cache=new Map<string,Promise<string>>();
  private diagnostics=new Map<string,PixelDiagnostics>();

  render(id:string,model:ResolvedModel){
    const key=`${id}@${GEOMETRY_PREVIEW_SIZE}`;
    let result=this.cache.get(key);
    if(!result){result=this.renderModel(id,model);this.cache.set(key,result);result.catch(()=>this.cache.delete(key));}
    return result;
  }
  getDiagnostics(id:string){return this.diagnostics.get(`${id}@${GEOMETRY_PREVIEW_SIZE}`)}

  private async renderModel(id:string,model:ResolvedModel){
    if(!this.renderer)this.renderer=new THREE.WebGLRenderer({alpha:true,antialias:false,preserveDrawingBuffer:true,powerPreference:'low-power'});
    const renderer=this.renderer;
    renderer.setSize(GEOMETRY_PREVIEW_SIZE,GEOMETRY_PREVIEW_SIZE,false);
    renderer.setPixelRatio(1);
    renderer.setClearColor(0,0);
    renderer.outputColorSpace=THREE.SRGBColorSpace;
    const scene=new THREE.Scene(),root=new THREE.Group();scene.add(root);
    for(const element of model.elements??[])root.add(await this.elementMesh(element,model));
    applyGuiTransform(root,model.display?.gui);
    const bounds=calculateBounds(root);
    const frame=calculateOrthographicFrame(bounds);
    scene.add(new THREE.HemisphereLight(0xffffff,0x48516a,2.3));
    const light=new THREE.DirectionalLight(0xffffff,2.4);light.position.set(-20,30,40);scene.add(light);
    const camera=new THREE.OrthographicCamera(-frame.halfExtent,frame.halfExtent,frame.halfExtent,-frame.halfExtent,frame.near,frame.far);
    camera.position.set(frame.center.x,frame.center.y,frame.center.z+frame.far/2);
    camera.lookAt(frame.center);
    camera.updateProjectionMatrix();
    renderer.render(scene,camera);
    const url=renderer.domElement.toDataURL('image/png');
    const analysis=document.createElement('canvas');analysis.width=analysis.height=GEOMETRY_PREVIEW_SIZE;
    const context=analysis.getContext('2d',{willReadFrequently:true});
    if(context){context.drawImage(renderer.domElement,0,0);this.diagnostics.set(`${id}@${GEOMETRY_PREVIEW_SIZE}`,analyzePixels(context.getImageData(0,0,GEOMETRY_PREVIEW_SIZE,GEOMETRY_PREVIEW_SIZE).data,GEOMETRY_PREVIEW_SIZE,GEOMETRY_PREVIEW_SIZE));}
    scene.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();const materials=Array.isArray(o.material)?o.material:[o.material];for(const material of materials){if(material instanceof THREE.MeshLambertMaterial||material instanceof THREE.MeshBasicMaterial)material.map?.dispose();material.dispose();}}});
    return url;
  }

  private async elementMesh(element:ModelElement,model:ResolvedModel){
    const size=new THREE.Vector3(element.to[0]-element.from[0],element.to[1]-element.from[1],element.to[2]-element.from[2]);
    // Avoid invalid BoxGeometry normals/bounds for effectively flat vanilla elements.
    size.set(Math.max(size.x,1e-4),Math.max(size.y,1e-4),Math.max(size.z,1e-4));
    const geometry=new THREE.BoxGeometry(size.x,size.y,size.z);
    const materials=await Promise.all(materialOrder.map(async side=>{
      const face=element.faces[side];if(!face)return new THREE.MeshBasicMaterial({transparent:true,opacity:0});
      const texture=(await this.textures.load(resolveTexture(face.texture,model.textures))).clone();texture.needsUpdate=true;
      texture.wrapS=texture.wrapT=THREE.RepeatWrapping;
      if(face.uv){const [u1,v1,u2,v2]=face.uv;texture.repeat.set((u2-u1)/16,(v2-v1)/16);texture.offset.set(u1/16,v1/16)}
      if(face.rotation){texture.center.set(.5,.5);texture.rotation=-THREE.MathUtils.degToRad(face.rotation)}
      return new THREE.MeshLambertMaterial({map:texture,transparent:true,alphaTest:.05,side:THREE.DoubleSide,color:element.shade===false?0xffffff:0xf4f4f4});
    }));
    return createElementPivot(element,new THREE.Mesh(geometry,materials));
  }
  get contextCount(){return this.renderer?1:0}
  get cachedPreviews(){return this.cache.size}
}
export const geometryPreviewRenderer=new GeometryPreviewRenderer();
