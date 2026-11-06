"""Explicit local narration/music mix; never opens an audio device."""
import fcntl
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import uuid

PRIVATE = {'.ssh', '.gnupg', '.aws', '.azure', '.codex', '.docker', '.kube', '.pki', '.config', '.hermes'}


def media(value, root, allow_profile_media):
    if not isinstance(value, str) or len(value) > 4096: raise ValueError('Choose an absolute local audio path')
    path = Path(value).expanduser()
    if not path.is_absolute() or path.is_symlink() or any(x in PRIVATE - {'.hermes'} for x in path.parts):
        raise ValueError('Choose a non-symlink audio file outside private configuration')
    original = path.parts; path = path.resolve(strict=True)
    data = Path(root).resolve().parent; profile = data.parent if data.name == 'plugin-data' else None
    allowed = allow_profile_media and profile is not None and path.is_relative_to(data)
    protected = '.hermes' in original or '.hermes' in path.parts or profile is not None and path.is_relative_to(profile)
    if any(x in PRIVATE - {'.hermes'} for x in path.parts) or protected and not allowed or not path.is_file() or path.suffix.lower() not in ('.wav', '.mp3', '.m4a'):
        raise ValueError('Unsupported or private audio file')
    if path.stat().st_size > 512 * 1024**2: raise ValueError('Audio source exceeds 512 MiB')
    return path


def mix(root, narration_path, music_path, music_db=-18, voice_db=0, allow_profile_media=False):
    if type(allow_profile_media) is not bool: raise ValueError('allow_profile_media must be boolean')
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in (music_db, voice_db)) or not -30 <= music_db <= 0 or not -12 <= voice_db <= 0:
        raise ValueError('Use music gain -30 to 0 dB and voice gain -12 to 0 dB')
    narration = media(narration_path, root, allow_profile_media); music = media(music_path, root, allow_profile_media)
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not ffmpeg or not ffprobe: raise ValueError('Install ffmpeg and ffprobe')
    def identity(path):
        value = path.stat()
        return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
    before = [identity(path) for path in (narration, music)]
    root = Path(root); root.mkdir(mode=0o700, parents=True, exist_ok=True)
    ident = uuid.uuid4().hex; partial = root/(ident+'.partial.wav'); output = root/(ident+'.wav')
    env = {'PATH': os.defpath, 'LANG': 'C.UTF-8'}
    with (root/'.mix.lock').open('a') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc: raise RuntimeError('Another podcast mix is running') from exc
        try:
            def probe(path):
                result = subprocess.run([ffprobe, '-v', 'error', '-protocol_whitelist', 'file,pipe', '-show_entries', 'format=duration:stream=codec_type', '-of', 'json', str(path)], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env, timeout=10, check=False)
                if result.returncode or len(result.stdout) > 65536: raise RuntimeError('Audio metadata check failed')
                info = json.loads(result.stdout); duration = float(info.get('format', {}).get('duration', 0))
                if not math.isfinite(duration) or not 0 < duration <= 7200 or not any(x.get('codec_type') == 'audio' for x in info.get('streams', [])):
                    raise ValueError('Audio duration or stream is unsupported')
                return duration
            duration = probe(narration); probe(music)
            if duration * 48000 * 4 + 1024 > 2 * 1024**3: raise ValueError('WAV output would exceed 2 GiB')
            os.close(os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600))
            filters = f'[0:a:0]aresample=48000,volume={voice_db}dB[voice];[1:a:0]aresample=48000,volume={music_db}dB[music];[voice][music]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95:level=0[out]'
            command = [ffmpeg, '-v', 'error', '-nostdin', '-filter_complex_threads', '1', '-protocol_whitelist', 'file,pipe', '-i', str(narration), '-stream_loop', '-1', '-protocol_whitelist', 'file,pipe', '-i', str(music), '-filter_complex', filters, '-map', '[out]', '-t', str(duration), '-c:a', 'pcm_s16le', '-ar', '48000', '-ac', '2', '-threads', '1', '-map_metadata', '-1', '-map_chapters', '-1', '-fs', str(2 * 1024**3), '-y', str(partial)]
            result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, timeout=120, check=False)
            if result.returncode or not partial.stat().st_size: raise RuntimeError('Audio mix failed')
            actual = probe(partial)
            if abs(actual-duration) > 0.25: raise RuntimeError('Mixed audio duration does not match narration')
            if before != [identity(path) for path in (narration, music)]: raise RuntimeError('An input changed during mixing; output discarded')
            os.replace(partial, output)
            return {'output_path': str(output), 'duration_seconds': actual, 'music_db': music_db, 'voice_db': voice_db,
                    'notice': 'Music loops under the narration; there is no automatic ducking or editorial/loudness review. Check licensing, attribution, music balance and final audio before sharing.'}
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            raise RuntimeError('Audio mix or metadata check failed') from exc
        finally:
            partial.unlink(missing_ok=True)
