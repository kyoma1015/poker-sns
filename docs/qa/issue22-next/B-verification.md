# B saved answer integrity, 2026-10-21
Pinned baseline a22d64d4f6b10927ea2e98b70871de263ac6f477. Formal host agent /root/b_next.
Original source Boolean(is_correct) accepted string false as correct. Fixed strict persisted result parser; malformed save cannot score or submit twice. Protected acceptance14: baseline3FAIL, final14PASS; mobile mocked baseline fails new sixth case, final6PASS.
Executed: npm ci; all tests/*.test.mjs (138PASS); npm run build; npm run lint (48 existing warnings); CHROMIUM_PATH=/usr/bin/chromium node tests/browser/tda-quiz.mjs (6PASS). Mock transport, no production DB or official350 verification.
Source commit ade6ba2a3436277f4ea1d530da34eaf04801a295; controller result included. Root adds CI trigger/evidence only after controller finalization. Do not merge duplicate PR23/28 features separately without ancestry review.
