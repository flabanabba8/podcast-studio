# Podcast Studio

A Hermes skill for source-first podcast production, with tools that fingerprint structured dialogue and check that a self-attested editorial review covers the current text. Inspired by the Breach Protocol editorial workflow, generalized to any show and voice cast. It does not generate speech, verify claims, or upload content; use a separately configured speech tool for production. No account or credentials are required.

Each segment contains `title`, `sources` (a list of references), and `turns` (speaker/text objects). `podcast_check_script` returns hashes; `podcast_check_review` compares a review against the ordered segment hashes and checks for substantive notes. Neither tool independently reads sources or certifies that a review took place. After review, `podcast_pagecast_plan` produces import text and a paragraph-to-speaker map for the optional PageCast Director plugin; assign all resulting passage IDs manually after inspecting them, because a turn may split into multiple passages.

Example `podcast_check_script` input:

```json
{"segments":[{"title":"The experiment","sources":["https://example.org/paper"],"turns":[{"speaker":"Host A","text":"The researchers compared two approaches."},{"speaker":"Host B","text":"The comparison only covered one task."}]}]}
```

After checking the sources and reviewing the complete segment, copy its returned `sha256` into a review entry and add nonempty `purpose`, `opening_check`, `source_check`, and `edits` notes. Send those entries in order with a `reviewer` to `podcast_check_review`. Re-run the review if the script or its source references change.
