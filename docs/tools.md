# Tools and authorization

- `pictureme_model_list`, `pictureme_model_get`: catalog/schema reads.
- `pictureme_upload_file`: uploads a **local file**, not a remote URL. This discloses its contents to the service. Restrict the agent's filesystem permissions.
- `pictureme_generate_create`: submits a paid generation; require explicit user authorization.
- `pictureme_generate_get`, `pictureme_generate_list`, `pictureme_generate_wait`: job reads/polling.
- `pictureme_generate_cancel`: cancellation request, not a guaranteed provider stop or refund.
- `pictureme_generate_cost`: local catalog-based estimate, NOT an authoritative quote; pricing rules may be more complex and billing is server-owned.
- `pictureme_token_balance`, `pictureme_token_transactions`: account reads requiring service permission.

Read tools can expose private account/job data to the MCP host. Use only trusted hosts and agents. There is no admin tool. Server authorization still applies. Never assume balance proves a job is affordable or cancellation means a refund. Read catalog/schema, present a nonbinding estimate, obtain approval before upload or paid submission, and inspect final status. API errors are returned without raw error bodies. All shared-client redirects
are disabled; 3xx responses fail without forwarding passwords, device exchange
codes or media to the redirect target.


[Documentation index](README.md) · [Project overview](../README.md)
