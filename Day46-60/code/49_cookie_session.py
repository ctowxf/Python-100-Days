"""
Day 49 - Cookie and Session Management in Django
=================================================

Comprehensive demo covering:
  1. Cookie operations (read, write, signed cookies)
  2. Session backends (database, cache, file, cookie)
  3. Custom session handling (store, serializer, middleware)
  4. Login / logout flow with CAPTCHA verification
  5. Enterprise features: remember-me, shopping cart, user preferences

C++ comparison included as inline comments.

Requirements:
    pip install django pillow
    # For the shopping-cart demo you need a Django project; the standalone
    # classes below can be imported into any Django app.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import string
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 1.  Utility helpers
# ---------------------------------------------------------------------------

def gen_md5_digest(content: str) -> str:
    """Return the 32-char hex MD5 digest of *content*."""
    return hashlib.md5(content.encode()).hexdigest()


def gen_random_code(length: int = 4) -> str:
    """Generate a random alphanumeric CAPTCHA string."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


# ---------------------------------------------------------------------------
# 2.  Cookie operations  (low-level, framework-agnostic helpers)
# ---------------------------------------------------------------------------

class CookieHelper:
    """
    Encapsulates common cookie read / write patterns used in Django views.

    Django's HttpRequest.COOKIES       -> dict[str, str]
    Django's HttpResponse.set_cookie() -> writes Set-Cookie header
    Django's HttpResponse.set_signed_cookie() -> tamper-proof cookie

    C++ comparison
    --------------
    In a C++ HTTP server (e.g. Crow, Drogon) you would manually build the
    "Set-Cookie" header string:
        response.set_header("Set-Cookie",
            "theme=dark; Path=/; Max-Age=86400; HttpOnly; Secure");
    and parse "Cookie:" from the request header map yourself.  Django wraps
    all of that behind request.COOKIES / response.set_cookie().
    """

    # -- basic cookie --------------------------------------------------------
    @staticmethod
    def set_cookie(
        response: Any,
        key: str,
        value: str,
        max_age: int = 86400,
        httponly: bool = True,
        secure: bool = False,
        samesite: str = "Lax",
    ) -> None:
        """Write a plain cookie via Django's HttpResponse.set_cookie."""
        response.set_cookie(
            key,
            value,
            max_age=max_age,
            httponly=httponly,
            secure=secure,
            samesite=samesite,
        )

    @staticmethod
    def get_cookie(request: Any, key: str, default: str = "") -> str:
        """Read a cookie from the request."""
        return request.COOKIES.get(key, default)

    # -- signed cookie (tamper-proof) ----------------------------------------
    @staticmethod
    def set_signed_cookie(
        response: Any,
        key: str,
        value: str,
        salt: str = "preferences",
        max_age: int = 86400 * 30,
    ) -> None:
        """
        Write a signed cookie.  Django uses SECRET_KEY + *salt* to produce
        an HMAC so that any tampering is detected on read.
        """
        response.set_signed_cookie(key, value, salt=salt, max_age=max_age)

    @staticmethod
    def get_signed_cookie(
        request: Any,
        key: str,
        salt: str = "preferences",
        default: str = "",
    ) -> str:
        """Read a signed cookie; returns *default* on BadSignature."""
        try:
            return request.get_signed_cookie(key, salt=salt)
        except Exception:
            return default


# ---------------------------------------------------------------------------
# 3.  Session backends  (Django built-in + custom)
# ---------------------------------------------------------------------------

