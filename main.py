import os
import json
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import hashlib

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import jwt
from dotenv import load_dotenv
import bcrypt

from webauthn import generate_registration_options, verify_registration_response, generate_authentication_options, verify_authentication_response
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential, AuthenticatorSelectionCriteria, UserVerificationRequirement

import serve  # Assuming serve.py contains init_folders, load_posts, save_posts, regenerate_all, save_image_file, generate_unique_slug

load_dotenv(override=True)

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

RP_ID = "localhost" # Adjust for Cloudflare tunnel if needed
RP_NAME = "whoami Admin"
ORIGIN = "http://localhost:8000" # Adjust for tunnel

app = FastAPI()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_admin_session(request: Request):
    token = request.cookies.get("admin_session")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role: str = payload.get("role")
        if role != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid role")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return True

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/v1/login")
def login(req: LoginRequest, response: Response):
    # Check username
    if req.username != ADMIN_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    # Verify the bcrypt hash of the password
    try:
        if not bcrypt.checkpw(req.password.encode('utf-8'), ADMIN_PASSWORD_HASH.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data={"role": "admin"})
    response.set_cookie(
        key="admin_session",
        value=access_token,
        httponly=True,
        secure=False, # Set to True in production with HTTPS
        samesite="lax",
        max_age=7*24*3600
    )
    return {"message": "Login successful"}

@app.post("/api/v1/logout")
def logout(response: Response):
    response.delete_cookie("admin_session")
    return {"message": "Logged out"}

# ---------------------------------------------------------------------------
# WEBAUTHN (BIOMETRICS)
# ---------------------------------------------------------------------------
db = {"credentials": []}
if os.path.exists(".webauthn_db.json"):
    with open(".webauthn_db.json", "r") as f:
        db = json.load(f)

def save_db():
    with open(".webauthn_db.json", "w") as f:
        json.dump(db, f)

challenges = {}

@app.get("/api/v1/webauthn/register/generate")
def webauthn_register_generate(request: Request, _ = Depends(verify_admin_session)):
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=b"admin",
        user_name="admin",
        user_display_name="Administrator",
    )
    challenges["register"] = options.challenge
    return json.loads(options.json())

@app.post("/api/v1/webauthn/register/verify")
async def webauthn_register_verify(request: Request, _ = Depends(verify_admin_session)):
    body = await request.json()
    challenge = challenges.get("register")
    if not challenge:
        raise HTTPException(status_code=400, detail="No challenge found")
    
    verification = verify_registration_response(
        credential=body,
        expected_challenge=challenge,
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
    )
    
    # Save the credential public key
    db["credentials"].append({
        "id": base64.b64encode(verification.credential_id).decode('utf-8'),
        "public_key": base64.b64encode(verification.credential_public_key).decode('utf-8'),
        "sign_count": verification.sign_count
    })
    save_db()
    return {"message": "Registration verified"}

@app.get("/api/v1/webauthn/authenticate/generate")
def webauthn_authenticate_generate():
    options = generate_authentication_options(
        rp_id=RP_ID,
    )
    challenges["auth"] = options.challenge
    return json.loads(options.json())

@app.post("/api/v1/webauthn/authenticate/verify")
async def webauthn_authenticate_verify(request: Request, response: Response):
    body = await request.json()
    challenge = challenges.get("auth")
    if not challenge:
        raise HTTPException(status_code=400, detail="No challenge found")
    
    # Find matching credential
    cred_id = body.get("id")
    stored_cred = next((c for c in db["credentials"] if c["id"] == cred_id), None)
    if not stored_cred:
        raise HTTPException(status_code=400, detail="Credential not registered")
    
    verification = verify_authentication_response(
        credential=body,
        expected_challenge=challenge,
        expected_rp_id=RP_ID,
        expected_origin=ORIGIN,
        credential_public_key=base64.b64decode(stored_cred["public_key"]),
        credential_current_sign_count=stored_cred["sign_count"]
    )
    
    # Update sign count
    stored_cred["sign_count"] = verification.new_sign_count
    save_db()
    
    # Issue cookie
    access_token = create_access_token(data={"role": "admin"})
    response.set_cookie(
        key="admin_session",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7*24*3600
    )
    return {"message": "Authentication verified"}


# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------
settings_db = {"cache_enabled": True, "image_quality": "high", "analytics_enabled": True, "maintenance_mode": False}
if os.path.exists(".settings.json"):
    with open(".settings.json", "r") as f:
        settings_db = json.load(f)

@app.get("/api/v1/settings")
def get_settings(_ = Depends(verify_admin_session)):
    return settings_db

@app.put("/api/v1/settings")
async def update_settings(request: Request, _ = Depends(verify_admin_session)):
    body = await request.json()
    settings_db.update(body)
    with open(".settings.json", "w") as f:
        json.dump(settings_db, f)
    return settings_db

# ---------------------------------------------------------------------------
# POST CRUD API (Requires Auth)
# ---------------------------------------------------------------------------

@app.get("/api/v1/posts")
def get_all_posts():
    return serve.load_posts()

