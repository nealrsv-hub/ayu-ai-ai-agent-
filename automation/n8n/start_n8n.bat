@echo off
rem Local hackathon setup: start the npm-based 2.x prototype.
set N8N_LISTEN_ADDRESS=127.0.0.1
set N8N_SSRF_ALLOWED_IP_RANGES=127.0.0.1/32
npx n8n@2