class SessionBackendDemo:
    """
    Django ships with several session storage backends.  You switch between
    them via the SESSION_ENGINE setting:

    | SESSION_ENGINE                                | Where data lives          |
    |-----------------------------------------------|---------------------------|
    | django.contrib.sessions.backends.db           | django_session table      |
    | django.contrib.sessions.backends.cache        | Memcached / Redis         |
    | django.contrib.sessions.backends.cached_db    | Cache + DB fallback       |
    | django.contrib.sessions.backends.file         | /tmp (one file per sess)  |
    | django.contrib.sessions.backends.signed_cookie| Encrypted cookie (no srv) |

    C++ comparison
    --------------
    In C++ server-side code there is no built-in session abstraction.
    A common pattern is:
        1. Generate a random session-id (UUID).
        2. Store a std::unordered_map<string, SessionData> in memory, or
           push the map into Redis / RocksDB.
        3. Manually set a "Set-Cookie: sid=<uuid>" header.
        4. On every request, look up the map by the cookie value.
    Django's SessionMiddleware automates all of this.
    """

    @staticmethod
    def settings_snippet_db() -> str:
        """Settings for database-backed sessions (the default)."""
        return (
            "# settings.py  -- database session backend (default)\n"
            "INSTALLED_APPS = [\n"
            "    ...\n"
            "    'django.contrib.sessions',\n"
            "]\n"
            "MIDDLEWARE = [\n"
            "    'django.contrib.sessions.middleware.SessionMiddleware',\n"
            "    ...\n"
            "]\n"
            "SESSION_ENGINE = 'django.contrib.sessions.backends.db'\n"
            "SESSION_COOKIE_AGE = 1209600          # 2 weeks\n"
            "SESSION_EXPIRE_AT_BROWSER_CLOSE = False\n"
        )

    @staticmethod
    def settings_snippet_cache() -> str:
        """Settings for cache-backed sessions (fastest)."""
        return (
            "# settings.py  -- cache session backend\n"
            "SESSION_ENGINE = 'django.contrib.sessions.backends.cache'\n"
            "SESSION_CACHE_ALIAS = 'default'\n"
            "CACHES = {\n"
            "    'default': {\n"
            "        'BACKEND': 'django.core.cache.backends.redis.RedisCache',\n"
            "        'LOCATION': 'redis://127.0.0.1:6379/1',\n"
            "    }\n"
            "}\n"
        )

    @staticmethod
    def settings_snippet_cached_db() -> str:
        """Settings for cache-with-DB-fallback sessions."""
        return (
            "# settings.py  -- cache + db fallback\n"
            "SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'\n"
            "SESSION_CACHE_ALIAS = 'default'\n"
        )

    @staticmethod
    def settings_snippet_file() -> str:
        """Settings for file-backed sessions."""
        return (
            "# settings.py  -- file session backend\n"
            "SESSION_ENGINE = 'django.contrib.sessions.backends.file'\n"
            "SESSION_FILE_PATH = '/tmp/django_sessions'\n"
        )

    @staticmethod
    def settings_snippet_signed_cookie() -> str:
        """Settings for signed-cookie sessions (no server storage)."""
        return (
            "# settings.py  -- signed-cookie session backend\n"
            "SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'\n"
            "SESSION_COOKIE_HTTPONLY = True\n"
            "SESSION_COOKIE_SECURE = True           # HTTPS only\n"
        )


# ---------------------------------------------------------------------------
# 4.  Custom session store (demonstrates how Django's session framework works
#     under the hood -- useful for C++ developers who roll their own)
# ---------------------------------------------------------------------------

class InMemorySessionStore:
    """
    A minimal, in-memory session store that mimics the interface Django's
    SessionBase expects.  Intended for teaching / testing -- NOT for
    production (data is lost on process exit).

    C++ comparison
    --------------
    This is essentially:
        std::unordered_map<std::string,
            std::unordered_map<std::string, nlohmann::json>> _store;
    with a TTL eviction loop.
    """

    _store: Dict[str, Dict[str, Any]] = {}
    _expiry: Dict[str, float] = {}

    # -- lifecycle -----------------------------------------------------------
    @classmethod
    def create(cls, expiry_seconds: int = 3600) -> Tuple[str, Dict[str, Any]]:
        """Create a new session, return (session_id, session_data)."""
        sid = uuid.uuid4().hex
        cls._store[sid] = {}
        cls._expiry[sid] = time.time() + expiry_seconds
        return sid, cls._store[sid]

    @classmethod
    def get(cls, sid: str) -> Optional[Dict[str, Any]]:
        """Return session data for *sid*, or None if expired / missing."""
        cls._evict()
        data = cls._store.get(sid)
        if data is None:
            return None
        if time.time() > cls._expiry.get(sid, 0):
            cls.delete(sid)
            return None
        return data

    @classmethod
    def delete(cls, sid: str) -> None:
        cls._store.pop(sid, None)
        cls._expiry.pop(sid, None)

    @classmethod
    def flush_expired(cls) -> int:
        """Remove all expired sessions; return count removed."""
        return cls._evict()

    # -- private -------------------------------------------------------------
    @classmethod
    def _evict(cls) -> int:
        now = time.time()
        expired = [sid for sid, exp in cls._expiry.items() if now > exp]
        for sid in expired:
            cls.delete(sid)
        return len(expired)


