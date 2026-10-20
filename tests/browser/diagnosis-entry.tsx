import { createRoot } from 'react-dom/client'
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom'
import PlayerTypeDiagnosis from '../../src/PlayerTypeDiagnosis'
function Harness() {
  const navigate = useNavigate()
  const location = useLocation()
  return <><nav aria-label="Test navigation">
    <button onClick={() => navigate('/player-type?result=one')}>QA result one</button>
    <button onClick={() => navigate('/player-type?result=two')}>QA result two</button>
    <button onClick={() => navigate('/player-type?result=visitor')}>QA visitor</button>
  </nav><output data-testid="route">{location.pathname + location.search}</output><PlayerTypeDiagnosis /></>
}
const initial = new URLSearchParams(location.search).get('intro') ? '/player-type' : '/player-type?result=one'
createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={[initial]}><Harness /></MemoryRouter>)
