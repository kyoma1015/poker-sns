# B next reviewed scope — rendered rule fields

PR59 validates rule_number and title_ja. The same search rows still expose
summary/conclusion/explanation, string collections, related-rule links and
expandable English text directly to React. Invalid fields can throw during
rendering or masquerade as verified rule links. This follows the existing
read-only RPC boundary contract; it does not edit or approve TDA content.

Before state storage, reject present, non-null fields with wrong runtime types:
summary_ja/conclusion_ja/explanation_ja/title_en/body_en must be strings;
keywords_ja/examples_ja/cautions_ja must be arrays of strings; related_rules must
be an array of safe positive integer rule numbers. Missing/null optional fields
remain compatible with existing minimal result payloads. Keep title/number gates,
latest-request invalidation and fixed recoverable error copy. No raw payload echo.

Only source allowed: src/TDA.tsx. Fixed browser16 includes the previous9,
six malformed display-field cases and one rich valid rendering/English expansion
control. Saved-answer14 remain protected and unchanged. Root owns locked parent
node_modules and temporary browser/Vite caches. Tests never contact Supabase.
Official350 accuracy and real authentication/DB integration remain unverified.
