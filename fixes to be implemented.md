* Add Password for enter admin (is face id or biometrics possible? in the post domain ill sync that with my account)
* in blog creation allow multiple images to be selected (insta post style), is it possible to implement a cropping feature if some pictures are Horizontal instead of framing thats shown
* In admin mode. Introduce settings menu with a whole lot of settings
* after a post has been made, allow to edit
* Create .env
* Admin authentification improvement, to be ran on backend Python (FastAPI)


Highly detailed Security Update description:
## [HIGH PRIORITY] Backend-Enforced Admin Authentication (Path A Migration)

### Objective
Migrate the administrative login interface from a client-side obfuscation pattern to an enterprise-grade, backend-enforced validation system. Ensure that unauthorized users cannot bypass the UI gate to hit database or file upload API endpoints.

### Current Issue
The existing password gate and WebAuthn (biometric) loop execute entirely within the visitor's browser. Access states are stored in volatile client memory (`sessionStorage`), and visibility is managed via CSS toggle states (`.hidden`). The underlying API routes (e.g., saving blog posts, uploading high-res gallery images) lack structural token validation, creating a bypass vulnerability via direct HTTP tools or browser console manipulation.

### Target Architecture (Path A)
1. **Cryptographic Signatures:** Leverage JSON Web Tokens (JWT) to issue tamper-proof session tokens upon successful authentication.
2. **Secure State Management:** Store the JWT inside an `HttpOnly`, `Secure` cookie. This prevents cross-site scripting (XSS) attacks from reading the token via JavaScript, while ensuring it passes securely across the Cloudflare tunnel interface.
3. **Route Guarding:** Inject a FastAPI dependency layer on all administrative endpoints to intercept incoming requests and reject them instantly if a valid, unexpired session cookie is missing.

---

### Implementation Roadmap

#### Phase 1: Backend Architecture (FastAPI)
- [ ] Install required cryptographic dependencies (`pip install python-jose`).
- [ ] Define environment configurations in a local `.env` file (e.g., `SECRET_KEY`, `ALGORITHM`, and the master `ADMIN_PASSWORD_HASH`). Ensure `.env` is added to `.gitignore`.
- [ ] Build a `/api/v1/login` POST endpoint:
    - Accepts an incoming SHA-256 password hash from the frontend.
    - Validates it against the master hash stored on the server.
    - Generates a signed JWT access token with an explicit expiration window (e.g., 12 hours).
    - Sets the token as an `HttpOnly`, `Secure`, `SameSite=Lax` cookie in the HTTP response headers.
- [ ] Create a `verify_admin_session` dependency function to extract, decode, and validate the cookie payload.
- [ ] Apply the dependency gate (`Depends(verify_admin_session)`) to all write-heavy endpoints:
    - [ ] `POST /api/v1/posts` (Blog upload logic)
    - [ ] `POST /api/v1/images` (High-fidelity gallery asset handling)

#### Phase 2: Frontend Refactoring (JavaScript)
- [ ] Modify the `#auth-submit` click event listener to run the native browser `hashPassword` function and immediately dispatch a `POST` request to `/api/v1/login` containing the payload.
- [ ] Configure the UI view state change (`unlockAdmin()`) to fire *only* if the backend returns an HTTP status code `200 OK`.
- [ ] Ensure that internal dashboard data fetching functions (e.g., `fetchPosts()`) require a verified session before executing.
- [ ] Add an explicit backend logout endpoint that clears the browser's cookie jar.

---

### Verification & Testing Checklist
- [ ] Verify that entering an incorrect password blocks UI access and returns an explicit `410 Unauthorized` response from the server.
- [ ] Inspect the browser application tab to confirm the `session_token` cookie flags are set to `HttpOnly` and `Secure`.
- [ ] Attempt to manually execute a `fetch()` POST request to `/api/v1/posts` from a completely unauthenticated, private incognito tab. Verify that the server returns a strict `401 Session missing` error.
- [ ] Confirm that your blog’s custom skeleton loaders and standard public view elements still render flawlessly without asking casual readers for an authentication token.


