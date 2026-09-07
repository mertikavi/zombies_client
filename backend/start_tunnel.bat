@echo off
title Zombies Multiplayer Tunnel
echo ===================================================
echo   Zombies Multiplayer - Cloudflare Tunnel Baslatiliyor...
echo ===================================================
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:8765
pause
