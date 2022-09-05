
echo off
SET pth=%~dp0
SET pth=%pth:~0, -5%
echo on

bash %pth%/bash/generate_doc.sh %*
