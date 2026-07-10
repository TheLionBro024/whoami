# whoami — Full Codebase Explainer

> A personal blog & portfolio server built with Python + FastAPI, featuring a secure admin panel, static site generation, and WebAuthn biometric login.

---

## Table of Contents

1. [Big Picture — How Everything Fits Together](#1-big-picture)
2. [Folder & File Map](#2-folder--file-map)
3. [The Configuration Files](#3-the-configuration-files)
4. [The Python Backend](#4-the-python-backend)
   - [main.py — The FastAPI Web Server](#mainpy--the-fastapi-web-server)
   - [serve.py — The HTML Generator & Legacy Server](#servepy--the-html-generator--legacy-server)
5. [The HTML Pages](#5-the-html-pages)
   - [index.html — Public Landing Page](#indexhtml--public-landing-page)
   - [personal_index.html — The Personal Site](#personal_indexhtml--the-personal-site)
   - [blog.html — The Blog Feed](#bloghtml--the-blog-feed)
   - [admin.html — The Admin Panel](#adminhtml--the-admin-panel)
   - [evolv_index.html — Evolv Platform Page](#evolv_indexhtml--the-evolv-platform-page)
6. [The Utility Scripts](#6-the-utility-scripts)
   - [generate_bcrypt.py — Password Hasher](#generate_bcryptpy--password-hasher)
   - [generate_admin.py — Admin HTML Generator](#generate_adminpy--admin-html-generator)
7. [The Data & Asset Directories](#7-the-data--asset-directories)
8. [Key Concepts Explained Simply](#8-key-concepts-explained-simply)
   - [How a Blog Post Goes from Creation to Live Page](#how-a-blog-post-goes-from-creation-to-live-page)
   - [How Authentication Works](#how-authentication-works)
   - [How Static HTML Generation Works](#how-static-html-generation-works)
9. [API Reference Cheat Sheet](#9-api-reference-cheat-sheet)
10. [How to Run the Server](#10-how-to-run-the-server)

---

## 1. Big Picture

Think of this project like a simple Instagram-style personal blog. Here's the journey:

```
You (admin) → /admin panel → create a post → server saves it →
server auto-generates blog.html + posts/my-post.html →
visitors → /blog → see the feed → click a post → read it
```

The server is written in **Python using FastAPI** (`main.py`). It has two jobs:

1. **Serve your HTML/CSS/JS files** to visitors (just like a web host).
2. **Provide a REST API** so the admin panel can create, edit, and delete posts.

When a post is created or changed, the server **immediately re-generates all the static HTML files** (blog.html, each post page, gallery pages). This is called **static site generation** — it means visitors always get fast, pre-built HTML pages, not slow server-rendered ones.

---

## 2. Folder & File Map

```
whoami/
│
├── 📄 main.py                  ← The FastAPI server. The heart of the app.
├── 📄 serve.py                 ← HTML templates + generator functions (imported by main.py)
├── 📄 requirements.txt         ← Python packages to install
│
├── 📄 index.html               ← Public landing page (shown to most visitors)
├── 📄 personal_index.html      ← Alternative home page (shown on op.evolvplatform.com)
├── 📄 blog.html                ← Auto-generated blog feed (DO NOT edit manually)
├── 📄 admin.html               ← Admin panel UI
├── 📄 evolv_index.html         ← Evolv Platform page
│
├── 📄 .env                     ← Secret keys & admin credentials (NEVER share this)
├── 📄 .gitignore               ← Tells Git which files to ignore
├── 📄 .webauthn_db.json        ← Biometric credential storage (auto-created)
├── 📄 .settings.json           ← Server settings (auto-created)
├── 📄 favicon.png              ← The small icon shown in browser tabs
│
├── 📄 generate_bcrypt.py       ← Tool to generate a password hash for .env
├── 📄 generate_admin.py        ← One-time script that generated admin.html
├── 📄 todo.md                  ← Personal notes/to-do list
│
├── 📁 blog_assets/             ← All blog data lives here
│   ├── 📄 posts.json           ← The database: list of all blog posts
│   ├── 📄 avatar.jpg           ← Your profile picture
│   ├── 📁 images/              ← Carousel images for posts
│   └── 📁 gallery/             ← Gallery images for posts
│
├── 📁 posts/                   ← Auto-generated individual post HTML pages
│   └── 📄 my-post-slug.html   ← e.g., posts/camping-trip.html
│
├── 📁 gallery/                 ← Auto-generated gallery HTML pages
│   └── 📄 my-post-slug.html   ← e.g., gallery/camping-trip.html
│
└── 📁 __pycache__/             ← Python's compiled bytecode (auto-created, ignore it)
```

---

## 3. The Configuration Files

### `.env` — Environment Variables (Secrets)

This file holds your **secret configuration**. It's loaded by `main.py` on startup using `python-dotenv`. It is **never committed to Git**.

```env
SECRET_KEY=3a897a9...           # A long random string used to sign JWT tokens
ALGORITHM=HS256                 # The algorithm used for JWT signing
ADMIN_PASSWORD_HASH='$2b$12...' # Your admin password stored as a bcrypt hash (not plain text!)
ADMIN_USERNAME='TheLionBro024'  # Your admin username
```

**Why is the password a hash and not plain text?**
A hash is a one-way transformation. If someone somehow reads this file, they see a scrambled version of your password that can't be reversed. When you log in, the server hashes what you type and compares it to this stored hash.

---

### `requirements.txt` — Python Dependencies

Lists all the Python packages needed to run the project. Install them with `pip install -r requirements.txt`.

| Package | What it does |
|---|---|
| `fastapi` | The web framework — handles HTTP requests and routing |
| `uvicorn` | The ASGI server that actually runs FastAPI |
| `python-dotenv` | Loads variables from `.env` into the app |
| `PyJWT` | Creates and verifies JWT tokens (used for admin sessions) |
| `passlib[bcrypt]` | The `bcrypt` library for password hashing |
| `webauthn` | Handles biometric/passkey (WebAuthn) authentication |
| `python-multipart` | Allows FastAPI to parse form/file uploads |

---

### `.gitignore` — Git Exclusions

Tells Git which files to **never track or upload** to GitHub:

- `.env` — Contains your secrets. Critical to ignore!
- `__pycache__/` — Auto-generated Python cache files.
- `blog_assets/images/`, `blog_assets/gallery/` — User-uploaded images (large binary files, don't belong in Git).
- `gallery/`, `posts/*.html` — Auto-generated files (can be re-generated by running the server).
- `generate_bcrypt.py` — Developer utility, not needed in production.

---

### `.webauthn_db.json` — Biometric Credentials

This file is **auto-created** the first time you register a device via WebAuthn (fingerprint/Face ID). It stores:

```json
{
  "credentials": [
    {
      "id": "base64-encoded-credential-id",
      "public_key": "base64-encoded-public-key",
      "sign_count": 5
    }
  ]
}
```

The `sign_count` is a security counter that increments every time you log in — it prevents replay attacks (where someone records your login attempt and plays it back).

---

### `.settings.json` — Admin Settings

Auto-created when you save settings in the admin panel. Stores toggles:

```json
{
  "cache_enabled": true,
  "image_quality": "high",
  "analytics_enabled": true,
  "maintenance_mode": false
}
```

> **Note:** These settings are stored but not all of them are actively wired up to change server behavior yet (e.g., `maintenance_mode` doesn't actually block traffic). They're in place for future use.

---

## 4. The Python Backend

### `main.py` — The FastAPI Web Server

This is **the entry point of the application**. When you run `python main.py`, this is what starts. It creates the web server and defines all the API endpoints.

#### Startup & Configuration (Lines 1–32)

```python
load_dotenv(override=True)

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

RP_ID = "localhost"
RP_NAME = "whoami Admin"
ORIGIN = "http://localhost:8000"

app = FastAPI()
```

- Reads your `.env` file secrets into variables.
- Sets up WebAuthn configuration (`RP_ID` = "Relying Party" ID, basically your domain).
- Creates the `app` object — everything else attaches to this.

---

#### JWT Token Functions (Lines 34–61)

**JWT (JSON Web Token)** is like a signed ID card. When you log in, the server creates one and stores it in your browser as a cookie.

```
create_access_token(data)  →  Signs a token that expires in 7 days
verify_admin_session(request)  →  Checks the cookie on every protected request
```

How it works:
1. You log in → server creates a token containing `{"role": "admin"}` → signs it with `SECRET_KEY` → puts it in a cookie.
2. You make an admin request → browser automatically sends the cookie → server verifies the signature → if valid, allows the action.

---

#### Login & Logout (Lines 67–94)

```
POST /api/v1/login   → Checks username + bcrypt password hash → sets admin_session cookie
POST /api/v1/logout  → Deletes the admin_session cookie
```

**Important detail:** The password check uses `bcrypt.checkpw()`, which correctly compares a plain-text password against the stored hash. Even if two people have the same password, their hashes look completely different.

---

#### WebAuthn (Biometric) Endpoints (Lines 96–189)

WebAuthn lets you log in with your fingerprint, Face ID, or hardware security key instead of a password. It follows a "challenge-response" protocol:

```
GET  /api/v1/webauthn/register/generate   → Server creates a challenge for device registration
POST /api/v1/webauthn/register/verify     → Browser sends back proof; server saves public key
GET  /api/v1/webauthn/authenticate/generate → Server creates a login challenge
POST /api/v1/webauthn/authenticate/verify   → Browser sends signed proof; server issues cookie
```

Think of it like this: the server says "prove you have this key by signing this random message." Your device signs it with your private key (stored securely on the device), and the server checks it using your public key (stored in `.webauthn_db.json`).

---

#### Settings Endpoints (Lines 194–210)

```
GET /api/v1/settings  → Returns current settings (admin only)
PUT /api/v1/settings  → Updates and saves settings to .settings.json (admin only)
```

---

#### Post CRUD API (Lines 212–374)

CRUD = Create, Read, Update, Delete. This is the core of the admin functionality.

| Method | Endpoint | Auth? | What it does |
|---|---|---|---|
| GET | `/api/v1/posts` | No | Returns all posts as JSON |
| POST | `/api/v1/posts` | Yes | Creates a new post |
| PUT | `/api/v1/posts/{slug}` | Yes | Edits an existing post |
| DELETE | `/api/v1/posts/{slug}` | Yes | Deletes a post and all its files |
| POST | `/api/v1/profile-picture` | Yes | Uploads a new avatar image |
| PATCH | `/api/posts/{slug}` | No | Updates likes count (public) |

**What happens when a post is created (simplified):**
1. Admin submits title + content + images.
2. `main.py` receives the request.
3. Images (sent as base64 strings) are decoded and saved to `blog_assets/images/`.
4. A "slug" is generated from the title (e.g., "My Trip" → `my-trip`).
5. The post object is added to `blog_assets/posts.json`.
6. `serve.regenerate_all(posts)` is called — this rebuilds all HTML pages.

---

#### Routing & Middleware (Lines 382–416)

```python
@app.middleware("http")
async def security_and_host_middleware(request, call_next):
    # Blocks access to /.git and /.env paths
    ...

@app.get("/admin")  → Serves admin.html
@app.get("/blog")   → Serves blog.html
@app.get("/")       → Serves index.html OR personal_index.html depending on the domain

app.mount("/", StaticFiles(directory=".", html=True), name="static")
```

**The middleware** runs before every single request. It blocks anyone from accessing `/.env` or `/.git` through the browser (prevents leaking your secrets).

**The host detection trick:** When a request comes in to `/`, it checks the `X-Forwarded-Host` header. If the domain is `op.evolvplatform.com`, it serves `personal_index.html`. Otherwise it serves `index.html`. This is how one server can serve two different homepages for two different domains via Cloudflare Tunnel.

**`StaticFiles` mount:** This is a catch-all that lets the server serve any file in the current directory (HTML, CSS, JS, images, etc.). It's mounted last so the explicit routes above take priority.

---

### `serve.py` — The HTML Generator & Legacy Server

This is a large, multi-purpose file. It has two roles:

1. **A library of functions** imported by `main.py` (`load_posts`, `save_posts`, `regenerate_all`, etc.)
2. **A standalone legacy HTTP server** (the `BlogHTTPRequestHandler` class and `if __name__ == "__main__"` block at the bottom) — this was the original server before `main.py` was written.

> **In practice, you always run `main.py`, not `serve.py` directly.**

#### The Shared Style Variables (Lines 16–182)

`serve.py` contains several Python string variables holding HTML/CSS/JS that gets injected into every generated page:

| Variable | Contains |
|---|---|
| `SHARED_CSS` | The global CSS design system (dark theme, colors, fonts, nav styles) |
| `NAV_TOGGLE_SCRIPT` | The JavaScript that animates the hamburger menu open/close |
| `NAV_HTML` | The hamburger nav HTML for the blog feed |
| `NAV_HTML_POST` | The hamburger nav HTML for individual post pages |
| `NAV_HTML_GALLERY` | The hamburger nav HTML for gallery pages |

All nav variants have the same links: Home, Blog, Instagram, BeReal, Evolv.Platform, Email.

---

#### The HTML Templates (Lines 186–1092)

These are large Python strings containing the HTML skeletons for each page type. They use Python's `.format()` syntax — `{placeholders}` get replaced with real content when a page is generated.

| Template | Used for | Key placeholders |
|---|---|---|
| `BLOG_TEMPLATE` | `blog.html` — the main feed | `{posts_feed_html}`, `{shared_css}`, `{nav_html}` |
| `POST_TEMPLATE` | `posts/{slug}.html` — individual post | `{post_title}`, `{post_content_html}`, `{post_carousel_html}` |
| `GALLERY_TEMPLATE` | `gallery/{slug}.html` — photo gallery | `{post_title}`, `{photos_html}`, `{images_json}` |

Each template includes:
- Full responsive CSS (mobile-first)
- The nav HTML
- Image carousels with swipe support on mobile
- A lightbox for the gallery (click a photo to see it fullscreen)

---

#### Utility Functions (Lines 1099–1271)

| Function | What it does |
|---|---|
| `get_ip_address()` | Finds your machine's local network IP (shown on startup) |
| `slugify(text)` | Converts "My Camping Trip!" → `"my-camping-trip"` (URL-safe) |
| `generate_unique_slug(title, posts)` | Creates a slug; adds `-1`, `-2` etc. if it already exists |
| `init_folders()` | Creates `blog_assets/images/`, `blog_assets/gallery/`, `posts/`, `gallery/` if missing |
| `load_posts()` | Reads `blog_assets/posts.json` and returns the list. Also migrates old post formats. |
| `save_posts(posts)` | Writes the post list back to `blog_assets/posts.json` |
| `format_date(iso_str)` | Converts `"2026-07-10T14:30:00"` → `"July 10, 2026 at 02:30 PM"` |
| `format_content_html(content)` | Converts plain text with newlines into `<p>` HTML paragraphs |
| `get_avatar_src(prefix)` | Returns path to avatar.jpg if it exists, or a Gravatar fallback URL |
| `build_carousel_html_blog(post)` | Builds the image carousel HTML for a blog feed card |
| `build_carousel_html_post(post)` | Builds the image carousel HTML for a full post page |
| `save_image_file(image_data, name, subfolder)` | Decodes a base64 image string and saves it to disk. Returns the file path. |

---

#### `regenerate_all(posts)` — The Site Generator (Lines 1274–1396)

This is the most important function. It runs every time a post is created, updated, or deleted. It does three things:

**Step 1: Rebuild `blog.html`**
- Loops through all posts.
- For each post, builds a "card" with the avatar, timestamp, carousel images, title, snippet, and like button.
- Fills the `BLOG_TEMPLATE` with all cards combined.
- Writes the result to `blog.html`.

**Step 2: Rebuild every `posts/{slug}.html`**
- For each post, formats the content as HTML paragraphs.
- Builds the post's image carousel.
- If the post has gallery images, adds a "See more photos" callout link.
- Fills the `POST_TEMPLATE` and writes to `posts/{slug}.html`.

**Step 3: Rebuild every `gallery/{slug}.html`**
- Only for posts that have gallery images.
- Builds the masonry photo grid.
- Creates the `images_json` array used by the lightbox JavaScript.
- Fills the `GALLERY_TEMPLATE` and writes to `gallery/{slug}.html`.

---

#### The Legacy HTTP Handler (Lines 1403–1610)

`BlogHTTPRequestHandler` is a class that extends Python's built-in `http.server.SimpleHTTPRequestHandler`. This was the original server before FastAPI was added. It handles:

- `GET /api/posts` → Returns posts JSON
- `GET /admin` → Redirects to admin.html
- `POST /api/posts` → Creates a post
- `POST /api/profile-picture` → Saves avatar
- `PATCH /api/posts/{slug}` → Updates likes
- `DELETE /api/posts/{slug}` → Deletes a post

> This code still exists and works, but `main.py` is the active server. Think of this as the old version kept for reference.

---

## 5. The HTML Pages

### `index.html` — Public Landing Page

The default homepage, served when someone visits your site from most domains. It's a hand-crafted HTML page (not auto-generated). Contains your public-facing intro, links, etc.

### `personal_index.html` — The Personal Site

An alternative homepage served specifically when the domain is `op.evolvplatform.com`. The server detects this via the `X-Forwarded-Host` header (set by Cloudflare). This lets you have a more personal page on one domain and a different landing on another.

### `blog.html` — The Blog Feed

**⚠️ Do not edit this file manually.** It is completely overwritten every time `regenerate_all()` runs.

It's generated from `BLOG_TEMPLATE` in `serve.py`. It shows all your posts as Instagram-style cards with:
- Your avatar and username
- A timestamp
- An image carousel (if the post has images)
- Like, comment, bookmark buttons (visual; likes persist via API)
- A post title, a text snippet, and a "Read Full Post" link

### `admin.html` — The Admin Panel

The control panel for managing the blog. It's a single-page app (SPA) meaning all its functionality lives in one HTML file with lots of JavaScript.

**Sections:**
- **Auth Gate** (shown first): A login screen with two options:
  1. **Biometric login** (fingerprint/Face ID via WebAuthn) — the fingerprint icon button
  2. **Password login** — classic username/password form
- **Sidebar** (shown after login): Navigation between tabs
  - **Create Post** — Form with title, content, and image uploader with a crop modal
  - **Manage Posts** — Table of all posts with Edit/Delete buttons
  - **Settings** — Checkboxes/dropdowns for server settings
  - **Logout** — Clears the session cookie

**The image cropper:** When you upload an image for a post, a cropping modal appears (powered by Cropper.js). After cropping, the image is converted to WebP format at 80% quality before being sent to the server. This keeps file sizes small.

### `evolv_index.html` — The Evolv Platform Page

A static HTML page for the Evolv Platform project. Served as a standalone page.

---

## 6. The Utility Scripts

### `generate_bcrypt.py` — Password Hasher

A **one-time setup script** you run in your terminal when setting up or changing your admin password.

```
python generate_bcrypt.py
> Enter your desired admin password: ••••••••
> Confirm password: ••••••••
> 
> Success! Here is your bcrypt hash:
> --------------------------------------------------
> $2b$12$POlKlv...
> --------------------------------------------------
> Add or update the following line in your .env file:
> ADMIN_PASSWORD_HASH='$2b$12$POlKlv...'
```

You then copy the hash into your `.env` file. The server will use it to verify logins.

> This script is listed in `.gitignore` — it doesn't need to be in version control.

### `generate_admin.py` — Admin HTML Generator

This was a **one-time script** used to initially generate `admin.html`. It contains the entire HTML for the admin panel as a Python string and writes it to a file.

It's no longer needed for regular operation — `admin.html` already exists. If you want to make changes to `admin.html`, you can either edit `admin.html` directly or edit the HTML string inside `generate_admin.py` and re-run it.

---

## 7. The Data & Asset Directories

### `blog_assets/`

The central data store for the blog.

| Path | Contents |
|---|---|
| `blog_assets/posts.json` | Array of all post objects. This is your "database." |
| `blog_assets/avatar.jpg` | Your profile photo (shown on every blog card). |
| `blog_assets/images/` | Carousel images uploaded with posts (named `{timestamp}_{slug}.webp`). |
| `blog_assets/gallery/` | Gallery images uploaded with posts. |

**A post object in `posts.json` looks like this:**
```json
{
  "slug": "my-camping-trip",
  "title": "My Camping Trip",
  "content": "We drove up the mountain...\n\nThe view was incredible.",
  "image_paths": ["blog_assets/images/1720643200_camping.webp"],
  "gallery_images": ["blog_assets/gallery/1720643201_camp1.webp"],
  "likes": 14,
  "created_at": "2026-07-10T14:30:00.000000",
  "updated_at": "2026-07-10T14:30:00.000000"
}
```

### `posts/`

Contains auto-generated HTML pages for each individual post. Example: `posts/my-camping-trip.html`. Each file is rebuilt by `regenerate_all()` whenever anything changes.

### `gallery/`

Contains auto-generated HTML gallery pages. Example: `gallery/my-camping-trip.html`. Only created for posts that have gallery images.

---

## 8. Key Concepts Explained Simply

### How a Blog Post Goes from Creation to Live Page

```
1. You open /admin and log in
2. You fill in the title, content, and upload images in the admin panel
3. Browser crops images → converts to WebP → encodes to base64 strings
4. Browser sends a POST request to /api/v1/posts with all data as JSON
5. main.py receives it:
   a. Decodes each base64 image → saves as a file in blog_assets/images/
   b. Generates a slug from the title (e.g., "My Trip" → "my-trip")
   c. Creates a post object with slug, title, content, image_paths, likes=0, timestamps
   d. Prepends it to the posts list (newest first)
   e. Saves the updated list to blog_assets/posts.json
   f. Calls serve.regenerate_all(posts) which:
      - Rebuilds blog.html (the full feed)
      - Rebuilds posts/my-trip.html (the individual post page)
      - Rebuilds gallery/my-trip.html (if gallery images exist)
6. Visitor navigates to /blog → sees the updated feed instantly
7. Visitor clicks "Read Full Post" → goes to /posts/my-trip.html
```

---

### How Authentication Works

The admin panel uses **two layers** of authentication: a login mechanism and a session cookie.

```
Login Flow:
─────────────────────────────────────────────────────────────
Option A: Password Login
  1. You type your password
  2. Browser sends it to POST /api/v1/login (with your username)
  3. Server checks: does username match? Does bcrypt.checkpw(password, stored_hash) return True?
  4. If yes → server creates a JWT token → sets it as an httponly cookie named "admin_session"
  5. All future admin requests automatically include this cookie → server validates it

Option B: WebAuthn (Biometric) Login
  1. Browser calls GET /api/v1/webauthn/authenticate/generate
  2. Server creates a random "challenge" (a string to sign) → stores it temporarily
  3. Browser passes challenge to your device → device signs it with your private key → returns proof
  4. Browser sends proof to POST /api/v1/webauthn/authenticate/verify
  5. Server verifies signature using stored public key → if valid → issues JWT cookie (same as Option A)

After Login:
  - Every request to a protected endpoint goes through verify_admin_session(request)
  - This reads the "admin_session" cookie, decodes the JWT, checks that role == "admin"
  - If anything is wrong → returns HTTP 401 Unauthorized
```

---

### How Static HTML Generation Works

Instead of building pages on-the-fly for every visitor (slow), this site **pre-builds all pages** whenever content changes (fast).

```
When you create/edit/delete a post:
  ↓
regenerate_all(posts) runs
  ↓
  ├── Reads all posts from memory
  ├── Loops through each post to build HTML strings
  ├── Injects them into template strings (BLOG_TEMPLATE, POST_TEMPLATE, etc.)
  └── Writes the finished HTML to disk:
      ├── blog.html
      ├── posts/camping-trip.html
      ├── posts/another-post.html
      └── gallery/camping-trip.html

When a visitor requests /blog:
  ↓
FastAPI's StaticFiles serves the pre-built blog.html directly from disk
  ↓
No Python code runs for this visitor → just plain file delivery → very fast
```

---

## 9. API Reference Cheat Sheet

### Public Endpoints (No Login Required)

| Method | URL | Description |
|---|---|---|
| GET | `/` | Homepage (index.html or personal_index.html) |
| GET | `/blog` | Blog feed page |
| GET | `/admin` | Admin panel |
| GET | `/api/v1/posts` | Get all posts as JSON |
| PATCH | `/api/posts/{slug}` | Update a post's like count |
| GET | `/api/v1/webauthn/authenticate/generate` | Start biometric login |
| POST | `/api/v1/webauthn/authenticate/verify` | Complete biometric login |

### Admin Endpoints (Login Required)

| Method | URL | Description |
|---|---|---|
| POST | `/api/v1/login` | Log in with password |
| POST | `/api/v1/logout` | Log out |
| POST | `/api/v1/posts` | Create a new post |
| PUT | `/api/v1/posts/{slug}` | Edit an existing post |
| DELETE | `/api/v1/posts/{slug}` | Delete a post |
| POST | `/api/v1/profile-picture` | Update avatar photo |
| GET | `/api/v1/settings` | Get server settings |
| PUT | `/api/v1/settings` | Save server settings |
| GET | `/api/v1/webauthn/register/generate` | Start biometric device registration |
| POST | `/api/v1/webauthn/register/verify` | Complete biometric device registration |

---

## 10. How to Run the Server

### First-Time Setup

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your admin password (run this once, copy output into .env)
python generate_bcrypt.py

# 3. Make sure your .env looks like this:
#    SECRET_KEY=<some long random string>
#    ALGORITHM=HS256
#    ADMIN_USERNAME=TheLionBro024
#    ADMIN_PASSWORD_HASH='$2b$12$...'
```

### Starting the Server

```powershell
python main.py
```

Output will look like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Accessing the Site

| URL | What you see |
|---|---|
| `http://localhost:8000/` | Public homepage |
| `http://localhost:8000/blog` | Blog feed |
| `http://localhost:8000/admin` | Admin panel (login required) |

### Stopping the Server

Press `Ctrl+C` in the terminal.

---

> **Summary:** `main.py` runs the server and defines the API. `serve.py` provides the HTML templates and functions to generate/rebuild all pages. `blog_assets/posts.json` is the database. All generated HTML files in `posts/` and `gallery/` are disposable — they get rebuilt automatically.
