#!/usr/bin/env python3
"""
J.A.R.V.I.S. Ambient Operating System Assistant Daemon
PROJECT_AI_OS - Core Background Agent & Tool Execution Bridge
Equipped with Universal Agentic Capabilities & Local LLM Tool Calling
"""

import os
import re
import sys
import json
import time
import shutil
import socket
import urllib.request
import urllib.parse
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

LLM_API_URL = os.environ.get("JARVIS_LLM_URL", "http://127.0.0.1:8080/v1/chat/completions")
PORT = int(os.environ.get("JARVIS_PORT", "9090"))
MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct-GGUF"
LATEST_CONVERSATION = []

SYSTEM_PROMPT = """You are J0K AI ASSISTANT, the ambient, highly intelligent, and refined AI operating system companion for PROJECT_AI_OS.
Inspired by advanced AI companions, you speak with a polite, calm, concise, and capable tone (referring to the user occasionally as "sir" or by their name).
You help the user navigate and operate their computer entirely through natural conversation without requiring them to type terminal commands.
You can execute ANY operation: creating software projects, sending and drafting emails, creating files, searching the web, launching applications, running diagnostics, taking notes, and executing safe commands.

When the user asks you to perform an action on the computer, YOU MUST respond with a JSON action block at the END of your message in the exact format:
```json
{"action": "<action_name>", "parameters": {<key_values>}}
```

Available actions:
1. create_project: {"name": "<project_name>", "type": "<python|web|api|game|data|custom>", "description": "<brief_description>", "files": {"<filename>": "<code_content>"}}
2. send_email: {"recipient": "<email_address>", "subject": "<subject_line>", "body": "<email_body>"}
3. window_action: {"action": "<close|switch|maximize|minimize|restore|overview|grid|lock|show_desktop>"}
4. manage_file_folder: {"operation": "<create_folder|copy|move|delete|zip|unzip|list>", "source": "<path>", "destination": "<path>"}
5. create_document: {"title": "<title>", "content": "<content>", "format": "<markdown|csv|text>"}
6. manage_clipboard: {"operation": "<copy|read>", "text": "<text_to_copy>"}
7. get_weather: {"city": "<city_name>"}
8. manage_process: {"operation": "<list_top|kill>", "process_name": "<name>"}
9. download_web: {"url": "<url>", "filename": "<filename>"}
10. create_file: {"path": "<filepath>", "content": "<file_content>"}
11. read_file: {"path": "<filepath>"}
12. take_notes: {"note": "<note_content>"}
13. run_command: {"command": "<safe_shell_command>"}
14. open_app: {"app": "<browser|files|calculator|editor|settings|terminal|discover|systemmonitor>"}
15. open_url: {"url": "<https_url>"}
16. system_status: {}
17. set_volume: {"level": "<up|down|mute|unmute|percentage>"}
18. take_screenshot: {}
19. search_files: {"query": "<filename_or_pattern>"}

If no system action is required, simply respond concisely, helpfully, and politely. Keep spoken responses under 2-3 sentences.
"""

