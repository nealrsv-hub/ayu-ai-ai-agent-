# Local n8n chat workflow

The repository includes a Python tool server and an agent prompt. It does not include an importable n8n workflow, so chat requires manual setup.

## Start the services

Run the backend from the repository root:

```bat
python -m backend.tool_server --demo
```

The Windows launcher starts a local n8n 2.x instance:

```bat
automation\n8n\start_n8n.bat
```

It requires Node.js/npm and downloads the selected 2.x release through `npx`. The exact n8n version is not locked. Check the [official installation requirements](https://docs.n8n.io/hosting/installation/npm/) for the release you use; this launcher is a prototype setup, not a tested deployment recipe.

## Workflow contract

Create this workflow in n8n:

1. Add a Webhook node using POST and the path `ayusarthi-chat`. Configure it to respond through a Respond to Webhook node.
2. Map the incoming `body.chatInput` and `body.sessionId` fields to the agent input and session key.
3. Add an AI Agent with your chosen chat model. Store its API credential in n8n and use the instructions in [the system prompt](../../prompts/agent_system_prompt.txt).
4. Attach only the read-only tools listed below. If conversation history is needed, configure a memory node keyed by the incoming session ID.
5. Return a JSON object whose `answer` value is the agent's output string. Use n8n's object/expression mapping so quotes and line breaks are encoded as JSON.
6. Publish or activate the workflow as required by your n8n version. Use the production webhook URL in `N8N_CHAT_URL`.

Exact node labels and expression settings depend on the installed n8n release. This contract describes the integration; it is not evidence that a full workflow execution has been tested.

Request:

```json
{"chatInput":"What do the room readings show?","sessionId":"demo-session"}
```

Response:

```json
{"answer":"The available reading is simulated."}
```

## Read-only tools

| Suggested tool name | Backend request |
|---|---|
| `get_sensor_status` | `GET http://127.0.0.1:8000/tools/sensor-status` |
| `get_demo_profile` | `GET http://127.0.0.1:8000/tools/profile` |
| `search_health_notes` | `GET http://127.0.0.1:8000/tools/health-notes?query=<topic>` |
| `get_event_history` | `GET http://127.0.0.1:8000/tools/event-history` |

Pass the search topic as a query parameter. Match the first three tool names to the supplied prompt. Do not attach `/control` as a model tool.

The launcher allows n8n to request the loopback backend. This assumes n8n runs on the same host; a container or cloud instance has a different loopback address.

## Troubleshooting

- Connection refused: confirm the backend and n8n terminals are still running.
- Webhook not found: check that the workflow is published/active and that the production URL matches `N8N_CHAT_URL`.
- Empty or malformed answer: inspect the response-node mapping and return a nonempty `answer` string.
- Model error: inspect n8n's provider response, quota, and billing. Creating another API key does not establish that a quota or billing problem is fixed.

Before adding a workflow export, remove credentials and execution data, then test an import in a clean instance.
