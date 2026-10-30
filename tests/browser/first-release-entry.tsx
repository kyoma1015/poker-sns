import { createRoot } from 'react-dom/client'
import Candidate from '../../src/first-release-entry'
;(window as unknown as {firstReleaseStats:{mounts:string[]}}).firstReleaseStats={mounts:[]}
createRoot(document.getElementById('root')!).render(<Candidate />)
