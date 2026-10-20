# Issue22 C acceptance — before implementation
Base PR20 / 8faea88802d0d34ae3e0319399e7f55ba71a9fcd.
Implement hand-derived synthetic settlement fixtures (ante priority, no-flop-no-drop,
uncalled refunds, side pots, dead-ante eligibility, odd chips, rounding and caps).
Replay legal actions against the preserved Python Betting reference and a separate
native binding of the exact G11 embedded Ledger used by all 3 solver variants.
Both implementations must match explicit expected chip results, not just each other.
Compare state/legal actions at every replay step and assert chip conservation.
No original G11 baseline or historical checkpoint is received/claimed. No original
source changes. Native dependency environment remains reconstructed/pinned.
Affected paths: gto/ only, C progress/evidence, native CI. No A/B/D/DB/prod changes.
