# Podcast Studio

A Hermes skill for source-first podcast production, with tools that fingerprint structured dialogue and check that a self-attested editorial review covers the current text. Inspired by the Breach Protocol editorial workflow, generalized to any show and voice cast. It does not generate speech, verify claims, or upload content; use a separately configured speech tool for production. No account or credentials are required.

Each segment contains `title`, `sources` (a list of references), and `turns` (speaker/text objects). `podcast_check_script` returns hashes; `podcast_check_review` compares a review against the ordered segment hashes and checks for substantive notes. Neither tool independently reads sources or certifies that a review took place. `podcast_show_notes` formats caller-supplied measured chapter starts and deduplicated source references without inspecting audio. `podcast_caption_cues` turns explicitly supplied, passage-timed PageCast text into draft cues, optionally removing Higgs delivery tags. For PageCast, pass the handoff and timeline fingerprints as `expected_source_sha256` and `actual_source_sha256`; a mismatch is rejected. You may also pass the timeline's `source_text_status`: `changed` and `unavailable` are rejected, while `unchanged` records a stronger point-in-time text comparison. Older PageCast books lack this baseline. The values are caller-supplied and not independently authenticated; neither comparison verifies speaker assignments or later changes. These cues are not a transcript or word-level alignment; listen and check the final video. After review, `podcast_pagecast_plan` produces import text and a paragraph-to-speaker and segment-index map for the optional PageCast Director plugin; assign all resulting passage IDs manually after inspecting them, because a turn may split into multiple passages. Compare the handoff `source_sha256` and PageCast text status before rendering and captioning. `pagecast_timeline` can report cached WAV passage boundaries; derive segment starts from the map and verify the final export timing. Update and review the structured script again after PageCast text edits.

Example `podcast_check_script` input:

```json
{"segments":[{"title":"The experiment","sources":["https://example.org/paper"],"turns":[{"speaker":"Host A","text":"The researchers compared two approaches."},{"speaker":"Host B","text":"The comparison only covered one task."}]}]}
```

After checking the sources and reviewing the complete segment, copy its returned `sha256` into a review entry and add nonempty `purpose`, `opening_check`, `source_check`, and `edits` notes. Send those entries in order with a `reviewer` to `podcast_check_review`. Re-run the review if the script or its source references change.

After assigning speakers in PageCast, `podcast_check_pagecast_cast` compares the
complete passage list with the handoff's paragraph-to-speaker map. Collect all
`pagecast_book` pages for the same book revision, then supply its total,
`book.source_hash`, `source_text_status`, the handoff `source_sha256` and
assignments. The check accepts at most 10,000 passages and 1,000 assignment
paragraphs. Missing passage IDs or paragraphs, mismatched source hashes and
changed or unavailable text baselines are rejected. Speaker mismatches are
reported without changing them; at most 100 details are returned with an
omitted count. The inputs are caller-supplied, not authenticated, and a match
does not verify voices, source claims or changes after the check.

`podcast_mix` requires local FFmpeg and ffprobe with the `alimiter` latency-compensation option and supported POSIX or Windows file locking (synthetic checks passed on Linux and Windows) and combines explicitly selected trusted narration and music files into a private 48 kHz stereo WAV. Music loops under the narration; `music_db` defaults to -18 dB and `voice_db` to 0 dB, with a peak limiter. It does not play audio, generate music, automatically duck or certify loudness. Each input is limited to 512 MiB and two hours; output is limited to 2 GiB, with a 120-second encode timeout. Selected active-profile plugin media requires `allow_profile_media`. Mixing may shift timing, so recheck passage captions against the final audio. Check the final mix, timing, metadata, source rights and any required voice/music attribution before sharing.

Example `podcast_mix` arguments, using files you selected and have rights to use:

```json
{"narration_path":"/path/to/narration.wav","music_path":"/path/to/music.wav","music_db":-18,"voice_db":0}
```

For a PageCast output inside the active profile's plugin-data directory, add
`"allow_profile_media":true`. This opt-in does not allow unrelated profile
configuration files.

For different beds across an episode, `podcast_mix_timeline` accepts 1–20
non-overlapping, ordered intervals in milliseconds. Each selected music file
loops only within its interval; gaps have no music. For example:

```json
{"narration_path":"/path/to/narration.wav","beds":[{"music_path":"/path/to/intro.wav","start_ms":0,"end_ms":30000,"music_db":-18,"fade_in_ms":500,"fade_out_ms":500},{"music_path":"/path/to/second.wav","start_ms":30000,"end_ms":60000,"music_db":-20}]}
```

Intervals must fit the narration. Each bed can optionally specify `fade_in_ms` and `fade_out_ms`; their total must fit the bed. There are no automatic fades, crossfades or ducking, so check boundaries and balance by listening. Both mix tools use the
same private-output, profile opt-in, source-size and timeout limits described
above.

Windows tests used synthetic media and did not verify Windows ACLs, perceptual quality, or real episodes. The Windows PageCast handoff was tested with a mocked provider, not live speech. Review the output directory’s access controls.


## Episode folders, linting and the pre-audio gate

`podcast_load_episode`, `podcast_lint_episode` and `podcast_preflight` work on a folder of `NN-slug.txt` segments (with `# title:` and `# paper:`/`# source:` headers and `SPEAKER: text` lines), an optional `meta.json`, `editorial-review.json` and a separate fact-check `source-check.md`. Lint rules come from a daily show's script linter but are a style profile you set per show: tag handling, banned tags and phrases, spoken-number rule, disabled rules, source requirement, and a `kids` preset (reading grade, sentence length, sensitive words, no spoken contact details). Lint and the review gate are mechanical and self-attested; they do not verify sources, listen to audio or judge quality. Any dialogue edit changes the file hashes and needs a fresh review.
