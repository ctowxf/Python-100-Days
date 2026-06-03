"""
Day 46 - Django Quickstart Demo
================================
A standalone script demonstrating core Django concepts (MVT pattern, URL routing,
template rendering, HTTP responses) without requiring a full Django project or
running server. Uses Django's test client and in-memory setup.

Requirements:  pip install django
"""

from __future__ import annotations

import os
import sys
import random
from typing import Any

# ---------------------------------------------------------------------------
# 1. Django bootstrap -- configure settings before importing Django components
# ---------------------------------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_quickstart_settings")

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        ROOT_URLCONF="_quickstart_urls",  # we define this module inline below
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": False,
                "OPTIONS": {
                    "context_processors": [],
                    "loaders": [
                        "django.template.loaders.locmem.Loader",
                    ],
                },
            }
        ],
        MIDDLEWARE=[],
        SECRET_KEY="demo-secret-key-not-for-production",
        ALLOWED_HOSTS=["*"],
    )

django.setup()

# ---------------------------------------------------------------------------
# 2. Django project structure explanation (printed to stdout)
# ---------------------------------------------------------------------------

PROJECT_STRUCTURE: str = """
======================================================================
  Django Project Structure (created by `django-admin startproject`)
======================================================================

  hellodjango/                 <-- outer project folder (name is arbitrary)
  |-- manage.py                <-- CLI entry point for project management
  |-- hellodjango/             <-- inner package (the real Django project)
  |   |-- __init__.py          <-- marks directory as a Python package
  |   |-- settings.py          <-- project configuration (DB, templates, ...)
  |   |-- urls.py              <-- top-level URL routing declarations
  |   |-- wsgi.py              <-- WSGI entry point for production servers
  |   +-- asgi.py              <-- ASGI entry point (async, Django 3.0+)
  +-- <app_name>/              <-- a Django application (created via startapp)
      |-- __init__.py
      |-- admin.py             <-- register models for Django admin site
      |-- apps.py              <-- application configuration
      |-- models.py            <-- data models  (M in MVT)
      |-- views.py             <-- request handlers / view functions (V in MVT)
      |-- tests.py             <-- unit tests
      |-- urls.py              <-- app-level URL routing (optional)
      +-- migrations/          <-- database migration files
          +-- __init__.py
"""

# ---------------------------------------------------------------------------
# 3. MVT pattern explanation
# ---------------------------------------------------------------------------

MVT_PATTERN: str = """
======================================================================
  Django MVT Pattern  vs  Classic MVC
======================================================================

  Classic MVC:
    Model      -- data / business logic
    View       -- UI / presentation
    Controller -- routes requests, mediates Model <-> View

  Django MVT:
    Model      -- same as MVC (models.py, ORM)
    Template   -- presentation / HTML with DTL placeholders (templates/)
    View       -- receives HTTP request, interacts with Model, picks a
                  Template, renders and returns HTTP response (views.py)
                  View + Django framework together play the Controller role.

  Request flow:
    Client  -->  URL dispatcher  -->  View function
                                          |
                                    Model (optional DB query)
                                          |
                                    Template (render with context)
                                          |
    Client  <--  HTTP Response  <---------+
"""

# ---------------------------------------------------------------------------
# 4. MVT Demonstration -- Models, Views, Templates working together
# ---------------------------------------------------------------------------

from django.http import HttpRequest, HttpResponse
from django.template import engines
from django.template.loader import render_to_string

# -- Simulated "Model" layer -------------------------------------------------

def get_fruit_recommendations(count: int = 3) -> list[str]:
    """Simulate a model / data-access function (like querying a DB)."""
    all_fruits: list[str] = [
        "Apple", "Orange", "Pitaya", "Durian", "Waxberry", "Blueberry",
        "Grape", "Peach", "Pear", "Banana", "Watermelon", "Mango",
    ]
    return random.sample(all_fruits, count)


# -- "Template" layer (stored in memory via locmem loader) --------------------

INDEX_TEMPLATE: str = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Fruit Recommendations</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        #fruits { font-size: 1.25em; }
    </style>
