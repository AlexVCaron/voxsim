
echo off
SET pth=%~dp0
SET pth=%pth:~0, -5%
echo on

bash %pth%/bash/build_doc.sh %*
