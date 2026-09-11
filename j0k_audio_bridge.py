"""
J0K AI ASSISTANT - Windows Host Audio Bridge
PROJECT_AI_OS Physical Sound Engine
Plays realistic Gemini neural voice responses directly through physical Windows speakers.
Uses winsound (Windows Multimedia API) for zero latency, 100% reliable hardware playback.
"""

import os
import sys

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import time
import socket
import tempfile
import urllib.request
import urllib.parse
import winsound

API_BASE = "http://127.0.0.1:9090"
CACHE_DIR = os.path.join(tempfile.gettempdir(), "j0k_host_audio")
os.makedirs(CACHE_DIR, exist_ok=True)
SINGLETON_PORT = 9099

def acquire_singleton():
    """Ensures only one instance of the audio bridge runs at a time."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", SINGLETON_PORT))
        s.listen(1)
        return s
    except socket.error:
        print("[J0K Audio Bridge] Another instance is already running on port 9099. Exiting.")
        sys.exit(0)

def speak_sapi_fallback(text):
    """Fallback Windows SAPI speech if network TTS is delayed."""
    try:
        import subprocess
        # Strip markdown syntax
        clean = re.sub(r'[*_`#<>]', '', text).strip()
        ps_cmd = "Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Speak([Console]::In.ReadToEnd())"
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], input=clean.encode("utf-8"), check=False, timeout=25)
    except Exception as e:
        print(f"[SAPI Fallback Error]: {e}", file=sys.stderr, flush=True)

def play_audio(wav_file):
    """Plays WAV audio directly through Windows default sound device."""
    try:
        if os.path.exists(wav_file) and os.path.getsize(wav_file) > 100:
            # SND_FILENAME: play from file
            # SND_NODEFAULT: don't play default beep if file fails
            # Synchronous playback guarantees full speech is heard without cut-offs or overlaps
            winsound.PlaySound(wav_file, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            return True
    except Exception as e:
        print(f"[Audio Playback Error]: {e}", file=sys.stderr, flush=True)
    return False

def run_bridge():
    _sock = acquire_singleton()
    print("=" * 60, flush=True)
    print("  [STAR] J0K AI ASSISTANT - WINDOWS HOST AUDIO BRIDGE ACTIVE", flush=True)
    print(f"  Target Server: {API_BASE}", flush=True)
    print(f"  Audio Cache  : {CACHE_DIR}", flush=True)
    print("  Physical Output: Windows Default Sound Device (winsound + SAPI)", flush=True)
    print("=" * 60, flush=True)

    last_id = ""
    # Prime last_id with currently active queue so we don't replay history upon startup
    try:
        req = urllib.request.Request(f"{API_BASE}/speech_poll?bridge=windows", headers={"Connection": "close"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("has_new"):
                last_id = data.get("id", "")
    except Exception:
        pass

    consecutive_errors = 0

    while True:
        try:
            poll_url = f"{API_BASE}/speech_poll?bridge=windows&last_id={urllib.parse.quote(last_id)}"
            req = urllib.request.Request(poll_url, headers={"Connection": "close"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                consecutive_errors = 0
                if data.get("has_new"):
                    speech_id = data.get("id", "")
                    text = data.get("text", "")
                    voice = data.get("voice", "Charon")
                    last_id = speech_id

                    print(f"[SPEAKING] [{voice}]: {text[:80]}", flush=True)

                    # Download WAV format
                    wav_url = f"{API_BASE}/tts?text={urllib.parse.quote(text)}&voice={urllib.parse.quote(voice)}&format=wav"
                    local_wav = os.path.join(CACHE_DIR, f"{speech_id}.wav")

                    played = False
                    if not os.path.exists(local_wav) or os.path.getsize(local_wav) < 100:
                        try:
                            dl_req = urllib.request.Request(wav_url, headers={"Connection": "close"})
                            with urllib.request.urlopen(dl_req, timeout=30) as dl_resp:
                                content = dl_resp.read()
                                with open(local_wav, "wb") as f:
                                    f.write(content)
                        except Exception as dl_err:
                            print(f"[Neural Download Fail, using SAPI]: {dl_err}", flush=True)

                    # Play physical audio
                    if os.path.exists(local_wav) and os.path.getsize(local_wav) > 100:
                        played = play_audio(local_wav)

                    if not played:
                        speak_sapi_fallback(text)

                    print(f"[FINISHED] {speech_id}", flush=True)

        except urllib.error.URLError:
            consecutive_errors += 1
            if consecutive_errors == 1:
                print("[Bridge] Waiting for J0K daemon at 127.0.0.1:9090...", flush=True)
            time.sleep(2)
        except Exception as e:
            consecutive_errors += 1
            time.sleep(1)

        time.sleep(0.3)

if __name__ == "__main__":
    run_bridge()