@app.post("/api/v1/posts", dependencies=[Depends(verify_admin_session)])
async def create_post(request: Request):
    data = await request.json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()

    if not title or not content:
        raise HTTPException(status_code=400, detail="Title and content are required")

    image_paths = []
    for img in data.get('images', []):
        if img.get('data'):
            path = serve.save_image_file(img['data'], img.get('name', 'image.jpg'), 'images')
            image_paths.append(path)

    gallery_image_paths = []
    for img in data.get('gallery_images', []):
        if img.get('data'):
            path = serve.save_image_file(img['data'], img.get('name', 'gallery.jpg'), 'gallery')
            gallery_image_paths.append(path)

    posts = serve.load_posts()
    slug = serve.generate_unique_slug(title, posts)
    now = datetime.now().isoformat()

    new_post = {
        "slug": slug,
        "title": title,
        "content": content,
        "image_paths": image_paths,
        "gallery_images": gallery_image_paths,
        "likes": 0,
        "created_at": now,
        "updated_at": now
    }

    posts.insert(0, new_post)
    serve.save_posts(posts)
    serve.regenerate_all(posts)
    return {"status": "success", "slug": slug}

@app.put("/api/v1/posts/{post_id}", dependencies=[Depends(verify_admin_session)])
async def update_post(post_id: str, request: Request):
    data = await request.json()
    posts = serve.load_posts()
    updated = False
    
    for post in posts:
        if post['slug'] == post_id:
            if 'title' in data:
                post['title'] = data['title']
            if 'content' in data:
                post['content'] = data['content']
            
            # For simplicity, if editing replaces images, we might handle base64 array here again.
            # But normally we would handle add/remove logic.
            # I will overwrite images if provided
            if 'images' in data and isinstance(data['images'], list):
                # We could delete old ones, but let's just do simple overwrite of paths if data is provided
                image_paths = []
                for img in data['images']:
                    if img.get('data'):
                        path = serve.save_image_file(img['data'], img.get('name', 'image.jpg'), 'images')
                        image_paths.append(path)
                    elif img.get('path'):
                        image_paths.append(img['path'])
                post['image_paths'] = image_paths
                
            post['updated_at'] = datetime.now().isoformat()
            updated = True
            break
            
    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")
        
    serve.save_posts(posts)
    serve.regenerate_all(posts)
    return {"status": "updated"}

@app.delete("/api/v1/posts/{post_id}", dependencies=[Depends(verify_admin_session)])
def delete_post(post_id: str):
    posts = serve.load_posts()
    post_to_delete = next((p for p in posts if p['slug'] == post_id), None)
    if not post_to_delete:
        raise HTTPException(status_code=404, detail="Post not found")

    posts.remove(post_to_delete)
    serve.save_posts(posts)

    # Delete carousel images
    for img_path in post_to_delete.get('image_paths', []):
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
        except Exception as e:
            pass

    # Delete gallery images
    for img_path in post_to_delete.get('gallery_images', []):
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
        except Exception as e:
            pass

    # Delete static HTML files
    for path in [
        os.path.join('posts', f"{post_id}.html"),
        os.path.join('gallery', f"{post_id}.html")
    ]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            pass

    serve.regenerate_all(posts)
    return {"status": "deleted", "slug": post_id}

@app.post("/api/v1/profile-picture", dependencies=[Depends(verify_admin_session)])
async def upload_profile_picture(request: Request):
    data = await request.json()
    img_data = data.get('image', '')
    if not img_data:
        raise HTTPException(status_code=400, detail="No image data provided")

    header, encoded = img_data.split(",", 1)
    decoded_img = base64.b64decode(encoded)
    with open('blog_assets/avatar.jpg', 'wb') as f:
        f.write(decoded_img)

    posts = serve.load_posts()
    serve.regenerate_all(posts)
    return {"status": "ok"}

# Public API for likes
@app.patch("/api/posts/{post_id}")
async def patch_likes(post_id: str, request: Request):
    data = await request.json()
    posts = serve.load_posts()
    updated = False
    for post in posts:
        if post['slug'] == post_id:
            if 'likes' in data:
                post['likes'] = int(data['likes'])
            post['updated_at'] = datetime.now().isoformat()
            updated = True
            break
            
    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")
        
    serve.save_posts(posts)
    serve.regenerate_all(posts)
    return {"status": "updated"}

# ---------------------------------------------------------------------------
# ROUTING
# ---------------------------------------------------------------------------

from fastapi.responses import JSONResponse

@app.middleware("http")
async def security_and_host_middleware(request: Request, call_next):
    # Block access to sensitive files
    path = request.url.path.lower()
    if "/.git" in path or "/.env" in path:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    # This middleware can handle Cloudflare tunnel forwarded host headers
    # e.g., X-Forwarded-Host if necessary
    response = await call_next(request)
    return response

# Explicit Admin Route
@app.get("/admin")
def read_admin():
    return FileResponse("admin.html")

# Explicit Blog Route
@app.get("/blog")
def read_blog():
    return FileResponse("blog.html")

# Static mock site at root
@app.get("/")
def read_root(request: Request):
    # Cloudflare often passes the original domain in the X-Forwarded-Host header
    raw_host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    host = str(raw_host).lower()
    if "op.evolvplatform.com" in host:
        return FileResponse("personal_index.html")
    return FileResponse("index.html")

# Mount the entire directory to serve all assets, blog, admin, and generated posts.
# `html=True` automatically lets you visit `/blog` and it will serve `blog.html` under the hood!
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
