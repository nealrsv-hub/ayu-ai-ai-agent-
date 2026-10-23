# n8n automation

The current local prototype uses this workflow shape:

`Webhook -> Edit Fields -> AI Agent -> Respond to Webhook`

The AI Agent may use read-only HTTP tools exposed by the local Python backend, including sensor status, the synthetic demo profile, event history, and reviewed health notes.

## Local webhook

The frontend defaults to:

```text
http://localhost:5678/webhook/ayusarthi-chat
```

The webhook should accept JSON shaped like:

```json
{
  "chatInput": "What is the current room status?",
  "sessionId": "example-session-id"
}
```

Return a JSON object containing a non-empty `answer` string. The frontend can also read a few simple nested/pass-through response shapes, but `{"answer":"..."}` is the recommended contract.

## Backend tools

Start the local tool server first:

```bat
python -m backend.tool_server --demo --speak
```

Useful read-only endpoints:

- `GET http://127.0.0.1:8000/tools/sensor-status`
- `GET http://127.0.0.1:8000/tools/event-history`
- `GET http://127.0.0.1:8000/tools/profile`
- `GET http://127.0.0.1:8000/tools/health-notes?query=walking`

Do **not** expose `/control` to the AI Agent as an autonomous tool. It is intended for local/manual prototype control.

## Credentials

Model API credentials belong in n8n's credential store and must never be committed to this repository. No exported n8n workflow is currently committed because a credential-reviewed export was not available in the source package.

## Start n8n

From the repository root on Windows:

```bat
automation\n8n\start_n8n.bat
```

Then configure/publish the workflow in the n8n UI and keep the production webhook URL aligned with `N8N_CHAT_URL` if you override the default.
