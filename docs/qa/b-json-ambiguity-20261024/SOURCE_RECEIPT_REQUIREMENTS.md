# Official-corpus receipt / per-clause review contract

Status: BLOCKED. No new official350-question corpus, key, editioned official text,
Japanese translation or row-by-row review proof has been received in this batch.
The preceding scoped source search is retained at
`../b-answer-conflict-20261023/source-search.json`; it is not proof of global absence.
This batch does not repeat an identical GitHub tree fetch or connect to production.

To enable review, provide immutable local files and an independently recorded ledger:
- Published question export,350unique question IDs/1400options, exact byte SHA256.
- Correct-answer export keyed by those immutable question/option IDs, explanation
  and clause references, exact byte SHA256. Correct answers stay offline and must
  not be added to the public quiz RPC.
- Official original text: authoritative URL/publisher, rule edition/date/language,
  download date and original file SHA256. A URL alone is not received sourcebytes.
- Japanese translation: revision, author/publisher, source edition link, exact bytes
  and SHA256. Translation wording and official English must be reviewed separately.
- Review rows keyed by immutable question ID and original clause ID: original
  quote/location, translated quote/location, correct-option evidence, plausible
  multiple-answer/ambiguity candidates, reviewer/date and unresolved status.

Run on approved local copies:

    node scripts/tda-snapshot-audit.mjs questions.json answer-keys.json manifest.json

Manifest version1 requires exact `question_sha256`, `answer_key_sha256`,
`expected_question_count:350`, `expected_option_count:1400`.
The JSON must be unambiguous UTF8, finite-valued and within value nesting depth128 (root depth0).
Even a successful run says HASH_MATCH_NOT_PROVENANCE / official UNVERIFIED /
publication_approved:false. The CLI proves byte correspondence and structure,
not authenticity, correct Japanese translation, per-clause accuracy, a unique
correct answer or permission to publish. Those require independent review proof.
Never use a synthetic350fixture to fill these evidence gaps.
