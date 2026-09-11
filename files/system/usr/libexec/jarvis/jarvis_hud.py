#!/usr/bin/env python3
"""
J0K AI ASSISTANT - Ambient Desktop HUD & Showcase
PROJECT_AI_OS - Native Qt6 (PySide6) Floating Voice & Conversational Assistant
Features:
- Right-side pinned Star Shape Button (⭐) that stays always on top
- Click/Press Star Button to toggle / pop up the J0K AI ASSISTANT Showcase
- Full conversational intelligence, Arc Reactor voice input, 16 quick directives
"""

import sys
import os
import html
import json
import time
import math
import urllib.request
import threading
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QScrollArea, QFrame,
    QGridLayout, QGraphicsDropShadowEffect, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPoint, QRectF, QPointF
from PySide6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPainter, QPainterPath,
    QBrush, QPen, QLinearGradient, QRadialGradient, QCursor
)

API_ENDPOINT = os.environ.get("J0K_API", "http://127.0.0.1:9090")

class WorkerSignals(QObject):
    response_received = Signal(str, object) # user_text, j0k_reply_or_dict
    status_updated = Signal(bool, str)

def make_star_path(cx, cy, r_outer, r_inner, points=5):
    """Generates a 5-pointed star QPainterPath."""
    path = QPainterPath()
    step = math.pi / points
    start_angle = -math.pi / 2
    for i in range(2 * points):
        r = r_outer if i % 2 == 0 else r_inner
        angle = start_angle + i * step
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.closeSubpath()
    return path


