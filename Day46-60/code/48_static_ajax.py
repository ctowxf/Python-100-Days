"""
Day 48 - Static Resources and Ajax Requests
============================================

This demo covers:
  1. Serving static files (CSS, JS, images) in Django
  2. Ajax requests using both vanilla fetch() and jQuery $.ajax / $.getJSON
  3. Returning JSON responses with JsonResponse
  4. CSRF token handling for POST requests
  5. Enterprise patterns:
       - Dynamic cascading form (province -> city -> district)
       - Live search with debounce
       - File upload with progress bar

Prerequisites:
  pip install django

Run:
  python 48_static_ajax.py          # creates project skeleton + starts dev server
  python 48_static_ajax.py --init   # only create the project files (no server)

The script bootstraps a self-contained Django project under ./demo_48_site/
so you can inspect every file after generation.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import textwrap
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Project skeleton generation
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent / "demo_48_site"


def write_file(path: Path, content: str) -> None:
    """Create *path* (and parents) with *content*, UTF-8 encoded."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
    print(f"  created {path.relative_to(PROJECT_DIR)}")


def generate_project() -> None:
    """Lay out the entire Django project on disk."""
    root = PROJECT_DIR
    if root.exists():
        print(f"[info] removing existing directory: {root}")
        shutil.rmtree(root)

    # ------------------------------------------------------------------
    # manage.py
    # ------------------------------------------------------------------
    write_file(root / "manage.py", """
        #!/usr/bin/env python
        \"\"\"Django's command-line utility for administrative tasks.\"\"\"
        import os, sys

        def main():
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            from django.core.management import execute_from_command_line
            execute_from_command_line(sys.argv)

        if __name__ == '__main__':
            main()
    """)

    # ------------------------------------------------------------------
    # config / settings.py
    # ------------------------------------------------------------------
    write_file(root / "config" / "__init__.py", "")

    write_file(root / "config" / "settings.py", """
        \"\"\"Minimal Django settings for the Day-48 demo.\"\"\"
        from pathlib import Path

        BASE_DIR = Path(__file__).resolve().parent.parent

        SECRET_KEY = 'day48-demo-secret-key-not-for-production'
        DEBUG = True
        ALLOWED_HOSTS = ['*']

        INSTALLED_APPS = [
            'django.contrib.contenttypes',
            'django.contrib.staticfiles',
            'core',                       # our app
        ]

        MIDDLEWARE = [
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
        ]

        ROOT_URLCONF = 'config.urls'
        WSGI_APPLICATION = 'config.wsgi.application'

        TEMPLATES = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [BASE_DIR / 'templates'],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.request',
                    ],
                },
            },
        ]

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

        # ---- Static files (CSS, JavaScript, Images) --------------------
        STATIC_URL = '/static/'
        STATICFILES_DIRS = [BASE_DIR / 'static']

        # ---- Media uploads ---------------------------------------------
        MEDIA_URL = '/media/'
        MEDIA_ROOT = BASE_DIR / 'media'

        DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
    """)

    write_file(root / "config" / "urls.py", """
        \"\"\"Root URL configuration.\"\"\"
        from django.conf import settings
        from django.conf.urls.static import static
        from django.contrib import admin
        from django.urls import path, include

        urlpatterns = [
            path('', include('core.urls')),
        ]

        # Serve media files during development
        if settings.DEBUG:
            urlpatterns += static(
                settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
            )
    """)

    write_file(root / "config" / "wsgi.py", """
        \"\"\"WSGI config.\"\"\"
        import os
        from django.core.wsgi import get_wsgi_application
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        application = get_wsgi_application()
    """)

    # ------------------------------------------------------------------
    # core app
    # ------------------------------------------------------------------
    write_file(root / "core" / "__init__.py", "")

    # -- models.py (in-memory data for demo; swap with real ORM if needed)
    write_file(root / "core" / "models.py", """
        \"\"\"
        Demo data structures.

        In a real project these would be Django ORM models.  Here we keep
        plain Python classes so the demo runs without migrations.
        \"\"\"
        from __future__ import annotations
        from dataclasses import dataclass, field

        @dataclass
        class Teacher:
            no: int
            name: str
            subject: str
            photo: str = 'default.png'
            intro: str = ''
            good_count: int = 0
            bad_count: int = 0

        # Seed data ----------------------------------------------------------
        TEACHERS: list[Teacher] = [
            Teacher(1, 'Alice',   'Python',   'alice.png',   'Senior Python instructor',  12, 1),
            Teacher(2, 'Bob',     'Java',     'bob.png',     'Java backend specialist',    8, 2),
            Teacher(3, 'Charlie', 'Frontend', 'charlie.png', 'React / Vue expert',         5, 0),
            Teacher(4, 'Diana',   'Database', 'diana.png',   'MySQL & PostgreSQL guru',    9, 1),
            Teacher(5, 'Eve',     'DevOps',   'eve.png',     'Docker & Kubernetes',        3, 0),
        ]

        # Province / City / District hierarchy for cascading-select demo -----
        REGIONS: dict[str, dict[str, list[str]]] = {
            'Guangdong': {
                'Guangzhou': ['Tianhe', 'Yuexiu', 'Haizhu', 'Baiyun'],
                'Shenzhen':  ['Futian', 'Nanshan', 'Luohu', 'Longgang'],
                'Dongguan':  ['Nancheng', 'Guancheng', 'Songshanhu'],
            },
            'Zhejiang': {
                'Hangzhou':  ['Xihu', 'Shangcheng', 'Gongshu', 'Binjiang'],
                'Ningbo':    ['Haishu', 'Jiangbei', 'Zhenhai'],
                'Wenzhou':   ['Lucheng', 'Longwan', 'Ouhai'],
            },
            'Jiangsu': {
                'Nanjing':   ['Xuanwu', 'Gulou', 'Qinhuai', 'Jianye'],
                'Suzhou':    ['Gusu', 'Huqiu', 'Wuzhong'],
                'Wuxi':      ['Liangxi', 'Xinwu', 'Binhu'],
            },
        }

        # Product catalogue for live-search demo -----------------------------
        PRODUCTS: list[dict[str, Any]] = [
            {'id': i, 'name': name, 'price': round(10 + i * 3.7, 2)}
            for i, name in enumerate([
                'Python Crash Course', 'Fluent Python', 'Effective Python',
                'Django for Professionals', 'Two Scoops of Django',
                'JavaScript: The Good Parts', 'Eloquent JavaScript',
                'You Don\'t Know JS', 'React Up & Running',
                'Vue.js in Action', 'Learning TypeScript',
                'Rust Programming Language', 'Go in Practice',
                'Clean Code', 'Clean Architecture',
                'Design Patterns', 'Refactoring',
                'The Pragmatic Programmer', 'Mythical Man-Month',
                'Algorithm Design Manual',
            ], start=1)
        ]
    """)

    # -- views.py  (the heart of the demo)
    write_file(root / "core" / "views.py", r'''
        """Views demonstrating static files, Ajax, JSON, and CSRF handling."""
        from __future__ import annotations

        import json
        import os
        import time
        import uuid
        from pathlib import Path
        from typing import Any

        from django.conf import settings
        from django.http import (
            HttpRequest, HttpResponse, JsonResponse,
        )
        from django.middleware.csrf import get_token
        from django.shortcuts import render
        from django.views.decorators.csrf import ensure_csrf_cookie
        from django.views.decorators.http import require_GET, require_POST

        from .models import TEACHERS, REGIONS, PRODUCTS


# =====================================================================
# 1.  Home page (renders a template that uses static files)
# =====================================================================
@ensure_csrf_cookie          # forces CSRF cookie to be set on GET
def index(request: HttpRequest) -> HttpResponse:
    """Landing page that loads static CSS / JS / images."""
    return render(request, 'index.html', {
        'teachers': TEACHERS,
        'csrf_token': get_token(request),
    })


# =====================================================================
# 2.  Ajax voting (GET-based, JSON response)
# =====================================================================
@require_GET
def praise_or_criticize(request: HttpRequest) -> JsonResponse:
    """
    Increment good_count or bad_count for a teacher.

    Expected query params:
        tno  -- teacher number (int)

    Returns JSON:
        {"code": 20000, "msg": "OK", "count": <new_count>}
        {"code": 20001, "msg": "Teacher not found"}
    """
    try:
        tno = int(request.GET.get('tno', 0))
        teacher = next(t for t in TEACHERS if t.no == tno)
    except (ValueError, StopIteration):
        return JsonResponse({'code': 20001, 'msg': 'Teacher not found'})

    if request.path.startswith('/praise'):
        teacher.good_count += 1
        count = teacher.good_count
    else:
        teacher.bad_count += 1
        count = teacher.bad_count

    return JsonResponse({'code': 20000, 'msg': 'OK', 'count': count})


# =====================================================================
# 3.  Cascading select (province -> city -> district)
# =====================================================================
@require_GET
def region_api(request: HttpRequest) -> JsonResponse:
    """
    Return next-level region data.

    Query params (all optional, used to drill down):
        province, city

    With no params  -> list of provinces
    With province   -> list of cities
    With province + city -> list of districts
    """
    province: str | None = request.GET.get('province')
    city: str | None = request.GET.get('city')

    if province and city:
        districts: list[str] = REGIONS.get(province, {}).get(city, [])
        return JsonResponse({'districts': districts})
    if province:
        cities: list[str] = list(REGIONS.get(province, {}).keys())
        return JsonResponse({'cities': cities})
    return JsonResponse({'provinces': list(REGIONS.keys())})


# =====================================================================
# 4.  Live product search (GET, JSON)
# =====================================================================
@require_GET
def product_search(request: HttpRequest) -> JsonResponse:
    """
    Case-insensitive substring search over PRODUCT catalogue.

    Query params:
        q -- search keyword

    Returns:
        {"results": [...], "count": N}
    """
    keyword: str = request.GET.get('q', '').strip().lower()
    if not keyword:
        return JsonResponse({'results': [], 'count': 0})

    matched = [
        p for p in PRODUCTS if keyword in p['name'].lower()
    ]
    return JsonResponse({'results': matched, 'count': len(matched)})


# =====================================================================
# 5.  File upload with progress (POST, multipart)
# =====================================================================
@require_POST
def upload_file(request: HttpRequest) -> JsonResponse:
    """
    Accept a single file upload.

    The file is saved under MEDIA_ROOT/uploads/<uuid>_<original_name>.

    Returns:
        {"code": 20000, "url": "/media/uploads/...", "name": "...", "size": N}
    """
    uploaded = request.FILES.get('file')
    if not uploaded:
        return JsonResponse({'code': 20001, 'msg': 'No file provided'}, status=400)

    # Save to media/uploads/
    upload_dir: Path = Path(settings.MEDIA_ROOT) / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex[:8]}_{uploaded.name}"
    dest = upload_dir / safe_name

    with open(dest, 'wb') as f:
        for chunk in uploaded.chunks():
            f.write(chunk)

    return JsonResponse({
        'code': 20000,
        'msg': 'Upload successful',
        'url': f'{settings.MEDIA_URL}uploads/{safe_name}',
        'name': uploaded.name,
        'size': uploaded.size,
    })


# =====================================================================
# 6.  Dynamic form submission (POST, CSRF-protected)
# =====================================================================
@require_POST
def submit_feedback(request: HttpRequest) -> JsonResponse:
    """
    Accept a JSON or form-encoded feedback payload.

    Expected fields:
        name, email, category, message

    Returns:
        {"code": 20000, "msg": "Feedback received", "ticket": "<uuid>"}
    """
    # Support both JSON body and form-encoded data
    if request.content_type == 'application/json':
        try:
            data: dict[str, Any] = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'code': 20001, 'msg': 'Invalid JSON'}, status=400)
    else:
        data = request.POST

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    category = data.get('category', '').strip()
    message = data.get('message', '').strip()

    if not all([name, email, message]):
        return JsonResponse(
            {'code': 20001, 'msg': 'name, email, and message are required'},
            status=400,
        )

    ticket = uuid.uuid4().hex[:12].upper()
    # In production you would persist to DB here.
    print(f"[feedback] ticket={ticket}  name={name}  email={email}  "
          f"category={category}  message={message[:80]}")

    return JsonResponse({
        'code': 20000,
        'msg': 'Feedback received',
        'ticket': ticket,
    })
''')

    # -- urls.py
    write_file(root / "core" / "urls.py", """
        \"\"\"App-level URL configuration.\"\"\"
        from django.urls import path
        from . import views

        urlpatterns = [
            path('',                        views.index,            name='index'),
            path('praise/',                 views.praise_or_criticize),
            path('criticize/',              views.praise_or_criticize),
            path('api/regions/',            views.region_api),
            path('api/products/search/',    views.product_search),
            path('api/upload/',             views.upload_file),
            path('api/feedback/',           views.submit_feedback),
        ]
    """)

    # ------------------------------------------------------------------
    # Static files
    # ------------------------------------------------------------------
    static = root / "static"

    # -- CSS
    write_file(static / "css" / "style.css", """
        /* ===== Day 48 Demo Stylesheet ==================================== */
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
        }

        .container { max-width: 960px; margin: 0 auto; padding: 20px; }

        h1 { color: #2c3e50; margin-bottom: 8px; }
        h2 { color: #34495e; margin: 24px 0 12px; border-bottom: 2px solid #3498db; padding-bottom: 4px; }

        /* -- Teacher cards ------------------------------------------------ */
        .teacher-card {
            display: flex;
            align-items: center;
            gap: 16px;
            background: #fff;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,.1);
        }
        .teacher-card img {
            width: 80px; height: 80px;
            border-radius: 50%;
            object-fit: cover;
            background: #ddd;
        }
        .teacher-info { flex: 1; }
        .teacher-info .name { font-weight: 700; font-size: 1.1rem; }
        .teacher-info .meta { color: #7f8c8d; font-size: .9rem; }
        .vote-btn {
            display: inline-block;
            padding: 6px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: .9rem;
            color: #fff;
            transition: background .2s;
        }
        .vote-btn.praise  { background: #27ae60; }
        .vote-btn.praise:hover  { background: #219a52; }
        .vote-btn.criticize { background: #e74c3c; }
        .vote-btn.criticize:hover { background: #c0392b; }
        .vote-count { font-weight: 700; margin: 0 6px; }

        /* -- Forms -------------------------------------------------------- */
        .form-group { margin-bottom: 14px; }
        .form-group label { display: block; font-weight: 600; margin-bottom: 4px; }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: .95rem;
        }
        .form-group textarea { resize: vertical; min-height: 80px; }
        .btn {
            display: inline-block;
            padding: 10px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
            color: #fff;
            background: #3498db;
            transition: background .2s;
        }
        .btn:hover { background: #2980b9; }

        /* -- Live search -------------------------------------------------- */
        #search-box {
            width: 100%;
            padding: 10px 14px;
            font-size: 1rem;
            border: 2px solid #3498db;
            border-radius: 6px;
            outline: none;
        }
        #search-box:focus { border-color: #2980b9; }
        #search-results { margin-top: 8px; }
        .search-item {
            padding: 10px 14px;
            background: #fff;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background .15s;
        }
        .search-item:hover { background: #ecf0f1; }
        .search-item .product-name { font-weight: 600; }
        .search-item .product-price { color: #27ae60; float: right; }
        .search-hint { color: #95a5a6; padding: 10px; }

        /* -- File upload -------------------------------------------------- */
        .upload-zone {
            border: 2px dashed #3498db;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            color: #7f8c8d;
            cursor: pointer;
            transition: border-color .2s, background .2s;
        }
        .upload-zone.dragover { border-color: #27ae60; background: #eafaf1; }
        .progress-bar {
            height: 20px;
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 12px;
        }
        .progress-bar .fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            transition: width .3s;
            border-radius: 10px;
        }
        .upload-status { margin-top: 8px; font-size: .9rem; color: #555; }

        /* -- Alert boxes -------------------------------------------------- */
        .alert {
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 12px;
            display: none;
        }
        .alert.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert.error   { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert.info    { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
    """)

    # -- JavaScript (vanilla fetch + helpers)
    write_file(static / "js" / "app.js", """
        /**
         * Day 48 Demo - Vanilla JavaScript (fetch API)
         * ==============================================
         * Covers:
         *   - Ajax with fetch()
         *   - CSRF token handling for POST
         *   - Cascading select
         *   - Live search with debounce
         *   - File upload with XMLHttpRequest (for progress events)
         */

        'use strict';

        // ---- CSRF helper ---------------------------------------------------
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return '';
        }

        const CSRF_TOKEN = getCookie('csrftoken');

        /**
         * Wrapper around fetch() that automatically includes the CSRF token
         * for non-safe HTTP methods.
         */
        async function csrfFetch(url, options = {}) {
            const method = (options.method || 'GET').toUpperCase();
            if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
                options.headers = options.headers || {};
                if (!options.headers['X-CSRFToken']) {
                    options.headers['X-CSRFToken'] = CSRF_TOKEN;
                }
            }
            return fetch(url, options);
        }

        // ---- Alert helper --------------------------------------------------
        function showAlert(selector, message, type = 'info') {
            const el = document.querySelector(selector);
            if (!el) return;
            el.textContent = message;
            el.className = `alert ${type}`;
            el.style.display = 'block';
            setTimeout(() => { el.style.display = 'none'; }, 4000);
        }

        // ---- 1. Vote buttons (fetch + JSON) --------------------------------
        function initVoting() {
            document.querySelectorAll('.vote-btn').forEach(btn => {
                btn.addEventListener('click', async (evt) => {
                    evt.preventDefault();
                    const url = btn.dataset.url;        // e.g. /praise/?tno=1
                    try {
                        const resp = await fetch(url);
                        const json = await resp.json();
                        if (json.code === 20000) {
                            const countEl = btn.parentElement.querySelector('.vote-count');
                            if (countEl) countEl.textContent = json.count;
                        } else {
                            alert(json.msg || 'Operation failed');
                        }
                    } catch (err) {
                        console.error('Vote error:', err);
                    }
                });
            });
        }

        // ---- 2. Cascading region select ------------------------------------
        function initCascadingSelect() {
            const provinceEl = document.getElementById('province');
            const cityEl     = document.getElementById('city');
            const districtEl = document.getElementById('district');
            if (!provinceEl) return;

            async function loadOptions(url, targetEl, placeholder) {
                targetEl.innerHTML = `<option value="">${placeholder}</option>`;
                try {
                    const resp = await fetch(url);
                    const data = await resp.json();
                    const items = data.provinces || data.cities || data.districts || [];
                    items.forEach(item => {
                        const opt = document.createElement('option');
                        opt.value = item;
                        opt.textContent = item;
                        targetEl.appendChild(opt);
                    });
                } catch (err) {
                    console.error('Region load error:', err);
                }
            }

            // Load provinces on page load
            loadOptions('/api/regions/', provinceEl, '-- Select Province --');

            provinceEl.addEventListener('change', () => {
                const prov = provinceEl.value;
                districtEl.innerHTML = '<option value="">-- Select District --</option>';
                if (prov) {
                    loadOptions(`/api/regions/?province=${encodeURIComponent(prov)}`,
                                cityEl, '-- Select City --');
                } else {
                    cityEl.innerHTML = '<option value="">-- Select City --</option>';
                }
            });

            cityEl.addEventListener('change', () => {
                const prov = provinceEl.value;
                const city = cityEl.value;
                if (prov && city) {
                    loadOptions(
                        `/api/regions/?province=${encodeURIComponent(prov)}&city=${encodeURIComponent(city)}`,
                        districtEl, '-- Select District --'
                    );
                }
            });
        }

        // ---- 3. Live search with debounce ----------------------------------
        function initLiveSearch() {
            const input   = document.getElementById('search-box');
            const results = document.getElementById('search-results');
            if (!input) return;

            let timer = null;

            function renderResults(products) {
                if (products.length === 0) {
                    results.innerHTML = '<div class="search-hint">No products found.</div>';
                    return;
                }
                results.innerHTML = products.map(p => `
                    <div class="search-item" data-id="${p.id}">
                        <span class="product-name">${p.name}</span>
                        <span class="product-price">$${p.price.toFixed(2)}</span>
                    </div>
                `).join('');
            }

            input.addEventListener('input', () => {
                clearTimeout(timer);
                const q = input.value.trim();
                if (!q) {
                    results.innerHTML = '<div class="search-hint">Type to search products...</div>';
                    return;
                }
                // Debounce: wait 300ms after the user stops typing
                timer = setTimeout(async () => {
                    try {
                        const resp = await fetch(
                            `/api/products/search/?q=${encodeURIComponent(q)}`
                        );
                        const data = await resp.json();
                        renderResults(data.results);
                    } catch (err) {
                        console.error('Search error:', err);
                    }
                }, 300);
            });
        }

        // ---- 4. File upload with progress bar (XMLHttpRequest) -------------
        function initFileUpload() {
            const zone     = document.getElementById('upload-zone');
            const fileIn   = document.getElementById('file-input');
            const progress = document.getElementById('upload-progress');
            const fill     = document.getElementById('upload-fill');
            const status   = document.getElementById('upload-status');
            if (!zone) return;

            // Click to browse
            zone.addEventListener('click', () => fileIn.click());

            // Drag-and-drop visual feedback
            ['dragenter', 'dragover'].forEach(evt => {
                zone.addEventListener(evt, (e) => {
                    e.preventDefault();
                    zone.classList.add('dragover');
                });
            });
            ['dragleave', 'drop'].forEach(evt => {
                zone.addEventListener(evt, (e) => {
                    e.preventDefault();
                    zone.classList.remove('dragover');
                });
            });

            zone.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                if (files.length) uploadFile(files[0]);
            });

            fileIn.addEventListener('change', () => {
                if (fileIn.files.length) uploadFile(fileIn.files[0]);
            });

            function uploadFile(file) {
                const formData = new FormData();
                formData.append('file', file);

                const xhr = new XMLHttpRequest();

                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const pct = Math.round((e.loaded / e.total) * 100);
                        fill.style.width = pct + '%';
                        status.textContent = `Uploading: ${pct}% (${(e.loaded/1024).toFixed(1)} KB)`;
                    }
                });

                xhr.addEventListener('load', () => {
                    if (xhr.status === 200) {
                        const data = JSON.parse(xhr.responseText);
                        if (data.code === 20000) {
                            status.textContent = `Upload complete: ${data.name} (${(data.size/1024).toFixed(1)} KB)`;
                            showAlert('#upload-alert', 'File uploaded successfully!', 'success');
                        } else {
                            status.textContent = 'Upload failed: ' + (data.msg || 'Unknown error');
                            showAlert('#upload-alert', 'Upload failed.', 'error');
                        }
                    } else {
                        status.textContent = 'Upload failed with status ' + xhr.status;
                        showAlert('#upload-alert', 'Upload failed.', 'error');
                    }
                });

                xhr.addEventListener('error', () => {
                    status.textContent = 'Network error during upload.';
                    showAlert('#upload-alert', 'Network error.', 'error');
                });

                xhr.open('POST', '/api/upload/');
                xhr.setRequestHeader('X-CSRFToken', CSRF_TOKEN);
                xhr.send(formData);

                progress.style.display = 'block';
                fill.style.width = '0%';
                status.textContent = 'Starting upload...';
            }
        }

        // ---- 5. Dynamic feedback form (fetch + JSON body, CSRF) ------------
        function initFeedbackForm() {
            const form = document.getElementById('feedback-form');
            if (!form) return;

            form.addEventListener('submit', async (evt) => {
                evt.preventDefault();

                const payload = {
                    name:     form.querySelector('[name="name"]').value,
                    email:    form.querySelector('[name="email"]').value,
                    category: form.querySelector('[name="category"]').value,
                    message:  form.querySelector('[name="message"]').value,
                };

                try {
                    const resp = await csrfFetch('/api/feedback/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    });
                    const data = await resp.json();
                    if (data.code === 20000) {
                        showAlert('#feedback-alert',
                                  `Thank you! Your ticket: ${data.ticket}`, 'success');
                        form.reset();
                    } else {
                        showAlert('#feedback-alert', data.msg || 'Submission failed.', 'error');
                    }
                } catch (err) {
                    console.error('Feedback error:', err);
                    showAlert('#feedback-alert', 'Network error.', 'error');
                }
            });
        }

        // ---- Bootstrap all modules on DOMContentLoaded ---------------------
        document.addEventListener('DOMContentLoaded', () => {
            initVoting();
            initCascadingSelect();
            initLiveSearch();
            initFileUpload();
            initFeedbackForm();
        });
    """)

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------
    write_file(root / "templates" / "index.html", """
        {% load static %}
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Day 48 - Static Resources & Ajax Demo</title>
            <link rel="stylesheet" href="{% static 'css/style.css' %}">
        </head>
        <body>
        <div class="container">

            <h1>Day 48 - Static Resources & Ajax Requests</h1>
            <p>This page demonstrates static file serving, Ajax (fetch API),
               JSON responses, and CSRF handling in Django.</p>

            <!-- ============================================================
                 Section 1: Teacher Voting (Ajax + JSON)
                 ============================================================ -->
            <h2>1. Teacher Voting (Ajax GET + JSON Response)</h2>
            <p>Click "Praise" or "Criticize" to vote without page reload.</p>

            {% for t in teachers %}
            <div class="teacher-card">
                <img src="{% static 'images/' %}{{ t.photo }}"
                     alt="{{ t.name }}"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2280%22 height=%2280%22><rect fill=%22%23ddd%22 width=%2280%22 height=%2280%22/><text x=%2240%22 y=%2244%22 text-anchor=%22middle%22 fill=%22%23999%22 font-size=%2214%22>{{ t.name|truncatechars:3 }}</text></svg>'">
                <div class="teacher-info">
                    <div class="name">{{ t.name }}</div>
                    <div class="meta">{{ t.subject }} &mdash; {{ t.intro }}</div>
                </div>
                <div>
                    <button class="vote-btn praise"
                            data-url="/praise/?tno={{ t.no }}">Praise</button>
                    <span class="vote-count">{{ t.good_count }}</span>
                    &nbsp;
                    <button class="vote-btn criticize"
                            data-url="/criticize/?tno={{ t.no }}">Criticize</button>
                    <span class="vote-count">{{ t.bad_count }}</span>
                </div>
            </div>
            {% endfor %}

            <!-- ============================================================
                 Section 2: Cascading Select (Ajax GET)
                 ============================================================ -->
            <h2>2. Cascading Region Select (Province &rarr; City &rarr; District)</h2>
            <div class="form-group">
                <label for="province">Province</label>
                <select id="province"><option value="">Loading...</option></select>
            </div>
            <div class="form-group">
                <label for="city">City</label>
                <select id="city"><option value="">-- Select City --</option></select>
            </div>
            <div class="form-group">
                <label for="district">District</label>
                <select id="district"><option value="">-- Select District --</option></select>
            </div>

            <!-- ============================================================
                 Section 3: Live Search (Ajax GET + debounce)
                 ============================================================ -->
            <h2>3. Live Product Search (Debounced Ajax)</h2>
            <input type="text" id="search-box" placeholder="Type to search products...">
            <div id="search-results">
                <div class="search-hint">Type to search products...</div>
            </div>

            <!-- ============================================================
                 Section 4: File Upload with Progress (XHR + CSRF)
                 ============================================================ -->
            <h2>4. File Upload with Progress Bar</h2>
            <div id="upload-alert" class="alert"></div>
            <div class="upload-zone" id="upload-zone">
                <p>Click or drag a file here to upload</p>
                <input type="file" id="file-input" style="display:none">
            </div>
            <div class="progress-bar" id="upload-progress" style="display:none">
                <div class="fill" id="upload-fill"></div>
            </div>
            <div class="upload-status" id="upload-status"></div>

            <!-- ============================================================
                 Section 5: Dynamic Feedback Form (Ajax POST + CSRF)
                 ============================================================ -->
            <h2>5. Feedback Form (CSRF-Protected Ajax POST)</h2>
            <div id="feedback-alert" class="alert"></div>
            <form id="feedback-form">
                <div class="form-group">
                    <label for="fb-name">Name *</label>
                    <input type="text" name="name" id="fb-name" required>
                </div>
                <div class="form-group">
                    <label for="fb-email">Email *</label>
                    <input type="email" name="email" id="fb-email" required>
                </div>
                <div class="form-group">
                    <label for="fb-category">Category</label>
                    <select name="category" id="fb-category">
                        <option value="general">General</option>
                        <option value="bug">Bug Report</option>
                        <option value="feature">Feature Request</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="fb-message">Message *</label>
                    <textarea name="message" id="fb-message" required></textarea>
                </div>
                <button type="submit" class="btn">Submit Feedback</button>
            </form>

            <hr style="margin:32px 0">
            <p style="color:#95a5a6; font-size:.85rem">
                Day 48 Demo &mdash; Static Resources and Ajax Requests &mdash;
                CSRF token: {{ csrf_token|truncatechars:16 }}...
            </p>
        </div>

        <!-- Load vanilla JS (covers fetch-based Ajax) -->
        <script src="{% static 'js/app.js' %}"></script>
        </body>
        </html>
    """)

    # ------------------------------------------------------------------
    # Placeholder static images (1x1 transparent PNG as base64)
    # ------------------------------------------------------------------
    placeholder_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80">'
        '<rect fill="#ddd" width="80" height="80"/>'
        '<text x="40" y="44" text-anchor="middle" fill="#999" font-size="14">?</text>'
        '</svg>'
    )
    for name in ['default.png', 'alice.png', 'bob.png', 'charlie.png',
                 'diana.png', 'eve.png']:
        img_path = static / "images" / name
        img_path.parent.mkdir(parents=True, exist_ok=True)
        if not img_path.exists():
            img_path.write_text(placeholder_svg, encoding="utf-8")

    print(f"\n[done] Project generated at: {root}")


# ---------------------------------------------------------------------------
# Django management helpers
# ---------------------------------------------------------------------------

def run_server(port: int = 8000) -> None:
    """Bootstrap Django settings and start the development server."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    sys.path.insert(0, str(PROJECT_DIR))

    import django
    django.setup()

    from django.core.management import call_command
    print(f"\nStarting Django dev server on http://127.0.0.1:{port}/")
    print("Press Ctrl+C to stop.\n")
    call_command('runserver', f'0.0.0.0:{port}', '--noreload')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Day 48 demo: Static Resources and Ajax Requests"
    )
    parser.add_argument(
        '--init', action='store_true',
        help='Only generate project files; do not start the server.'
    )
    parser.add_argument(
        '--port', type=int, default=8000,
        help='Port for the Django dev server (default: 8000).'
    )
    args = parser.parse_args()

    generate_project()

    if not args.init:
        run_server(port=args.port)


if __name__ == '__main__':
    main()
