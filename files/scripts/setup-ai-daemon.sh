#!/usr/bin/env bash
set -oue pipefail

echo "==> Configuring AI Daemon (RamaLama) user service..."

# Create target directories in immutable system path
mkdir -p /usr/lib/systemd/user/default.target.wants

# Install unit file from build context (/tmp/files or /files)
if [[ -f /tmp/files/systemd/ai-daemon.service ]]; then
    install -Dm644 /tmp/files/systemd/ai-daemon.service /usr/lib/systemd/user/ai-daemon.service
elif [[ -f /files/systemd/ai-daemon.service ]]; then
    install -Dm644 /files/systemd/ai-daemon.service /usr/lib/systemd/user/ai-daemon.service
else
    echo "ERROR: ai-daemon.service not found in build context!" >&2
    exit 1
fi

# Enable unit globally for all user sessions at build time
ln -sf /usr/lib/systemd/user/ai-daemon.service /usr/lib/systemd/user/default.target.wants/ai-daemon.service

echo "==> Configuring J.A.R.V.I.S. ambient agent user service..."
if [[ -f /tmp/files/systemd/jarvis-agent.service ]]; then
    install -Dm644 /tmp/files/systemd/jarvis-agent.service /usr/lib/systemd/user/jarvis-agent.service
elif [[ -f /files/systemd/jarvis-agent.service ]]; then
    install -Dm644 /files/systemd/jarvis-agent.service /usr/lib/systemd/user/jarvis-agent.service
fi

if [[ -f /usr/lib/systemd/user/jarvis-agent.service ]]; then
    ln -sf /usr/lib/systemd/user/jarvis-agent.service /usr/lib/systemd/user/default.target.wants/jarvis-agent.service
    echo "==> Successfully enabled jarvis-agent.service in /usr/lib/systemd/user/default.target.wants/"
fi

# Ensure executable bit on libexec scripts and CLI wrappers
chmod +x /usr/libexec/jarvis/*.py 2>/dev/null || true
chmod +x /usr/bin/jok-app-run 2>/dev/null || true
update-mime-database /usr/share/mime 2>/dev/null || true

echo "==> Applying JOK-AI-OS identity and branding..."
if [[ -f /usr/share/jok-ai-os/os-release ]]; then
    cp -f /usr/share/jok-ai-os/os-release /usr/lib/os-release
    rm -f /etc/os-release 2>/dev/null || true
    ln -sf ../usr/lib/os-release /etc/os-release 2>/dev/null || cp -f /usr/share/jok-ai-os/os-release /etc/os-release
    echo "==> JOK-AI-OS 1.0 os-release applied."
fi

echo "==> Successfully configured AI Daemon, J.A.R.V.I.S., and Universal Compatibility services."

