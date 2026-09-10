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

# Ensure executable bit on libexec scripts
chmod +x /usr/libexec/jarvis/*.py 2>/dev/null || true

echo "==> Successfully configured AI Daemon and J.A.R.V.I.S. services."
