import http.server
import socketserver
import socket
import json
import os
import re
import urllib.parse
from datetime import datetime
import base64

PORT = 8000

# --- TEMPLATE DEFINITIONS ---
BLOG_TEMPLATE = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog // whoami</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f12;
            --accent-green: #00ff66;
            --text-main: #f0f3f6;
            --text-muted: #95a5b2;
            --border-light: rgba(255, 255, 255, 0.08);
            --font-mono: 'JetBrains Mono', monospace;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            scroll-behavior: smooth;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.8;
            overflow-x: hidden;
        }}

        /* --- NAVIGATION & HAMBURGER MENU --- */
        nav {{
            position: fixed;
            top: 0;
            width: 100%;
            padding: 24px 5%;
            display: flex;
            justify-content: flex-end;
            z-index: 100;
        }}

        .hamburger {{
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 6px;
            z-index: 101;
        }}

        .hamburger span {{
            display: block;
            width: 30px;
            height: 2px;
            background-color: #ffffff;
            transition: 0.3s ease;
        }}

        .hamburger:hover span {{
            background-color: var(--accent-green);
        }}

        .menu-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            background-color: rgba(11, 15, 18, 0.98);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 30px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            z-index: 99;
        }}

        .menu-overlay.active {{
            opacity: 1;
            pointer-events: all;
        }}

        .menu-overlay a {{
            font-size: 24px;
            color: #ffffff;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s ease;
        }}

        .menu-overlay a:hover {{
            color: var(--accent-green);
        }}

        /* --- FEED CONTAINER --- */
        .feed-container {{
            max-width: 600px;
            margin: 100px auto 60px auto;
            padding: 0 16px;
            box-sizing: border-box;
        }}

        .post-card {{
            background-color: #12181c;
            border: 1px solid var(--border-light);
            border-radius: 8px;
            margin-bottom: 32px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }}

        .post-card:hover {{
            border-color: var(--accent-green);
            box-shadow: 0 8px 24px rgba(0, 255, 102, 0.1);
        }}

        .card-header {{
            display: flex;
            align-items: center;
            padding: 14px 16px;
            gap: 12px;
        }}

        .card-avatar {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 1px solid var(--accent-green);
            object-fit: cover;
            background-color: var(--bg-color);
        }}

        .card-user-info {{
            display: flex;
            flex-direction: column;
            line-height: 1.3;
        }}

        .card-username {{
            font-size: 14px;
            font-weight: 600;
            color: #ffffff;
        }}

        .card-time {{
            font-family: var(--font-mono);
            font-size: 10px;
            color: var(--text-muted);
            margin-top: 2px;
        }}

        .card-image-link {{
            display: block;
            width: 100%;
            overflow: hidden;
            background-color: #0b0f12;
            border-top: 1px solid rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid rgba(255, 255, 255, 0.02);
        }}

        .card-image {{
            width: 100%;
            height: auto;
            display: block;
            object-fit: cover;
            max-height: 550px;
            transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        .card-image-link:hover .card-image {{
            transform: scale(1.02);
        }}

        .card-actions {{
            display: flex;
            gap: 16px;
            padding: 14px 16px 10px 16px;
        }}

        .action-icon {{
            color: var(--text-muted);
            cursor: pointer;
            transition: color 0.2s ease, transform 0.1s ease;
        }}

        .action-icon:hover {{
            color: var(--accent-green);
            transform: scale(1.1);
        }}

        .bookmark-container {{
            margin-left: auto;
            display: flex;
            align-items: center;
        }}

        .card-caption {{
            padding: 0 16px 16px 16px;
            font-size: 15px;
            line-height: 1.6;
        }}

        .card-title {{
            font-family: var(--font-mono);
            font-size: 16px;
            font-weight: 700;
            color: var(--accent-green);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}

        .card-text {{
            color: var(--text-main);
            margin-bottom: 12px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            font-size: 14px;
        }}

        .card-text p {{
            margin-bottom: 8px;
        }}

        .card-read-more {{
            display: inline-block;
            color: var(--accent-green);
            font-family: var(--font-mono);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            text-decoration: none;
            border-bottom: 1px dashed rgba(0, 255, 102, 0.3);
            transition: border-color 0.2s ease, color 0.2s ease;
        }}

        .card-read-more:hover {{
            border-bottom-color: var(--accent-green);
            color: var(--accent-green);
        }}

        .no-posts {{
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted);
            font-family: var(--font-mono);
            font-size: 14px;
            border: 1px dashed var(--border-light);
            border-radius: 6px;
        }}

        footer {{
            text-align: center;
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-muted);
            border-top: 1px solid var(--border-light);
            padding: 30px 0;
            margin-top: 40px;
        }}

        /* --- MOBILE RESPONSIVE --- */
        @media (max-width: 768px) {{
            .feed-container {{
                margin-top: 80px;
                padding: 0 12px;
            }}

            .post-card {{
                margin-bottom: 24px;
                border-radius: 6px;
            }}
        }}
    </style>
</head>

<body>

    <nav>
        <div class="hamburger" onclick="toggleMenu()" id="menu-btn">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </nav>

    <div class="menu-overlay" id="mobile-menu">
        <a href="index.html" onclick="toggleMenu()">Home</a>
        <a href="blog.html" onclick="toggleMenu()">Blog</a>
        <a href="https://www.instagram.com/thelionbro024/" target="_blank" onclick="toggleMenu()">Instagram</a>
        <a href="https://bere.al/thelionbro024/" target="_blank" onclick="toggleMenu()">BeReal</a>
        <a href="https://evolvplatform.com/" target="_blank" onclick="toggleMenu()">Evolv.Platform</a>
        <a href="mailto:thelionbro024@gmail.com" onclick="toggleMenu()">Email</a>
    </div>

    <main class="feed-container">
        {posts_feed_html}
        
        <footer>
            <div>Operated/Saved by Grace // © 2026</div>
        </footer>
    </main>

    <script>
        function toggleMenu() {{
            const menu = document.getElementById('mobile-menu');
            menu.classList.toggle('active');

            const lines = document.querySelectorAll('.hamburger span');
            if (menu.classList.contains('active')) {{
                lines[0].style.transform = 'translateY(8px) rotate(45deg)';
                lines[1].style.opacity = '0';
                lines[2].style.transform = 'translateY(-8px) rotate(-45deg)';
            }} else {{
                lines[0].style.transform = 'none';
                lines[1].style.opacity = '1';
                lines[2].style.transform = 'none';
            }}
        }}
    </script>
</body>

</html>"""

POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post_title} // Blog</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f12;
            --accent-green: #00ff66;
            --text-main: #f0f3f6;
            --text-muted: #95a5b2;
            --border-light: rgba(255, 255, 255, 0.08);
            --font-mono: 'JetBrains Mono', monospace;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            scroll-behavior: smooth;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.8;
            overflow-x: hidden;
        }}

        /* --- NAVIGATION & HAMBURGER MENU --- */
        nav {{
            position: fixed;
            top: 0;
            width: 100%;
            padding: 24px 5%;
            display: flex;
            justify-content: flex-end;
            z-index: 100;
        }}

        .hamburger {{
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 6px;
            z-index: 101;
        }}

        .hamburger span {{
            display: block;
            width: 30px;
            height: 2px;
            background-color: #ffffff;
            transition: 0.3s ease;
        }}

        .hamburger:hover span {{
            background-color: var(--accent-green);
        }}

        .menu-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            background-color: rgba(11, 15, 18, 0.98);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 30px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            z-index: 99;
        }}

        .menu-overlay.active {{
            opacity: 1;
            pointer-events: all;
        }}

        .menu-overlay a {{
            font-size: 24px;
            color: #ffffff;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s ease;
        }}

        .menu-overlay a:hover {{
            color: var(--accent-green);
        }}

        /* --- POST VIEW --- */
        .post-container {{
            max-width: 680px;
            margin: 120px auto 100px auto;
            padding: 0 20px;
        }}

        .back-link {{
            display: inline-block;
            font-family: var(--font-mono);
            color: var(--accent-green);
            text-decoration: none;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 30px;
            border-bottom: 1px dashed rgba(0, 255, 102, 0.3);
            transition: border-color 0.2s ease, color 0.2s ease;
        }}

        .back-link:hover {{
            color: var(--accent-green);
            border-bottom-color: var(--accent-green);
        }}

        .post-header-title {{
            font-size: 40px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #ffffff;
            line-height: 1.2;
            margin-bottom: 15px;
        }}

        .post-meta {{
            font-family: var(--font-mono);
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 40px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .post-meta span {{
            color: var(--accent-green);
        }}

        .post-featured-image {{
            width: 100%;
            border-radius: 6px;
            border: 1px solid var(--border-light);
            margin-bottom: 40px;
            max-height: 500px;
            object-fit: cover;
        }}

        .post-content {{
            font-size: 16px;
            color: var(--text-main);
            line-height: 1.8;
        }}

        .post-content p {{
            margin-bottom: 24px;
        }}

        .post-content a {{
            color: var(--accent-green);
            text-decoration: none;
            border-bottom: 1px dashed rgba(0, 255, 102, 0.4);
            transition: border-color 0.2s ease;
        }}

        .post-content a:hover {{
            border-bottom-color: var(--accent-green);
        }}

        footer {{
            text-align: center;
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-muted);
            border-top: 1px solid var(--border-light);
            padding-top: 40px;
            margin-top: 60px;
        }}

        /* --- MOBILE RESPONSIVE --- */
        @media (max-width: 768px) {{
            .post-container {{
                margin-top: 80px;
            }}

            .post-header-title {{
                font-size: 32px;
            }}
        }}
    </style>
</head>

<body>

    <nav>
        <div class="hamburger" onclick="toggleMenu()" id="menu-btn">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </nav>

    <div class="menu-overlay" id="mobile-menu">
        <a href="../index.html" onclick="toggleMenu()">Home</a>
        <a href="../blog.html" onclick="toggleMenu()">Blog</a>
        <a href="https://www.instagram.com/thelionbro024/" target="_blank" onclick="toggleMenu()">Instagram</a>
        <a href="https://bere.al/thelionbro024/" target="_blank" onclick="toggleMenu()">BeReal</a>
        <a href="https://evolvplatform.com/" target="_blank" onclick="toggleMenu()">Evolv.Platform</a>
        <a href="mailto:thelionbro024@gmail.com" onclick="toggleMenu()">Email</a>
    </div>

    <main class="post-container">
        <a href="../blog.html" class="back-link">← Back to Blog</a>
        
        <article>
            <h1 class="post-header-title">{post_title}</h1>
            <div class="post-meta">
                Last edited <span>{post_date}</span>
            </div>
            
            {post_image_html}
            
            <div class="post-content">
                {post_content_html}
            </div>
        </article>

        <footer>
            <div>Operated/Saved by Grace // © 2026</div>
        </footer>
    </main>

    <script>
        function toggleMenu() {{
            const menu = document.getElementById('mobile-menu');
            menu.classList.toggle('active');

            const lines = document.querySelectorAll('.hamburger span');
            if (menu.classList.contains('active')) {{
                lines[0].style.transform = 'translateY(8px) rotate(45deg)';
                lines[1].style.opacity = '0';
                lines[2].style.transform = 'translateY(-8px) rotate(-45deg)';
            }} else {{
                lines[0].style.transform = 'none';
                lines[1].style.opacity = '1';
                lines[2].style.transform = 'none';
            }}
        }}
    </script>
</body>

</html>"""


# --- UTILITY FUNCTIONS ---

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def slugify(text):
    text = text.lower()
    # Replace anything that's not alphanumeric, spaces, or hyphens
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    # Replace spaces or multiple hyphens with a single hyphen
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


def generate_unique_slug(title, posts):
    base_slug = slugify(title)
    if not base_slug:
        base_slug = "post"
    slug = base_slug
    count = 1
    while any(p['slug'] == slug for p in posts):
        slug = f"{base_slug}-{count}"
        count += 1
    return slug


def init_folders():
    os.makedirs('blog_assets/images', exist_ok=True)
    os.makedirs('posts', exist_ok=True)
    if not os.path.exists('blog_assets/posts.json'):
        with open('blog_assets/posts.json', 'w', encoding='utf-8') as f:
            json.dump([], f)


def load_posts():
    init_folders()
    try:
        with open('blog_assets/posts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_posts(posts):
    with open('blog_assets/posts.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=4, ensure_ascii=False)


def format_date(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        return iso_str


def format_content_html(content):
    paragraphs = content.split('\n\n')
    formatted = []
    for p in paragraphs:
        if p.strip():
            p_html = p.strip().replace('\n', '<br>')
            # Prevent raw tags, keep line breaks
            formatted.append(f"<p>{p_html}</p>")
    return '\n'.join(formatted)


def regenerate_all(posts):
    init_folders()
    
    # 1. Generate blog.html
    posts_feed_html = ""
    if not posts:
        posts_feed_html = '<div class="no-posts">No blog posts yet. Visit the local admin panel to add one!</div>'
    else:
        for post in posts:
            formatted_date = format_date(post['updated_at'])
            
            img_html = ""
            if post['image_path']:
                img_src = post['image_path']
                img_html = f"""
                <a href="posts/{post['slug']}.html" class="card-image-link">
                    <img class="card-image" src="{img_src}" alt="{post['title']}" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 fill=%22%2312181c%22/><text x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 fill=%22%2395a5b2%22 font-family=%22sans-serif%22 font-size=%2210%22>No Image</text></svg>'">
                </a>
                """
            
            snippet = post['content'][:250] + "..." if len(post['content']) > 250 else post['content']
            snippet_html = format_content_html(snippet)

            posts_feed_html += f"""
            <article class="post-card">
                <header class="card-header">
                    <img class="card-avatar" src="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=100&q=80" alt="Avatar" onerror="this.src='https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y'">
                    <div class="card-user-info">
                        <span class="card-username">thelionbro024</span>
                        <time class="card-time" datetime="{post['updated_at']}">{formatted_date}</time>
                    </div>
                </header>
                
                {img_html}
                
                <div class="card-actions">
                    <svg class="action-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                    <svg class="action-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                    <svg class="action-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                    <div class="bookmark-container">
                        <svg class="action-icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
                    </div>
                </div>
                
                <div class="card-caption">
                    <h3 class="card-title">{post['title']}</h3>
                    <div class="card-text">
                        {snippet_html}
                    </div>
                    <a href="posts/{post['slug']}.html" class="card-read-more">Read Full Post</a>
                </div>
            </article>
            """
            
    blog_content = BLOG_TEMPLATE.format(
        posts_feed_html=posts_feed_html
    )
    with open('blog.html', 'w', encoding='utf-8') as f:
        f.write(blog_content)
        
    # 2. Generate each post's HTML page in posts/
    for post in posts:
        post_date = format_date(post['updated_at'])
        post_content_html = format_content_html(post['content'])
        
        post_image_html = ""
        if post['image_path']:
            # Prefix path with ../ because files are generated inside posts/
            img_src = f"../{post['image_path']}"
            post_image_html = f'<img class="post-featured-image" src="{img_src}" alt="{post["title"]}">'
            
        post_content = POST_TEMPLATE.format(
            post_title=post['title'],
            post_date=post_date,
            post_image_html=post_image_html,
            post_content_html=post_content_html
        )
        
        filepath = os.path.join('posts', f"{post['slug']}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(post_content)


# --- CUSTOM HTTP REQUEST HANDLER ---

class BlogHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # API: get list of posts
        if self.path == '/api/posts':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            # Disable caching
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            posts = load_posts()
            self.wfile.write(json.dumps(posts).encode('utf-8'))
            return
        
        # Admin redirection utility
        elif self.path == '/admin' or self.path == '/admin/':
            self.send_response(301)
            self.send_header('Location', '/admin.html')
            self.end_headers()
            return
            
        return super().do_GET()

    def do_POST(self):
        # API: create new post
        if self.path == '/api/posts':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                title = data.get('title', '').strip()
                content = data.get('content', '').strip()
                image_data = data.get('image', '')
                image_name = data.get('image_name', 'image.png')
                
                if not title or not content:
                    self.send_error_response(400, "Title and content are required")
                    return
                
                # Process image
                image_path = ""
                if image_data:
                    try:
                        header, encoded = image_data.split(",", 1)
                        decoded_img = base64.b64decode(encoded)
                        
                        ext = os.path.splitext(image_name)[1] or ".png"
                        if ext.lower() not in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                            ext = '.png'
                        
                        timestamp = int(datetime.now().timestamp())
                        safe_title = slugify(title)[:20]
                        img_filename = f"{timestamp}_{safe_title}{ext}"
                        img_filepath = os.path.join('blog_assets', 'images', img_filename)
                        
                        with open(img_filepath, 'wb') as f:
                            f.write(decoded_img)
                        
                        image_path = f"blog_assets/images/{img_filename}"
                    except Exception as e:
                        print(f"Error saving image: {e}")
                        self.send_error_response(500, f"Failed to save image: {str(e)}")
                        return

                posts = load_posts()
                slug = generate_unique_slug(title, posts)
                
                now = datetime.now().isoformat()
                
                new_post = {
                    "slug": slug,
                    "title": title,
                    "content": content,
                    "image_path": image_path,
                    "created_at": now,
                    "updated_at": now
                }
                
                posts.insert(0, new_post)
                save_posts(posts)
                
                # Rebuild all pages
                regenerate_all(posts)
                
                self.send_success_response({"status": "success", "slug": slug})
                
            except Exception as e:
                print(f"Error creating post: {e}")
                self.send_error_response(500, str(e))
            return
            
        self.send_error_response(404, "Not Found")

    def do_DELETE(self):
        # API: delete post
        if self.path.startswith('/api/posts/'):
            slug = self.path.split('/')[-1]
            posts = load_posts()
            
            post_to_delete = None
            for post in posts:
                if post['slug'] == slug:
                    post_to_delete = post
                    break
            
            if not post_to_delete:
                self.send_error_response(404, "Post not found")
                return
            
            # Remove from JSON
            posts.remove(post_to_delete)
            save_posts(posts)
            
            # Delete corresponding image file
            if post_to_delete['image_path']:
                try:
                    if os.path.exists(post_to_delete['image_path']):
                        os.remove(post_to_delete['image_path'])
                except Exception as e:
                    print(f"Error removing image file: {e}")
            
            # Delete corresponding static HTML file
            post_html_path = os.path.join('posts', f"{slug}.html")
            try:
                if os.path.exists(post_html_path):
                    os.remove(post_html_path)
            except Exception as e:
                print(f"Error removing post HTML file: {e}")
                
            # Rebuild all remaining pages
            regenerate_all(posts)
            
            self.send_success_response({"status": "deleted", "slug": slug})
            return
            
        self.send_error_response(404, "Not Found")

    def send_success_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))


# --- MAIN RUNNER ---

if __name__ == "__main__":
    init_folders()
    
    # Generate initial pages if none exist
    current_posts = load_posts()
    regenerate_all(current_posts)
    
    IP_ADDRESS = get_ip_address()
    
    with socketserver.TCPServer(("", PORT), BlogHTTPRequestHandler) as httpd:
        print(f"\n-- Blog Server started!")
        print(f"-- Local site:     http://localhost:{PORT}/index.html")
        print(f"-- Local blog:     http://localhost:{PORT}/blog.html")
        print(f"-- Local admin:    http://localhost:{PORT}/admin.html")
        print(f"-- Network access: http://{IP_ADDRESS}:{PORT}")
        print(f"\n-- Press Ctrl+C to stop the server.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n-- Server stopped.")
            httpd.server_close()
