#!/usr/bin/env bash
set -e
echo "=============================================================================="
echo "      J AI ENTERPRISES - JOK-AI-OS 1.0 Production ISO Reassembler"
echo "=============================================================================="
echo ""
echo "Rejoining multi-part split archives into bootable ISO..."
cat JOK-AI-OS-v1.0-x86_64.iso.part-* > JOK-AI-OS-v1.0-x86_64.iso
echo "Calculating SHA-256 Checksum..."
sha256sum JOK-AI-OS-v1.0-x86_64.iso
echo "Expected Checksum: 5b6d17a33169c38e8ce72b43fceed91d0669b5d76762a05097446161aaaf734f"
echo "Verification complete. Flash with: sudo dd if=JOK-AI-OS-v1.0-x86_64.iso of=/dev/sdX bs=4M status=progress"
