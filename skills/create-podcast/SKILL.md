---
name: create-podcast
description: Research, write, review and produce a podcast of any format (news, research, interview, story, tutorial, commentary) with source-backed claims, an editorial gate before audio, and a repeatable episode folder.
---

Make a podcast for the user's actual subject, audience and format. Nothing here assumes a news show, two hosts or a particular cast: pick the format first, then choose a style profile, a cast and a source policy that fit it. Everything is listener-first: the episode exists to serve the person listening, never to narrate how it was made.

## 0. Choose the format and set the rules once

Decide, and write down in the episode folder's `meta.json`: format (daily news brief, deep-dive on research, interview, narrative or fiction, tutorial, commentary, audiobook), cast and voices the user is allowed to use, and whether claims need sources. Then set the style profile you will pass to `podcast_lint_episode` and `podcast_preflight`:

- `tags`: `none` if the voice engine would read control tags aloud, `higgs` if it supports Higgs delivery tags.
- `banned_tags`: delivery tags the user has heard and disliked, for example `style:whispering` or `ERIS:emotion:contemplation` (speaker prefix optional).
- `banned_phrases`: the user's own tics and clichés. Add to this list whenever the user objects to a line.
- `spoken_numbers`: `error` for news and research (bare statistics sound bad aloud), `off` for fiction, finance walkthroughs or anything where numbers are the point.
- `disabled_rules`: switch off any rule that does not fit the format, such as `audience-ref` for a show that talks to "you" on purpose.
- `require_sources`: true for factual formats; false for fiction, personal essays or improvised interviews.

## 0b. Kids shows

For a children's show start with `style: {"preset": "kids"}` and then adjust. It turns off the rules that do not fit (spoken numbers, the audience-reference rule, one-word reactions), blocks spoken contact details, links and invitations to message or follow the show (this protects children from being steered to contact strangers), warns on sensitive words so you confirm the context, and warns when a segment's estimated reading grade (default 4) or sentence length (default 18 words) is above target. These are mechanical aids, not a child-safety review: a person still has to read the whole script for age-appropriateness, fear, manipulation, and anything a child could copy.

