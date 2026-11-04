import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { MemoryRouter, useNavigate, useLocation } from 'react-router-dom'
import PlayerTypeDiagnosis from '../../src/PlayerTypeDiagnosis'
function Harness() {
 const navigate=useNavigate(),location=useLocation()
 const [mounted,setMounted]=useState(true)
 return <><button onClick={()=>navigate('/player-type?result=qa-next')}>QA次結果</button><button onClick={()=>setMounted(false)}>QAアンマウント</button><output data-testid="qa-route">{location.pathname+location.search}</output>{mounted && <PlayerTypeDiagnosis />}</>
}
const mode=new URLSearchParams(window.location.search).get('mode')
createRoot(document.getElementById('root')!).render(<MemoryRouter initialEntries={[mode?.startsWith('questions') ? '/player-type' : '/player-type?result=qa-result']}><Harness /></MemoryRouter>)