# ---------------------------------------------------------------------------
# 5.  Custom session middleware (skeleton)
# ---------------------------------------------------------------------------

class SimpleSessionMiddleware:
    """
    Skeleton middleware that demonstrates the request/response lifecycle
    Django's SessionMiddleware follows:

        process_request:
            1. Read sessionid from cookie.
            2. Load session data from the backend.
            3. Attach data to request.session.

        process_response:
            1. Save session data back to the backend.
            2. Write sessionid cookie on the response.
            3. Return the response.

    Usage in settings.py:
        MIDDLEWARE = ['myapp.middleware.SimpleSessionMiddleware', ...]
    """

    SESSION_COOKIE_NAME: str = "sessionid"
    SESSION_COOKIE_AGE: int = 86400

    def __init__(self, get_response: Any) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        # -- process_request -------------------------------------------------
        sid = request.COOKIES.get(self.SESSION_COOKIE_NAME)
        if sid:
            session_data = InMemorySessionStore.get(sid)
            if session_data is None:
                sid, session_data = InMemorySessionStore.create(
                    self.SESSION_COOKIE_AGE
                )
        else:
            sid, session_data = InMemorySessionStore.create(
                self.SESSION_COOKIE_AGE
            )

        request.session = session_data  # attach to request
        request._session_id = sid       # private attr for response phase

        response = self.get_response(request)

        # -- process_response ------------------------------------------------
        response.set_cookie(
            self.SESSION_COOKIE_NAME,
            request._session_id,
            max_age=self.SESSION_COOKIE_AGE,
            httponly=True,
            samesite="Lax",
        )
        return response


# ---------------------------------------------------------------------------
# 6.  User model (simplified for the demo, mirrors the tutorial)
# ---------------------------------------------------------------------------

class User:
    """
    In-memory stand-in for Django's User model.  In a real project you would
    write:

        class User(models.Model):
            no        = models.AutoField(primary_key=True)
            username  = models.CharField(max_length=20, unique=True)
            password  = models.CharField(max_length=32)   # MD5 hash
            tel       = models.CharField(max_length=20)
            reg_date  = models.DateTimeField(auto_now_add=True)
            last_visit = models.DateTimeField(null=True)
    """

    _users: Dict[str, "User"] = {}

    def __init__(
        self,
        no: int,
        username: str,
        password_hash: str,
        tel: str,
    ) -> None:
        self.no = no
        self.username = username
        self.password_hash = password_hash
        self.tel = tel
        self.reg_date = datetime.now()
        self.last_visit: Optional[datetime] = None

    # -- seed data -----------------------------------------------------------
    @classmethod
    def seed(cls) -> None:
        """Insert two test users (passwords: 1qaz2wsx / Abc123!!)."""
        cls._users["wangdachui"] = cls(
            no=1,
            username="wangdachui",
            password_hash="1c63129ae9db9c60c3e8aa94d3e00495",
            tel="13122334455",
        )
        cls._users["hellokitty"] = cls(
            no=2,
            username="hellokitty",
            password_hash="c6f8cf68e5f68b0aa4680e089ee4742c",
            tel="13890006789",
        )

    @classmethod
    def authenticate(cls, username: str, password: str) -> Optional["User"]:
        """Return the user if credentials are valid, else None."""
        user = cls._users.get(username)
        if user and user.password_hash == gen_md5_digest(password):
            user.last_visit = datetime.now()
            return user
        return None

    def __repr__(self) -> str:
        return f"User(no={self.no}, username={self.username!r})"


