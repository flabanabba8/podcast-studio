# Verification

- The PageCast cast check detects a wrong speaker, duplicate or missing passage coverage, source-hash mismatch and unavailable text baseline. A separate PageCast fixture split a long turn into multiple passages, reported mismatches before assignment and matched after all passages were assigned. Inputs remain caller-supplied and point-in-time; this does not verify voice quality or later edits.

- The optional PageCast text-status handoff accepts a matching source and `unchanged` status, rejects `changed` and `unavailable`, and requires both source fingerprints when status is provided. A Linux PageCast/Podcast fixture and a native Windows text-only fixture exercised edits and missing baselines. Caller-supplied values are not independently authenticated; speaker assignments, speech and later edits still require review.
- Mixed-case private-directory boundaries were checked using synthetic paths on Linux and native Windows; no real credentials were used.

- An initial native Windows check exposed the POSIX-locking limitation. After adding Windows locking, synthetic single-bed and timed-bed mixes passed on Python 3.14 with FFmpeg; the timed check measured both beds and a silent gap, and a separate process was refused while the lock was held. A synthetic mix also fed the video plugin. No audio was played or perceptually reviewed; Windows ACLs, real episodes and broader Windows coverage remain unverified.

- Unit checks cover missing sources, incomplete reviews, and stale review detection when dialogue or source references change.
- Hermes manifest validation, Plugin Doctor, and actual runtime skill discovery passed.
- A private CPU-only integration fixture used the review-bound handoff to import two synthetic turns into PageCast Director, assigned distinct Flite voices, rendered and exported WAV. It did not use a GPU, contact a hosted voice service, or play or listen to the output. A separate longer-turn test confirmed PageCast split one turn into multiple passages with the same paragraph index. PageCast is a separate optional plugin and speaker assignment must be checked.
- Source fidelity, editorial judgment, naturalness, long-form production, and publishing are not automatically verified. This candidate is not a completed contest submission.
- A synthetic two-segment PageCast WAV timeline was mapped back to podcast segments and used to build chapter notes; its final passage boundary matched the exported WAV duration. No listening review was performed.
- A synthetic PageCast timeline with explicitly requested passage text produced draft cues accepted by YouTube Video Studio. No speech transcription, word-level alignment or listening review was performed.
- A synthetic PageCast caption handoff checks matching original-source fingerprints and rejects a mismatch. The fingerprint cannot detect later edits inside PageCast.
- A synthetic narration/music file mix verified looped audio, WAV format, duration, private output mode, source preservation, profile opt-in and timeout cleanup without opening an audio device. A separate synthetic PageCast-to-mix-to-video integration passed. No audio was listened to and no loudness or music-balance judgment was made.
- A temporary ten-minute synthetic mix and a music bed starting at nine minutes passed duration, silent-gap and signal checks on CPU. This does not establish realistic music balance, audio quality or performance for every machine.
- A mocked Inworld response passed through PageCast WAV export and this mixer; the mixer made no additional provider request. No live Inworld request or audio playback was performed by that integration fixture.
- A separate CPU-only check reused an existing fictional six-second PageCast export from an earlier live Inworld/Flite test, mixed a synthetic bed and passed the mix to the video plugin. No new provider request or playback occurred; perceptual quality remains unreviewed.
- A synthetic silent narration with two different tone beds verified the selected intervals, a silent gap, and overlap rejection. No audio device or listening review was used.
- The two-bed synthetic mix test also checks explicit fade-in and fade-out amplitudes and rejects fades longer than the bed. It does not establish perceptual quality.
- A synthetic narration impulse was about 4.8 ms late with the limiter default; enabling FFmpeg latency compensation brought the tested onset within 2 ms. This is not a general synchronization or listening-quality guarantee.