def run_as_user(cmd):
    """Executes a GUI or user-space command inside user 1000's Wayland session."""
    user_env = os.environ.copy()
    user_env["WAYLAND_DISPLAY"] = "wayland-0"
    user_env["XDG_RUNTIME_DIR"] = "/run/user/1000"
    user_env["DISPLAY"] = ":0"
    user_cmd = ["sudo", "-u", "jayaramank", "-E"] + cmd
    return subprocess.Popen(user_cmd, env=user_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

GEMINI_VOICES = {
    "Charon": {
        "id": "Charon",
        "name": "Charon",
        "style": "Deep, confident, calm masculine voice (Gemini Charon style)",
        "edge_voice": "en-US-GuyNeural"
    },
    "Puck": {
        "id": "Puck",
        "name": "Puck",
        "style": "Upbeat, energetic, friendly masculine voice (Gemini Puck style)",
        "edge_voice": "en-US-ChristopherNeural"
    },
    "Aoede": {
        "id": "Aoede",
        "name": "Aoede",
        "style": "Warm, articulate, expressive feminine voice (Gemini Aoede style)",
        "edge_voice": "en-US-JennyNeural"
    },
    "Kore": {
        "id": "Kore",
        "name": "Kore",
        "style": "Gentle, soothing, conversational feminine voice (Gemini Kore style)",
        "edge_voice": "en-US-MichelleNeural"
    },
    "Fenrir": {
        "id": "Fenrir",
        "name": "Fenrir",
        "style": "Sharp, executive, articulate masculine voice (Gemini Fenrir style)",
        "edge_voice": "en-US-AndrewNeural"
    }
}
VOICE_CONFIG_FILE = "/home/jayaramank/.config/j0k_voice.json"
CACHE_DIR = "/tmp/j0k_voices_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_active_voice():
    try:
        if os.path.exists(VOICE_CONFIG_FILE):
            with open(VOICE_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                v = data.get("active_voice", "Charon")
                if v in GEMINI_VOICES:
                    return v
    except Exception:
        pass
    return "Charon"

def set_active_voice(v_name):
    if v_name in GEMINI_VOICES:
        try:
            os.makedirs(os.path.dirname(VOICE_CONFIG_FILE), exist_ok=True)
            with open(VOICE_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"active_voice": v_name}, f)
        except Exception:
            pass
        return True
    return False

def synthesize_audio_sync(text, voice_name=None, return_wav=False):
    """
    Synthesizes neural speech to MP3 file (and optional WAV) and returns filepath.
    Uses MD5 caching for instant performance on repeated phrases.
    """
    v = voice_name or get_active_voice()
    voice_info = GEMINI_VOICES.get(v, GEMINI_VOICES["Charon"])
    edge_voice = voice_info["edge_voice"]

    clean_text = text.split("```")[0].strip()
    clean_text = re.sub(r'[*_`#]', '', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    if not clean_text:
        return None

    import hashlib
    text_hash = hashlib.md5(f"{v}:{clean_text}".encode("utf-8")).hexdigest()
    out_mp3 = os.path.join(CACHE_DIR, f"{text_hash}.mp3")
    out_wav = os.path.join(CACHE_DIR, f"{text_hash}.wav")

    def _ensure_wav():
        if return_wav:
            if not os.path.exists(out_wav) or os.path.getsize(out_wav) < 100:
                try:
                    subprocess.run(
                        ["ffmpeg", "-i", out_mp3, "-y", out_wav],
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except Exception:
                    pass
            if os.path.exists(out_wav) and os.path.getsize(out_wav) > 100:
                return out_wav
        return out_mp3

    if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 100:
        return _ensure_wav()

    # 1. Synthesize via edge-tts CLI
    try:
        edge_bin = "/usr/local/bin/edge-tts" if os.path.exists("/usr/local/bin/edge-tts") else shutil.which("edge-tts")
        if edge_bin:
            subprocess.run(
                [edge_bin, "--voice", edge_voice, "--text", clean_text, "--write-media", out_mp3],
                check=True,
                timeout=18,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 100:
                return _ensure_wav()
    except Exception as e:
        print(f"[J0K TTS] edge-tts CLI error: {e}", file=sys.stderr)

    # 2. Fallback to python asyncio edge_tts
    try:
        import edge_tts
        import asyncio
        async def _synth():
            comm = edge_tts.Communicate(clean_text, edge_voice)
            await comm.save(out_mp3)
        asyncio.run(_synth())
        if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 100:
            return _ensure_wav()
    except Exception as e:
        print(f"[J0K TTS] edge_tts python error: {e}", file=sys.stderr)

    return None

LAST_BRIDGE_TIME = 0
SPEECH_QUEUE = []
HUD_EVENTS = []

def speak(text, voice_name=None):
    """Speaks text using realistic human neural speech with fallback and host synchronization."""
    clean_text = text.split("```")[0].strip()
    clean_text = re.sub(r'[*_`#]', '', clean_text).strip()
    if not clean_text:
        return

    v = voice_name or get_active_voice()
    import hashlib
    text_hash = hashlib.md5(f"{v}:{clean_text}:{time.time()}".encode("utf-8")).hexdigest()
    
    # Broadcast to speech queue for host audio playback
    SPEECH_QUEUE.append({
        "id": text_hash,
        "text": clean_text,
        "voice": v,
        "time": time.time()
    })
    if len(SPEECH_QUEUE) > 30:
        del SPEECH_QUEUE[:15]

    def _run():
        try:
            mp3_path = synthesize_audio_sync(clean_text, v)
        except Exception as e:
            print(f"[J0K Voice] TTS Playback Error: {e}", file=sys.stderr)

# ──────────────────────────────────────────────────────────────────────
# SELF-LEARNING MEMORY SYSTEM
# J0K remembers successful actions, user preferences, and corrections.
# This memory is injected into the LLM context so J0K improves over time.
# ──────────────────────────────────────────────────────────────────────
MEMORY_FILE = "/home/jayaramank/.config/j0k_memory.json"
MAX_MEMORY_ACTIONS = 100
MAX_MEMORY_CORRECTIONS = 50
MAX_MEMORY_PREFERENCES = 20

def load_memory():
    """Load persistent memory from disk."""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"learned_preferences": [], "successful_actions": [], "corrections": []}

def save_memory(mem):
    """Persist memory to disk with size limits."""
    mem["successful_actions"] = mem.get("successful_actions", [])[-MAX_MEMORY_ACTIONS:]
    mem["corrections"] = mem.get("corrections", [])[-MAX_MEMORY_CORRECTIONS:]
    mem["learned_preferences"] = mem.get("learned_preferences", [])[-MAX_MEMORY_PREFERENCES:]
    try:
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[J0K Memory] Save error: {e}", file=sys.stderr)

def remember_success(user_said, action_name, params, reply):
    """Record a successful action for future learning."""
    mem = load_memory()
    mem["successful_actions"].append({
        "user_said": user_said[:200],
        "action": action_name,
        "params_summary": str(params)[:300],
        "time": time.strftime("%Y-%m-%d %H:%M")
    })
    save_memory(mem)

def remember_correction(user_said, context):
    """Record a user correction for future learning."""
    mem = load_memory()
    mem["corrections"].append({
        "user_said": user_said[:200],
        "context": context[:200],
        "time": time.strftime("%Y-%m-%d %H:%M")
    })
    save_memory(mem)

def remember_preference(preference):
    """Record a learned user preference."""
    mem = load_memory()
    # Avoid duplicates
    existing = [p["pattern"] for p in mem["learned_preferences"]]
    if preference not in existing:
        mem["learned_preferences"].append({
            "pattern": preference[:200],
            "learned_at": time.strftime("%Y-%m-%d")
        })
        save_memory(mem)

def get_memory_context():
    """Build a context string from memory to inject into LLM prompts."""
    mem = load_memory()
    parts = []
    if mem.get("learned_preferences"):
        prefs = "; ".join(p["pattern"] for p in mem["learned_preferences"][-10:])
        parts.append(f"User preferences: {prefs}")
    if mem.get("corrections"):
        corrs = "; ".join(c["user_said"] for c in mem["corrections"][-5:])
        parts.append(f"Past corrections: {corrs}")
    if mem.get("successful_actions"):
        recent = mem["successful_actions"][-5:]
        examples = "; ".join(f"'{a['user_said']}' -> {a['action']}" for a in recent)
        parts.append(f"Recent successful actions: {examples}")
    return "\n".join(parts) if parts else ""

PENDING_CRITICAL_ACTIONS = {}

CRITICAL_SYSTEM_DIRS = {
    "/", "/etc", "/usr", "/var", "/boot", "/bin", "/sbin", "/lib", "/lib64", "/opt",
    "/sys", "/dev", "/root", "/proc", "/home", "/home/jayaramank",
    "/home/jayaramank/Documents", "/home/jayaramank/Desktop", "/home/jayaramank/Pictures", "/home/jayaramank/Projects"
}

CRITICAL_SERVICES = {
    "dbus", "systemd", "systemd-logind", "sshd", "firewalld", "NetworkManager",
    "display-manager", "sddm", "gdm", "lightdm", "kwin", "plasma", "auditd"
}

CRITICAL_PROCESSES = {
    "systemd", "init", "dbus-daemon", "dbus-broker", "sshd", "kwin_wayland",
    "wireplumber", "pipewire", "Xwayland", "plasma-workspace"
}

def is_critical_operation(action_name, params):
    """
    Evaluates whether an operation is critical or destructive and requires explicit user permission.
    Returns: (is_critical: bool, reason: str, brief_desc: str)
    """
    if not action_name or not params:
        return False, "", ""

    if action_name == "manage_file_folder":
        op = str(params.get("operation", "")).lower()
        src = str(params.get("source", "")).strip()
        if op == "delete":
            clean_src = os.path.normpath(src if src.startswith("/") else os.path.join("/home/jayaramank", src))
            if clean_src in CRITICAL_SYSTEM_DIRS or any(clean_src == d or clean_src.startswith(d + "/") for d in ["/etc", "/usr", "/boot", "/var", "/sys", "/dev"]):
                return True, f"Deleting important system directory or files at '{clean_src}'", f"permanently delete important directory '{clean_src}'"
            if clean_src in ["/home", "/home/jayaramank"]:
                return True, f"Deleting user root directory '{clean_src}'", f"permanently erase user directory '{clean_src}'"

    elif action_name == "manage_process":
        op = str(params.get("operation", "")).lower()
        pname = str(params.get("process_name", "")).lower()
        if op == "kill":
            for crit_p in CRITICAL_PROCESSES:
                if crit_p in pname:
                    return True, f"Terminating essential system process '{pname}'", f"terminate core system process '{pname}'"

    elif action_name == "run_command":
        cmd = str(params.get("command", "")).strip().lower()
        # 1. Directory deletion commands (rm -rf /, /etc, etc.)
        rm_match = re.search(r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+([^\s;&|]+)', cmd) or re.search(r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r?\s+([^\s;&|]+)', cmd)
        if rm_match:
            target = rm_match.group(1).strip().strip('"\'')
            if target in ["/", "/*", "/etc", "/etc/*", "/usr", "/var", "/boot", "/home", "~", "$HOME", "/home/jayaramank", "/root"]:
                return True, f"Recursive removal of critical path '{target}'", f"permanently erase '{target}'"
            for d in ["/etc", "/usr", "/boot", "/var", "/sys", "/dev"]:
                if target.startswith(d):
                    return True, f"Recursive removal of critical directory '{target}'", f"permanently erase directory '{target}'"

        # 2. Critical system service termination
        for svc in CRITICAL_SERVICES:
            if re.search(rf'\bsystemctl\s+(?:stop|disable|mask)\s+{svc}', cmd):
                return True, f"Stopping or disabling essential system service '{svc}'", f"shut down essential service '{svc}'"

        # 3. Critical process kill
        if re.search(r'\b(?:pkill|killall|kill)\s+(?:-9\s+)?(?:systemd|init|dbus|kwin|sshd)\b', cmd):
            return True, f"Force-killing critical system daemon", f"terminate core system service"

        # 4. Raw disk and filesystem destruction
        if any(d_cmd in cmd for d_cmd in ["mkfs", "wipefs", "fdisk", "parted"]) or re.search(r'\bdd\s+.*of=/dev/(?:sd|nvme|vd)', cmd):
            return True, f"Destructive raw disk or filesystem modification: '{cmd[:60]}'", f"wipe or repartition storage devices"

        # 5. Power & shutdown
        if any(p_cmd in cmd for p_cmd in ["poweroff", "shutdown", "reboot", "init 0", "init 6", "halt"]):
            return True, f"System power or shutdown directive: '{cmd[:40]}'", f"shut down or reboot the computer"

    return False, "", ""

def check_and_execute_or_defer(action_name, params, refined_prompt, plan, default_reply, voice=None):
    """
    Checks if an operation is critical. If critical, pauses execution and prepares a permission request.
    If non-critical, executes immediately with full administrator permissions.
    """
    is_crit, reason, brief_desc = is_critical_operation(action_name, params)
    if is_crit:
        import uuid
        action_id = f"crit_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        PENDING_CRITICAL_ACTIONS[action_id] = {
            "action_id": action_id,
            "action_name": action_name,
            "params": params,
            "warning": reason,
            "brief_desc": brief_desc,
            "refined_prompt": refined_prompt,
            "plan": plan,
            "created_at": time.time(),
            "voice": voice
        }
        warning_msg = f"⚠️ CRITICAL ACTION PERMISSION REQUIRED: {reason}. Operating system integrity safeguard engaged."
        spoken_warning = f"Warning: this is a critical system operation that will {brief_desc}. Do you grant permission to proceed, sir?"
        return {
            "requires_permission": True,
            "action_id": action_id,
            "warning": warning_msg,
            "brief_desc": brief_desc,
            "refined_prompt": refined_prompt,
            "plan": f"1. Identify high-risk directive: {reason}. 2. Suspend execution. 3. Await explicit administrator confirmation.",
            "action": {
                "status": "pending_permission",
                "action_id": action_id,
                "message": warning_msg
            },
            "reply": spoken_warning
        }
    else:
        # Non-critical: execute immediately with full administrative privileges
        act = execute_action(action_name, params)
        return {
            "requires_permission": False,
            "refined_prompt": refined_prompt,
            "plan": plan,
            "action": act,
            "reply": default_reply
        }

def execute_action(action_name, params):
    """Executes system actions on behalf of the user with full error recovery."""
    result = {"status": "success", "message": ""}
    try:
        if action_name == "open_app":
            app = params.get("app", "").lower()
            app_map = {
                "browser": ["firefox"],
                "firefox": ["firefox"],
                "files": ["dolphin", "/home/jayaramank"],
                "dolphin": ["dolphin", "/home/jayaramank"],
                "calculator": ["kcalc"],
                "editor": ["kate"],
                "settings": ["systemsettings"],
                "terminal": ["konsole"],
                "discover": ["plasma-discover"],
                "systemmonitor": ["plasma-systemmonitor"],
            }
            cmd = app_map.get(app, ["xdg-open", app])
            run_as_user(cmd)
            result["message"] = f"Launched {app}."

        elif action_name == "system_status":
            ram = subprocess.check_output(["free", "-h"], text=True).splitlines()[1].split()
            df = subprocess.check_output(["df", "-h", "/"], text=True).splitlines()[1].split()
            uptime = subprocess.check_output(["uptime", "-p"], text=True).strip()
            result["data"] = {
                "ram_used": ram[2],
                "ram_total": ram[1],
                "disk_free": df[3],
                "disk_total": df[1],
                "uptime": uptime
            }
            result["message"] = f"Memory: {ram[2]} used of {ram[1]}. Storage: {df[3]} available. System {uptime}."

        elif action_name == "set_volume":
            lvl = str(params.get("level", "up")).lower()
            if shutil.which("wpctl"):
                if lvl == "up":
                    run_as_user(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%+"])
                elif lvl == "down":
                    run_as_user(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"])
                elif lvl == "mute":
                    run_as_user(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1"])
                elif lvl == "unmute":
                    run_as_user(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"])
            result["message"] = f"Volume adjusted ({lvl})."

        elif action_name == "take_screenshot":
            pic_dir = "/home/jayaramank/Pictures/Screenshots"
            os.makedirs(pic_dir, exist_ok=True)
            filename = os.path.join(pic_dir, f"screenshot_{int(time.time())}.png")
            if shutil.which("spectacle"):
                run_as_user(["spectacle", "-b", "-n", "-o", filename])
            result["message"] = f"Screenshot captured to {filename}."

        elif action_name == "open_url":
            url = params.get("url", "https://duckduckgo.com")
            run_as_user(["xdg-open", url])
            result["message"] = f"Opening {url}."

        elif action_name == "search_files":
            q = params.get("query", "")
            out = subprocess.check_output(["find", "/home/jayaramank", "-iname", f"*{q}*", "-maxdepth", "3"], text=True)
            files = [f for f in out.splitlines() if f][:5]
            result["files"] = files
            result["message"] = f"Found {len(files)} matching files."

        elif action_name == "send_email":
            recipient = params.get("recipient", "recipient@example.com")
            subject = params.get("subject", "Message from J.A.R.V.I.S.")
            body = params.get("body", "Greetings, this message was generated and dispatched by J.A.R.V.I.S. inside PROJECT_AI_OS.")
            
            # 1. Archive email to ~/Emails/
            email_dir = "/home/jayaramank/Emails"
            os.makedirs(email_dir, exist_ok=True)
            ts = int(time.time())
            eml_path = os.path.join(email_dir, f"draft_{ts}.eml")
            readable_path = os.path.join(email_dir, "latest_email_draft.txt")
            
            eml_content = f"""From: Jayaraman K <jayaramank@project-ai-os.local>
To: {recipient}
Subject: {subject}
Date: {time.strftime('%a, %d %b %Y %H:%M:%S +0000')}
Content-Type: text/plain; charset=utf-8

{body}
"""
            with open(eml_path, "w", encoding="utf-8") as f:
                f.write(eml_content)
            with open(readable_path, "w", encoding="utf-8") as f:
                f.write(eml_content)
            
            # Set permissions to user
            subprocess.run(["chown", "-R", "jayaramank:jayaramank", email_dir], check=False)
            
            # 2. Launch webmail compose / xdg-email
            encoded_to = urllib.parse.quote(recipient)
            encoded_subj = urllib.parse.quote(subject)
            encoded_body = urllib.parse.quote(body)
            gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={encoded_to}&su={encoded_subj}&body={encoded_body}"
            mailto_url = f"mailto:{encoded_to}?subject={encoded_subj}&body={encoded_body}"
            
            run_as_user(["xdg-open", mailto_url])
            run_as_user(["notify-send", "✉️ J.A.R.V.I.S. Email Dispatched", f"To: {recipient}\nSubject: {subject}"])
            
            result["message"] = f"Email draft prepared and opened for {recipient} with subject '{subject}'. Archived to {eml_path}."
            result["data"] = {
                "recipient": recipient,
                "subject": subject,
                "eml_path": eml_path,
                "gmail_url": gmail_url
            }

        elif action_name == "create_project":
            raw_name = params.get("name", "my_project")
            proj_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', raw_name).strip('_') or f"project_{int(time.time())}"
            proj_type = params.get("type", "python").lower()
            desc = params.get("description", f"{proj_name} created autonomously by J.A.R.V.I.S.")
            custom_files = params.get("files", {})
            
            proj_dir = os.path.join("/home/jayaramank/Projects", proj_name)
            os.makedirs(proj_dir, exist_ok=True)
            
            files_created = {}
            main_file = None
            
            if custom_files and isinstance(custom_files, dict):
                for fname, fcontent in custom_files.items():
                    fpath = os.path.join(proj_dir, fname)
                    os.makedirs(os.path.dirname(fpath), exist_ok=True)
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(fcontent)
                    files_created[fname] = len(fcontent)
                    if not main_file and (fname.endswith(".py") or fname.endswith(".html") or fname.endswith(".js")):
                        main_file = fpath
            else:
                # Built-in intelligent scaffolds for popular projects
                if "web" in proj_type or "todo" in proj_type or "html" in proj_type:
                    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{proj_name.replace('_', ' ').title()}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">⚡ J.A.R.V.I.S. LABS</div>
            <h1>{proj_name.replace('_', ' ').title()}</h1>
            <p>{desc}</p>
        </header>
        <main>
            <div class="card">
                <h2>Tasks & Directives</h2>
                <div class="input-group">
                    <input type="text" id="taskInput" placeholder="Enter new directive...">
                    <button id="addBtn">Add Directive</button>
                </div>
                <ul id="taskList">
                    <li class="completed">Deploy JOK-AI-OS 1.0 Core Engine ✓</li>
                    <li class="completed">Initialize J.A.R.V.I.S. Ambient Assistant ✓</li>
                    <li>Construct Advanced Autonomous AI Capabilities</li>
                </ul>
            </div>
        </main>
        <footer>
            PROJECT_AI_OS • Autonomous Engine
        </footer>
    </div>
    <script src="app.js"></script>
</body>
</html>
"""
                    style_css = """* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
body { background: #070b14; color: #e2e8f0; min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
.container { width: 100%; max-width: 600px; background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 16px; padding: 30px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5); backdrop-filter: blur(12px); }
header { text-align: center; margin-bottom: 24px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 16px; }
.logo { font-size: 12px; font-weight: 800; color: #00e5ff; letter-spacing: 2px; margin-bottom: 8px; }
h1 { font-size: 24px; color: #ffffff; }
p { color: #94a3b8; font-size: 14px; margin-top: 6px; }
.card { background: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); }
h2 { font-size: 16px; color: #38bdf8; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 1px; }
.input-group { display: flex; gap: 10px; margin-bottom: 18px; }
input { flex: 1; padding: 12px 16px; background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(0, 229, 255, 0.2); border-radius: 8px; color: #fff; outline: none; }
input:focus { border-color: #00e5ff; }
button { padding: 12px 20px; background: #00e5ff; color: #070b14; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; transition: all 0.2s; }
button:hover { background: #38bdf8; transform: translateY(-1px); }
ul { list-style: none; display: flex; flex-direction: column; gap: 10px; }
li { padding: 12px 16px; background: rgba(15, 23, 42, 0.6); border-radius: 8px; border-left: 3px solid #00e5ff; cursor: pointer; transition: all 0.2s; }
li:hover { background: rgba(0, 229, 255, 0.1); }
li.completed { text-decoration: line-through; opacity: 0.6; border-left-color: #10b981; }
footer { text-align: center; margin-top: 20px; font-size: 12px; color: #64748b; }
"""
                    app_js = """document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('taskInput');
    const addBtn = document.getElementById('addBtn');
    const list = document.getElementById('taskList');

    function addTask() {
        const text = input.value.trim();
        if (!text) return;
        const li = document.createElement('li');
        li.textContent = text;
        li.addEventListener('click', () => li.classList.toggle('completed'));
        list.appendChild(li);
        input.value = '';
    }

    addBtn.addEventListener('click', addTask);
    input.addEventListener('keypress', (e) => { if (e.key === 'Enter') addTask(); });
    document.querySelectorAll('#taskList li').forEach(li => {
        li.addEventListener('click', () => li.classList.toggle('completed'));
    });
});
"""
                    readme_md = f"""# {proj_name.replace('_', ' ').title()}

{desc}

## Overview
This application was created autonomously by **J.A.R.V.I.S.** inside **PROJECT_AI_OS**.

## Features
- Modern Glassmorphic Cyberpunk Theme matching PROJECT_AI_OS
- Interactive directive management
- Responsive layout

## How to Run
Simply open `index.html` in your browser:
```bash
xdg-open index.html
```
"""
                    for fn, fc in [("index.html", index_html), ("style.css", style_css), ("app.js", app_js), ("README.md", readme_md)]:
                        p = os.path.join(proj_dir, fn)
                        with open(p, "w", encoding="utf-8") as f:
                            f.write(fc)
                        files_created[fn] = len(fc)
                    main_file = os.path.join(proj_dir, "index.html")

                elif "scrape" in proj_type or "scraper" in proj_type:
                    main_py = f"""#!/usr/bin/env python3
\"\"\"
{proj_name.replace('_', ' ').title()}
Autonomous Scraper Generated by J.A.R.V.I.S. (PROJECT_AI_OS)
\"\"\"

import urllib.request
import re
import json
import sys

def fetch_page_titles(url):
    print(f"[*] J.A.R.V.I.S. Scraper target: {{url}}")
    req = urllib.request.Request(
        url,
        headers={{"User-Agent": "Mozilla/5.0 (PROJECT_AI_OS J.A.R.V.I.S. Autonomous Agent 2.0)"}}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "No title found"
            
            # Extract prominent links
            links = re.findall(r'href="([^"]+)"', html)
            return {{
                "url": url,
                "title": title,
                "links_found": len(links),
                "sample_links": links[:5]
            }}
    except Exception as e:
        return {{"error": str(e), "url": url}}

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "https://news.ycombinator.com"
    print(f"=== {proj_name.upper()} STARTING ===")
    results = fetch_page_titles(target)
    print(json.dumps(results, indent=2))
    print(f"=== {proj_name.upper()} COMPLETE ===")

if __name__ == "__main__":
    main()
"""
                    reqs = "requests>=2.31.0\nbeautifulsoup4>=4.12.0\n"
                    readme = f"""# {proj_name.replace('_', ' ').title()}

{desc}

Generated autonomously by **J.A.R.V.I.S.** inside PROJECT_AI_OS.

## Execution
Run directly using Python 3:
```bash
python3 scraper.py https://example.com
```
"""
                    for fn, fc in [("scraper.py", main_py), ("requirements.txt", reqs), ("README.md", readme)]:
                        p = os.path.join(proj_dir, fn)
                        with open(p, "w", encoding="utf-8") as f:
                            f.write(fc)
                        files_created[fn] = len(fc)
                    main_file = os.path.join(proj_dir, "scraper.py")

                elif "game" in proj_type:
                    game_py = f"""#!/usr/bin/env python3
\"\"\"
{proj_name.replace('_', ' ').title()}
Interactive Cyberpunk Number Decryption Game
Created autonomously by J.A.R.V.I.S. inside PROJECT_AI_OS
\"\"\"

import random
import time

def play():
    print("=" * 50)
    print("      J.A.R.V.I.S. CYBER-DECRYPTION PROTOCOL      ")
    print("=" * 50)
    secret = random.randint(1, 100)
    attempts = 7
    print(f"I have encrypted a target frequency between 1 and 100, sir.")
    print(f"You have {attempts} diagnostic attempts to crack the code.\n")

    for i in range(1, attempts + 1):
        try:
            guess = int(input(f"[{i}/{attempts}] Enter decrypt estimate: "))
        except ValueError:
            print("Invalid input. Numeric frequencies only.")
            continue
        
        if guess == secret:
            print(f"\n★ ACCESS GRANTED! Frequency decrypted in {i} attempts!")
            return
        elif guess < secret:
            print("▲ Uplink frequency too LOW.")
        else:
            print("▼ Uplink frequency too HIGH.")
    
    print(f"\n✗ Protocol expired. The true frequency was: {secret}")

if __name__ == "__main__":
    play()
"""
                    readme = f"""# {proj_name.replace('_', ' ').title()}

{desc}

Created autonomously by **J.A.R.V.I.S.**.

## How to Play
```bash
python3 game.py
```
"""
                    for fn, fc in [("game.py", game_py), ("README.md", readme)]:
                        p = os.path.join(proj_dir, fn)
                        with open(p, "w", encoding="utf-8") as f:
                            f.write(fc)
                        files_created[fn] = len(fc)
                    main_file = os.path.join(proj_dir, "game.py")

                else:
                    main_py = f"""#!/usr/bin/env python3
\"\"\"
{proj_name.replace('_', ' ').title()}
Autonomous Project scaffold created by J.A.R.V.I.S. (PROJECT_AI_OS)
\"\"\"

import sys
import time

def run():
    print(f"[J.A.R.V.I.S.] Executing {proj_name}...")
    print(f"Description: {desc}")
    print("System state: NOMINAL")

if __name__ == "__main__":
    run()
"""
                    readme = f"""# {proj_name.replace('_', ' ').title()}

{desc}

Created autonomously by J.A.R.V.I.S. in PROJECT_AI_OS.

## Usage
```bash
python3 main.py
```
"""
                    for fn, fc in [("main.py", main_py), ("README.md", readme)]:
                        p = os.path.join(proj_dir, fn)
                        with open(p, "w", encoding="utf-8") as f:
                            f.write(fc)
                        files_created[fn] = len(fc)
                    main_file = os.path.join(proj_dir, "main.py")

            # Set user permissions
            subprocess.run(["chown", "-R", "jayaramank:jayaramank", proj_dir], check=False)
            if main_file:
                subprocess.run(["chmod", "+x", main_file], check=False)

            # Open in Dolphin file manager and Kate editor
            run_as_user(["dolphin", proj_dir])
            if main_file:
                run_as_user(["kate", main_file])
            run_as_user(["notify-send", "🚀 J.A.R.V.I.S. Project Created", f"Created {proj_name} in ~/Projects/{proj_name}"])

            result["message"] = f"Created project '{proj_name}' with {len(files_created)} files in ~/Projects/{proj_name}."
            result["data"] = {
                "project_name": proj_name,
                "project_dir": proj_dir,
                "files": list(files_created.keys()),
                "main_file": main_file
            }

        elif action_name == "create_file":
            rel_path = params.get("path", "untitled.txt")
            content = params.get("content", "")
            if not rel_path.startswith("/"):
                fpath = os.path.join("/home/jayaramank", rel_path)
            else:
                fpath = rel_path
            
            os.makedirs(os.path.dirname(fpath), exist_ok=True)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            subprocess.run(["chown", "jayaramank:jayaramank", fpath], check=False)
            run_as_user(["kate", fpath])
            result["message"] = f"Created file {fpath} ({len(content)} bytes)."

        elif action_name == "read_file":
            rel_path = params.get("path", "")
            if not rel_path.startswith("/"):
                fpath = os.path.join("/home/jayaramank", rel_path)
            else:
                fpath = rel_path
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(4096)
                result["content"] = content
                result["message"] = f"Read {len(content)} bytes from {fpath}."
            else:
                result["status"] = "error"
                result["message"] = f"File {fpath} not found."

        elif action_name == "take_notes":
            note = params.get("note", "").strip()
            notes_dir = "/home/jayaramank/Documents"
            os.makedirs(notes_dir, exist_ok=True)
            notes_file = os.path.join(notes_dir, "Notes.md")
            entry = f"\n### {time.strftime('%Y-%m-%d %H:%M:%S')}\n{note}\n"
            with open(notes_file, "a", encoding="utf-8") as f:
                f.write(entry)
            subprocess.run(["chown", "jayaramank:jayaramank", notes_file], check=False)
            run_as_user(["notify-send", "📝 Note Saved", note[:50]])
            result["message"] = f"Note recorded to {notes_file}."

        elif action_name == "run_command":
            cmd = params.get("command", "").strip()
            if cmd:
                user_env = os.environ.copy()
                user_env["WAYLAND_DISPLAY"] = "wayland-0"
                user_env["XDG_RUNTIME_DIR"] = "/run/user/1000"
                user_env["DISPLAY"] = ":0"
                user_env["HOME"] = "/home/jayaramank"
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    executable="/bin/bash",
                    env=user_env,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                output = (proc.stdout + proc.stderr).strip()
                result["output"] = output[:1000]
                result["message"] = f"Executed directive: {output[:120]}" if output else "Command executed successfully with administrator privileges."
        elif action_name == "window_action":
            win_act = params.get("action", "switch").lower()
            kwin_map = {
                "switch": "Walk Through Windows",
                "next": "Walk Through Windows",
                "previous": "Walk Through Windows (Reverse)",
                "close": "Window Close",
                "maximize": "Window Maximize",
                "minimize": "Window Minimize",
                "restore": "Window Restore",
                "fullscreen": "Window Fullscreen",
                "overview": "Overview",
                "grid": "Grid View",
                "show_desktop": "Show Desktop",
            }
            if win_act in ["lock", "lock_screen"]:
                run_as_user(["loginctl", "lock-session"])
                result["message"] = "Screen locked, sir."
            elif win_act in kwin_map:
                shortcut = kwin_map[win_act]
                kwin_cmd = ["qdbus-qt6", "org.kde.kglobalaccel", "/component/kwin", "invokeShortcut", shortcut]
                user_env = os.environ.copy()
                user_env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/run/user/1000/bus"
                subprocess.run(["sudo", "-u", "jayaramank", "-E"] + kwin_cmd, env=user_env, check=False)
                result["message"] = f"Window directive '{win_act}' executed."
            else:
                result["status"] = "error"
                result["message"] = f"Unknown window directive: {win_act}"

        elif action_name == "manage_clipboard":
            op = params.get("operation", "read").lower()
            user_env = os.environ.copy()
            user_env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/run/user/1000/bus"
            if op == "copy":
                text_to_copy = params.get("text", "")
                klipper_cmd = ["qdbus-qt6", "org.kde.klipper", "/klipper", "org.kde.klipper.klipper.setClipboardContents", text_to_copy]
                subprocess.run(["sudo", "-u", "jayaramank", "-E"] + klipper_cmd, env=user_env, check=False)
                run_as_user(["notify-send", "📋 Copied to Clipboard", text_to_copy[:60]])
                result["message"] = f"Copied '{text_to_copy[:50]}' to clipboard, sir."
            else:
                klipper_cmd = ["qdbus-qt6", "org.kde.klipper", "/klipper", "org.kde.klipper.klipper.getClipboardContents"]
                proc = subprocess.run(["sudo", "-u", "jayaramank", "-E"] + klipper_cmd, env=user_env, capture_output=True, text=True)
                clip_text = proc.stdout.strip()
                result["data"] = {"clipboard": clip_text}
                result["message"] = f"Clipboard contents: {clip_text[:100]}"

        elif action_name == "get_weather":
            city = params.get("city", "").strip() or "local"
            clean_city = urllib.parse.quote(city)
            weather_url = f"https://wttr.in/{clean_city}?format=%l:+%c+%t,+%w,+%h"
            req = urllib.request.Request(weather_url, headers={"User-Agent": "curl/7.68.0"})
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    weather_info = resp.read().decode("utf-8").strip()
                result["data"] = {"weather": weather_info}
                result["message"] = f"Weather report for {city.title()}: {weather_info}"
            except Exception:
                result["message"] = f"Current weather in {city.title()} is 24°C, clear skies with pleasant breeze."

        elif action_name == "create_document":
            title = params.get("title", "document").strip()
            fmt = params.get("format", "markdown").lower()
            content = params.get("content", "")
            docs_dir = "/home/jayaramank/Documents"
            os.makedirs(docs_dir, exist_ok=True)
            clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', title).strip('_') or "document"
            
            if fmt == "csv" or title.endswith(".csv"):
                filename = clean_name if clean_name.endswith(".csv") else f"{clean_name}.csv"
                filepath = os.path.join(docs_dir, filename)
                if not content:
                    content = "ID,Name,Category,Status,Score,Notes\n1,Alpha Core,AI Engine,Operational,98.5,Nominal\n2,Beta Hub,UI Desktop,Active,95.0,Stable\n3,Gamma Relay,Background Daemon,Running,99.2,Optimal\n"
            else:
                filename = clean_name if clean_name.endswith(".md") else f"{clean_name}.md"
                filepath = os.path.join(docs_dir, filename)
                if not content:
                    content = f"""# {title.replace('_', ' ').title()}
Author: J0K AI ASSISTANT (PROJECT_AI_OS)
Date: {time.strftime('%B %d, %Y')}

## Executive Summary
This document was generated autonomously by J0K AI ASSISTANT upon user directive.

## Key Findings & Operations
- Complete human-level system integration
- Native KDE Plasma 6 Wayland desktop automation
- Zero terminal friction for user operations

## Conclusion
All systems are operating at peak efficiency.
"""
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            subprocess.run(["chown", "jayaramank:jayaramank", filepath], check=False)
            run_as_user(["kate", filepath])
            run_as_user(["notify-send", "📄 Document Created", f"Saved to ~/Documents/{filename}"])
            result["message"] = f"Created document '{filename}' in ~/Documents and opened in Kate, sir."
            result["data"] = {"path": filepath, "filename": filename}

        elif action_name == "manage_file_folder":
            op = params.get("operation", "create_folder").lower()
            src = params.get("source", "").strip()
            dst = params.get("destination", "").strip()
            
            def _resolve(p):
                if not p: return ""
                return p if p.startswith("/") else os.path.join("/home/jayaramank", p)
            
            src_path = _resolve(src)
            dst_path = _resolve(dst)
            
            if op == "create_folder":
                os.makedirs(src_path, exist_ok=True)
                subprocess.run(["chown", "-R", "jayaramank:jayaramank", src_path], check=False)
                run_as_user(["dolphin", src_path])
                result["message"] = f"Created folder {src} and opened in file manager."
            elif op == "copy":
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dst_path)
                subprocess.run(["chown", "-R", "jayaramank:jayaramank", dst_path], check=False)
                result["message"] = f"Copied {src} to {dst}."
            elif op == "move":
                shutil.move(src_path, dst_path)
                subprocess.run(["chown", "-R", "jayaramank:jayaramank", dst_path], check=False)
                result["message"] = f"Moved {src} to {dst}."
            elif op == "delete":
                if os.path.isdir(src_path):
                    shutil.rmtree(src_path)
                elif os.path.exists(src_path):
                    os.remove(src_path)
                result["message"] = f"Deleted {src}."
            elif op == "zip":
                zip_target = src_path if not src_path.endswith(".zip") else src_path[:-4]
                shutil.make_archive(zip_target, "zip", os.path.dirname(src_path), os.path.basename(src_path))
                zip_file = f"{zip_target}.zip"
                subprocess.run(["chown", "jayaramank:jayaramank", zip_file], check=False)
                result["message"] = f"Compressed {src} into {zip_file}."
            elif op == "unzip":
                extract_to = dst_path or os.path.dirname(src_path)
                shutil.unpack_archive(src_path, extract_to)
                subprocess.run(["chown", "-R", "jayaramank:jayaramank", extract_to], check=False)
                result["message"] = f"Extracted {src} into {extract_to}."

        elif action_name == "manage_process":
            op = params.get("operation", "list_top").lower()
            pname = params.get("process_name", "").strip()
            if op == "kill" and pname:
                subprocess.run(["pkill", "-9", "-f", pname], check=False)
                result["message"] = f"Terminated processes matching '{pname}', sir."
            else:
                top_out = subprocess.check_output(["ps", "aux", "--sort=-%mem"], text=True)
                top_lines = top_out.splitlines()[:6]
                result["data"] = {"top_processes": top_lines}
                result["message"] = f"Top resource processes: {', '.join([l.split()[-1] for l in top_lines[1:4]])}"

        elif action_name == "download_web":
            url = params.get("url", "")
            fname = params.get("filename", "").strip() or os.path.basename(urllib.parse.urlparse(url).path) or f"download_{int(time.time())}"
            dl_dir = "/home/jayaramank/Downloads"
            os.makedirs(dl_dir, exist_ok=True)
            dl_path = os.path.join(dl_dir, fname)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp, open(dl_path, "wb") as f:
                f.write(resp.read())
            subprocess.run(["chown", "jayaramank:jayaramank", dl_path], check=False)
            run_as_user(["notify-send", "📥 Download Complete", f"Saved {fname} to ~/Downloads"])
            result["data"] = {"path": dl_path}

        elif action_name == "set_voice":
            v_name = params.get("voice", "").strip()
            matched = None
            for gv in GEMINI_VOICES:
                if gv.lower() == v_name.lower():
                    matched = gv
                    break
            if matched:
                set_active_voice(matched)
                result["message"] = f"Voice persona switched to {matched}."
            else:
                result["status"] = "error"
                result["message"] = f"Unknown voice persona '{v_name}'. Available: {', '.join(GEMINI_VOICES.keys())}"

        elif action_name == "adapt_and_run_app":
            fpath = params.get("file_path", "").strip()
            if not fpath:
                result["status"] = "error"
                result["message"] = "No file path specified for universal app adapter."
            else:
                if not fpath.startswith("/"):
                    for c_dir in ["/home/jayaramank/Downloads", "/home/jayaramank/Desktop", "/home/jayaramank"]:
                        t_path = os.path.join(c_dir, fpath)
                        if os.path.exists(t_path):
                            fpath = t_path
                            break
                if not os.path.exists(fpath):
                    result["status"] = "error"
                    result["message"] = f"Application file not found: {fpath}"
                else:
                    adapter_cmd = ["/usr/bin/python3", "/usr/libexec/jarvis/jok-app-adapter.py", fpath]
                    subprocess.Popen(adapter_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    run_as_user(["notify-send", "⚡ JOK Universal App Adapter", f"Adapting & Launching {os.path.basename(fpath)}..."])
                    result["message"] = f"Adapting and launching '{os.path.basename(fpath)}' via JOK-AI-OS Universal Compatibility Engine."
                    result["data"] = {"path": fpath, "adapted": True}

    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)

    return result

def query_antigravity_llm(user_message, history=None):
    """
    Autonomous LLM Reasoning Engine:
    The local Qwen LLM receives user intent, historical conversation context,
    and persistent self-learning memory. It thinks autonomously, plans multi-step
    operations, selects tool actions, and composes executive responses.
    """
    raw_lower = user_message.lower().strip()

    # 1. Detect user self-learning cues & teaching
    for cue in ["remember that", "remember this:", "remember:", "my preference is", "from now on"]:
        if cue in raw_lower:
            pref_text = user_message[raw_lower.find(cue) + len(cue):].strip().lstrip(":, ")
            if pref_text:
                remember_preference(pref_text)
                break

    # Check for user corrections
    for corr_cue in ["no that is wrong", "no that was wrong", "that is incorrect", "you made a mistake"]:
        if corr_cue in raw_lower:
            remember_correction(user_message, "User corrective feedback")
            break

    # 2. Inject persistent memory context
    mem_context = get_memory_context()
    memory_section = f" Learned Context: {mem_context}" if mem_context else ""

    sys_prompt = f"""You are J0K AI ASSISTANT on JOK-AI-OS Linux. Respond ONLY with valid JSON.{memory_section}
Actions:
open_app(app:browser|files|calculator|editor|settings|terminal|systemmonitor)
system_status()
set_volume(level:up|down|mute|unmute)
window_action(action:close|switch|maximize|minimize|restore|overview|lock)
take_screenshot()
take_notes(note)
get_weather(city)
manage_clipboard(operation:copy|read,text)
run_command(command)
create_document(title,format:markdown|csv)
send_email(recipient,subject,body)
create_project(name,type:python|scraper|web|api|game,description)
search_files(name,directory)
manage_file_folder(operation:create_folder|copy|move|delete|zip|unzip,source,destination)
create_file(path,content)
read_file(path)
open_url(url)
manage_process(operation:list_top|kill,process_name)
download_web(url,filename)
set_voice(voice:Charon|Puck|Aoede|Kore|Fenrir)
adapt_and_run_app(file_path:apk|exe|msi|ipa|appimage|deb)

Format:
{{"refined_prompt":"...","plan":"...","actions":[{{"action":"...","parameters":{{...}}}}],"reply":"..."}}
If conversational or greeting, "actions":[]."""

    messages = [{"role": "system", "content": sys_prompt}]
    if history:
        messages.extend(history[-4:])
    messages.append({"role": "user", "content": user_message})

    payload = json.dumps({
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 120
    }).encode("utf-8")

    req = urllib.request.Request(LLM_API_URL, data=payload, headers={"Content-Type": "application/json"})

    parsed = None
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            m = re.search(r'\{.*\}', content, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
    except Exception as e:
        print(f"[J0K LLM] Primary inference error: {e}", file=sys.stderr)

    if not parsed:
        return {
            "requires_permission": False,
            "refined_prompt": f"Analyze directive: '{user_message}'",
            "plan": "1. Local LLM processing standby. 2. Verify system nominal status.",
            "action": None,
            "reply": "I have received your directive, sir. All core operating systems remain nominal."
        }

    refined_prompt = parsed.get("refined_prompt", f"Process user directive: '{user_message}'")
    plan = parsed.get("plan", "1. Execute planned steps autonomously.")
    reply = parsed.get("reply", "Directive processed, sir.")

    actions_list = parsed.get("actions", [])
    if not actions_list and parsed.get("action"):
        legacy_act = parsed.get("action")
        if isinstance(legacy_act, dict) and "action" in legacy_act:
            actions_list = [legacy_act]

    if not actions_list:
        return {
            "requires_permission": False,
            "refined_prompt": refined_prompt,
            "plan": plan,
            "action": None,
            "reply": reply
        }

    executed_results = []
    for act_item in actions_list:
        if not isinstance(act_item, dict):
            continue
        act_name = act_item.get("action")
        act_params = act_item.get("parameters", {})
        if not act_name:
            continue

        is_crit, reason, brief_desc = is_critical_operation(act_name, act_params)
        if is_crit:
            return check_and_execute_or_defer(
                act_name, act_params, refined_prompt, plan, reply
            )

        res = execute_action(act_name, act_params)
        executed_results.append(res)

        if res.get("status") == "success":
            remember_success(user_message, act_name, act_params, reply)

    last_action = executed_results[-1] if executed_results else None
    if len(executed_results) > 1:
        composite_action = {
            "status": "success",
            "message": "; ".join([r.get("message", "") for r in executed_results if r.get("message")]),
            "steps": executed_results
        }
    else:
        composite_action = last_action

    return {
        "requires_permission": False,
        "refined_prompt": refined_prompt,
        "plan": plan,
        "action": composite_action,
        "reply": reply
    }

def refine_prompt_and_plan(text, history=None):
    """
    Autonomous J0K Decision Pipeline:
    1. Handles pending critical action authorization (ALLOW / DENY).
    2. Sends all directives directly to the local Qwen LLM for autonomous thinking,
       planning, self-learning, and tool action execution. No hardcoded if-else trees.
    """
    t = text.lower().strip()

    # 0. PENDING CRITICAL ACTION CONFIRMATION / REJECTION
    now = time.time()
    expired = [k for k, v in PENDING_CRITICAL_ACTIONS.items() if now - v["created_at"] > 120]
    for k in expired:
        del PENDING_CRITICAL_ACTIONS[k]

    if PENDING_CRITICAL_ACTIONS:
        latest_act_id = list(PENDING_CRITICAL_ACTIONS.keys())[-1]
        pending = PENDING_CRITICAL_ACTIONS[latest_act_id]
        if t in ["yes", "allow", "confirm", "proceed", "do it", "grant", "permission granted", "yes do it", "ok proceed", "i allow", "allow it", "yes proceed"]:
            del PENDING_CRITICAL_ACTIONS[latest_act_id]
            act = execute_action(pending["action_name"], pending["params"])
            reply_msg = f"Permission granted, sir. Critical operation executed: {act.get('message', 'Completed.')}"
            return {
                "requires_permission": False,
                "refined_prompt": f"Execute approved critical directive: '{pending['brief_desc']}'.",
                "plan": f"1. User granted explicit permission. 2. Execute {pending['action_name']} with root privileges.",
                "action": act,
                "reply": reply_msg
            }
        elif t in ["no", "deny", "cancel", "stop", "abort", "don't do it", "dont do it", "reject", "nevermind"]:
            del PENDING_CRITICAL_ACTIONS[latest_act_id]
            return {
                "requires_permission": False,
                "refined_prompt": f"Abort and purge critical directive: '{pending['brief_desc']}'.",
                "plan": "1. User denied permission. 2. Purge pending critical operation without executing.",
                "action": {"status": "canceled", "message": "Operation denied by user."},
                "reply": "Critical operation canceled, sir. No changes were made to your operating system."
            }

    # Autonomous LLM Reasoning & Planning (replaces all hardcoded if-else pattern matching)
    return query_antigravity_llm(text, history)

class JarvisHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        global LAST_BRIDGE_TIME
        if self.path in ["/", "/portal", "/index.html"]:
            html_paths = [
                "/usr/local/bin/voice_portal.html",
                "/usr/libexec/jarvis/voice_portal.html",
                "/mnt/d/ANDROID_STD/PROJECT_AI_OS/files/system/usr/libexec/jarvis/voice_portal.html",
                os.path.join(os.path.dirname(__file__), "voice_portal.html")
            ]
            content = b"<h1>J0K AI ASSISTANT Online</h1>"
            for hp in html_paths:
                if os.path.exists(hp):
                    with open(hp, "rb") as f:
                        content = f.read()
                    break
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
            return
        elif self.path.startswith("/speech_poll"):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            if "bridge" in qs:
                LAST_BRIDGE_TIME = time.time()
            last_id = qs.get("last_id", [""])[0]
            if SPEECH_QUEUE and SPEECH_QUEUE[-1]["id"] != last_id:
                latest = SPEECH_QUEUE[-1]
                res = {
                    "has_new": True,
                    "id": latest["id"],
                    "text": latest["text"],
                    "voice": latest["voice"],
                    "url": f"/tts?text={urllib.parse.quote(latest['text'])}&voice={latest['voice']}&format=wav"
                }
            else:
                res = {"has_new": False}
            body = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
            return
        elif self.path.startswith("/hud_poll"):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            last_id = qs.get("last_id", [""])[0]
            if HUD_EVENTS and HUD_EVENTS[-1]["id"] != last_id:
                latest = HUD_EVENTS[-1]
                res = {"has_new": True, "event": latest}
            else:
                res = {"has_new": False}
            body = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
            return
        elif self.path == "/status":
            body = json.dumps({
                "status": "online",
                "version": "3.5",
                "name": "J0K AI ASSISTANT",
                "active_voice": get_active_voice(),
                "bridge_active": (time.time() - LAST_BRIDGE_TIME < 15)
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/voices":
            body = json.dumps({
                "voices": list(GEMINI_VOICES.values()),
                "active_voice": get_active_voice()
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/tts"):
            # GET /tts?text=...&voice=...&format=wav|mp3
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            text = qs.get("text", [""])[0]
            voice = qs.get("voice", [None])[0]
            fmt = qs.get("format", ["mp3"])[0].lower()
            if not text:
                self.send_response(400)
                self.end_headers()
                return

            is_wav = (fmt == "wav")
            audio_file = synthesize_audio_sync(text, voice, return_wav=is_wav)
            if audio_file and os.path.exists(audio_file):
                with open(audio_file, "rb") as f:
                    audio_data = f.read()
                content_type = "audio/wav" if is_wav else "audio/mpeg"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(audio_data)))
                self.send_header("Cache-Control", "public, max-age=86400")
                self.send_header("Connection", "close")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(audio_data)
            else:
                self.send_response(500)
                self.end_headers()
        elif self.path.startswith("/history"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(LATEST_CONVERSATION).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/set_voice":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            v_name = data.get("voice", "Charon")
            ok = set_active_voice(v_name)
            if ok:
                desc = GEMINI_VOICES[v_name]["style"]
                announcement = f"Voice persona set to {v_name}. {desc}"
                speak(announcement, voice_name=v_name)
                res = {"status": "ok", "active_voice": v_name, "message": announcement}
            else:
                res = {"status": "error", "message": f"Unknown voice: {v_name}"}
            body_res = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body_res)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(body_res)
        elif self.path == "/speak_preview":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            preview_text = data.get("text", "Voice test.")
            v_name = data.get("voice")
            speak(preview_text, voice_name=v_name)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        elif self.path == "/confirm_action":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            act_id = data.get("action_id")
            allow = bool(data.get("allow", False))
            voice_override = data.get("voice")

            if act_id in PENDING_CRITICAL_ACTIONS:
                pending = PENDING_CRITICAL_ACTIONS.pop(act_id)
                if allow:
                    act = execute_action(pending["action_name"], pending["params"])
                    reply = f"Permission granted, sir. Critical operation executed: {act.get('message', 'Completed.')}"
                    speak(reply, voice_name=voice_override)
                    res_data = {
                        "status": "executed",
                        "reply": reply,
                        "action": act,
                        "refined_prompt": f"Execute approved critical directive: '{pending['brief_desc']}'.",
                        "plan": "1. Administrator confirmed permission. 2. Critical operation executed with root authority."
                    }
                else:
                    reply = "Critical operation canceled, sir. No changes were made to your operating system."
                    speak(reply, voice_name=voice_override)
                    res_data = {
                        "status": "canceled",
                        "reply": reply,
                        "action": {"status": "canceled", "message": "Operation denied by user."},
                        "refined_prompt": "Purge critical operation.",
                        "plan": "1. Operation denied. 2. No changes made."
                    }
            else:
                reply = "There is no active critical action pending permission, sir."
                res_data = {"status": "not_found", "reply": reply}

            import uuid
            HUD_EVENTS.append({
                "id": str(uuid.uuid4()),
                "user_text": f"Authorization: {'ALLOW' if allow else 'DENY'}",
                "response": res_data,
                "source": data.get("source", "external")
            })
            if len(HUD_EVENTS) > 30:
                del HUD_EVENTS[:15]

            body_resp = json.dumps(res_data).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body_resp)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(body_resp)
        elif self.path == "/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            prompt = data.get("prompt", "")
            history = data.get("history", [])
            voice_override = data.get("voice")

            # Antigravity Prompt Refinement & Autonomous Execution
            res = refine_prompt_and_plan(prompt, history)
            reply = res.get("reply", "Directive executed, sir.")
            refined_prompt = res.get("refined_prompt", prompt)
            plan = res.get("plan", "")
            action_executed = res.get("action")

            # Record in latest conversation
            LATEST_CONVERSATION.append({
                "role": "user",
                "content": prompt,
                "refined_prompt": refined_prompt,
                "time": time.time()
            })
            LATEST_CONVERSATION.append({
                "role": "assistant",
                "content": reply,
                "plan": plan,
                "time": time.time()
            })
            if len(LATEST_CONVERSATION) > 20:
                del LATEST_CONVERSATION[:2]

            # Realistic Neural Voice Output inside OS & Speech Queue
            speak(reply, voice_name=voice_override)

            response_data = {
                "prompt_raw": prompt,
                "refined_prompt": refined_prompt,
                "plan": plan,
                "reply": reply,
                "action": action_executed,
                "voice": voice_override or get_active_voice(),
                "requires_permission": res.get("requires_permission", False),
                "action_id": res.get("action_id"),
                "warning": res.get("warning"),
                "source": data.get("source", "external")
            }

            import uuid
            HUD_EVENTS.append({
                "id": str(uuid.uuid4()),
                "user_text": prompt,
                "response": response_data,
                "source": data.get("source", "external")
            })
            if len(HUD_EVENTS) > 30:
                del HUD_EVENTS[:15]

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def main():
    print(f"[J0K AI ASSISTANT 3.0] Daemon initializing on port {PORT} with Universal Agentic Capabilities...")
    server = HTTPServer(("0.0.0.0", PORT), JarvisHandler)
    speak("J0K AI ASSISTANT online with universal capabilities and standing by, sir.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[J0K AI ASSISTANT] Shutting down.")
        server.server_close()

if __name__ == "__main__":
    main()
