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

# ---------------------------------------------------------------------------
# SHARED STYLE BLOCK (injected into every page)
# ---------------------------------------------------------------------------
SHARED_CSS = """
        :root {
            --bg-color: #0b0f12;
            --accent-green: #00ff66;
            --accent-red: #ff3366;
            --text-main: #f0f3f6;
            --text-muted: #95a5b2;
            --border-light: rgba(255, 255, 255, 0.08);
            --font-mono: 'JetBrains Mono', monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            scroll-behavior: smooth;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.8;
            overflow-x: hidden;
        }

        /* --- NAVIGATION & HAMBURGER MENU --- */
        nav {
            position: fixed;
            top: 0;
            width: 100%;
            padding: 24px 5%;
            display: flex;
            justify-content: flex-end;
            z-index: 100;
        }

        .hamburger {
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 6px;
            z-index: 101;
        }

        .hamburger span {
            display: block;
            width: 30px;
            height: 2px;
            background-color: #ffffff;
            transition: 0.3s ease;
        }

        .hamburger:hover span {
            background-color: var(--accent-green);
        }

        .menu-overlay {
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
        }

        .menu-overlay.active {
            opacity: 1;
            pointer-events: all;
        }

        .menu-overlay a {
            font-size: 24px;
            color: #ffffff;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s ease;
        }

        .menu-overlay a:hover {
            color: var(--accent-green);
        }
"""

NAV_TOGGLE_SCRIPT = """
        function toggleMenu() {
            const menu = document.getElementById('mobile-menu');
            menu.classList.toggle('active');
            const lines = document.querySelectorAll('.hamburger span');
            if (menu.classList.contains('active')) {
                lines[0].style.transform = 'translateY(8px) rotate(45deg)';
                lines[1].style.opacity = '0';
                lines[2].style.transform = 'translateY(-8px) rotate(-45deg)';
            } else {
                lines[0].style.transform = 'none';
                lines[1].style.opacity = '1';
                lines[2].style.transform = 'none';
            }
        }
"""

NAV_HTML = """
    <nav>
        <div class="hamburger" onclick="toggleMenu()" id="menu-btn">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </nav>

    <div class="menu-overlay" id="mobile-menu">
        <a href="https://op.evolvplatform.com/" onclick="toggleMenu()">Home</a>
        <a href="/blog" onclick="toggleMenu()">Blog</a>
        <a href="https://www.instagram.com/thelionbro024/" target="_blank" onclick="toggleMenu()">Instagram</a>
        <a href="https://bere.al/thelionbro024/" target="_blank" onclick="toggleMenu()">BeReal</a>
        <a href="https://evolvplatform.com/" target="_blank" onclick="toggleMenu()">Evolv.Platform</a>
        <a href="mailto:thelionbro024@gmail.com" onclick="toggleMenu()">Email</a>
    </div>
"""

NAV_HTML_POST = """
    <nav>
        <div class="hamburger" onclick="toggleMenu()" id="menu-btn">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </nav>

    <div class="menu-overlay" id="mobile-menu">
        <a href="https://op.evolvplatform.com/" onclick="toggleMenu()">Home</a>
        <a href="/blog" onclick="toggleMenu()">Blog</a>
        <a href="https://www.instagram.com/thelionbro024/" target="_blank" onclick="toggleMenu()">Instagram</a>
        <a href="https://bere.al/thelionbro024/" target="_blank" onclick="toggleMenu()">BeReal</a>
        <a href="https://evolvplatform.com/" target="_blank" onclick="toggleMenu()">Evolv.Platform</a>
        <a href="mailto:thelionbro024@gmail.com" onclick="toggleMenu()">Email</a>
    </div>
"""

NAV_HTML_GALLERY = """
    <nav>
        <div class="hamburger" onclick="toggleMenu()" id="menu-btn">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </nav>

    <div class="menu-overlay" id="mobile-menu">
        <a href="https://op.evolvplatform.com/" onclick="toggleMenu()">Home</a>
        <a href="/blog" onclick="toggleMenu()">Blog</a>
        <a href="https://www.instagram.com/thelionbro024/" target="_blank" onclick="toggleMenu()">Instagram</a>
        <a href="https://bere.al/thelionbro024/" target="_blank" onclick="toggleMenu()">BeReal</a>
        <a href="https://evolvplatform.com/" target="_blank" onclick="toggleMenu()">Evolv.Platform</a>
        <a href="mailto:thelionbro024@gmail.com" onclick="toggleMenu()">Email</a>
    </div>
"""

