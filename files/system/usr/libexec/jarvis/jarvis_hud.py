#!/usr/bin/env python3
"""
J.A.R.V.I.S. Ambient Desktop HUD
PROJECT_AI_OS - Floating Voice & Conversational Desktop Interface
"""

import os
import sys
import json
import time
import shutil
import urllib.request
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox

JARVIS_API = "http://127.0.0.1:9090/chat"

class JarvisHUD(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("J.A.R.V.I.S. Ambient Assistant")
        self.geometry("540x620")
        self.minsize(450, 500)
        self.configure(bg="#0b0f19")

        # Keep on top option
        self.attributes("-topmost", True)

        self.history = []
        self.is_listening = False

        self.setup_ui()
        self.check_status()

    def setup_ui(self):
        # Header Frame
        header = tk.Frame(self, bg="#0f172a", height=60)
        header.pack(fill=tk.X)

        # Glowing Arc Indicator / Title
        self.title_label = tk.Label(
            header,
            text="● J.A.R.V.I.S. CORE",
            font=("Segoe UI", 13, "bold"),
            fg="#00e5ff",
            bg="#0f172a",
            padx=15,
            pady=12
        )
        self.title_label.pack(side=tk.LEFT)

        self.status_label = tk.Label(
            header,
            text="ONLINE",
            font=("Segoe UI", 9, "bold"),
            fg="#10b981",
            bg="#0f172a",
            padx=15
        )
        self.status_label.pack(side=tk.RIGHT)

        # Quick Actions Bar
        actions_bar = tk.Frame(self, bg="#0b0f19", pady=6)
        actions_bar.pack(fill=tk.X, padx=12)

        quick_buttons = [
            ("🌐 Browser", "Open the web browser"),
            ("📁 Files", "Open my files"),
            ("📊 Status", "Give me a full system status report"),
            ("📸 Screenshot", "Take a screenshot"),
        ]

        for text, prompt in quick_buttons:
            btn = tk.Button(
                actions_bar,
                text=text,
                font=("Segoe UI", 9),
                bg="#1e293b",
                fg="#e2e8f0",
                activebackground="#0284c7",
                activeforeground="#ffffff",
                relief=tk.FLAT,
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda p=prompt: self.send_prompt(p)
            )
            btn.pack(side=tk.LEFT, padx=3)

        # Chat Feed
        feed_frame = tk.Frame(self, bg="#0b0f19")
        feed_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self.chat_display = tk.Text(
            feed_frame,
            bg="#0f172a",
            fg="#f8fafc",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED,
            padx=12,
            pady=10
        )
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(feed_frame, command=self.chat_display.yview, bg="#1e293b")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.config(yscrollcommand=scrollbar.set)

        # Tag Styles
        self.chat_display.tag_config("user", foreground="#38bdf8", font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_config("jarvis", foreground="#f1f5f9", font=("Segoe UI", 10))
        self.chat_display.tag_config("action", foreground="#34d399", font=("Segoe UI", 9, "italic"))
        self.chat_display.tag_config("system", foreground="#94a3b8", font=("Segoe UI", 9, "italic"))

        # Input Area Frame
        input_frame = tk.Frame(self, bg="#0f172a", pady=8, padx=10)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Mic Button (Push to Talk / Voice)
        self.mic_btn = tk.Button(
            input_frame,
            text="🎙️ Voice",
            font=("Segoe UI", 10, "bold"),
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.toggle_voice
        )
        self.mic_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Text Entry
        self.entry = tk.Entry(
            input_frame,
            font=("Segoe UI", 11),
            bg="#1e293b",
            fg="#ffffff",
            insertbackground="#00e5ff",
            relief=tk.FLAT
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=5)
        self.entry.bind("<Return>", lambda e: self.on_send())
        self.entry.focus_set()

        # Send Button
        send_btn = tk.Button(
            input_frame,
            text="Send",
            font=("Segoe UI", 10, "bold"),
            bg="#10b981",
            fg="#ffffff",
            activebackground="#059669",
            relief=tk.FLAT,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.on_send
        )
        send_btn.pack(side=tk.RIGHT)

        self.append_message("JARVIS", "At your service, sir. What can I assist you with today?", "jarvis")

    def append_message(self, sender, text, tag):
        self.chat_display.config(state=tk.NORMAL)
        if sender:
            self.chat_display.insert(tk.END, f"{sender}: ", tag)
        self.chat_display.insert(tk.END, f"{text}\n\n", tag)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def check_status(self):
        def _check():
            try:
                with urllib.request.urlopen("http://127.0.0.1:9090/status", timeout=2) as r:
                    self.status_label.config(text="ONLINE", fg="#10b981")
            except Exception:
                self.status_label.config(text="CONNECTING...", fg="#f59e0b")
            self.after(5000, self.check_status)
        threading.Thread(target=_check, daemon=True).start()

    def on_send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.send_prompt(text)

    def send_prompt(self, prompt):
        self.append_message("You", prompt, "user")
        self.title_label.config(text="● J.A.R.V.I.S. (Thinking...)", fg="#f59e0b")

        def _worker():
            try:
                payload = json.dumps({"prompt": prompt, "history": self.history[-6:]}).encode("utf-8")
                req = urllib.request.Request(JARVIS_API, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=35) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    reply = res.get("reply", "")
                    action = res.get("action")

                    self.after(0, lambda: self.handle_reply(prompt, reply, action))
            except Exception as e:
                self.after(0, lambda: self.append_message("JARVIS", f"Unable to complete request: {e}", "system"))
                self.after(0, lambda: self.title_label.config(text="● J.A.R.V.I.S. CORE", fg="#00e5ff"))

        threading.Thread(target=_worker, daemon=True).start()

    def handle_reply(self, user_prompt, reply, action):
        self.history.append({"role": "user", "content": user_prompt})
        self.history.append({"role": "assistant", "content": reply})

        self.append_message("JARVIS", reply, "jarvis")
        if action and action.get("message"):
            self.append_message("", f"⚡ [Action] {action.get('message')}", "action")

        self.title_label.config(text="● J.A.R.V.I.S. CORE", fg="#00e5ff")

    def toggle_voice(self):
        if self.is_listening:
            return
        self.is_listening = True
        self.mic_btn.config(text="🔴 Listening...", bg="#ef4444")
        self.title_label.config(text="● J.A.R.V.I.S. (Listening...)", fg="#ef4444")

        def _listen():
            # Record 4 seconds of audio or until silence
            rec_file = "/tmp/jarvis_input.wav"
            try:
                if shutil.which("arecord"):
                    subprocess.run(["arecord", "-d", "4", "-f", "cd", "-t", "wav", rec_file],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif shutil.which("sox"):
                    subprocess.run(["sox", "-d", rec_file, "trim", "0", "4"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"Record error: {e}", file=sys.stderr)

            self.after(0, self.finish_voice)

        threading.Thread(target=_listen, daemon=True).start()

    def finish_voice(self):
        self.is_listening = False
        self.mic_btn.config(text="🎙️ Voice", bg="#0284c7")
        self.title_label.config(text="● J.A.R.V.I.S. CORE", fg="#00e5ff")
        # For immediate testing without a heavy whisper model, prompt the user or handle
        self.append_message("System", "Audio captured. Processing voice command...", "system")

if __name__ == "__main__":
    app = JarvisHUD()
    app.mainloop()
