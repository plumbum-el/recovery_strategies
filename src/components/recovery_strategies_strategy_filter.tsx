import { Button, Col, Form, Row } from 'react-bootstrap';
export type FilterValues={search:string;minTime:string;maxTime:string};
export function StrategyFilter({values,onChange,onReset}:{values:FilterValues;onChange:(value:FilterValues)=>void;onReset:()=>void}) {
 return <Form className="filter-panel mb-4" onSubmit={e=>e.preventDefault()}><Row className="g-3 align-items-end">
  <Col md={6}><Form.Group><Form.Label>Поиск стратегии по названию</Form.Label><Form.Control placeholder="Например, репликация" value={values.search} onChange={e=>onChange({...values,search:e.target.value})}/></Form.Group></Col>
  <Col xs={6} md={2}><Form.Group><Form.Label>Время от, мин</Form.Label><Form.Control type="number" min="0" value={values.minTime} onChange={e=>onChange({...values,minTime:e.target.value})}/></Form.Group></Col>
  <Col xs={6} md={2}><Form.Group><Form.Label>Время до, мин</Form.Label><Form.Control type="number" min="0" value={values.maxTime} onChange={e=>onChange({...values,maxTime:e.target.value})}/></Form.Group></Col>
  <Col md={2}><Button variant="outline-secondary" className="w-100" onClick={onReset}>Сбросить</Button></Col>
 </Row></Form>;
}
