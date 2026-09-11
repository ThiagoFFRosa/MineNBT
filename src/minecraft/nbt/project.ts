import { isEditableItem, type NBTGenProject } from '../item/model';
export const exportProjectJson=(project:NBTGenProject)=>JSON.stringify(project,null,2);
export function importProjectJson(text:string):NBTGenProject {const value=JSON.parse(text) as NBTGenProject;if(value.version!==1||value.target!=='26.2'||value.rootType!=='item'||!isEditableItem(value.rootObject))throw new Error('Projeto NBT GEN inválido ou incompatível');return value}
