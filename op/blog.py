#op.evolv — Post CRUD, profile picture, and public likes API for op.evolvplatform.com
import base64
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

import op.serve as serve
from op.auth import verify_admin_session

router = APIRouter(tags=["blog"])

_OP_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Post CRUD (admin only)
# ---------------------------------------------------------------------------

@router.get("/api/v1/posts")
def get_all_posts():
    return serve.load_posts()


@router.post("/api/v1/posts", dependencies=[Depends(verify_admin_session)])
async def create_post(request: Request):
    data = await request.json()
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        raise HTTPException(status_code=400, detail="Title and content are required")

    image_paths = []
    for img in data.get("images", []):
        if img.get("data"):
            path = serve.save_image_file(img["data"], img.get("name", "image.jpg"), "images")
            image_paths.append(path)

    gallery_image_paths = []
    for img in data.get("gallery_images", []):
        if img.get("data"):
            path = serve.save_image_file(img["data"], img.get("name", "gallery.jpg"), "gallery")
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
        "updated_at": now,
    }

    posts.insert(0, new_post)
    serve.save_posts(posts)
    serve.regenerate_all(posts)
    return {"status": "success", "slug": slug}


@router.put("/api/v1/posts/{post_id}", dependencies=[Depends(verify_admin_session)])
async def update_post(post_id: str, request: Request):
    data = await request.json()
    posts = serve.load_posts()
    updated = False

    for post in posts:
        if post["slug"] == post_id:
            if "title" in data:
                post["title"] = data["title"]
            if "content" in data:
                post["content"] = data["content"]
            if "images" in data and isinstance(data["images"], list):
                image_paths = []
                for img in data["images"]:
                    if img.get("data"):
                        path = serve.save_image_file(img["data"], img.get("name", "image.jpg"), "images")
                        image_paths.append(path)
                    elif img.get("path"):
                        image_paths.append(img["path"])
                post["image_paths"] = image_paths
            post["updated_at"] = datetime.now().isoformat()
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")

    serve.save_posts(posts)
    serve.regenerate_all(posts)
    return {"status": "updated"}


@router.delete("/api/v1/posts/{post_id}", dependencies=[Depends(verify_admin_session)])
def delete_post(post_id: str):
    posts = serve.load_posts()
    post_to_delete = next((p for p in posts if p["slug"] == post_id), None)
    if not post_to_delete:
        raise HTTPException(status_code=404, detail="Post not found")

    posts.remove(post_to_delete)
    serve.save_posts(posts)

    for img_path in post_to_delete.get("image_paths", []):
        try:
            full = os.path.join(_OP_DIR, img_path)
            if os.path.exists(full):
                os.remove(full)
        except Exception:
            pass

    for img_path in post_to_delete.get("gallery_images", []):
        try:
            full = os.path.join(_OP_DIR, img_path)
            if os.path.exists(full):
                os.remove(full)
        except Exception:
            pass

    for rel in [
        os.path.join("posts", f"{post_id}.html"),
        os.path.join("gallery", f"{post_id}.html"),
    ]:
        full = os.path.join(_OP_DIR, rel)
        try:
            if os.path.exists(full):
                os.remove(full)
        except Exception:
            pass

    serve.regenerate_all(posts)
    return {"status": "deleted", "slug": post_id}


@router.post("/api/v1/profile-picture", dependencies=[Depends(verify_admin_session)])
async def upload_profile_picture(request: Request):
    data = await request.json()
    img_data = data.get("image", "")
    if not img_data:
        raise HTTPException(status_code=400, detail="No image data provided")

    header, encoded = img_data.split(",", 1)
    decoded_img = base64.b64decode(encoded)
    avatar_path = os.path.join(_OP_DIR, "blog_assets", "avatar.jpg")
    with open(avatar_path, "wb") as f:
        f.write(decoded_img)

    posts = serve.load_posts()
    serve.regenerate_all(posts)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Public API: likes
# ---------------------------------------------------------------------------

@router.patch("/api/posts/{post_id}")
async def patch_likes(post_id: str, request: Request):
    data = await request.json()
    posts = serve.load_posts()
    updated = False
    for post in posts:
        if post["slug"] == post_id:
            if "likes" in data:
                post["likes"] = int(data["likes"])
            post["updated_at"] = datetime.now().isoformat()
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")

    serve.save_posts(posts)
    serve.regenerate_all(posts)
    return {"status": "updated"}
