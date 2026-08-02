# Student Portal — Secure Web App Development & OWASP Top 10 Evaluation

A role-based Student Portal built with **Flask + SQLite**, developed and then
deliberately security-tested against the **OWASP Top 10 (2025)** framework.
The project follows a **build → break → fix** workflow: a working app was
built first, then attacked using industry-standard tools (Burp Suite,
Nessus, Wireshark), and finally hardened based on those findings.

> ⚠️ **Educational project.** The `vulnerable-version` folder intentionally
> contains security flaws (SQL Injection, Broken Access Control, plaintext
> passwords, etc.) for learning/demo purposes only. **Do not deploy it
> publicly or reuse this pattern in production.** Run it only on
> `localhost` in an isolated environment.

## Project Structure

```
.
├── vulnerable-version/     # Original build — contains intentional OWASP Top 10 flaws
├── secure-version/         # Hardened build — flaws fixed with secure coding practices
└── docs/
    └── OWASP_TOP10_FINDINGS.md   # Full vulnerability-by-vulnerability writeup
```

Both versions are complete, runnable Flask apps sharing the same feature set
(Student + Admin roles, marks, attendance, announcements) so they can be
compared side by side.

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS
- **Database:** SQLite
- **Security testing tools:** Burp Suite, Nessus, Wireshark, Kali Linux

## How to Run Either Version

```bash
cd vulnerable-version   # or secure-version
pip install flask
python app.py
```

Then open `http://127.0.0.1:5000` in your browser. A demo database
(`student_portal.db`) with seeded dummy accounts is included — **these are
fabricated demo credentials for local testing only**, not real accounts.

## What Was Tested — OWASP Top 10 (2025)

| Category | Found In | Status |
|---|---|---|
| A01 – Broken Access Control | Admin routes reachable without role checks | ✅ Fixed |
| A02 – Security Misconfiguration | Debug mode on, server info in headers | ✅ Fixed |
| A03 – Software Supply Chain Failures | Outdated dependencies flagged by Nessus | ✅ Fixed |
| A04 – Cryptographic Failures | Login traffic sent in plaintext (HTTP) | ✅ Fixed |
| A05 – Injection (SQL Injection) | Login built with raw string-concatenated SQL | ✅ Fixed |
| A06 – Insecure Design | Delete-announcement endpoint had no authorization check | ✅ Fixed |
| A07/A09 – Authentication & Logging Failures | No rate-limiting; distinguishable success/fail responses | ✅ Fixed |
| A08 – Data/Software Integrity Failures | Marks could be tampered with via request interception | ✅ Fixed |
| A10 – Mishandling of Exceptional Conditions | Raw stack traces exposed internal app details | ✅ Fixed |

Full methodology, payloads used, before/after code, and remediation details
for each category are in [`docs/OWASP_TOP10_FINDINGS.md`](./docs/OWASP_TOP10_FINDINGS.md).

## Testing Methodology
1. **Reconnaissance** — mapped the app's routes, forms, and roles.
2. **Automated scanning** — Nessus for known CVEs / misconfigurations.
3. **Manual testing** — Burp Suite (Proxy, Repeater, Intruder) for
   injection, access-control, and tampering tests; Wireshark for traffic
   analysis.
4. **Remediation** — applied parameterized queries, server-side role
   validation, password hashing, HTTPS-ready config, generic error
   handling, and session/logging hardening.
5. **Re-testing** — repeated every test against the fixed version to
   confirm each vulnerability was closed.

## Known Follow-up (not yet addressed)
- `app.secret_key` is currently a hardcoded string in both versions — move
  this to an environment variable (`os.environ.get("SECRET_KEY")`) before
  any real deployment.
- HTTPS/TLS was recommended in testing but the app currently runs over
  plain HTTP by default (fine for local demo, not for deployment).

> **Packaging note:** a handful of lines in both `app.py` files had lost
> their indentation (likely from a copy/paste or export step) and would not
> run as-is. These were corrected before packaging — both files have been
> verified to parse and load as valid Flask apps with all routes
> registering correctly. No logic was changed, only indentation.


## Academic Context
Special Project, B.Tech Computer Science & Engineering, ICFAI Foundation
for Higher Education, IFHE University — supervised by Dr. Sowjanya
Ramisetty (Apr 2026).
