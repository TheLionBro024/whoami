# whoami Todo — Implementation Plan

## What I Found

### 🔒 Security Vulnerabilities

| # | Severity | Location | Issue |
|---|---|---|---|
| 1 | 🔴 High | `main.py:85` | `secure=False` on the session cookie — cookie sent over plain HTTP, sniffable on a network |
| 2 | 🔴 High | `main.py:28-30` | `RP_ID`, `ORIGIN` are hardcoded to `localhost` — WebAuthn will always fail on your real domain |
| 3 | 🟡 Medium | `main.py:356` | `PATCH /api/posts/{slug}` (likes) is fully public with no rate limiting — anyone can set likes to any number via curl |
| 4 | 🟡 Medium | `main.py:67` | No login rate limiting — brute-force password guessing is possible |
| 5 | 🟢 Low | `main.py:195` | Settings values are stored but never validated — arbitrary JSON can be injected |
| 6 | 🟢 Low | `admin.html:296` | `innerHTML` with `p.title` and `p.slug` — an XSS vector if a malicious title is saved |

### 🖐️ Biometric Auth (WebAuthn) Broken on Real Domain
`main.py` has these two hardcoded lines:
```python
RP_ID = "localhost"
ORIGIN = "http://localhost:8000"
```
WebAuthn is domain-bound by the spec. A biometric registered on `localhost` **cannot** be used on `op.evolvplatform.com`, and vice versa. These need to be read from `.env` so you can set them per-environment.

### 🖼️ Gallery Upload Missing
The gallery upload form group was removed from `admin.html` at some point. The backend still supports `gallery_images` in full — the server-side code in `main.py` and `serve.py` is intact. Only the admin UI is missing.

---

## Proposed Changes

### Fix 1 — Security: Hardened cookie + read RP_ID/ORIGIN from .env

#### [MODIFY] [main.py](file:///c:/Users/alfre/Server/whoami/main.py)
- Read `RP_ID` and `ORIGIN` from `.env` with `localhost` fallback
- Change cookie `secure=False` → `secure` based on whether ORIGIN is HTTPS

#### [MODIFY] [.env](file:///c:/Users/alfre/Server/whoami/.env)
- Add `RP_ID=op.evolvplatform.com`
- Add `ORIGIN=https://op.evolvplatform.com`

### Fix 2 — Security: XSS-safe post table in admin

#### [MODIFY] [admin.html](file:///c:/Users/alfre/Server/whoami/admin.html)
- Replace `innerHTML` with `textContent` for untrusted fields (title, date)

### Fix 3 — Gallery upload reimplemented in admin

#### [MODIFY] [admin.html](file:///c:/Users/alfre/Server/whoami/admin.html)
- Add a **Gallery Images** file input section (separate from carousel) with its own thumbnail strip
- Wire up the crop modal to work for both carousel and gallery images
- Include `gallery_images` in the POST/PUT payload

### Fix 4 — IoT guide

#### [NEW] [iot_setup_guide.md](file:///c:/Users/alfre/Server/whoami/iot_setup_guide.md)
- Written in `whoami/` so it lives with the project

---

## What I'm NOT fixing (by design)
- **Rate limiting** — Requires adding a library (`slowapi`) and is a bigger change. Will note it.
- **Settings validation** — Minor; settings are admin-only so impact is low.
- **Likes manipulation** — Low priority since likes are cosmetic.

---

> Proceed to apply all changes?