# ---------------------------------------------------------------------------
# 7.  Login / Logout view helpers (pure functions, no Django dependency)
# ---------------------------------------------------------------------------

class AuthViews:
    """
    Demonstrates the full login / logout flow without requiring a running
    Django server.  Each method is annotated to show which Django objects
    (request, response) it would use.
    """

    @staticmethod
    def login(
        session: Dict[str, Any],
        username: str,
        password: str,
        captcha_input: str = "",
        captcha_expected: str = "",
    ) -> Dict[str, Any]:
        """
        Simulate POST /login/.

        In a real Django view:
            def login(request: HttpRequest) -> HttpResponse:
                ...
        """
        # -- verify CAPTCHA (skip if empty, for unit-test convenience) ------
        if captcha_expected and captcha_input.lower() != captcha_expected.lower():
            return {"status": "error", "hint": "CAPTCHA incorrect"}

        # -- verify credentials ----------------------------------------------
        user = User.authenticate(username, password)
        if user is None:
            return {"status": "error", "hint": "Invalid username or password"}

        # -- store user info in session --------------------------------------
        session["userid"] = user.no
        session["username"] = user.username
        session["login_time"] = datetime.now().isoformat()

        return {"status": "ok", "user": user}

    @staticmethod
    def logout(session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate POST /logout/.

        Django's session.flush() does two things:
            1. Deletes session data on the server.
            2. Deletes the sessionid cookie on the client.
        """
        session.clear()
        return {"status": "ok", "hint": "Logged out"}

    @staticmethod
    def check_login(session: Dict[str, Any]) -> bool:
        """Return True if the session contains a valid userid."""
        return "userid" in session


# ---------------------------------------------------------------------------
# 8.  Enterprise feature: "Remember Me"
# ---------------------------------------------------------------------------

class RememberMeManager:
    """
    Implements a persistent "remember me" token.

    Flow:
        1. On login with remember=True, generate a random token.
        2. Store   token -> (user_id, expiry)   in a DB table or dict.
        3. Write   remember_token=<token>   as a long-lived cookie.
        4. On subsequent visits, if session is empty, check the cookie.

    C++ comparison
    --------------
    In C++ you would store tokens in Redis:
        redis.setex("remember:" + token, 86400*30, user_id);
    and check the cookie on every request in your auth middleware.
    """

    _tokens: Dict[str, Tuple[int, datetime]] = {}
    TOKEN_MAX_AGE_DAYS: int = 30

    @classmethod
    def create_token(cls, user_id: int) -> str:
        token = uuid.uuid4().hex
        expiry = datetime.now() + timedelta(days=cls.TOKEN_MAX_AGE_DAYS)
        cls._tokens[token] = (user_id, expiry)
        return token

    @classmethod
    def validate_token(cls, token: str) -> Optional[int]:
        """Return user_id if token is valid and not expired, else None."""
        entry = cls._tokens.get(token)
        if entry is None:
            return None
        user_id, expiry = entry
        if datetime.now() > expiry:
            del cls._tokens[token]
            return None
        return user_id

    @classmethod
    def revoke_token(cls, token: str) -> None:
        cls._tokens.pop(token, None)


# ---------------------------------------------------------------------------
# 9.  Enterprise feature: Shopping Cart (session-based)
# ---------------------------------------------------------------------------

class ShoppingCart:
    """
    A session-backed shopping cart.  The cart data is stored inside the
    session dict, so it survives page navigations but is lost on logout.

    Structure stored in session:
        session["cart"] = [
            {"product_id": 101, "name": "Widget", "price": 9.99, "qty": 2},
            ...
        ]

    C++ comparison
    --------------
    In C++ you might store the cart in a Redis hash:
        HSET cart:<session_id> 101 '{"name":"Widget","qty":2}'
    or in an in-memory struct attached to the session object.
    """

    CART_KEY: str = "cart"

    @classmethod
    def _get_cart(cls, session: Dict[str, Any]) -> List[Dict[str, Any]]:
        if cls.CART_KEY not in session:
            session[cls.CART_KEY] = []
        return session[cls.CART_KEY]

    @classmethod
    def add_item(
        cls,
        session: Dict[str, Any],
        product_id: int,
        name: str,
        price: float,
        qty: int = 1,
    ) -> None:
        cart = cls._get_cart(session)
        for item in cart:
            if item["product_id"] == product_id:
                item["qty"] += qty
                return
        cart.append(
            {"product_id": product_id, "name": name, "price": price, "qty": qty}
        )

    @classmethod
    def remove_item(cls, session: Dict[str, Any], product_id: int) -> None:
        cart = cls._get_cart(session)
        session[cls.CART_KEY] = [
            item for item in cart if item["product_id"] != product_id
        ]

    @classmethod
    def update_qty(
        cls, session: Dict[str, Any], product_id: int, qty: int
    ) -> None:
        cart = cls._get_cart(session)
        for item in cart:
            if item["product_id"] == product_id:
                item["qty"] = max(0, qty)
                break
        # remove zero-qty items
        session[cls.CART_KEY] = [
            item for item in cart if item["qty"] > 0
        ]

    @classmethod
    def total(cls, session: Dict[str, Any]) -> float:
        cart = cls._get_cart(session)
        return sum(item["price"] * item["qty"] for item in cart)

    @classmethod
    def items(cls, session: Dict[str, Any]) -> List[Dict[str, Any]]:
        return cls._get_cart(session)

    @classmethod
    def clear(cls, session: Dict[str, Any]) -> None:
        session[cls.CART_KEY] = []


# ---------------------------------------------------------------------------
# 10. Enterprise feature: User Preferences (cookie-based)
# ---------------------------------------------------------------------------

class UserPreferences:
    """
    Stores non-sensitive user preferences in a signed cookie so they
    persist across sessions without requiring a database lookup.

    Typical preferences: theme (dark/light), language, font-size, etc.

    In a real Django view:
        response = render(request, "index.html")
        CookieHelper.set_signed_cookie(response, "prefs", json.dumps(prefs))
        return response
    """

    DEFAULTS: Dict[str, Any] = {
        "theme": "light",
        "language": "zh-hans",
        "font_size": 14,
        "items_per_page": 20,
    }

    @classmethod
    def load(cls, raw_cookie: str) -> Dict[str, Any]:
        """Parse preferences from a cookie value, falling back to defaults."""
        if not raw_cookie:
            return dict(cls.DEFAULTS)
        try:
            prefs = json.loads(raw_cookie)
            merged = dict(cls.DEFAULTS)
            merged.update(prefs)
            return merged
        except (json.JSONDecodeError, TypeError):
            return dict(cls.DEFAULTS)

    @classmethod
    def dump(cls, prefs: Dict[str, Any]) -> str:
        """Serialize preferences to a JSON string suitable for a cookie."""
        return json.dumps(prefs, ensure_ascii=False)

    @classmethod
    def update(
        cls, raw_cookie: str, **overrides: Any
    ) -> str:
        """Merge *overrides* into existing preferences and return new cookie."""
        prefs = cls.load(raw_cookie)
        prefs.update(overrides)
        return cls.dump(prefs)


# ---------------------------------------------------------------------------
# 11. CAPTCHA generator (simplified -- no Pillow dependency)
# ---------------------------------------------------------------------------

class SimpleCaptcha:
    """
    Generates a text-based CAPTCHA.  In production you would use PIL to
    render an image (see the tutorial's Captcha class).
    """

    @staticmethod
    def generate(length: int = 4) -> str:
        return gen_random_code(length)


# ---------------------------------------------------------------------------
# 12. Integrated demo: full login + cart + preferences scenario
# ---------------------------------------------------------------------------

def run_demo() -> None:
    """
    Walk through a realistic scenario:
        1. Seed users.
        2. Create a session.
        3. Generate CAPTCHA, attempt login.
        4. Add items to shopping cart.
        5. Save user preferences to a signed cookie.
        6. Demonstrate "remember me".
        7. Logout and verify cleanup.
    """
    separator = "=" * 70

    print(separator)
    print("  Day 49 -- Cookie & Session Comprehensive Demo")
    print(separator)

    # -- 0. Seed data --------------------------------------------------------
    User.seed()
    print("\n[Seed] Two users created: wangdachui / hellokitty")

    # -- 1. Create a session -------------------------------------------------
    session_id, session_data = InMemorySessionStore.create(expiry_seconds=3600)
    print(f"\n[Session] Created session  sid={session_id[:12]}...")

    # -- 2. CAPTCHA flow -----------------------------------------------------
    captcha_code = SimpleCaptcha.generate()
    session_data["captcha"] = captcha_code
    print(f"[CAPTCHA] Generated code: {captcha_code}")

    # -- 3. Login (wrong CAPTCHA) --------------------------------------------
    result = AuthViews.login(
        session_data,
        username="wangdachui",
        password="1qaz2wsx",
        captcha_input="WRONG",
        captcha_expected=captcha_code,
    )
    print(f"[Login] Wrong CAPTCHA -> {result}")

    # -- 4. Login (correct) --------------------------------------------------
    result = AuthViews.login(
        session_data,
        username="wangdachui",
        password="1qaz2wsx",
        captcha_input=captcha_code,
        captcha_expected=captcha_code,
    )
    print(f"[Login] Success -> userid={session_data.get('userid')}, "
          f"username={session_data.get('username')}")

    # -- 5. Shopping cart -----------------------------------------------------
    cart = ShoppingCart
    cart.add_item(session_data, product_id=101, name="Python Book", price=59.90, qty=1)
    cart.add_item(session_data, product_id=202, name="USB-C Cable", price=12.50, qty=3)
    cart.add_item(session_data, product_id=101, name="Python Book", price=59.90, qty=1)

    print(f"\n[Cart] Items after adding:")
    for item in cart.items(session_data):
        print(f"       {item['name']} x{item['qty']} @ {item['price']}")
    print(f"       Total: {cart.total(session_data):.2f}")

    cart.update_qty(session_data, product_id=202, qty=1)
    cart.remove_item(session_data, product_id=101)
    print(f"\n[Cart] After update/remove:")
    for item in cart.items(session_data):
        print(f"       {item['name']} x{item['qty']} @ {item['price']}")
    print(f"       Total: {cart.total(session_data):.2f}")

    # -- 6. User preferences (cookie-based) ----------------------------------
    prefs_cookie_value = UserPreferences.dump(
        {"theme": "dark", "language": "en", "font_size": 16}
    )
    print(f"\n[Prefs] Cookie value: {prefs_cookie_value}")

    # Simulate reading the cookie back and updating
    updated = UserPreferences.update(
        prefs_cookie_value, items_per_page=50, font_size=18
    )
    loaded = UserPreferences.load(updated)
    print(f"[Prefs] After update: {loaded}")

    # -- 7. Remember-me token ------------------------------------------------
    user_id = session_data.get("userid", 0)
    token = RememberMeManager.create_token(user_id)
    print(f"\n[RememberMe] Token created: {token[:16]}... "
          f"(expires in {RememberMeManager.TOKEN_MAX_AGE_DAYS} days)")

    validated_id = RememberMeManager.validate_token(token)
    print(f"[RememberMe] Token valid for user_id={validated_id}")

    RememberMeManager.revoke_token(token)
    print(f"[RememberMe] After revoke: {RememberMeManager.validate_token(token)}")

    # -- 8. Logout -----------------------------------------------------------
    result = AuthViews.logout(session_data)
    print(f"\n[Logout] {result}")
    print(f"[Logout] Session empty: {len(session_data) == 0}")
    print(f"[Logout] Logged in: {AuthViews.check_login(session_data)}")

    # -- 9. Session backend settings ------------------------------------------
    print(f"\n{separator}")
    print("  Session backend configuration examples")
    print(separator)
    backends = SessionBackendDemo
    for name, method in [
        ("Database",        backends.settings_snippet_db),
        ("Cache",           backends.settings_snippet_cache),
        ("Cache + DB",      backends.settings_snippet_cached_db),
        ("File",            backends.settings_snippet_file),
        ("Signed Cookie",   backends.settings_snippet_signed_cookie),
    ]:
        print(f"\n--- {name} ---")
        print(method())

    # -- 10. Cookie helper summary -------------------------------------------
    print(f"{separator}")
    print("  CookieHelper API summary")
    print(separator)
    print("""
    CookieHelper.set_cookie(response, key, value, max_age, httponly, ...)
    CookieHelper.get_cookie(request, key, default)
    CookieHelper.set_signed_cookie(response, key, value, salt, max_age)
    CookieHelper.get_signed_cookie(request, key, salt, default)

    In C++ (e.g. Crow framework):
        auto val = req.get_cookie_value("theme");          // read
        response.set_cookie("theme", "dark")               // write
                 .max_age(86400)
                 .httponly()
                 .secure();
    """)

    print(separator)
    print("  Demo complete.")
    print(separator)


# ---------------------------------------------------------------------------
# 13. Django view examples (ready to paste into a real project)
# ---------------------------------------------------------------------------

# The following functions are commented-out skeletons that show how the
# helpers above integrate with actual Django views.  Uncomment them inside
# a Django project to use.

"""
# views.py
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from .models import User
from .utils import gen_md5_digest, gen_random_code
from .captcha import Captcha


def get_captcha(request: HttpRequest) -> HttpResponse:
    \"\"\"Generate and return a CAPTCHA image; store code in session.\"\"\"
    captcha_text = gen_random_code()
    request.session['captcha'] = captcha_text
    image_data = Captcha.instance().generate(captcha_text)
    return HttpResponse(image_data, content_type='image/png')


def login(request: HttpRequest) -> HttpResponse:
    hint = ''
    if request.method == 'POST':
        # Optional: test cookie support
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
        else:
            return HttpResponse("Please enable cookies and try again.")

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        captcha_input = request.POST.get('captcha', '').strip()
        captcha_expected = request.session.get('captcha', '')

        if not username or not password:
            hint = 'Please enter valid username and password.'
        elif captcha_input.lower() != captcha_expected.lower():
            hint = 'CAPTCHA incorrect.'
        else:
            password_hash = gen_md5_digest(password)
            user = User.objects.filter(
                username=username, password=password_hash
            ).first()
            if user:
                request.session['userid'] = user.no
                request.session['username'] = user.username
                # Remember-me support
                if request.POST.get('remember_me'):
                    token = RememberMeManager.create_token(user.no)
                    CookieHelper.set_signed_cookie(
                        response=None,  # use redirect response instead
                        key='remember_token',
                        value=token,
                        max_age=86400 * 30,
                    )
                return redirect('/')
            else:
                hint = 'Invalid username or password.'

    request.session.set_test_cookie()
    return render(request, 'login.html', {'hint': hint})


def logout(request: HttpRequest) -> HttpResponse:
    \"\"\"Destroy session and redirect to home.\"\"\"
    # Optionally revoke remember-me token
    token = CookieHelper.get_cookie(request, 'remember_token')
    if token:
        RememberMeManager.revoke_token(token)
    request.session.flush()          # deletes server data + client cookie
    return redirect('/')


def profile(request: HttpRequest) -> HttpResponse:
    \"\"\"Show user profile -- requires login.\"\"\"
    if not request.session.get('userid'):
        return redirect('/login/')
    return render(request, 'profile.html', {
        'username': request.session.get('username'),
    })


def add_to_cart(request: HttpRequest) -> JsonResponse:
    \"\"\"AJAX endpoint: add product to session-based cart.\"\"\"
    product_id = int(request.POST.get('product_id', 0))
    name = request.POST.get('name', '')
    price = float(request.POST.get('price', 0))
    qty = int(request.POST.get('qty', 1))
    ShoppingCart.add_item(request.session, product_id, name, price, qty)
    return JsonResponse({'total': ShoppingCart.total(request.session)})
"""


# ---------------------------------------------------------------------------
# __main__ guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_demo()