# ---------------------------------------------------------------------------
# BLOG TEMPLATE
# ---------------------------------------------------------------------------
BLOG_TEMPLATE = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1">
    <title>Blog // whoami</title>
    <link rel="icon" type="image/png" href="/favicon.png">
    <meta name="description" content="Adriel Loewen's personal blog — life, faith, engineering, and everything in between.">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
{shared_css}

        /* --- FEED CONTAINER --- */
        .feed-container {{
            max-width: 600px;
            margin: 100px auto 60px auto;
            padding: 0 16px;
            box-sizing: border-box;
        }}

        /* --- POST CARD --- */
        .post-card {{
            background-color: #12181c;
            border: 1px solid var(--border-light);
            border-radius: 12px;
            margin-bottom: 32px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }}

        .post-card:hover {{
            border-color: rgba(0, 255, 102, 0.35);
            box-shadow: 0 8px 24px rgba(0, 255, 102, 0.08);
        }}

        .card-header {{
            display: flex;
            align-items: center;
            padding: 14px 16px;
            gap: 12px;
        }}

        .card-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: 1.5px solid var(--accent-green);
            object-fit: cover;
            background-color: var(--bg-color);
            flex-shrink: 0;
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

        /* --- CAROUSEL --- */
        .card-carousel {{
            position: relative;
            width: 100%;
            overflow: hidden;
            background-color: #0b0f12;
            border-top: 1px solid rgba(255,255,255,0.03);
            border-bottom: 1px solid rgba(255,255,255,0.03);
            user-select: none;
        }}

        .carousel-track {{
            display: flex;
            transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            will-change: transform;
        }}

        .carousel-slide {{
            min-width: 100%;
            overflow: hidden;
        }}

        .carousel-slide img {{
            width: 100%;
            height: auto;
            display: block;
            object-fit: cover;
            max-height: 560px;
        }}

        .carousel-btn {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background-color: rgba(11,15,18,0.7);
            border: 1px solid rgba(255,255,255,0.12);
            color: #ffffff;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s ease;
            z-index: 2;
            backdrop-filter: blur(4px);
        }}

        .carousel-btn:hover {{
            background-color: rgba(0, 255, 102, 0.2);
            border-color: var(--accent-green);
        }}

        .carousel-btn.prev {{ left: 10px; }}
        .carousel-btn.next {{ right: 10px; }}
        .carousel-btn.hidden {{ display: none; }}

        .carousel-dots {{
            position: absolute;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 5px;
            z-index: 2;
        }}

        .carousel-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: rgba(255,255,255,0.4);
            transition: background-color 0.2s ease, transform 0.2s ease;
        }}

        .carousel-dot.active {{
            background-color: #ffffff;
            transform: scale(1.2);
        }}

        .carousel-counter {{
            position: absolute;
            top: 10px;
            right: 10px;
            font-family: var(--font-mono);
            font-size: 11px;
            color: #ffffff;
            background-color: rgba(11,15,18,0.7);
            padding: 3px 8px;
            border-radius: 20px;
            backdrop-filter: blur(4px);
        }}

        /* --- ACTIONS --- */
        .card-actions {{
            display: flex;
            gap: 16px;
            padding: 12px 16px 8px 16px;
            align-items: center;
        }}

        .action-btn {{
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            font-family: var(--font-mono);
            font-size: 12px;
            transition: color 0.2s ease, transform 0.1s ease;
            padding: 0;
        }}

        .action-btn:hover {{
            color: var(--accent-green);
            transform: scale(1.08);
        }}

        .action-btn.liked {{
            color: #ff3366;
        }}

        .action-btn svg {{
            display: block;
        }}

        .bookmark-container {{
            margin-left: auto;
        }}

        /* --- CAPTION AREA --- */
        .card-caption {{
            padding: 4px 16px 16px 16px;
        }}

        .card-title {{
            font-family: var(--font-mono);
            font-size: 15px;
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
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
            font-size: 14px;
            line-height: 1.65;
        }}

        /* Text-only post style */
        .post-card.text-only .card-caption {{
            padding: 16px;
        }}

        .post-card.text-only .card-title {{
            font-size: 17px;
            margin-bottom: 10px;
        }}

        .post-card.text-only .card-text {{
            font-size: 15px;
            -webkit-line-clamp: 6;
            color: var(--text-main);
            line-height: 1.75;
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
            transition: border-color 0.2s ease;
        }}

        .card-read-more:hover {{
            border-bottom-color: var(--accent-green);
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

        @media (max-width: 768px) {{
            .feed-container {{
                margin-top: 80px;
                padding: 0 10px;
            }}
            .post-card {{
                margin-bottom: 20px;
                border-radius: 8px;
            }}
        }}
    </style>
</head>

<body>
{nav_html}
    <main class="feed-container">
        {posts_feed_html}

        <footer>
            <div>Operated/Saved by Grace // &copy; 2026</div>
        </footer>
    </main>

    <script>
{nav_toggle_script}

        // Like button toggle (visual only)
        document.querySelectorAll('.like-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                btn.classList.toggle('liked');
                const icon = btn.querySelector('svg path');
                if (btn.classList.contains('liked')) {{
                    btn.querySelector('svg').setAttribute('fill', '#ff3366');
                    btn.querySelector('svg').setAttribute('stroke', '#ff3366');
                }} else {{
                    btn.querySelector('svg').setAttribute('fill', 'none');
                    btn.querySelector('svg').setAttribute('stroke', 'currentColor');
                }}
            }});
        }});

        // Carousel initializer
        document.querySelectorAll('.card-carousel').forEach(carousel => {{
            const track = carousel.querySelector('.carousel-track');
            const slides = carousel.querySelectorAll('.carousel-slide');
            const dots = carousel.querySelectorAll('.carousel-dot');
            const prevBtn = carousel.querySelector('.carousel-btn.prev');
            const nextBtn = carousel.querySelector('.carousel-btn.next');
            const counter = carousel.querySelector('.carousel-counter');
            if (!track || slides.length <= 1) return;

            let current = 0;

            function goTo(idx) {{
                current = Math.max(0, Math.min(idx, slides.length - 1));
                track.style.transform = `translateX(-${{current * 100}}%)`;
                dots.forEach((d, i) => d.classList.toggle('active', i === current));
                if (counter) counter.textContent = `${{current + 1}}/${{slides.length}}`;
                if (prevBtn) prevBtn.classList.toggle('hidden', current === 0);
                if (nextBtn) nextBtn.classList.toggle('hidden', current === slides.length - 1);
            }}

            if (prevBtn) prevBtn.addEventListener('click', () => goTo(current - 1));
            if (nextBtn) nextBtn.addEventListener('click', () => goTo(current + 1));

            // Touch swipe
            let startX = 0;
            track.addEventListener('touchstart', e => {{ startX = e.touches[0].clientX; }}, {{passive: true}});
            track.addEventListener('touchend', e => {{
                const diff = startX - e.changedTouches[0].clientX;
                if (Math.abs(diff) > 40) goTo(diff > 0 ? current + 1 : current - 1);
            }}, {{passive: true}});

            goTo(0);
        }});
    </script>