- Pick the age band first (for example 3 to 5, 6 to 8). Write to it: short complete sentences, concrete things, one idea at a time, kind and honest characters, repetition where it helps learning.
- Make-believe needs no sources; facts the show teaches (animals, science, history, safety) still do. Check them against a children's reference or a primary source and keep `# source:` headers for every factual segment. Do not teach something unsafe a child could imitate.
- Do not clone or imitate a real child's voice, and do not use any real child's name, photo or personal details. Use only voices the user is authorized to use. Say which voices are synthetic if the platform asks.
- YouTube requires every video to be set as made for kids or not, at the channel or video level, and a wrong setting can cause FTC or COPPA problems and platform action. Made-for-kids videos lose comments, the notification bell, personalized ads, end screens and similar features ([YouTube Help](https://support.google.com/youtube/answer/9527654)). Treat any kids show as made for kids unless you have checked the definition on YouTube's own help page. Check YouTube's current help pages for its altered-or-synthetic-content disclosure and its monetization rules for repetitive or mass-produced content before publishing a series; the summaries available while building this skill were from secondary sources and have not been checked against YouTube's own wording.
- A series is not a template run: vary stories, characters' problems and the lessons so episodes are genuinely different.

## 1. Research (factual formats): keep these methods

1. **Gather and scan.** Collect candidates from the show's real sources (papers, official posts, filings, transcripts, community reaction). Judge each on community signal, novelty, whether it connects to the others, whether it can be explained in conversation, and subfield balance. Choose the set that fits the format, not a fixed number.
2. **Find the thread only if it is real.** A theme must emerge from the sources; never impose one. No theme is a valid outcome.
3. **Read primary sources in full.** Never write about a paper, announcement or talk from an abstract, title, blurb or memory. Fetch and read the whole text (arXiv HTML, a transcript, the original article). Before relying on an ID or link, confirm it resolves to the right title. Summaries from earlier rounds or other tools are leads, not sources. Bot-walled pages need a stealth fetcher; a page you could not read is a gap you state, not a source you cite.
4. **Keep an append-only dossier.** One file per episode where each research round appends a dated section: item, verified primary link, the real mechanism or result, expert and community reception, and verification status. Never overwrite earlier rounds. Each round should go deeper or wider than the last: full-source reads of the most significant items, sweeps of source clusters not yet covered, adversarial checks of the shakiest claims against a primary source, and gap-filling for important things missing.
5. **Separate what is confirmed from what is claimed.** Announcement, allegation, observed result and interpretation are different things; attribute disputed claims.
6. **Never fabricate.** If a number, quote, date or detail cannot be supported, remove it or say it is unknown.

## 2. Write the episode folder

One text file per story or chapter, named so filename order is running order: `01-short-slug.txt`, `02-...`, then a closing file such as `98-wrapup.txt`. Each file starts with headers:

```
# title: The chapter title as it will appear in the chapter list
# paper: https://primary-source-url
```

(`# source:` works too, and a file may list several.) Spoken lines are `SPEAKER: text`; untagged lines continue the previous turn. Only a wrap-up, outro or credits file may have no source header in a factual show. There is no separate opener file: begin with the first story itself. `meta.json` can hold title, platform title, blurb and cover concept.

## 3. Write for the ear

- State the subject and what happened in the first sentence, then the setting, who did what and in what order, before any opinion. A person arriving at a chapter boundary should know the topic.
- Introduce each term when it is needed, in ordinary words. Pronouns need clear referents.
- Describe results by what they let a system or person do. Do not read statistics aloud; say what the number means in felt terms. Name the actual action behind an abstraction.
- Give every speaker complete thoughts. No finishing each other's sentences, no directing the co-host ("walk us through it"), no praise fillers, no agreement-only turns, no forced humor, no manufactured disagreement or excitement. Reactions must say something specific and be at least a short phrase.
- Length follows the explanation. No padding, no minimum runtime, and no quota for jokes, cameos or recaps.
- Close with a short, genuine pointer to the sources and a specific invitation to respond if the show wants one.
- For a non-news format (story, interview, tutorial), keep the same discipline of clarity and listener value, and loosen only the rules the style profile turns off.

## 4. Gates before any audio

1. Run `podcast_lint_episode` with the style profile and fix every error. Warnings are for judgment, not mechanical replacement.
2. Do a **separate fact-check pass** that does not edit: compare every specific claim (names, dates, numbers, quotes, who did what, what the method and result actually were, caveats) with the sources and write `source-check.md` with `OK` and `PROBLEM` lines per segment, ending `SUMMARY: N problems in M segments`. The editor who fixes the script may be unable to open the sources, so each problem quotes the script text, says what the source says, and recommends the fix.
3. Read the whole script in order as spoken text, cold, without titles or notes. Check comprehension, accuracy, delivery tags and humor. Then write `editorial-review.json`:

```
{"status": "passed", "reviewer": "who actually did it",
 "segments": {"01-slug.txt": {"sha256": "...", "purpose": "...", "opening_check": "...", "source_check": "...", "edits": "..."}}}
```

Each hash is the SHA-256 of that exact file. Record real cuts and corrections; never write a review that did not happen, and never claim someone listened to audio that has not been generated.
4. Run `podcast_preflight` (add `require_source_check` for factual shows). It blocks on lint errors, a missing or stale review, and reports open source-check problems. Any dialogue edit changes the hashes and requires review again. Do not synthesize audio past a blocked gate.

## 5. Voices and audio

Use only voices the user is authorized to use. Hosted or local speech engines cost money or hardware; say which one you are using and what it will cost before rendering. Use `podcast_pagecast_plan` and PageCast for casting, locked voices and resumable renders; compare the handoff with `podcast_check_pagecast_cast` and timing fingerprints. Keep delivery tags out of captions (`strip_higgs_tags`). A tagged expressiveness pass after the editorial review needs its own check and a fresh review record.

Mix with `podcast_mix` or `podcast_mix_timeline`: music is a separate bed with explicit start, end, fade and gain; beds bridge pauses between segments; one loudness target for the finished file (for example about -16 LUFS integrated for spoken word). Check rights for any music. Listen before sharing: matching hashes and passing checks say nothing about how it sounds.

## 6. Chapters, captions and notes

Use measured segment start times with `podcast_show_notes` for chapter labels and deduplicated source references, and `podcast_caption_cues` for passage-timed draft captions. Each story is one chapter. Show notes and captions come from the script, not from the audio, so confirm timing by playing it.

## 7. Report honestly

State which gates passed, which claims were verified against which sources, what remains unverified, and what nobody has listened to. Do not call an episode ready because the files are consistent.
