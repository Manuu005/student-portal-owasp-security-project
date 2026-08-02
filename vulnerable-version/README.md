# Vulnerable Version

This is the **original build** of the Student Portal, before any security
fixes were applied. It intentionally contains the flaws documented in
[`../docs/OWASP_TOP10_FINDINGS.md`](../docs/OWASP_TOP10_FINDINGS.md),
including:

- SQL Injection in the login form (string-concatenated queries)
- Broken Access Control on the `/admin` route (no role check)
- No authorization check on delete/update actions
- Plaintext password storage
- Verbose error messages exposing internal details
- Debug mode enabled

## Run locally
```bash
pip install flask
python app.py
```

⚠️ Run on `localhost` only. This version is for demonstrating the
vulnerabilities described in the write-up — never deploy it to a public
server or reuse this pattern in real projects.