</body>

</html>"""

# ---------------------------------------------------------------------------
# POST TEMPLATE
# ---------------------------------------------------------------------------
POST_TEMPLATE = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1">
    <title>{post_title} // Blog</title>
    <link rel="icon" type="image/png" href="/favicon.png">
    <meta name="description" content="{post_excerpt}">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
{shared_css}

        /* --- POST VIEW --- */
        .post-container {{
            max-width: 680px;
            margin: 120px auto 100px auto;
            padding: 0 20px;
        }}

        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-family: var(--font-mono);
            color: var(--accent-green);
            text-decoration: none;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 36px;
            border-bottom: 1px dashed rgba(0, 255, 102, 0.3);
            transition: border-color 0.2s ease;
        }}

        .back-link:hover {{
            border-bottom-color: var(--accent-green);
        }}

        .post-header-title {{
            font-size: 38px;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #ffffff;
            line-height: 1.2;
            margin-bottom: 14px;
        }}

        .post-meta {{
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-muted);
            margin-bottom: 36px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .post-meta span {{ color: var(--accent-green); }}

        /* --- POST CAROUSEL --- */
        .post-carousel {{
            position: relative;
            width: 100%;
            overflow: hidden;
            background-color: #0b0f12;
            border-radius: 8px;
            border: 1px solid var(--border-light);
            margin-bottom: 36px;
            user-select: none;
        }}

        .carousel-track {{
            display: flex;
            transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        .carousel-slide {{
            min-width: 100%;
        }}

        .carousel-slide img {{
            width: 100%;
            height: auto;
            display: block;
            object-fit: cover;
            max-height: 600px;
        }}

        .carousel-btn {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background-color: rgba(11,15,18,0.7);
            border: 1px solid rgba(255,255,255,0.12);
            color: #ffffff;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.2s ease;
            z-index: 2;
            backdrop-filter: blur(4px);
        }}

        .carousel-btn:hover {{
            background-color: rgba(0, 255, 102, 0.2);
            border-color: var(--accent-green);
        }}

        .carousel-btn.prev {{ left: 12px; }}
        .carousel-btn.next {{ right: 12px; }}
        .carousel-btn.hidden {{ display: none; }}

        .carousel-dots {{
            position: absolute;
            bottom: 12px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 6px;
            z-index: 2;
        }}

        .carousel-dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: rgba(255,255,255,0.4);
            transition: background-color 0.2s ease, transform 0.2s ease;
        }}

        .carousel-dot.active {{
            background-color: #ffffff;
            transform: scale(1.3);
        }}

        .carousel-counter {{
            position: absolute;
            top: 12px;
            right: 12px;
            font-family: var(--font-mono);
            font-size: 11px;
            color: #ffffff;
            background-color: rgba(11,15,18,0.7);
            padding: 3px 10px;
            border-radius: 20px;
            backdrop-filter: blur(4px);
        }}

        /* --- POST CONTENT --- */
        .post-content {{
            font-size: 16px;
            color: var(--text-main);
            line-height: 1.85;
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

        /* --- GALLERY LINK --- */
        .gallery-callout {{
            margin-top: 40px;
            padding: 20px 24px;
            border: 1px solid rgba(0, 255, 102, 0.2);
            border-radius: 8px;
            background-color: rgba(0, 255, 102, 0.03);
            font-size: 15px;
            color: var(--text-muted);
            line-height: 1.6;
        }}

        .gallery-callout a {{
            color: var(--accent-green);
            font-weight: 600;
            text-decoration: none;
            border-bottom: 1px solid rgba(0, 255, 102, 0.4);
            transition: border-color 0.2s ease;
        }}

        .gallery-callout a:hover {{
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

        @media (max-width: 768px) {{
            .post-container {{ margin-top: 80px; }}
            .post-header-title {{ font-size: 28px; }}
        }}
    </style>
</head>

<body>
{nav_html}

    <main class="post-container">
        <a href="../blog.html" class="back-link">&#8592; Back to Blog</a>

        <article>
            <h1 class="post-header-title">{post_title}</h1>
            <div class="post-meta">
                Posted <span>{post_date}</span>
            </div>

            {post_carousel_html}

            <div class="post-content">
                {post_content_html}
            </div>
        </article>

        {gallery_callout_html}

        <footer>
            <div>Operated/Saved by Grace // &copy; 2026</div>
        </footer>
    </main>

    <script>
{nav_toggle_script}

        // Post carousel
        (function() {{
            const carousel = document.querySelector('.post-carousel');
            if (!carousel) return;
            const track = carousel.querySelector('.carousel-track');
            const slides = carousel.querySelectorAll('.carousel-slide');
            const dots = carousel.querySelectorAll('.carousel-dot');
            const prevBtn = carousel.querySelector('.carousel-btn.prev');
            const nextBtn = carousel.querySelector('.carousel-btn.next');
            const counter = carousel.querySelector('.carousel-counter');
            if (!track || slides.length <= 1) return;

            let current = 0;

            function goTo(idx) {{
                current = Math.max(0, Math.min(idx, slides.length - 1));
                track.style.transform = `translateX(-${{current * 100}}%)`;
                dots.forEach((d, i) => d.classList.toggle('active', i === current));
                if (counter) counter.textContent = `${{current + 1}}/${{slides.length}}`;
                if (prevBtn) prevBtn.classList.toggle('hidden', current === 0);
                if (nextBtn) nextBtn.classList.toggle('hidden', current === slides.length - 1);
            }}

            if (prevBtn) prevBtn.addEventListener('click', () => goTo(current - 1));
            if (nextBtn) nextBtn.addEventListener('click', () => goTo(current + 1));

            let startX = 0;
            track.addEventListener('touchstart', e => {{ startX = e.touches[0].clientX; }}, {{passive: true}});
            track.addEventListener('touchend', e => {{
                const diff = startX - e.changedTouches[0].clientX;
                if (Math.abs(diff) > 40) goTo(diff > 0 ? current + 1 : current - 1);
            }}, {{passive: true}});

            goTo(0);
        }})();
    </script>
</body>

</html>"""

