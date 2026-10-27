import { useState } from 'react';
import { BottomNav } from './components/recovery_strategies_bottom_nav';
import type { Page } from './components/recovery_strategies_bottom_nav';
import { CatalogPage } from './pages/recovery_strategies_catalog_page';
import { FeedPage } from './pages/recovery_strategies_feed_page';
export default function App(){
 const [page,setPage]=useState<Page>('feed');
 const [selectedId,setSelectedId]=useState<number|null>(null);
 function openStrategy(id:number){setSelectedId(id);setPage('feed')}
 function navigate(next:Page){setSelectedId(null);setPage(next)}
 return <div className="app-shell"><header className="app-header"><span className="brand-mark">↻</span><span>Recovery <b>Strategies</b></span><small>ЛР №5 · React</small></header>
 {page==='feed'?<FeedPage initialId={selectedId}/>:<CatalogPage onOpen={openStrategy}/>}
 <BottomNav page={page} onNavigate={navigate}/></div>;
}
