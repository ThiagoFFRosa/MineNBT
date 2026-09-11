import { describe,expect,it } from 'vitest';
import * as THREE from 'three';
import { applyGuiTransform,calculateBounds,calculateOrthographicFrame,createElementPivot,FRAME_PADDING } from './framing';
import { analyzePixels } from './geometryRenderer';
import type { ModelElement } from '../../types/minecraft';

const element=(overrides:Partial<ModelElement>={}):ModelElement=>({from:[0,0,0],to:[2,2,2],faces:{},...overrides});
describe('geometry framing',()=>{
  it('rotates an element around its declared pivot',()=>{const object=createElementPivot(element({rotation:{origin:[0,0,0],axis:'z',angle:90}}),new THREE.Object3D());object.updateMatrixWorld(true);const position=new THREE.Vector3();object.children[0].getWorldPosition(position);expect(position.x).toBeCloseTo(-1);expect(position.y).toBeCloseTo(1)});
  it('calculates world bounds after parent and GUI transforms',()=>{const root=new THREE.Group();root.add(new THREE.Mesh(new THREE.BoxGeometry(16,1,16)));applyGuiTransform(root,{rotation:[0,0,0],translation:[2,3,4],scale:[.5,2,1]});const size=calculateBounds(root).getSize(new THREE.Vector3());expect(size.toArray()).toEqual([8,2,16]);expect(root.position.toArray()).toEqual([-6,-5,-4])});
  it.each([['thin',new THREE.Box3(new THREE.Vector3(0,0,0),new THREE.Vector3(16,.001,16))],['tiny',new THREE.Box3(new THREE.Vector3(0,0,0),new THREE.Vector3(2,1,2))],['zero thickness',new THREE.Box3(new THREE.Vector3(0,0,0),new THREE.Vector3(16,0,16))]])('frames a %s model from projected width and height',(_name,bounds)=>{const frame=calculateOrthographicFrame(bounds);expect(frame.halfExtent).toBeCloseTo(8*FRAME_PADDING);for(const value of [...frame.center.toArray(),frame.halfExtent,frame.near,frame.far])expect(Number.isFinite(value)).toBe(true)});
  it('adds the configured camera margin',()=>{expect(calculateOrthographicFrame(new THREE.Box3(new THREE.Vector3(-5,-10,-1),new THREE.Vector3(5,10,1))).halfExtent).toBeCloseTo(10*FRAME_PADDING)});
  it('preserves explicit display rotation, translation, and scale',()=>{const root=new THREE.Group();applyGuiTransform(root,{rotation:[10,20,30],translation:[1,2,3],scale:[2,3,4]});expect(root.position.toArray()).toEqual([-7,-6,-5]);expect(root.scale.toArray()).toEqual([2,3,4]);expect(root.rotation.x).toBeCloseTo(THREE.MathUtils.degToRad(10))});
  it('diagnoses empty, edge-touching, and normally occupied pixels',()=>{expect(analyzePixels(new Uint8ClampedArray(4*4*4),4,4).status).toBe('EMPTY');const edge=new Uint8ClampedArray(4*4*4);edge[3]=255;expect(analyzePixels(edge,4,4).status).toBe('TOUCHING EDGE');const ok=new Uint8ClampedArray(100*100*4);for(let y=20;y<80;y++)for(let x=20;x<80;x++)ok[(y*100+x)*4+3]=255;expect(analyzePixels(ok,100,100).status).toBe('OK')});
});
