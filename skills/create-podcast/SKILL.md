---
name: create-podcast
description: Develop a source-backed podcast script, review it, and prepare an audio production plan.
---

Create a listener-first podcast for the user's actual subject, audience, format, and chosen voices. Do not assume Breach Protocol's characters belong in someone else's show.

1. Research each story from primary sources; read full papers when making claims about them, not just abstracts. Separate confirmed facts, interpretation, disputes, and unknowns. Track source references for every segment.
2. Begin by explaining the subject and what happened. Give necessary context and causal sequence before interpretation. Explain technical terms; avoid filler, invented banter, unsupported claims, and padding. Multiple hosts should respond substantively with complete thoughts.
3. Assemble ordered segments with `title`, `sources` (references), and `turns` (objects with `speaker` and `text`). Run `podcast_check_script` to record exact segment fingerprints. Counts and source references do not validate factual claims.
4. Compare all specific claims against original sources, then review the complete script for clarity, source fidelity, opening, and substantive edits. Build a review object with `reviewer` and ordered `segments`; each segment has its matching `sha256` and notes `purpose`, `opening_check`, `source_check`, and `edits`. Run `podcast_check_review` after the final edit. A match is self-attested, not independent proof. Redo review for changed text.
5. Use an available and explicitly selected speech engine and authorized voices only. If using Higgs, account for its hardware cost and use supported delivery tags; keep tags out of listener-facing captions. If PageCast Director is installed, it can import text, assign passages to approved speaker voices, render bounded batches and export audio; inspect its passage assignments carefully, as its quote parser is not a podcast diarizer. Check generated audio against script, retry only failed portions, then mix and check loudness and timing. Do not claim audio was generated or verified when no engine ran.
6. Prepare descriptive show notes, source links and chapters from measured audio times. Keep outputs private until the user authorizes distribution; do not publish or upload automatically.
