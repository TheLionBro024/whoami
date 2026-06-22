# Engineering Roadmap & Feature Fixes

## 1. Core Backend Security & Environment

### Objective
Migrate the administrative login interface from a client-side obfuscation pattern to a secure backend validation system running on Python (FastAPI), and align local routing architectures for production-parity edge tunneling.

### Tasks
- [ ] **Create Local Environment Management**
  - Create a root `.env` file containing `SECRET_KEY`, `ALGORITHM`, and `ADMIN_PASSWORD_HASH`.
  - Add `.env` to `.gitignore` to protect production secrets.
- [ ] **Configure Local Architecture for Cloudflare Tunneling**
  - Set up the main application architecture to run the active backend/admin site on `localhost:8000/whoami`.
  - Build out a clean, public-facing informative mockup website for **evolv.platform** served at the root `localhost:8000`.
  - Ensure routing logic handles Host header forwarding gracefully to streamline Cloudflare zero-trust edge tunneling routes.
- [ ] **Build FastAPI Authentication Endpoints**
  - Implement `POST /api/v1/login` to verify incoming SHA-256 password hashes.
  - Issue a cryptographically signed JSON Web Token (JWT) on success.
  - Bake the JWT into an `HttpOnly`, `Secure`, `SameSite=Lax` cookie.
- [ ] **Build Secure WebAuthn (Biometric) Handshake**
  - Move the Face ID / Touch ID credential validation from pure frontend storage to the backend.
  - Save your device's public key identifier securely on the server to prevent browser console bypasses.
- [ ] **Implement Route Guard Dependency Layer**
  - Create a `verify_admin_session` dependency in FastAPI.
  - Apply `Depends(verify_admin_session)` to protect all write/upload API endpoints.

---

## 2. Admin Dashboard & Settings Menu (Desktop-First Layout)

### Objective
Design a spacious side pannel tabbed layout for the administrative control center.

### Tasks
- [ ] **Build Global Settings Menu Module in Admin Center**
  - Integrate a settings component into the main sidebar.
  - Add toggle controls for site configurations (e.g., cache controls, image quality sliders, toggle analytics, maintenance switches).
  - Connect toggles to a backend configuration file or a `PUT /api/v1/settings` endpoint.

---

## 3. Blog Creation & Image Processing (Instagram-Style)

### Objective
Provide advanced image handling inside the creation window, optimized for uploading multiple high-fidelity assets.

### Tasks
- [ ] **Integrate Aspect-Ratio Image Cropper**
  - Inject an HTML5 canvas or a lightweight frontend cropper library (e.g., `Cropper.js`).
  - Intercept horizontal/wide photos and open an overlay crop modal to let you manually compose or auto-center images into your design grid's framing.
  - Process and optimize image data arrays down to WebP or AVIF formats natively before triggering the upload payload.

---

## 4. Post Lifecycle Management (CRUD Engine)

### Objective
Extend API routes to allow post editing and layout corrections post-publication.

### Tasks
- [ ] **Build Backend Content Edit API**
  - Implement a `PUT /api/v1/posts/{post_id}` endpoint in FastAPI.
  - Enforce the admin verification cookie check on this edit pathway.
- [ ] **Construct Frontend Management Grid**
  - Build a "Manage Content" tabular view in the admin workspace.
  - Add quick-action [Edit] and [Delete] button components to each post line item card.
- [ ] **Build Active Editor Mode State**
  - Configure the markdown creator window to parse and pre-populate fields with an existing post's text strings and image arrays when the edit action is invoked.

---

## 5. System Verification & Testing Checklist

- [ ] **Authentication Lock Out:** Try uploading a post payload using direct network scripts (curl or Postman) from an unauthenticated context. Verify that the server returns a strict `401 Unauthorized` message.
- [ ] **Cookie Verification:** Verify via browser developer tools that the session token cookie is explicitly flagged as `HttpOnly` and `Secure`.
- [ ] **Tunnel Routing Integrity:** Validate that requests hitting `localhost:8000` accurately serve the mock landing page, while structural panel assets and APIs isolate cleanly under `/whoami` without resource leakage or cross-origin breakdown.
- [ ] **Asset Framing:** Upload a combination of vertical, horizontal, and square imagery using your crop canvas interface. Confirm that placeholder aspect-ratio sizes match, layout shifts are completely gone, and skeleton loader blocks track properly.