class StarButton(QWidget):
    """
    Floating right-side Star Shape Button (⭐).
    Always stays on top on the right side of the screen.
    When clicked/pressed, pops up the J0K AI ASSISTANT Showcase.
    """
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("J0K_STAR_BUTTON")
        self.setObjectName("j0k_star_btn")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(76, 76)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("⭐ Click to show J0K AI ASSISTANT Showcase")

        self.hovered = False
        self.pressed = False
        self.pulse_phase = 0.0
        self.drag_start_pos = None

        # Subtle pulsing animation timer
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.on_pulse)
        self.pulse_timer.start(50)

    def on_pulse(self):
        self.pulse_phase = (self.pulse_phase + 0.08) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # 1. Outer Glow Aura (Gold / Cyan Neon)
        glow_size = 32 + (3 * math.sin(self.pulse_phase) if not self.hovered else 5)
        glow_grad = QRadialGradient(cx, cy, glow_size + 6)
        if self.hovered:
            glow_grad.setColorAt(0.0, QColor(0, 229, 255, 180))
            glow_grad.setColorAt(0.5, QColor(245, 158, 11, 140))
            glow_grad.setColorAt(1.0, QColor(245, 158, 11, 0))
        else:
            glow_grad.setColorAt(0.0, QColor(245, 158, 11, 140))
            glow_grad.setColorAt(0.6, QColor(217, 119, 6, 80))
            glow_grad.setColorAt(1.0, QColor(217, 119, 6, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glow_grad))
        painter.drawEllipse(QRectF(cx - glow_size - 4, cy - glow_size - 4, (glow_size + 4) * 2, (glow_size + 4) * 2))

        # 2. Outer Circular Backing Plate with Glassmorphism
        bg_radius = 32
        bg_rect = QRectF(cx - bg_radius, cy - bg_radius, bg_radius * 2, bg_radius * 2)
        plate_grad = QLinearGradient(0, 0, w, h)
        plate_grad.setColorAt(0.0, QColor(15, 23, 42, 230))
        plate_grad.setColorAt(1.0, QColor(7, 11, 20, 245))
        painter.setBrush(QBrush(plate_grad))

        border_color = QColor(0, 229, 255) if self.hovered else QColor(245, 158, 11)
        painter.setPen(QPen(border_color, 2.0))
        painter.drawEllipse(bg_rect)

        # 3. 5-Pointed Geometric Star
        r_outer = 25.0 if not (self.hovered or self.pressed) else (27.0 if self.hovered else 24.0)
        r_inner = 11.5 if not (self.hovered or self.pressed) else (12.5 if self.hovered else 11.0)
        star_path = make_star_path(cx, cy - 1, r_outer, r_inner, points=5)

        star_grad = QLinearGradient(0, cy - r_outer, 0, cy + r_outer)
        if self.hovered:
            star_grad.setColorAt(0.0, QColor(255, 255, 255))
            star_grad.setColorAt(0.3, QColor(255, 224, 102))
            star_grad.setColorAt(0.8, QColor(245, 158, 11))
            star_grad.setColorAt(1.0, QColor(217, 119, 6))
        else:
            star_grad.setColorAt(0.0, QColor(255, 235, 120))
            star_grad.setColorAt(0.5, QColor(245, 158, 11))
            star_grad.setColorAt(1.0, QColor(180, 83, 9))

        painter.setBrush(QBrush(star_grad))
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1.2))
        painter.drawPath(star_path)

        # 4. Center J0K Badge
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.setPen(QColor(10, 15, 29))
        painter.drawText(QRectF(cx - 15, cy - 6, 30, 12), Qt.AlignCenter, "J0K")

    def enterEvent(self, event):
        self.hovered = True
        self.update()

    def leaveEvent(self, event):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressed = True
            self.drag_start_pos = event.globalPosition().toPoint()
            self.update()

    def mouseMoveEvent(self, event):
        if self.pressed and self.drag_start_pos:
            delta = event.globalPosition().toPoint() - self.drag_start_pos
            if delta.manhattanLength() > 5:
                screen = QApplication.primaryScreen().availableGeometry()
                new_y = self.y() + delta.y()
                new_y = max(screen.top() + 10, min(new_y, screen.bottom() - self.height() - 10))
                self.move(self.x(), new_y)
                self.drag_start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressed = False
            self.update()
            self.clicked.emit()

    def dock_to_right_edge(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - 8
        y = screen.top() + (screen.height() - self.height()) // 2
        self.move(x, y)


class J0KShowcaseWindow(QWidget):
    """
    The J0K AI ASSISTANT Showcase Popup Window.
    Pops up smoothly beside the right-side Star button with full capabilities.
    """
    def __init__(self, star_button):
        super().__init__()
        self.star_button = star_button
        self.setWindowTitle("J0K_SHOWCASE_WINDOW")
        self.setObjectName("j0k_showcase_window")
        self.resize(520, 690)
        self.setMinimumSize(460, 580)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.signals = WorkerSignals()
        self.signals.response_received.connect(self.on_response_received)
        self.signals.status_updated.connect(self.on_status_updated)

        self.is_listening = False
        self.history = []
        self.drag_pos = None

        self.init_ui()
        self.check_daemon_status()

        # Status check timer every 4 seconds
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_daemon_status)
        self.status_timer.start(4000)

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)

        # Main glassmorphic container frame
        self.container = QFrame(self)
        self.container.setObjectName("mainFrame")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(16, 14, 16, 16)
        container_layout.setSpacing(12)

        # Styling
        self.setStyleSheet("""
            QFrame#mainFrame {
                background-color: #070b14;
                border: 2px solid #00e5ff;
                border-radius: 16px;
            }
            QWidget {
                color: #e2e8f0;
                font-family: 'Segoe UI', 'Ubuntu', sans-serif;
            }
            QFrame#headerFrame {
                background-color: #0d1527;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
            QTextEdit#chatArea {
                background-color: #0a0f1d;
                border: 1px solid #1e293b;
                border-radius: 10px;
                font-size: 13px;
                color: #cbd5e1;
                padding: 10px;
            }
            QLineEdit#inputField {
                background-color: #0d1527;
                border: 1px solid #0284c7;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                color: #f8fafc;
            }
            QLineEdit#inputField:focus {
                border: 1px solid #00e5ff;
                background-color: #0e1a33;
            }
            QPushButton {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #94a3b8;
                font-weight: bold;
                padding: 8px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                border: 1px solid #00e5ff;
                color: #00e5ff;
            }
            QPushButton#sendBtn {
                background-color: #0284c7;
                border: 1px solid #38bdf8;
                border-radius: 8px;
                color: #ffffff;
                font-size: 12px;
                padding: 10px 18px;
            }
            QPushButton#sendBtn:hover {
                background-color: #0369a1;
                border: 1px solid #00e5ff;
            }
            QPushButton#micBtn {
                background-color: #1e1b4b;
                border: 1px solid #6366f1;
                border-radius: 8px;
                color: #a5b4fc;
                font-size: 12px;
                padding: 10px 16px;
            }
            QPushButton#micBtn:hover {
                background-color: #312e81;
                border: 1px solid #818cf8;
                color: #ffffff;
            }
            QPushButton#winBtn {
                background-color: transparent;
                border: none;
                color: #94a3b8;
                font-size: 14px;
                padding: 2px 6px;
            }
            QPushButton#winBtn:hover {
                color: #ef4444;
            }
        """)

        # Drop shadow for floating effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 229, 255, 90))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        # 1. Header with Drag Handle, Brand & Window Controls
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)

        star_icon = QLabel("⭐")
        star_icon.setStyleSheet("font-size: 16px;")

        title_label = QLabel("J0K AI ASSISTANT")
        title_font = QFont("Segoe UI", 12, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #00e5ff; font-weight: 800; letter-spacing: 1px;")

        self.status_label = QLabel("● CONNECTING...")
        self.status_label.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 11px;")

        min_btn = QPushButton("🗕")
        min_btn.setObjectName("winBtn")
        min_btn.setToolTip("Minimize to Star Button")
        min_btn.clicked.connect(self.hide)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("winBtn")
        close_btn.setToolTip("Close to Star Button")
        close_btn.clicked.connect(self.hide)

        header_layout.addWidget(star_icon)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addSpacing(10)
        header_layout.addWidget(min_btn)
        header_layout.addWidget(close_btn)

        container_layout.addWidget(header_frame)

        # Voice Persona Selection Bar (Gemini-Style Realistic Voices)
        voice_bar = QFrame()
        voice_bar.setStyleSheet("""
            QFrame {
                background-color: #0b1324;
                border: 1px solid #1e3a5f;
                border-radius: 10px;
                padding: 2px 4px;
            }
        """)
        voice_layout = QHBoxLayout(voice_bar)
        voice_layout.setContentsMargins(8, 4, 8, 4)
        voice_layout.setSpacing(8)

        v_label = QLabel("🎙️ Voice:")
        v_label.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px;")

        self.voice_combo = QComboBox()
        self.voice_combo.setStyleSheet("""
            QComboBox {
                background-color: #0d1527;
                border: 1px solid #0284c7;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                color: #38bdf8;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #00e5ff;
            }
            QComboBox QAbstractItemView {
                background-color: #070b14;
                border: 1px solid #00e5ff;
                color: #e2e8f0;
                selection-background-color: #1e3a8a;
            }
        """)
        self.voice_combo.addItem("Charon (Deep & Calm - Gemini)", "Charon")
        self.voice_combo.addItem("Puck (Upbeat & Friendly - Gemini)", "Puck")
        self.voice_combo.addItem("Aoede (Warm & Articulate - Gemini)", "Aoede")
        self.voice_combo.addItem("Kore (Gentle & Conversational - Gemini)", "Kore")
        self.voice_combo.addItem("Fenrir (Sharp & Executive - Gemini)", "Fenrir")
        self.voice_combo.currentIndexChanged.connect(self.on_voice_changed)

        self.test_voice_btn = QPushButton("▶ Test")
        self.test_voice_btn.setToolTip("Listen to selected realistic Gemini voice")
        self.test_voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #38bdf8;
                border-radius: 6px;
                color: #38bdf8;
                font-size: 10px;
                font-weight: bold;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)
        self.test_voice_btn.clicked.connect(self.test_current_voice)

        voice_layout.addWidget(v_label)
        voice_layout.addWidget(self.voice_combo, stretch=1)
        voice_layout.addWidget(self.test_voice_btn)

        container_layout.addWidget(voice_bar)

        # 2. Conversation Log Area
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatArea")
        self.chat_display.setReadOnly(True)
        container_layout.addWidget(self.chat_display, stretch=1)

        # Welcome message
        self.append_j0k_message("Good day, sir. I am <b>J0K AI ASSISTANT</b>. All core systems are nominal. Speak aloud or type any command.")

        # 4. Input Controls (Mic + Text + Send)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.mic_button = QPushButton("🎙️ Push-to-Talk")
        self.mic_button.setObjectName("micBtn")
        self.mic_button.clicked.connect(self.toggle_mic)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText("Speak or type command for J0K AI ASSISTANT...")
        self.input_field.returnPressed.connect(self.on_send_clicked)

        self.send_button = QPushButton("SEND")
        self.send_button.setObjectName("sendBtn")
        self.send_button.clicked.connect(self.on_send_clicked)

        input_layout.addWidget(self.mic_button)
        input_layout.addWidget(self.input_field, stretch=1)
        input_layout.addWidget(self.send_button)

        container_layout.addLayout(input_layout)
        outer_layout.addWidget(self.container)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    def toggle_showcase(self):
        """Pops up the showcase if hidden, or hides if visible."""
        if self.isVisible():
            self.hide()
        else:
            self.pop_up_showcase()

    def pop_up_showcase(self):
        """Positions smoothly near the star button and shows on top."""
        screen = QApplication.primaryScreen().availableGeometry()
        star_geo = self.star_button.geometry()
        target_x = max(screen.left() + 20, star_geo.left() - self.width() - 12)
        target_y = max(screen.top() + 30, min(star_geo.top() - 160, screen.bottom() - self.height() - 20))
        self.move(target_x, target_y)
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_field.setFocus()

    def check_daemon_status(self):
        def _check():
            try:
                req = urllib.request.Request(f"{API_ENDPOINT}/status", headers={"User-Agent": "J0KHUD"})
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        self.signals.status_updated.emit(True, "● J0K ONLINE")
                        return
            except Exception:
                pass
            self.signals.status_updated.emit(False, "○ RECONNECTING...")
        threading.Thread(target=_check, daemon=True).start()

    def on_voice_changed(self):
        v = self.voice_combo.currentData()
        def _set():
            try:
                payload = json.dumps({"voice": v}).encode("utf-8")
                req = urllib.request.Request(
                    f"{API_ENDPOINT}/set_voice",
                    data=payload,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    pass
            except Exception as e:
                print(f"Error setting voice: {e}")
        threading.Thread(target=_set, daemon=True).start()

    def test_current_voice(self):
        v = self.voice_combo.currentData()
        self.send_command(f"Hello, I am J0K AI ASSISTANT speaking with the {v} voice persona.")

    def on_status_updated(self, is_online, text):
        if is_online:
            self.status_label.setText(text)
            self.status_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 11px;")
        else:
            self.status_label.setText(text)
            self.status_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")

    def append_user_message(self, text):
        html = f"""
        <div style='margin-bottom: 12px; text-align: right;'>
            <span style='background-color: #1e3a8a; color: #ffffff; padding: 8px 14px; border-radius: 12px; display: inline-block; font-size: 13px;'>
                <b>You:</b> {text}
            </span>
        </div>
        """
        self.chat_display.append(html)

    def append_j0k_message(self, reply, refined_prompt="", plan="", action_msg=""):
        thought_html = ""
        if refined_prompt:
            thought_html = f"""
            <div style='background-color: rgba(15, 23, 42, 0.9); border-left: 3px solid #00e5ff; border-radius: 6px; padding: 8px 12px; margin-bottom: 8px;'>
                <span style='background-color: rgba(0, 229, 255, 0.15); color: #00e5ff; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;'>🎯 ANTIGRAVITY REFINED DIRECTIVE</span><br>
                <b style='color: #f8fafc; font-size: 12px;'>{html.escape(refined_prompt)}</b>
            """
            if plan:
                thought_html += f"<div style='color: #94a3b8; font-size: 11px; margin-top: 4px;'>📋 <b>Plan:</b> {html.escape(plan)}</div>"
            if action_msg:
                thought_html += f"<div style='color: #10b981; font-size: 10px; font-weight: bold; margin-top: 4px;'>⚡ {html.escape(action_msg)}</div>"
            thought_html += "</div>"

        formatted_reply = reply if ("<" in reply and ">" in reply) else html.escape(reply)
        html_text = f"""
        <div style='margin-bottom: 12px; text-align: left;'>
            {thought_html}
            <span style='background-color: #0f172a; border: 1px solid #00e5ff; color: #f8fafc; padding: 8px 14px; border-radius: 12px; display: inline-block; font-size: 13px; line-height: 1.4;'>
                <b style='color: #00e5ff;'>⭐ J0K AI ASSISTANT:</b> {formatted_reply}
            </span>
        </div>
        """
        self.chat_display.append(html_text)

    def on_send_clicked(self):
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.send_command(text)

    def send_command(self, text):
        self.append_user_message(text)
        self.status_label.setText("⚡ PROCESSING...")
        self.status_label.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")

        def _worker():
            payload = json.dumps({"prompt": text, "history": self.history[-6:]}).encode("utf-8")
            req = urllib.request.Request(
                f"{API_ENDPOINT}/chat",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=25) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    reply = res.get("reply", "")
                    self.history.append({"role": "user", "content": text})
                    self.history.append({"role": "assistant", "content": reply})
                    self.signals.response_received.emit(text, res)
            except Exception as e:
                self.signals.response_received.emit(text, {"reply": f"I apologize, sir. Connection to J0K service failed: {e}"})

        threading.Thread(target=_worker, daemon=True).start()

    def on_response_received(self, user_text, res):
        if isinstance(res, dict):
            reply = res.get("reply", "")
            refined = res.get("refined_prompt", "")
            plan = res.get("plan", "")
            act = res.get("action", {})
            act_msg = act.get("message", "") if isinstance(act, dict) else ""
            self.append_j0k_message(reply, refined_prompt=refined, plan=plan, action_msg=act_msg)
        else:
            self.append_j0k_message(str(res))
        self.check_daemon_status()

    def toggle_mic(self):
        if not self.is_listening:
            self.is_listening = True
            self.mic_button.setText("🔴 Listening...")
            self.mic_button.setStyleSheet("background-color: #b91c1c; color: #ffffff; border: 1px solid #ef4444;")
            QTimer.singleShot(2500, self.finish_voice_input)
        else:
            self.finish_voice_input()

    def finish_voice_input(self):
        if self.is_listening:
            self.is_listening = False
            self.mic_button.setText("🎙️ Push-to-Talk")
            self.mic_button.setStyleSheet("""
                background-color: #1e1b4b;
                border: 1px solid #6366f1;
                border-radius: 8px;
                color: #a5b4fc;
            """)
            query = self.input_field.text().strip() or "system status"
            self.send_command(query)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("J0K AI ASSISTANT")

    # 1. Create right-side Star Shape Button
    star_btn = StarButton()
    star_btn.dock_to_right_edge()
    star_btn.show()

    # 2. Create Showcase Popup Window
    showcase = J0KShowcaseWindow(star_btn)

    # 3. Connect star button click to pop up showcase
    star_btn.clicked.connect(showcase.toggle_showcase)

    # Initially pop up the showcase so user sees it right away
    showcase.pop_up_showcase()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
