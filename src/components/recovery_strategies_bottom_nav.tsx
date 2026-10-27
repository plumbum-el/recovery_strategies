import { Nav } from 'react-bootstrap';
export type Page='feed'|'catalog';
export function BottomNav({page,onNavigate}:{page:Page;onNavigate:(page:Page)=>void}) {
 return <Nav className="bottom-nav" justify variant="pills" aria-label="Нижнее меню">
  <Nav.Item><Nav.Link active={page==='feed'} onClick={()=>onNavigate('feed')}>▤<span>Лента</span></Nav.Link></Nav.Item>
  <Nav.Item><Nav.Link disabled title="Недоступно в ЛР5">＋<span>Добавление</span></Nav.Link></Nav.Item>
  <Nav.Item><Nav.Link active={page==='catalog'} onClick={()=>onNavigate('catalog')}>▦<span>Плитка</span></Nav.Link></Nav.Item>
  <Nav.Item><Nav.Link disabled title="Недоступно в ЛР5">♙<span>Вход</span></Nav.Link></Nav.Item>
 </Nav>;
}
