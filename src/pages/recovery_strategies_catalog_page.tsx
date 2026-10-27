import { useMemo,useState } from 'react';
import { Alert,Col,Row } from 'react-bootstrap';
import { StrategyCard } from '../components/recovery_strategies_strategy_card';
import { StrategyFilter } from '../components/recovery_strategies_strategy_filter';
import type { FilterValues } from '../components/recovery_strategies_strategy_filter';
import { mockStrategies } from '../data/recovery_strategies_mock_data';
const initialFilters:FilterValues={search:'',minTime:'',maxTime:''};
export function CatalogPage({onOpen}:{onOpen:(id:number)=>void}) {
 const [filters,setFilters]=useState<FilterValues>(initialFilters);
 const filtered=useMemo(()=>mockStrategies.filter(s=>s.title.toLowerCase().includes(filters.search.trim().toLowerCase()) && (filters.minTime===''||s.estimated_time>=Number(filters.minTime)) && (filters.maxTime===''||s.estimated_time<=Number(filters.maxTime))),[filters]);
 return <main className="page-content container"><h1 className="page-heading">Стратегии восстановления</h1><p className="text-secondary">Каталог · данные из локальных mock-объектов</p>
 <StrategyFilter values={filters} onChange={setFilters} onReset={()=>setFilters(initialFilters)}/><p className="result-count">Найдено стратегий: {filtered.length}</p>
 {filtered.length===0?<Alert variant="secondary">По заданным параметрам стратегии не найдены.</Alert>:<Row className="g-3">{filtered.map(s=><Col key={s.id} xs={12} sm={6} lg={4}><StrategyCard strategy={s} onOpen={onOpen}/></Col>)}</Row>}
 </main>;
}
