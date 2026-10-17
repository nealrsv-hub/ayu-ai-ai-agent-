# Security and privacy

Use this prototype on a trusted local computer with synthetic data.

The Python backend binds to loopback and has no application authentication. Its `/control` endpoint can arm monitoring and change demo state. Keep it out of model tools and do not publish it through a tunnel or reverse proxy without a separate authentication and network-security design.

Run Streamlit with `--server.address 127.0.0.1`. Environment variables can change service URLs, so check their destinations before sending chat text or sensor data. Model requests and any n8n memory or execution history are handled by the workflow and provider you configure.

Do not commit API keys, tokens, passwords, Wi-Fi credentials, private records, credential exports, `.env`, or ESP32 `secrets.h` files. Runtime event/greeting files are ignored, but Git ignore rules do not protect files already tracked.

If a credential is committed, revoke or rotate it at the provider. Removing it from the latest file does not remove it from Git history.

No dependency lock or automated vulnerability scan is configured. Backend tests do not establish deployment security or clinical safety.