</head>
<body>
    <h1>{{ greeting }}</h1>
    <hr>
    <ul id="fruits">
        {% for fruit in fruits %}
        <li>{{ fruit }}</li>
        {% endfor %}
    </ul>
    <p><em>Total recommendations: {{ fruits|length }}</em></p>
</body>
</html>"""

# Register template into the locmem loader so render_to_string can find it.
engines["django"].engine.template_loaders[0].templates["index.html"] = (
    INDEX_TEMPLATE
)


# -- "View" layer (view function) --------------------------------------------

def index_view(request: HttpRequest) -> HttpResponse:
    """
    A Django view function demonstrating the full MVT cycle:
      1. Receive request
      2. Call model layer for data
      3. Render template with context
      4. Return HttpResponse
    """
    fruits: list[str] = get_fruit_recommendations(3)
    context: dict[str, Any] = {
        "greeting": "Today's Recommended Fruits:",
        "fruits": fruits,
    }
    html: str = render_to_string("index.html", context)
    return HttpResponse(html)


def hello_view(request: HttpRequest) -> HttpResponse:
    """Simple view returning a plain HTML response (no template)."""
    return HttpResponse("<h1>Hello, Django!</h1>")


def dynamic_view(request: HttpRequest) -> HttpResponse:
    """View that generates dynamic content by directly building HTML."""
    fruits: list[str] = get_fruit_recommendations(4)
    content: str = "<h3>Random Fruit Salad:</h3><hr><ul>"
    for fruit in fruits:
        content += f"<li>{fruit}</li>"
    content += "</ul>"
    return HttpResponse(content)


# ---------------------------------------------------------------------------
# 5. URL routing (equivalent to urls.py)
# ---------------------------------------------------------------------------

from django.urls import path

urlpatterns = [
    path("", index_view, name="index"),
    path("hello/", hello_view, name="hello"),
    path("dynamic/", dynamic_view, name="dynamic"),
]

# Manually attach urlpatterns to the module Django will look up.
_urlmod = sys.modules["__main__"]
_urlmod.urlpatterns = urlpatterns  # type: ignore[attr-defined]

# Also register the module under the ROOT_URLCONF name so Django resolves it.
sys.modules["_quickstart_urls"] = _urlmod  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# 6. Demonstrate all concepts using Django's test client
# ---------------------------------------------------------------------------

from django.test import RequestFactory, Client


def demonstrate_mvt_pattern() -> None:
    """Show how View, Model, and Template collaborate to produce a response."""
    print(MVT_PATTERN)

    factory: RequestFactory = RequestFactory()

    # -- A. Plain HTTP response (no template) ---------------------------------
    print("--- A. Simple hello_view (plain HttpResponse) ---")
    request: HttpRequest = factory.get("/hello/")
    response: HttpResponse = hello_view(request)
    print(f"Status code : {response.status_code}")
    print(f"Content-Type: {response['Content-Type']}")
    print(f"Body        : {response.content.decode()}")
    print()

    # -- B. Dynamic content generated in view ---------------------------------
    print("--- B. dynamic_view (built-in HTML string) ---")
    request = factory.get("/dynamic/")
    response = dynamic_view(request)
    print(f"Status code : {response.status_code}")
    print(f"Body (first 200 chars):\n{response.content.decode()[:200]}...")
    print()

    # -- C. Full MVT: Model + Template + View ---------------------------------
    print("--- C. index_view (Model -> Template -> View -> Response) ---")
    request = factory.get("/")
    response = index_view(request)
    print(f"Status code : {response.status_code}")
    print(f"Body:\n{response.content.decode()}")
    print()


def demonstrate_url_routing() -> None:
    """Demonstrate URL routing via Django's test client."""
    print("=" * 70)
    print("  URL Routing Demonstration (Django Test Client)")
    print("=" * 70)

    client: Client = Client()

    urls: list[str] = ["/", "/hello/", "/dynamic/"]
    for url in urls:
        response: HttpResponse = client.get(url)
        status: int = response.status_code
        snippet: str = response.content.decode()[:120].replace("\n", " ")
        print(f"  GET {url:<15s} -> {status} | {snippet}...")

    # Demonstrate a 404
    response = client.get("/nonexistent/")
    print(f"  GET {'/nonexistent/':<15s} -> {response.status_code} (not found)")
    print()


