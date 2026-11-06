"""Local source-aware podcast script and editorial-receipt checks."""
import hashlib
import json
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
    for segment in segments:
        for turn in segment['turns']:
            text, speaker = turn['text'].strip(), turn['speaker'].strip()
            if text.splitlines() != [text] or not any(c.isalnum() for c in text):
                raise ValueError('Each PageCast turn must be one speakable line')
            if len(speaker) > 80 or any(ord(c) < 32 for c in speaker):
                raise ValueError('PageCast speakers must be at most 80 printable characters')
            assignments.append({'paragraph': len(lines), 'speaker': speaker})
            lines.append(text)
    if len(lines) > 1000 or sum(len(line) + 1 for line in lines) > 1_000_000:
        raise ValueError('PageCast draft exceeds the turn or character limit')
    return {'text': '\n'.join(lines), 'assignments': assignments,
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
        if any(ord(c) < 32 for c in title): raise ValueError('Chapter titles must be single-line printable text')
        chapters.append(f'{timestamp(start)} {title}')
        for source in segment['sources']:
            if any(ord(c) < 32 for c in source): raise ValueError('Source references must be single-line printable text')
            if source not in references: references.append(source)
    return {'chapters': chapters, 'sources': references,
            'notice': 'Times and source references are supplied by the caller, not verified against audio or source content.'}


TOOLS = {
    'podcast_check_script': ('Fingerprint ordered sourced dialogue segments and report basic counts. Does not verify claims.', {'segments': {'type': 'array'}}, ['segments']),
    'podcast_show_notes': ('Prepare chapter labels and deduplicated source references from caller-supplied measured start times; does not inspect audio or verify sources.', {'segments': {'type': 'array'}, 'starts': {'type': 'array', 'items': {'type': 'integer', 'minimum': 0}}}, ['segments', 'starts']),
    'podcast_pagecast_plan': ('Prepare reviewed dialogue for optional PageCast import with an explicit paragraph-to-speaker map. Does not render audio.', {'segments': {'type': 'array'}, 'review': {'type': 'object'}}, ['segments', 'review']),
    'podcast_check_review': ('Check a supplied full editorial review covers the current exact segments. Review is self-attested.', {'segments': {'type': 'array'}, 'review': {'type': 'object'}}, ['segments', 'review']),
}


def invoke(name, args):
    try:
        return json.dumps({'podcast_check_script': check_script, 'podcast_check_review': check_review, 'podcast_pagecast_plan': pagecast_plan, 'podcast_show_notes': show_notes}[name](**args))
    except (TypeError, KeyError, ValueError) as exc:
        return json.dumps({'error': str(exc)})


def register(ctx):
    ctx.register_skill('create-podcast', Path(__file__).parent / 'skills/create-podcast/SKILL.md', description='Develop a source-backed podcast with an editorial review before production.')
    for name, (description, properties, required) in TOOLS.items():
        ctx.register_tool(name=name, toolset='podcast_studio', schema={'name': name, 'description': description, 'parameters': {'type': 'object', 'properties': properties, 'required': required, 'additionalProperties': False}}, handler=lambda args, _name=name, **kw: invoke(_name, args))
