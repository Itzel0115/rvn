# Safety Red-Team Evaluation

The offline `redteam.v1.jsonl` suite covers prompt/tool-output injection, tool spoofing, path traversal, secret requests, oversized inputs, semantic amount/quantity confusion, and approval bypass. Expected rejection is a security success: no write, publication, hidden MCP tool, path access, or secret exposure occurs.

Add a case as JSONL with a synthetic input, safe expected status, and explicit security invariant. Never include company rows, credentials, paths, or approver names.