def demonstrate_request_response_cycle() -> None:
    """Show request and response object attributes."""
    print("=" * 70)
    print("  Request / Response Object Inspection")
    print("=" * 70)

    factory: RequestFactory = RequestFactory()
    request: HttpRequest = factory.get(
        "/hello/?name=Django",
        HTTP_USER_AGENT="PythonDemo/1.0",
        HTTP_ACCEPT="text/html",
    )

    print(f"  request.method      : {request.method}")
    print(f"  request.path        : {request.path}")
    print(f"  request.GET         : {dict(request.GET)}")
    print(f"  request.META[UA]    : {request.META.get('HTTP_USER_AGENT')}")
    print()

    response: HttpResponse = hello_view(request)
    response["X-Custom-Header"] = "DjangoRocks"
    print(f"  response.status_code: {response.status_code}")
    print(f"  response.headers    : {dict(response.items())}")
    print(f"  response.content    : {response.content.decode()}")
    print()


# ---------------------------------------------------------------------------
# 7. C++ comparison
# ---------------------------------------------------------------------------

CPP_COMPARISON: str = """
======================================================================
  Django MVT  vs  C++ MVC Frameworks (e.g., Qt MVC, JUCE, cpprestsdk)
======================================================================

  +-------------------+----------------------------+---------------------------+
  | Aspect            | Django (Python)            | C++ MVC Framework         |
  +-------------------+----------------------------+---------------------------+
  | Language          | Python (interpreted)       | C++ (compiled)            |
  | Typing            | Dynamic + optional hints   | Static, strict            |
  | Model layer       | Django ORM (declarative)   | Manual structs/classes or |
  |                   | auto-migrations from model | ORM like ODB / SOCI;     |
  |                   | changes                    | migrations often manual   |
  | View / Controller | View functions receive     | Controller classes with   |
  |                   | HttpRequest, return        | virtual methods handle    |
  |                   | HttpResponse; framework    | events; developer wires   |
  |                   | acts as the controller     | routing explicitly        |
  | Template / View   | DTL (Django Template       | QML, JUCE Component,     |
  |                   | Language) with {% %} and   | or HTML via Crow/pistache |
  |                   | {{ }} syntax               | with Mustache/Jinja       |
  | URL routing       | Declarative path() calls   | Manual switch/router or   |
  |                   | in urls.py                 | framework-specific routes |
  | Dev speed         | Very fast (batteries       | Slower (compile cycle,    |
  |                   | included, auto-reload)     | linker, header mgmt)     |
  | Performance       | Moderate (GIL-bound);      | High (native code,       |
  |                   | scale with ASGI / workers  | zero-cost abstractions)  |
  | Deployment        | WSGI/ASGI servers (Gunicorn| Single binary or shared   |
  |                   | + Nginx), Docker           | lib; systemd / Docker    |
  | Use cases         | Web apps, APIs, CMS,       | Game UIs, desktop apps,  |
  |                   | data dashboards            | embedded web servers,    |
  |                   |                            | high-perf microservices  |
  +-------------------+----------------------------+---------------------------+

  Key takeaway:
    Django trades raw execution speed for developer productivity.
    C++ frameworks trade development speed for runtime performance.
    For most web applications, Django's approach yields faster delivery.
    For latency-critical or resource-constrained systems, C++ shines.
"""


def main() -> None:
    """Entry point: demonstrate all Django quickstart concepts."""
    print(PROJECT_STRUCTURE)
    demonstrate_mvt_pattern()
    demonstrate_url_routing()
    demonstrate_request_response_cycle()
    print(CPP_COMPARISON)
    print("Demo complete. To run a real Django server:")
    print("  1. django-admin startproject hellodjango")
    print("  2. cd hellodjango && python manage.py startapp first")
    print("  3. Edit views.py, urls.py, then: python manage.py runserver")


if __name__ == "__main__":
    main()
