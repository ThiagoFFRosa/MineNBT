import type { RenderLayer } from '../../types/minecraft';
const load=(src:string)=>new Promise<HTMLImageElement>((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error(`Could not load texture ${src}`));image.src=src;});
export async function renderLayers(layers:RenderLayer[]):Promise<string>{
  const images=await Promise.all(layers.map(layer=>load(layer.textureUrl)));const size=Math.max(...images.map(image=>image.naturalWidth));const canvas=document.createElement('canvas');canvas.width=canvas.height=size;const context=canvas.getContext('2d');if(!context)throw new Error('Canvas 2D unavailable');context.imageSmoothingEnabled=false;
  for(let index=0;index<images.length;index++){const image=images[index],layer=layers[index];if(layer.tint===undefined){context.drawImage(image,0,0,size,size);continue;}const buffer=document.createElement('canvas');buffer.width=buffer.height=size;const paint=buffer.getContext('2d')!;paint.imageSmoothingEnabled=false;paint.drawImage(image,0,0,size,size);paint.globalCompositeOperation='source-in';paint.fillStyle=`#${(layer.tint&0xffffff).toString(16).padStart(6,'0')}`;paint.fillRect(0,0,size,size);context.drawImage(buffer,0,0);}
  return canvas.toDataURL('image/png');
}
