# Secure Version

This is the **hardened build** of the Student Portal, after applying fixes
for every issue identified during OWASP Top 10 testing. See
[`../docs/OWASP_TOP10_FINDINGS.md`](../docs/OWASP_TOP10_FINDINGS.md) for the
full before/after breakdown.

Key security improvements over the vulnerable version:
- Parameterized SQL queries (no more injectable string concatenation)
- Server-side role validation on every admin/protected route
- Password hashing via `werkzeug.security`
- Authorization checks before delete/update actions
- Generic error handling (no internal details leaked)
- Security response headers added (`X-Frame-Options`, `X-Content-Type-Options`)
- Debug mode disabled

## Run locally
```bash
pip install flask
python app.py
```

## Still worth hardening further before real deployment
- Move `app.secret_key` out of source code and into an environment variable
- Serve over HTTPS (SSL/TLS)
- Add login rate-limiting / account lockout and structured logging
