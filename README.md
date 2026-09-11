# JOK-AI-OS — Universal Autonomous AI Operating System
**Proprietary Operating System by J AI ENTERPRISES**  
*Founder & Chief Architect: Jayaraman K*

---

## ⚡ Overview

**JOK-AI-OS** is an autonomous, on-device AI operating system engineered from the ground up to replace traditional OS interactions with intelligent, local-first reasoning. Built on an immutable containerized core with zero cloud dependency, JOK-AI-OS empowers users with an ambient neural engine capable of managing system workflows, automating daily tasks, and interacting via voice and natural language.

---

## 🚀 Key Features

- **Autonomous LLM-First Kernel & Reasoning**:
  Powered on-device by high-performance quantized neural models (Qwen 2.5-3B Instruct / Qwen 2.5-7B Coder) served locally via RamaLama. The AI plans, thinks, decides, and executes complex system directives without rigid hardcoded rules.

- **J.A.R.V.I.S. Ambient OS Assistant**:
  An on-screen floating cyber-neon interface branded with the glowing **"J"** emblem. Supports two-way voice synthesis (offline eSpeak-NG / SAPI5 bridge) and interactive chat.

- **Adaptive Self-Learning Memory**:
  The assistant dynamically adapts to user habits, records corrections, remembers preferences, and evolves over time without requiring cloud uploads or telemetry.

- **Admin Permission & Safety Architecture**:
  Non-destructive operations (app launches, audio, workspace creation, notes, status checks) execute automatically and seamlessly. Destructive operations (directory deletion, critical service termination) mandate user confirmation.

- **Modern Cyber-Neon Desktop**:
  Custom 4K neon aesthetics, Windows-intuitive desktop paradigm powered by KDE Plasma, unified dark palette, and branded CLI terminal greetings.

---

## 📀 Installation & Bootable ISO

JOK-AI-OS is distributed as a self-contained, bootable x86_64 installer ISO:

- **ISO Image**: `JOK-AI-OS-v1.0-x86_64.iso`
- **Architecture**: `x86_64 (UEFI / BIOS compatible)`
- **Base Footprint**: Immutable OSTree deployment

### Flashing to USB
You can write the ISO image to a USB flash drive using `dd` on Linux/macOS or `Rufus` / `BalenaEtcher` on Windows:

```bash
sudo dd if=JOK-AI-OS-v1.0-x86_64.iso of=/dev/sdX bs=4M status=progress conv=fsync
```

### Running in Virtual Machines (QEMU / KVM)
```bash
qemu-system-x86_64 \
    -enable-kvm \
    -m 8G \
    -smp 4 \
    -cdrom JOK-AI-OS-v1.0-x86_64.iso \
    -boot d \
    -vga virtio \
    -net nic -net user,hostfwd=tcp::2222-:22
```

---

## 🔒 Proprietary License

```
Copyright (c) 2026 J AI ENTERPRISES. All Rights Reserved.
Proprietary Commercial Software.
```

JOK-AI-OS, the JOK Assistant branding, and associated autonomous agent algorithms are proprietary intellectual property of **J AI ENTERPRISES**. Unauthorized duplication, distribution, reverse engineering, or creation of derivative works without express written permission from J AI ENTERPRISES is strictly prohibited.

For licensing inquiries and enterprise deployments, contact: `contact@jaienterprises.com`.
