import { createRoot } from 'react-dom/client'
import { MemoryRouter, useNavigate } from 'react-router-dom'
import PlayerTypeDiagnosis from '../../src/PlayerTypeDiagnosis'
function Harness() { const navigate=useNavigate();return <><button onClick={()=>navigate('/player-type?result=qa-next')}>QA別の結果</button><PlayerTypeDiagnosis /></> }
createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={['/player-type?result=qa-result']}><Harness /></MemoryRouter>)
