import { useState } from 'react';
import type { SyntheticEvent } from 'react';
export const DEFAULT_IMAGE = '/media/recovery_strategies_default_image.png';
export const DEFAULT_VIDEO = '/media/recovery_strategies_default_video.mp4';
export function StrategyImage({src,alt,className=''}:{src:string|null;alt:string;className?:string}) {
 const [failed,setFailed] = useState(false);
 return <img className={className} src={!src||failed?DEFAULT_IMAGE:src} alt={alt} onError={()=>setFailed(true)}/>;
}
export function StrategyVideo({src,poster}:{src:string|null;poster:string|null}) {
 const [failed,setFailed] = useState(false);
 const [posterFailed,setPosterFailed] = useState(false);
 const actualSrc = !src||failed?DEFAULT_VIDEO:src;
 const onError=(_event:SyntheticEvent<HTMLVideoElement>)=>{if(!failed)setFailed(true)};
 return <video key={actualSrc} className="strategy-video" controls muted playsInline preload="metadata" poster={!poster||posterFailed?DEFAULT_IMAGE:poster} onError={onError} onLoadedData={()=>setPosterFailed(false)}><source src={actualSrc} type="video/mp4"/></video>;
}
