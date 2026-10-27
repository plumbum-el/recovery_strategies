import { useEffect,useState } from 'react';
import { Badge,Button,Card } from 'react-bootstrap';
import { mockStrategies } from '../data/recovery_strategies_mock_data';
import { StrategyVideo } from '../components/recovery_strategies_media';
export function FeedPage({initialId}:{initialId:number|null}) {
 const initialIndex=Math.max(0,mockStrategies.findIndex(s=>s.id===initialId));
 const [index,setIndex]=useState(initialIndex);
 // При открытии карточки из плитки показываем именно выбранную стратегию.
 useEffect(()=>{if(initialId!==null){const found=mockStrategies.findIndex(s=>s.id===initialId);if(found>=0)setIndex(found)}},[initialId]);
 const strategy=mockStrategies[index];
 return <main className="page-content feed-page container"><div className="feed-head"><h1 className="page-heading">Лента стратегий</h1><span className="text-secondary">{index+1} / {mockStrategies.length}</span></div>
 <Card className="feed-card"><StrategyVideo src={strategy.video_url} poster={strategy.image_url}/><Card.Body><h2>{strategy.title}</h2><p>{strategy.short_description}</p><div className="d-flex gap-2 flex-wrap mb-3"><Badge bg="light" text="dark">⏱ {strategy.estimated_time} мин</Badge><Badge bg="light" text="dark">💰 {strategy.cost} ₽</Badge><Badge bg="light" text="dark">♡ {strategy.likes_count}</Badge></div>
 <div className="d-flex gap-2"><Button variant="info" onClick={()=>setIndex(i=>(i+1)%mockStrategies.length)}>Следующая →</Button></div></Card.Body></Card>
 </main>;
}
