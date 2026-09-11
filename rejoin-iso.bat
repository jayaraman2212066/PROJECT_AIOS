@echo off
echo ==============================================================================
echo       J AI ENTERPRISES - JOK-AI-OS 1.0 Production ISO Reassembler
echo ==============================================================================
echo.
echo Rejoining multi-part split archives into bootable ISO...
copy /b JOK-AI-OS-v1.0-x86_64.iso.part-00 + JOK-AI-OS-v1.0-x86_64.iso.part-01 + JOK-AI-OS-v1.0-x86_64.iso.part-02 JOK-AI-OS-v1.0-x86_64.iso
echo.
echo Calculating SHA-256 Checksum...
certutil -hashfile JOK-AI-OS-v1.0-x86_64.iso SHA256
echo.
echo Expected Checksum: 5b6d17a33169c38e8ce72b43fceed91d0669b5d76762a05097446161aaaf734f
echo.
echo If hashes match, you can now flash JOK-AI-OS-v1.0-x86_64.iso using Rufus or BalenaEtcher!
pause
