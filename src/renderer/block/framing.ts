import * as THREE from 'three';
import type { ModelElement, ModelTransform } from '../../types/minecraft';

export const FRAME_PADDING = 1.14;
const EPSILON = 1e-4;

export interface OrthographicFrame {
  center: THREE.Vector3;
  halfExtent: number;
  near: number;
  far: number;
}

/** Apply Minecraft's GUI transform without changing it to make the model fit. */
export function applyGuiTransform(root: THREE.Object3D, gui?: ModelTransform) {
  const rotation = gui?.rotation ?? [30, 225, 0];
  const translation = gui?.translation ?? [0, 0, 0];
  const scale = gui?.scale ?? [1, 1, 1];
  root.position.set(-8 + translation[0], -8 + translation[1], -8 + translation[2]);
  root.rotation.set(
    THREE.MathUtils.degToRad(rotation[0]),
    THREE.MathUtils.degToRad(rotation[1]),
    THREE.MathUtils.degToRad(rotation[2]),
  );
  root.scale.set(scale[0], scale[1], scale[2]);
}

/** Create an element around its true Minecraft rotation origin. */
export function createElementPivot(element: ModelElement, mesh: THREE.Object3D) {
  const center = new THREE.Vector3(
    (element.from[0] + element.to[0]) / 2,
    (element.from[1] + element.to[1]) / 2,
    (element.from[2] + element.to[2]) / 2,
  );
  if (!element.rotation) {
    mesh.position.copy(center);
    return mesh;
  }

  const { axis, angle, origin, rescale } = element.rotation;
  const pivot = new THREE.Group();
  pivot.position.fromArray(origin);
  mesh.position.copy(center).sub(pivot.position);
  pivot.rotation[axis] = THREE.MathUtils.degToRad(angle);
  if (rescale) {
    const correction = 1 / Math.max(Math.abs(Math.cos(THREE.MathUtils.degToRad(angle))), EPSILON);
    if (axis !== 'x') mesh.scale.x = correction;
    if (axis !== 'y') mesh.scale.y = correction;
    if (axis !== 'z') mesh.scale.z = correction;
  }
  pivot.add(mesh);
  return pivot;
}

export function calculateBounds(object: THREE.Object3D) {
  object.updateMatrixWorld(true);
  return new THREE.Box3().setFromObject(object, true);
}

/** Frame the final, world-transformed model in the camera's projected X/Y plane. */
export function calculateOrthographicFrame(bounds: THREE.Box3, padding = FRAME_PADDING): OrthographicFrame {
  if (bounds.isEmpty()) throw new Error('Cannot frame empty geometry');
  const center = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3());
  const projectedExtent = Math.max(size.x, size.y, EPSILON);
  const depth = Math.max(size.z, EPSILON);
  return {
    center,
    halfExtent: (projectedExtent * Math.max(padding, 1)) / 2,
    near: 0.1,
    far: Math.max(10, depth * 4 + 2),
  };
}
