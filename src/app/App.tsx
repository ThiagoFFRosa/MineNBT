import { useCallback,useEffect,useMemo,useState } from 'react';
import { LandingPage } from '../components/LandingPage';
import { EditorPage } from '../components/editor/EditorPage';
import { RendererTestPage } from '../components/RendererTestPage';
import type { NBTGenProject } from '../minecraft/item/model';
import './styles.css';

const navigate=(path:string)=>{history.pushState({},'',path);window.dispatchEvent(new PopStateEvent('popstate'))};
export default function App(){
 const [path,setPath]=useState(location.pathname);const [incoming,setIncoming]=useState<NBTGenProject>();
 useEffect(()=>{const listener=()=>setPath(location.pathname);addEventListener('popstate',listener);return()=>removeEventListener('popstate',listener)},[]);
 const openEditor=useCallback((project?:NBTGenProject)=>{setIncoming(project);navigate('/editor')},[]);
 if(import.meta.env.DEV&&path==='/renderer-test')return <RendererTestPage/>;
 if(path==='/editor')return <EditorPage initialProject={incoming} onHome={()=>navigate('/')}/>;
 return <LandingPage onCreate={()=>openEditor()} onImport={openEditor}/>;
}
