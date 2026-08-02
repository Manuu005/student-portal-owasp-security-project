# OWASP Top 10 (2025) — Findings, Exploitation & Fixes

Each section below covers: what was tested, how it was exploited, the
vulnerable code, the fix applied, and how it was verified.

---

## A01 — Broken Access Control
**Test:** Logged in as a student, then manually navigated to the `/admin`
route to see if the server enforced role checks.

**Vulnerable code:**
```python
@app.route('/admin')
def admin():
    return render_template('admin.html')
```
Any authenticated session — regardless of role — could reach the admin
page. Only the frontend hid the admin links; there was no backend check.

**Fix:**
```python
if 'user_id' not in session or session.get('role') != 'admin':
    return redirect('/login')
```
**Verified:** student sessions attempting `/admin` are now redirected to login.

---

## A02 — Security Misconfiguration
**Test:** Nessus scan + manual header inspection.

**Finding:** Flask was running with `debug=True` in a non-development
context, and HTTP response headers leaked server/framework details.

**Fix:**
```python
app.run(debug=False)
```
Debug endpoints and verbose error pages were disabled; Nessus no longer
flagged the app as running in debug mode on re-scan.

---

## A03 — Software Supply Chain Failures
**Test:** Nessus dependency/version scanning.

**Finding:** Some third-party components/libraries were outdated and tied
to known CVEs.

**Fix:** Updated all dependencies to current stable versions and adopted a
practice of pinning/reviewing dependency versions going forward.

---

## A04 — Cryptographic Failures
**Test:** Captured login traffic with Wireshark while submitting
credentials.

**Finding:** The app ran over plain HTTP — login credentials were visible
in plaintext in the captured packets. No TLS/HTTPS in place.

**Fix (password storage):**
```python
from werkzeug.security import generate_password_hash
hashed_password = generate_password_hash(password)
```
Passwords are now hashed before storage; login verification uses
`check_password_hash`. **Recommendation carried forward:** serve the app
behind HTTPS (SSL/TLS) in any real deployment — this wasn't fully
implemented in the local demo since it requires a certificate/reverse proxy.

---

## A05 — Injection (SQL Injection)
**Test:** Submitted `admin' OR '1'='1--`-style payloads into the login form.

**Vulnerable code:**
```python
query = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
```
String-concatenated SQL let attacker input change the query's logic and
bypass authentication entirely.

**Fix:**
```python
cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
```
Parameterized queries treat user input strictly as data. Re-testing the
same payload against the fixed login form failed to bypass authentication.

---

## A06 — Insecure Design
**Test:** Intercepted the "delete announcement" request in Burp Suite and
replayed it while logged in as a non-admin student.

**Vulnerable code:**
```python
cursor.execute("DELETE FROM announcements WHERE id=?", (announcement_id,))
```
The delete action executed with no authorization check at all — the
endpoint assumed anyone who could reach it was allowed to use it.

**Fix:**
```python
if session.get('role') != 'admin':
    return "Unauthorized"
cursor.execute("DELETE FROM announcements WHERE id=?", (announcement_id,))
```
Re-tested: non-admin delete attempts are now rejected.

---

## A07 + A09 — Authentication & Logging Failures
**Test:** Ran Burp Suite Intruder (Sniper attack) against the login
endpoint, cycling through password guesses and comparing response codes
(`302` = success, `200` = failure).

**Finding:** No rate-limiting or account lockout existed, so unlimited
login attempts were possible, and no logging captured failed attempts —
making brute-force attacks both feasible and invisible.

**Fix:** Added session management hardening (`session.clear()` on
logout/failure paths) and flagged the need for login-attempt logging and
rate-limiting as a hardening step for production use.

---

## A08 — Software/Data Integrity Failures (Request Tampering)
**Test:** Intercepted a "manage marks" request in Burp Suite and modified
the `marks` parameter directly (including to a negative value) before
forwarding it.

**Vulnerable code:**
```python
cursor.execute("UPDATE marks SET marks=? WHERE student_id=?", (marks, student_id))
```
The update executed with no server-side validation or permission check —
even a negative mark value was accepted and saved.

**Fix:**
```python
if session.get('role') != 'admin':
    return "Unauthorized"
```
Re-tested: unauthorized/invalid mark updates are now blocked.

---

## A10 — Mishandling of Exceptional Conditions
**Test:** Submitted a non-numeric string into the marks field to trigger a
server-side error.

**Vulnerable code:**
```python
except Exception as e:
    print("SQL Error:", e)
```
Flask's debug error page rendered a full stack trace, revealing internal
file paths and application logic to the client.

**Fix:**
```python
except:
    return "Something went wrong"
```
Generic error messages are now returned to the client; internal details no
longer leak on exceptions.

---

## Summary

| # | Category | Root Cause | Fix Applied |
|---|---|---|---|
| A01 | Broken Access Control | No server-side role check | Session/role validation on protected routes |
| A02 | Security Misconfiguration | Debug mode enabled | `debug=False` |
| A03 | Supply Chain Failures | Outdated dependencies | Updated to latest stable versions |
| A04 | Cryptographic Failures | Plaintext HTTP traffic, plaintext passwords | Password hashing (`werkzeug.security`); HTTPS recommended |
| A05 | Injection | String-concatenated SQL | Parameterized queries |
| A06 | Insecure Design | No authorization check on delete | Role check before delete |
| A07/A09 | Auth & Logging Failures | No rate-limit / no logging | Session hardening; logging & rate-limiting recommended |
| A08 | Data Integrity Failures | No validation on update requests | Role check before update |
| A10 | Exceptional Conditions | Verbose error messages | Generic error responses |
