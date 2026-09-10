#!/usr/bin/env python3
"""
J.A.R.V.I.S. Ambient Operating System Assistant Daemon
PROJECT_AI_OS - Core Background Agent & Tool Execution Bridge
"""

import os
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
MODEL_NAME = "qwen2.5:3b"

SYSTEM_PROMPT = """You are J.A.R.V.I.S., the ambient, intelligent, and refined AI operating system companion for PROJECT_AI_OS.
Inspired by Tony Stark's assistant in Iron Man, you speak with a polite, calm, concise, and capable tone (referring to the user occasionally as "sir" or by their name).
You help the user navigate and operate their computer entirely through natural conversation without requiring them to type terminal commands.

When the user asks you to perform an action on the computer, YOU MUST respond with a JSON action block at the END of your message in the exact format:
```json
{"action": "<action_name>", "parameters": {<key_values>}}
```

Available actions:
1. open_app: {"app": "<browser|files|calculator|editor|settings|terminal|discover>"}
2. system_status: {}
3. set_volume: {"level": "<up|down|mute|unmute|percentage>"}
4. take_screenshot: {}
5. search_files: {"query": "<filename_or_pattern>"}
6. open_url: {"url": "<https_url>"}

If no system action is required, simply respond concisely and intelligently. Keep spoken responses under 2-3 sentences.
"""

def speak(text):
    """Speaks text using espeak-ng in a polite British accent (like Jarvis)."""
    clean_text = text.split("```")[0].strip()
    if not clean_text:
        return
    def _run():
        try:
            if shutil.which("espeak-ng"):
                subprocess.run(["espeak-ng", "-v", "en-gb", "-s", "150", "-p", "45", clean_text],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif shutil.which("espeak"):
                subprocess.run(["espeak", "-v", "en-gb", "-s", "150", "-p", "45", clean_text],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[Jarvis Voice] TTS Error: {e}", file=sys.stderr)
    threading.Thread(target=_run, daemon=True).start()

def execute_action(action_name, params):
    """Executes system actions on behalf of the user."""
    result = {"status": "success", "message": ""}
    try:
        if action_name == "open_app":
            app = params.get("app", "").lower()
            app_map = {
                "browser": ["xdg-open", "https://duckduckgo.com"],
                "firefox": ["firefox"],
                "files": ["dolphin", os.path.expanduser("~")],
                "dolphin": ["dolphin", os.path.expanduser("~")],
                "calculator": ["kcalc"],
                "editor": ["kate"],
                "settings": ["systemsettings"],
                "terminal": ["konsole"],
                "discover": ["plasma-discover"],
            }
            cmd = app_map.get(app, ["xdg-open", app])
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
                    subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%+"])
                elif lvl == "down":
                    subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"])
                elif lvl == "mute":
                    subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1"])
                elif lvl == "unmute":
                    subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"])
            result["message"] = f"Volume adjusted ({lvl})."

        elif action_name == "take_screenshot":
            pic_dir = os.path.expanduser("~/Pictures/Screenshots")
            os.makedirs(pic_dir, exist_ok=True)
            filename = os.path.join(pic_dir, f"screenshot_{int(time.time())}.png")
            if shutil.which("spectacle"):
                subprocess.Popen(["spectacle", "-b", "-n", "-o", filename])
            result["message"] = f"Screenshot captured to {filename}."

        elif action_name == "open_url":
            url = params.get("url", "https://duckduckgo.com")
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            result["message"] = f"Opening {url}."

        elif action_name == "search_files":
            q = params.get("query", "")
            out = subprocess.check_output(["find", os.path.expanduser("~"), "-iname", f"*{q}*", "-maxdepth", "3"], text=True)
            files = [f for f in out.splitlines() if f][:5]
            result["files"] = files
            result["message"] = f"Found {len(files)} matching files."

    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)

    return result

def query_llm(user_message, history=None):
    """Queries the local RamaLama Qwen model."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    payload = json.dumps({
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 300
    }).encode("utf-8")

    req = urllib.request.Request(LLM_API_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return content
    except Exception as e:
        return f"I apologize, sir. I am currently unable to reach the neural core at {LLM_API_URL}. Error: {e}"

class JarvisHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "online", "version": "1.0", "name": "JARVIS"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            prompt = data.get("prompt", "")
            history = data.get("history", [])

            # Get reply from LLM
            reply = query_llm(prompt, history)

            # Check if an action was requested in the reply
            action_executed = None
            clean_reply = reply
            if "```json" in reply:
                try:
                    parts = reply.split("```json")
                    clean_reply = parts[0].strip()
                    action_json = parts[1].split("```")[0].strip()
                    act = json.loads(action_json)
                    action_name = act.get("action")
                    params = act.get("parameters", {})
                    action_executed = execute_action(action_name, params)
                except Exception as e:
                    print(f"Action parse error: {e}", file=sys.stderr)

            # Voice output
            speak(clean_reply)

            response_data = {
                "reply": clean_reply,
                "action": action_executed
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def main():
    print(f"[JARVIS] Daemon initializing on port {PORT}...")
    server = HTTPServer(("127.0.0.1", PORT), JarvisHandler)
    speak("Jarvis online and standing by, sir.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[JARVIS] Shutting down.")
        server.server_close()

if __name__ == "__main__":
    main()