# ---------------------------------------------------------------------------
# GALLERY TEMPLATE
# ---------------------------------------------------------------------------
GALLERY_TEMPLATE = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1">
    <title>Gallery — {post_title} // Blog</title>
    <link rel="icon" type="image/png" href="/favicon.png">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
{shared_css}

        .gallery-container {{
            max-width: 900px;
            margin: 120px auto 100px auto;
            padding: 0 20px;
        }}

        .back-link {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-family: var(--font-mono);
            color: var(--accent-green);
            text-decoration: none;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 36px;
            border-bottom: 1px dashed rgba(0, 255, 102, 0.3);
            transition: border-color 0.2s ease;
        }}

        .back-link:hover {{ border-bottom-color: var(--accent-green); }}

        .gallery-header {{
            margin-bottom: 36px;
        }}

        .gallery-label {{
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--accent-green);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 8px;
        }}

        .gallery-title {{
            font-size: 32px;
            font-weight: 700;
            color: #ffffff;
            line-height: 1.2;
        }}

        /* Masonry-style grid */
        .photo-grid {{
            columns: 3;
            column-gap: 10px;
        }}

        .photo-item {{
            break-inside: avoid;
            margin-bottom: 10px;
            overflow: hidden;
            border-radius: 6px;
            border: 1px solid var(--border-light);
            cursor: pointer;
            position: relative;
        }}

        .photo-item img {{
            width: 100%;
            height: auto;
            display: block;
            transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease;
        }}

        .photo-item:hover img {{
            transform: scale(1.03);
            opacity: 0.9;
        }}

        /* Lightbox */
        .lightbox {{
            display: none;
            position: fixed;
            inset: 0;
            background-color: rgba(5, 8, 10, 0.96);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }}

        .lightbox.open {{
            display: flex;
        }}

        .lightbox-img {{
            max-width: 90vw;
            max-height: 85vh;
            object-fit: contain;
            border-radius: 4px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.8);
        }}

        .lightbox-close {{
            position: absolute;
            top: 20px;
            right: 24px;
            font-size: 28px;
            color: #ffffff;
            cursor: pointer;
            background: none;
            border: none;
            line-height: 1;
            opacity: 0.7;
            transition: opacity 0.2s ease;
        }}

        .lightbox-close:hover {{ opacity: 1; }}

        .lightbox-nav {{
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background-color: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.15);
            color: #ffffff;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 18px;
            transition: background-color 0.2s ease;
        }}

        .lightbox-nav:hover {{ background-color: rgba(0, 255, 102, 0.2); border-color: var(--accent-green); }}
        .lightbox-nav.prev {{ left: 20px; }}
        .lightbox-nav.next {{ right: 20px; }}

        .lightbox-counter {{
            margin-top: 14px;
            font-family: var(--font-mono);
            font-size: 12px;
            color: rgba(255,255,255,0.5);
        }}

        footer {{
            text-align: center;
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-muted);
            border-top: 1px solid var(--border-light);
            padding-top: 30px;
            margin-top: 60px;
        }}

        @media (max-width: 768px) {{
            .gallery-container {{ margin-top: 80px; }}
            .photo-grid {{ columns: 2; }}
            .gallery-title {{ font-size: 24px; }}
        }}

        @media (max-width: 480px) {{
            .photo-grid {{ columns: 1; }}
        }}
    </style>
