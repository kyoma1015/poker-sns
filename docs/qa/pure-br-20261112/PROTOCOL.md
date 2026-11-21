# Pure BR policy extraction and independent realization, before full outcomes

Research HU50/noante/norake/same3size restrictedgame only. Protect frozenbaseline,
allold Q/S,oldZIP,cache and UI. Do not repeat completedlearning/oldsuccessfulCI.
Read-only baseline /workspace/joint-stream-run/frozen.sqlite; source/game/cache
and numeric hashes pinned. Two exact passes over all1755orbits/22100flops/9branches.

Pass1: newnative extractor computes flopargmax at legal OWN-private/public/history
information sets. Opponent private cards appear only in chance/payoff integration.
NO board-dependent preflop argmax: aggregate allcounterfactual leafvectors first,
then global preflop class169 BR. Stablefirstlegalaction tie-break. Save onlyonebyte
per information set andglobal169prechoices in newdurableSQLite; never fake R/S.
Temporarybaseline selected-action advantage/CFmass may go to independent/tmp;
it is reconstructable from immutablebaseline/cache. Compactpolicy cap64MiB,
temporarydiagnostics cap768MiB, bothfilesystems minimum2GiB free,onefiniteworker.
Pass1 max1755blocks/1800activewall seconds; atomiccursor/identity/budgetstop.

Pass2: evaluate SB-BR vs originalBB and originalSB vs BB-BR using ORIGINAL world
enumeration trainingkernel utility,not the newextractor. Compare realized gains
with stored independent baselineBR and newextractedvalue; tolerance1e-8BB.
Bothfullpopulation required for PASS. Max1755blocks/2400activewall seconds.

Pre-run refinement: protectedfrozen fullDBdigest differs from the historical
evaluation's fullstate digest (which includes metadata/evalcache). Do not assume
the difference is harmless. Pass1 therefore also runs originalworld BR on the
same currentbaseline andcompares allleaf/root values; same1800s cap,not reset.
Resume elapsedwall includes downtime conservatively; budgettimestamps neverreset.

Additive diagnostic: unilateral performance-difference identity,baseline advantage
(chance*opponentreach*(baselineQ-baselineV)) times OWN BRreach at eachinfoset.
Sum allpositive andnegative contributions; do not sum onlypositive rows or count
futuregain repeatedly. Independent check equals actualrootBRgain. Actualinfoset
reach = ownBRreach*opponentCFmass,weighted by trueboardmultiplicity. Aggregate
by owner/street/publichistory/hand/action andreporttoppositive/negative drivers.
This is attribution withinthisgame,not actualpoker exploitability or externalGTO.

Beforefullpass: two-board hidden-card explicitworlds,pureenumeration/independentBR,
commonprepolicy acrossboards, legalonehotchoices, zeroownreach,opponent-hidden-info
invariance,corruptstate/partialpopulation refusal,atomicresume andpreservedinputs.
No newfulllearningtrial until smallmatched-early-history comparison supports it
and durablecapacity proven. FrozenNC.932107152722 remainsbaseline,0.1research
target unchanged. Formal0/12/ordinary0; externalGTO/realgameerror UNKNOWN.
