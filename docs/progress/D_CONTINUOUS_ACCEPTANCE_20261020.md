# D continuous acceptance — recorded before changes
Base: 3ca87764e988cac588fef915d48823702a1a3326 (PR #13).
- When changing a result deep link, a previously opened share editor and caption must not follow the new result.
- A completed or rejected older save/share must not change a newer screen's status.
- Failed Q50 submission can retry with exactly 50 option IDs; no Q50 duplication.
- Mobile viewport renders 50-question flow, saved-result refresh, non-owner controls, PNG download and restart with no horizontal overflow.
- Preserve all 36 asset mappings, trait ceilings, classification/scoring and DB contracts. Existing 40 fixture tests remain required.
- Browser uses actual TSX with in-memory transport, blocks external requests and never uses DB credentials. This is not isolated-DB/auth QA.
