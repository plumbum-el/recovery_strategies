import { Badge, Card } from 'react-bootstrap';
import type { Strategy } from '../recovery_strategies_types';
import { StrategyImage } from './recovery_strategies_media';
export function StrategyCard({strategy,onOpen}:{strategy:Strategy;onOpen:(id:number)=>void}) {
 return <Card className="strategy-card h-100" onClick={()=>onOpen(strategy.id)} role="button" tabIndex={0} onKeyDown={e=>{if(e.key==='Enter')onOpen(strategy.id)}}>
  <StrategyImage src={strategy.image_url} alt={strategy.title} className="card-cover"/>
  <Card.Body><Card.Title>{strategy.title}</Card.Title><Card.Text className="small muted-clamp">{strategy.short_description}</Card.Text>
  <div className="d-flex gap-2 flex-wrap"><Badge bg="light" text="dark">⏱ {strategy.estimated_time} мин</Badge><Badge bg="light" text="dark">💰 {strategy.cost} ₽</Badge><Badge bg="light" text="dark">♡ {strategy.likes_count}</Badge></div></Card.Body>
 </Card>;
}
