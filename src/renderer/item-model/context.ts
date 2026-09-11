export interface ItemRenderContext {
  itemId:string;
  components?:Record<string,unknown>;
  count?:number;
  displayContext?:'gui';
  state?:Record<string,unknown>;
  /** Explicit time makes date-dependent models deterministic. */
  time?:Date|string|number;
}

export function defaultRenderContext(itemId:string):ItemRenderContext {
  return {itemId, count:1, displayContext:'gui', components:{}, state:{}, time:'2000-01-01T12:00:00.000Z'};
}

export function visualContextKey(context:ItemRenderContext):string {
  const visual={components:context.components??{},count:context.count??1,state:context.state??{},displayContext:context.displayContext??'gui',time:new Date(context.time??'2000-01-01T12:00:00.000Z').toISOString()};
  return `${context.itemId}:${stableStringify(visual)}`;
}
function stableStringify(value:unknown):string {
  if(Array.isArray(value))return `[${value.map(stableStringify).join(',')}]`;
  if(value&&typeof value==='object')return `{${Object.entries(value as Record<string,unknown>).sort(([a],[b])=>a.localeCompare(b)).map(([k,v])=>`${JSON.stringify(k)}:${stableStringify(v)}`).join(',')}}`;
  return JSON.stringify(value);
}
