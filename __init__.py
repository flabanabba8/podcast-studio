"""Local source-aware podcast script and editorial-receipt checks."""
import hashlib
import json
import math
import re
from pathlib import Path


def check_script(segments):
    if not isinstance(segments, list) or not 1 <= len(segments) <= 100:
        raise ValueError('Provide 1 to 100 ordered segments')
    output = []
    for segment in segments:
        if not isinstance(segment, dict) or set(segment) != {'title', 'sources', 'turns'}:
            raise ValueError('Each segment needs title, sources and turns')
        title, sources, turns = segment['title'], segment['sources'], segment['turns']
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise ValueError('Invalid segment title')
        if not isinstance(sources, list) or not 1 <= len(sources) <= 30 or any(not isinstance(s, str) or not s.strip() or len(s) > 2000 for s in sources):
            raise ValueError('Provide source references for every segment')
        if not isinstance(turns, list) or not 1 <= len(turns) <= 500:
            raise ValueError('Provide dialogue turns for each segment')
        words = 0
        for turn in turns:
            if not isinstance(turn, dict) or set(turn) != {'speaker', 'text'} or any(not isinstance(turn[x], str) or not turn[x].strip() for x in ('speaker', 'text')) or len(turn['text']) > 10000:
                raise ValueError('Each turn needs a speaker and text')
            words += len(turn['text'].split())
        digest = hashlib.sha256(json.dumps(segment, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        output.append({'title': title, 'sha256': digest, 'turns': len(turns), 'words': words})
    return {'segments': output, 'notice': 'Sources and dialogue are unverified; a full source and editorial review is still required.'}


def check_review(segments, review):
    script = check_script(segments)
    if not isinstance(review, dict) or set(review) != {'reviewer', 'segments'} or not isinstance(review['reviewer'], str) or not review['reviewer'].strip() or not isinstance(review['segments'], list):
        raise ValueError('Provide a reviewer and ordered segment review records')
    records = review['segments']
    if len(records) != len(script['segments']):
        raise ValueError('Review must cover every segment')
    for expected, record in zip(script['segments'], records):
        if not isinstance(record, dict) or record.get('sha256') != expected['sha256']:
            raise ValueError('Script changed or review coverage is incomplete')
        if any(not isinstance(record.get(k), str) or not record[k].strip() for k in ('purpose', 'opening_check', 'source_check', 'edits')):
            raise ValueError('Each review needs purpose, opening_check, source_check and edits')
    return {'status': 'review_record_matches_script', 'segments': len(records), 'notice': 'Review is self-attested; matching hashes do not verify source claims or editorial quality.'}


def pagecast_plan(segments, review):
    check_review(segments, review)
    lines, assignments = [], []
    for segment_index, segment in enumerate(segments):
        for turn in segment['turns']:
            text, speaker = turn['text'].strip(), turn['speaker'].strip()
            if text.splitlines() != [text] or not any(c.isalnum() for c in text):
                raise ValueError('Each PageCast turn must be one speakable line')
            if len(speaker) > 80 or any(ord(c) < 32 for c in speaker):
                raise ValueError('PageCast speakers must be at most 80 printable characters')
            assignments.append({'paragraph': len(lines), 'speaker': speaker, 'segment_index': segment_index})
            lines.append(text)
    if len(lines) > 1000 or sum(len(line) + 1 for line in lines) > 1_000_000:
        raise ValueError('PageCast draft exceeds the turn or character limit')
    text = '\n'.join(lines)
    return {'text': text, 'source_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'assignments': assignments,
            'notice': 'Import text into PageCast, inspect every resulting paragraph and assign all of its passage IDs to the listed speaker. PageCast may split turns. Review is self-attested; no speech was generated.'}


def show_notes(segments, starts):
    check_script(segments)
    if not isinstance(starts, list) or len(starts) != len(segments) or any(type(x) is not int or not 0 <= x <= 86400 for x in starts):
        raise ValueError('Provide one whole-second chapter start for each segment')
    if starts[0] != 0 or any(b <= a for a, b in zip(starts, starts[1:])):
        raise ValueError('Chapter starts must begin at zero and increase')
    def timestamp(value):
        h, rem = divmod(value, 3600)
        m, sec = divmod(rem, 60)
        return f'{h}:{m:02d}:{sec:02d}' if h else f'{m}:{sec:02d}'
    chapters, references = [], []
    for segment, start in zip(segments, starts):
        title = segment['title'].strip()
        if title.splitlines() != [title] or any(ord(c) < 32 for c in title): raise ValueError('Chapter titles must be single-line printable text')
        chapters.append(f'{timestamp(start)} {title}')
        for source in segment['sources']:
            if source.splitlines() != [source] or any(ord(c) < 32 for c in source): raise ValueError('Source references must be single-line printable text')
            if source not in references: references.append(source)
    return {'chapters': chapters, 'sources': references,
            'notice': 'Times and source references are supplied by the caller, not verified against audio or source content.'}


def caption_cues(passages, strip_higgs_tags=False, expected_source_sha256=None, actual_source_sha256=None, source_text_status=None):
    if type(strip_higgs_tags) is not bool: raise ValueError('strip_higgs_tags must be boolean')
    if (expected_source_sha256 is None) != (actual_source_sha256 is None): raise ValueError('Provide both source fingerprints or neither')
    if expected_source_sha256 is not None:
        if any(not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value) for value in (expected_source_sha256, actual_source_sha256)):
            raise ValueError('Source fingerprints must be lowercase SHA-256')
        if expected_source_sha256 != actual_source_sha256: raise ValueError('Timeline came from a different original source')
    if source_text_status is not None:
        if source_text_status not in ('unchanged', 'changed', 'unavailable'): raise ValueError('Invalid PageCast source text status')
        if expected_source_sha256 is None: raise ValueError('Source text status requires both source fingerprints')
        if source_text_status != 'unchanged': raise ValueError('PageCast text changed or its import baseline is unavailable; review the current script')
    if not isinstance(passages, list) or not 1 <= len(passages) <= 100:
        raise ValueError('Provide 1 to 100 timed passages with text')
    cues, last = [], 0
    for item in passages:
        if not isinstance(item, dict) or not isinstance(item.get('text'), str): raise ValueError('Each passage needs text and timing')
        start, end = item.get('start_seconds'), item.get('end_seconds')
        if any(type(x) not in (int, float) or not math.isfinite(x) for x in (start, end)) or start < last or end <= start or end > 86400 or round(start*1000) >= round(end*1000):
            raise ValueError('Passage times must be ordered and non-overlapping')
        text = item['text']
        if strip_higgs_tags:
            text = re.sub(r'<\|(?:emotion|style|prosody|sfx):[A-Za-z0-9_]+\|>', '', text)
        text = text.strip()
        if not text or len(text) > 4000 or any(c in text for c in ('\r', '\u0085', '\u2028', '\u2029')) or '-->' in text or re.search(r'\n[ \t]*\n', text) or any(ord(c) < 32 and c != '\n' for c in text):
            raise ValueError('Passage text cannot form a valid caption cue')
        cues.append({'start': start, 'end': end, 'text': text})
        last = end
    binding = 'matched_original_import_and_unchanged_text' if source_text_status == 'unchanged' else 'matched_original_import' if expected_source_sha256 is not None else 'not_checked'
    return {'cues': cues, 'source_binding': binding, 'notice': 'Caller-supplied fingerprints and text status are not independently authenticated; without a text status, an import-hash match does not detect later edits. Text status does not cover speaker assignments. Caption text is supplied script, not a speech transcript; passage-level timing is approximate. Listen, check final media timing and review all captions.'}


TOOLS = {
    'podcast_check_script': ('Fingerprint ordered sourced dialogue segments and report basic counts. Does not verify claims.', {'segments': {'type': 'array'}}, ['segments']),
    'podcast_mix_timeline': ('Mix 1–20 explicitly selected music beds over non-overlapping narration intervals into a private WAV. Times are milliseconds; optional explicit fades, no playback or automatic ducking.', {'narration_path': {'type': 'string'}, 'beds': {'type': 'array', 'minItems': 1, 'maxItems': 20, 'items': {'type': 'object', 'properties': {'music_path': {'type': 'string'}, 'start_ms': {'type': 'integer', 'minimum': 0}, 'end_ms': {'type': 'integer', 'minimum': 1}, 'music_db': {'type': 'number', 'minimum': -30, 'maximum': 0}, 'fade_in_ms': {'type': 'integer', 'minimum': 0}, 'fade_out_ms': {'type': 'integer', 'minimum': 0}}, 'required': ['music_path', 'start_ms', 'end_ms', 'music_db'], 'additionalProperties': False}}, 'voice_db': {'type': 'number', 'minimum': -12, 'maximum': 0}, 'allow_profile_media': {'type': 'boolean'}}, ['narration_path', 'beds']),
    'podcast_mix': ('Mix explicitly selected narration and music files into a private WAV without audio playback. Music loops; no automatic ducking. Check rights and listen before sharing.', {'narration_path': {'type': 'string'}, 'music_path': {'type': 'string'}, 'music_db': {'type': 'number', 'minimum': -30, 'maximum': 0}, 'voice_db': {'type': 'number', 'minimum': -12, 'maximum': 0}, 'allow_profile_media': {'type': 'boolean'}}, ['narration_path', 'music_path']),
    'podcast_caption_cues': ('Prepare passage-timed draft caption cues from explicitly supplied PageCast timeline text. Text is script, not verified speech; no word-level timing.', {'passages': {'type': 'array', 'minItems': 1, 'maxItems': 100, 'items': {'type': 'object', 'properties': {'start_seconds': {'type': 'number'}, 'end_seconds': {'type': 'number'}, 'text': {'type': 'string'}}, 'required': ['start_seconds', 'end_seconds', 'text']}}, 'strip_higgs_tags': {'type': 'boolean'}, 'expected_source_sha256': {'type': 'string'}, 'actual_source_sha256': {'type': 'string'}, 'source_text_status': {'type': 'string', 'enum': ['unchanged', 'changed', 'unavailable']}}, ['passages']),
    'podcast_show_notes': ('Prepare chapter labels and deduplicated source references from caller-supplied measured start times; does not inspect audio or verify sources.', {'segments': {'type': 'array'}, 'starts': {'type': 'array', 'items': {'type': 'integer', 'minimum': 0}}}, ['segments', 'starts']),
    'podcast_pagecast_plan': ('Prepare reviewed dialogue for optional PageCast import with an explicit paragraph-to-speaker map. Does not render audio.', {'segments': {'type': 'array'}, 'review': {'type': 'object'}}, ['segments', 'review']),
    'podcast_check_review': ('Check a supplied full editorial review covers the current exact segments. Review is self-attested.', {'segments': {'type': 'array'}, 'review': {'type': 'object'}}, ['segments', 'review']),
}


def invoke(name, args):
    try:
        if name in ('podcast_mix', 'podcast_mix_timeline'):
            from plugins.plugin_storage import plugin_data_dir
            from .mix import mix, mix_timeline
            method = mix if name == 'podcast_mix' else mix_timeline
            return json.dumps(method(plugin_data_dir('podcast-studio'), **args))
        return json.dumps({'podcast_check_script': check_script, 'podcast_check_review': check_review, 'podcast_pagecast_plan': pagecast_plan, 'podcast_show_notes': show_notes, 'podcast_caption_cues': caption_cues}[name](**args))
    except (TypeError, KeyError, ValueError, OSError, RuntimeError) as exc:
        return json.dumps({'error': str(exc)})


def register(ctx):
    ctx.register_skill('create-podcast', Path(__file__).parent / 'skills/create-podcast/SKILL.md', description='Develop a source-backed podcast with an editorial review before production.')
    for name, (description, properties, required) in TOOLS.items():
        ctx.register_tool(name=name, toolset='podcast_studio', schema={'name': name, 'description': description, 'parameters': {'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False}}, handler=lambda args, _name=name, **kw: invoke(_name, args))