</head>

<body>
{nav_html}

    <main class="gallery-container">
        <a href="../posts/{post_slug}.html" class="back-link">&#8592; Back to Post</a>

        <div class="gallery-header">
            <div class="gallery-label">Photo Gallery</div>
            <h1 class="gallery-title">{post_title}</h1>
        </div>

        <div class="photo-grid" id="photo-grid">
            {photos_html}
        </div>

        <footer>
            <div>Operated/Saved by Grace // &copy; 2026</div>
        </footer>
    </main>

    <!-- Lightbox -->
    <div class="lightbox" id="lightbox">
        <button class="lightbox-close" id="lb-close">&#215;</button>
        <button class="lightbox-nav prev" id="lb-prev">&#8249;</button>
        <img class="lightbox-img" id="lb-img" src="" alt="Gallery photo">
        <button class="lightbox-nav next" id="lb-next">&#8250;</button>
        <div class="lightbox-counter" id="lb-counter"></div>
    </div>

    <script>
{nav_toggle_script}

        const images = {images_json};
        let lbIdx = 0;
        const lightbox = document.getElementById('lightbox');
        const lbImg = document.getElementById('lb-img');
        const lbCounter = document.getElementById('lb-counter');

        function openLightbox(idx) {{
            lbIdx = idx;
            lbImg.src = images[lbIdx];
            lbCounter.textContent = `${{lbIdx + 1}} / ${{images.length}}`;
            lightbox.classList.add('open');
        }}

        document.querySelectorAll('.photo-item').forEach((item, i) => {{
            item.addEventListener('click', () => openLightbox(i));
        }});

        document.getElementById('lb-close').addEventListener('click', () => lightbox.classList.remove('open'));
        lightbox.addEventListener('click', e => {{ if (e.target === lightbox) lightbox.classList.remove('open'); }});

        document.getElementById('lb-prev').addEventListener('click', e => {{
            e.stopPropagation();
            lbIdx = (lbIdx - 1 + images.length) % images.length;
            lbImg.src = images[lbIdx];
            lbCounter.textContent = `${{lbIdx + 1}} / ${{images.length}}`;
        }});

        document.getElementById('lb-next').addEventListener('click', e => {{
            e.stopPropagation();
            lbIdx = (lbIdx + 1) % images.length;
            lbImg.src = images[lbIdx];
            lbCounter.textContent = `${{lbIdx + 1}} / ${{images.length}}`;
        }});

        document.addEventListener('keydown', e => {{
            if (!lightbox.classList.contains('open')) return;
            if (e.key === 'ArrowLeft') document.getElementById('lb-prev').click();
            if (e.key === 'ArrowRight') document.getElementById('lb-next').click();
            if (e.key === 'Escape') lightbox.classList.remove('open');
        }});
    </script>
