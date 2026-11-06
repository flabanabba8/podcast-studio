# Podcast Studio

A Hermes skill for source-first podcast production, with tools that fingerprint structured dialogue and check that a self-attested editorial review covers the current text. Inspired by the Breach Protocol editorial workflow, generalized to any show and voice cast. It does not generate speech, verify claims, or upload content; use a separately configured speech tool for production. No account or credentials are required.

Each segment contains `title`, `sources` (a list of references), and `turns` (speaker/text objects). `podcast_check_script` returns hashes; `podcast_check_review` compares a review against the ordered segment hashes and checks for substantive notes. Neither tool independently reads sources or certifies that a review took place.
