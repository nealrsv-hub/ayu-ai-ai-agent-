# n8n automation

The hackathon system used a local n8n workflow:

`Webhook -> Edit Fields -> AI Agent -> Respond to Webhook`

The AI Agent had read-only HTTP tools for sensor status, the fictional demo profile, and reviewed health notes. Model API credentials belong in n8n's credential store and must never be committed to this repository.

No exported workflow is committed here because the current source package did not include a credential-reviewed n8n export. The detailed manual setup remains in `docs/original_hackathon_setup.md`.
