# D score container and descriptor boundary

Start:2e13863a056b0427ec41b894599cdf2641564de7, existing PR124/PR118 ancestry retained.
Fixed acceptance18: before9PASS/9FAIL; after18PASS/0FAIL. Existing53+5+6+14+6 regressions remain84PASS; combined102PASS.
Malformed score container formerly threw; inherited array row/custom prototype/hidden or symbol extra fields escaped schema; getter-backed axis executed. Now invalid container/entry/row emits INVALID_SCORE_ROW_SCHEMA and suppresses scoreDistribution/strategyReviewEvidence. Accessor test asserts zero getter calls. JSON own __proto__ rejected; Object.prototype unchanged.
Scope: offline audit ordinary JSON/plain objects and constructed test inputs. Arbitrary Proxy behavior and cross-realm objects are not a security sandbox guarantee. Null-prototype data rows remain compatible. Fixture/scores/classifier/UI/DB unchanged;9protected files match start byte-for-byte (protected.json).
Formal classifier/threshold/tie definitions/expert labels remainBLOCKED. Prior discovery: docs/qa/d-persona-reference-20261023/README.md; no new artifact supplied, so identical searches are not repeated. Historical960references and synthetic distribution do not prove36animal meaning/accuracy.
Existing branch only; no newPR/manualCI/mainmerge/production/heldstate/host/scheduler operations.
Validation: npm ci initial attempt failed network EPERM under restricted session; a single retry with explicit network permission succeeded (178packages/4s). npm run build and npm run lint bothPASS (existing warnings retained). Network-scoped git ls-remote confirms startHEAD equal remote. No credential/environment changes.