</body>

</html>"""


# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
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
    os.makedirs('blog_assets/gallery', exist_ok=True)
    os.makedirs('posts', exist_ok=True)
    os.makedirs('gallery', exist_ok=True)
    if not os.path.exists('blog_assets/posts.json'):
        with open('blog_assets/posts.json', 'w', encoding='utf-8') as f:
            json.dump([], f)


def load_posts():
    init_folders()
    try:
        with open('blog_assets/posts.json', 'r', encoding='utf-8') as f:
            posts = json.load(f)
        # Migrate old posts that don't have new fields
        for post in posts:
            if 'image_paths' not in post:
                old = post.get('image_path', '')
                post['image_paths'] = [old] if old else []
            if 'gallery_images' not in post:
                post['gallery_images'] = []
            if 'likes' not in post:
                post['likes'] = 0
        return posts
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
            formatted.append(f"<p>{p_html}</p>")
    return '\n'.join(formatted)


def get_avatar_src(prefix=''):
    """Return the avatar src — local file if it exists, else fallback."""
    local = 'blog_assets/avatar.jpg'
    if os.path.exists(local):
        return f"{prefix}blog_assets/avatar.jpg"
    return "https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y"


def build_carousel_html_blog(post):
    """Build the carousel block for blog.html feed cards."""
    paths = post.get('image_paths', [])
    if not paths:
        return ''  # text-only post, no image block

    slug = post['slug']
    title = post['title']

    if len(paths) == 1:
        # Single image — no nav buttons
        img_src = paths[0]
        return f"""
                <a href="posts/{slug}.html" class="card-carousel" style="display:block;">
                    <div class="carousel-track">
                        <div class="carousel-slide">
                            <img src="{img_src}" alt="{title}">
                        </div>
                    </div>
                </a>"""

    # Multiple images
    slides_html = ''
    dots_html = ''
    for i, img_src in enumerate(paths):
        active = ' active' if i == 0 else ''
        slides_html += f'<div class="carousel-slide"><img src="{img_src}" alt="{title} {i+1}"></div>'
        dots_html += f'<div class="carousel-dot{active}"></div>'

    return f"""
                <div class="card-carousel">
                    <div class="carousel-track">
                        {slides_html}
                    </div>
                    <button class="carousel-btn prev hidden">&#8249;</button>
                    <button class="carousel-btn next">&#8250;</button>
                    <div class="carousel-dots">{dots_html}</div>
                    <div class="carousel-counter">1/{len(paths)}</div>
                </div>"""


def build_carousel_html_post(post):
    """Build the carousel block for individual post pages."""
    paths = post.get('image_paths', [])
    if not paths:
        return ''

    if len(paths) == 1:
        img_src = f"../{paths[0]}"
        return f'<img class="post-featured-image" src="{img_src}" alt="{post["title"]}" style="width:100%;border-radius:8px;border:1px solid var(--border-light);margin-bottom:36px;max-height:600px;object-fit:cover;">'

    slides_html = ''
    dots_html = ''
    for i, p in enumerate(paths):
        src = f"../{p}"
        active = ' active' if i == 0 else ''
        slides_html += f'<div class="carousel-slide"><img src="{src}" alt="{post["title"]} {i+1}"></div>'
        dots_html += f'<div class="carousel-dot{active}"></div>'

    return f"""<div class="post-carousel">
                    <div class="carousel-track">{slides_html}</div>
                    <button class="carousel-btn prev hidden">&#8249;</button>
                    <button class="carousel-btn next">&#8250;</button>
                    <div class="carousel-dots">{dots_html}</div>
                    <div class="carousel-counter">1/{len(paths)}</div>
                </div>"""


def save_image_file(image_data, image_name, subfolder='images'):
    """Decode base64 image and save to disk. Returns relative path."""
    header, encoded = image_data.split(",", 1)
    decoded_img = base64.b64decode(encoded)
    ext = os.path.splitext(image_name)[1] or ".jpg"
    if ext.lower() not in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
        ext = '.jpg'
    timestamp = int(datetime.now().timestamp())
    safe_name = slugify(os.path.splitext(image_name)[0])[:20] or 'img'
    filename = f"{timestamp}_{safe_name}{ext}"
    filepath = os.path.join('blog_assets', subfolder, filename)
    with open(filepath, 'wb') as f:
        f.write(decoded_img)
    return f"blog_assets/{subfolder}/{filename}"


def regenerate_all(posts):
    """Rebuild blog.html, all post pages, and all gallery pages."""
    init_folders()

    avatar_src = get_avatar_src()

    # ── 1. Generate blog.html ──────────────────────────────────────────────
    posts_feed_html = ""
    if not posts:
        posts_feed_html = '<div class="no-posts">No blog posts yet. Visit the local admin panel to add one!</div>'
    else:
        for post in posts:
            formatted_date = format_date(post['updated_at'])
            has_images = bool(post.get('image_paths'))
            card_class = 'post-card' if has_images else 'post-card text-only'

            carousel_html = build_carousel_html_blog(post)
            snippet = post['content'][:300] + "..." if len(post['content']) > 300 else post['content']
            snippet_html = format_content_html(snippet)
            likes = post.get('likes', 0)

            posts_feed_html += f"""
            <article class="{card_class}">
                <header class="card-header">
                    <img class="card-avatar" src="{avatar_src}" alt="Avatar" onerror="this.src='https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y'">
                    <div class="card-user-info">
                        <span class="card-username">thelionbro024</span>
                        <time class="card-time" datetime="{post['updated_at']}">{formatted_date}</time>
                    </div>
                </header>

                {carousel_html}

                <div class="card-actions">
                    <button class="action-btn like-btn" title="Like">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                        <span class="like-count">{likes}</span>
                    </button>
                    <button class="action-btn" title="Comment" onclick="window.location.href='posts/{post['slug']}.html'">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                    </button>
                    <div class="bookmark-container">
                        <button class="action-btn" title="Bookmark">
                            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
                        </button>
                    </div>
                </div>

                <div class="card-caption">
                    <div class="card-title">{post['title']}</div>
                    <div class="card-text">{snippet_html}</div>
                    <a href="posts/{post['slug']}.html" class="card-read-more">Read Full Post</a>
                </div>
            </article>
            """

    blog_content = BLOG_TEMPLATE.format(
        shared_css=SHARED_CSS,
        nav_html=NAV_HTML,
        nav_toggle_script=NAV_TOGGLE_SCRIPT,
        posts_feed_html=posts_feed_html
    )
    with open('blog.html', 'w', encoding='utf-8') as f:
        f.write(blog_content)

    # ── 2. Generate each post's HTML page ─────────────────────────────────
    for post in posts:
        post_date = format_date(post['updated_at'])
        post_content_html = format_content_html(post['content'])
        post_excerpt = post['content'][:160].replace('"', '&quot;')
        post_carousel_html = build_carousel_html_post(post)

        # Gallery callout
        gallery_images = post.get('gallery_images', [])
        if gallery_images:
            gallery_callout_html = f"""<div class="gallery-callout">
            Do you want to see more about what I did? Click <a href="../gallery/{post['slug']}.html">here</a> to see more photos.
        </div>"""
        else:
            gallery_callout_html = ''

        post_content_str = POST_TEMPLATE.format(
            shared_css=SHARED_CSS,
            nav_html=NAV_HTML_POST,
            nav_toggle_script=NAV_TOGGLE_SCRIPT,
            post_title=post['title'],
            post_date=post_date,
            post_excerpt=post_excerpt,
            post_carousel_html=post_carousel_html,
            post_content_html=post_content_html,
            gallery_callout_html=gallery_callout_html
        )

        filepath = os.path.join('posts', f"{post['slug']}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(post_content_str)

    # ── 3. Generate gallery pages ─────────────────────────────────────────
    for post in posts:
        gallery_images = post.get('gallery_images', [])
        if not gallery_images:
            continue

        photos_html = ''
        images_json_list = []
        for img_path in gallery_images:
            src = f"../{img_path}"
            photos_html += f'<div class="photo-item"><img src="{src}" alt="Gallery photo" loading="lazy"></div>\n'
            images_json_list.append(src)

        gallery_content = GALLERY_TEMPLATE.format(
            shared_css=SHARED_CSS,
            nav_html=NAV_HTML_GALLERY,
            nav_toggle_script=NAV_TOGGLE_SCRIPT,
            post_title=post['title'],
            post_slug=post['slug'],
            photos_html=photos_html,
            images_json=json.dumps(images_json_list)
        )

        filepath = os.path.join('gallery', f"{post['slug']}.html")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(gallery_content)


# ---------------------------------------------------------------------------
# CUSTOM HTTP REQUEST HANDLER
# ---------------------------------------------------------------------------

class BlogHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        # API: get list of posts
        if self.path == '/api/posts':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            posts = load_posts()
            self.wfile.write(json.dumps(posts).encode('utf-8'))
            return

        # Admin redirect
        elif self.path in ('/admin', '/admin/'):
            self.send_response(301)
            self.send_header('Location', '/admin.html')
            self.end_headers()
            return

        return super().do_GET()

    def do_POST(self):
        # ── Create new post ──────────────────────────────────────────────
        if self.path == '/api/posts':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                title = data.get('title', '').strip()
                content = data.get('content', '').strip()

                if not title or not content:
                    self.send_error_response(400, "Title and content are required")
                    return

                # Process carousel images (array of {data, name})
                image_paths = []
                for img in data.get('images', []):
                    if img.get('data'):
                        try:
                            path = save_image_file(img['data'], img.get('name', 'image.jpg'), 'images')
                            image_paths.append(path)
                        except Exception as e:
                            print(f"Error saving carousel image: {e}")

                # Process gallery images (array of {data, name})
                gallery_image_paths = []
                for img in data.get('gallery_images', []):
                    if img.get('data'):
                        try:
                            path = save_image_file(img['data'], img.get('name', 'gallery.jpg'), 'gallery')
                            gallery_image_paths.append(path)
                        except Exception as e:
                            print(f"Error saving gallery image: {e}")

                posts = load_posts()
                slug = generate_unique_slug(title, posts)
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
                save_posts(posts)
                regenerate_all(posts)
                self.send_success_response({"status": "success", "slug": slug})

            except Exception as e:
                print(f"Error creating post: {e}")
                self.send_error_response(500, str(e))
            return

        # ── Upload profile picture ───────────────────────────────────────
        if self.path == '/api/profile-picture':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                img_data = data.get('image', '')
                if not img_data:
                    self.send_error_response(400, "No image data provided")
                    return

                header, encoded = img_data.split(",", 1)
                decoded_img = base64.b64decode(encoded)
                with open('blog_assets/avatar.jpg', 'wb') as f:
                    f.write(decoded_img)

                # Regenerate all pages so avatar is updated
                posts = load_posts()
                regenerate_all(posts)
                self.send_success_response({"status": "ok"})

            except Exception as e:
                print(f"Error saving avatar: {e}")
                self.send_error_response(500, str(e))
            return

        self.send_error_response(404, "Not Found")

    def do_PATCH(self):
        # ── Update post (likes, etc.) ────────────────────────────────────
        if self.path.startswith('/api/posts/'):
            slug = self.path.split('/')[-1]
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                posts = load_posts()
                updated = False
                for post in posts:
                    if post['slug'] == slug:
                        if 'likes' in data:
                            post['likes'] = int(data['likes'])
                        post['updated_at'] = datetime.now().isoformat()
                        updated = True
                        break

                if not updated:
                    self.send_error_response(404, "Post not found")
                    return

                save_posts(posts)
                regenerate_all(posts)
                self.send_success_response({"status": "updated"})

            except Exception as e:
                print(f"Error updating post: {e}")
                self.send_error_response(500, str(e))
            return

        self.send_error_response(404, "Not Found")

    def do_DELETE(self):
        # ── Delete post ──────────────────────────────────────────────────
        if self.path.startswith('/api/posts/'):
            slug = self.path.split('/')[-1]
            posts = load_posts()

            post_to_delete = next((p for p in posts if p['slug'] == slug), None)
            if not post_to_delete:
                self.send_error_response(404, "Post not found")
                return

            posts.remove(post_to_delete)
            save_posts(posts)

            # Delete carousel images
            for img_path in post_to_delete.get('image_paths', []):
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                except Exception as e:
                    print(f"Error removing image: {e}")

            # Delete gallery images
            for img_path in post_to_delete.get('gallery_images', []):
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                except Exception as e:
                    print(f"Error removing gallery image: {e}")

            # Delete static HTML files
            for path in [
                os.path.join('posts', f"{slug}.html"),
                os.path.join('gallery', f"{slug}.html")
            ]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    print(f"Error removing html file: {e}")

            regenerate_all(posts)
            self.send_success_response({"status": "deleted", "slug": slug})
            return

        self.send_error_response(404, "Not Found")

    def send_success_response(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode('utf-8'))

    def log_message(self, format, *args):
        # Suppress noisy GET logs for static assets
        if args and isinstance(args[0], str) and any(ext in args[0] for ext in ['.css', '.js', '.png', '.jpg', '.ico', '.woff']):
            return
        super().log_message(format, *args)


# ---------------------------------------------------------------------------
# MAIN RUNNER
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    init_folders()
    current_posts = load_posts()
    save_posts(current_posts)  # migrate schema
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
