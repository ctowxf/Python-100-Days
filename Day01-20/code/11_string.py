"""
Day 11 - String Data Structure (常用数据结构之字符串)

Comprehensive demonstration of Python string operations, methods, formatting,
encoding/decoding, slicing, and enterprise-grade usage patterns.

C++ Comparison Notes:
    1. Python str is IMMUTABLE -- every "modification" creates a new string object.
       C++ std::string is MUTABLE -- characters can be changed in-place via [] or at().
    2. Python f-string (3.6+) provides inline expression evaluation for formatting.
       C++20 std::format uses compile-time checked format specifiers (similar idea,
       but statically typed and resolved at compile time).
    3. Python strings are always Unicode (UTF-16 or UTF-8 internal representation).
       C++ std::string is a byte container -- encoding is the programmer's burden.
"""


# =============================================================================
# 1. STRING DEFINITION (字符串的定义)
# =============================================================================

def string_definition():
    """Demonstrate various ways to define strings in Python."""
    print("=" * 60)
    print("1. STRING DEFINITION")
    print("=" * 60)

    # Single-quoted and double-quoted strings are identical
    s1 = 'hello, world!'
    s2 = "你好，世界！❤️"
    print(f"s1 = {s1!r}")
    print(f"s2 = {s2!r}")

    # Triple-quoted strings can span multiple lines
    s3 = '''hello,
wonderful
world!'''
    print(f"s3 (multiline):\n{s3}")

    # Escape characters (转义字符)
    s4 = '\'hello, world!\''
    s5 = '\\hello, world!\\'
    print(f"Escaped quotes:  {s4}")
    print(f"Escaped backslash: {s5}")

    # Raw strings (原始字符串) -- no escape processing
    s6 = '\it \is \time \to \read \now'   # \t, \r, \n are escapes
    s7 = r'\it \is \time \to \read \now'  # raw: every char is literal
    print(f"Normal string: {s6}")
    print(f"Raw string:    {s7}")

    # Character representations via octal, hex, and Unicode
    s8 = '\141\142\143\x61\x62\x63'  # octal and hex for 'a','b','c'
    s9 = '骆昊'               # Unicode for Chinese chars
    print(f"Octal/Hex: {s8}")         # abcabc
    print(f"Unicode:   {s9}")         # 骆昊


# =============================================================================
# 2. STRING OPERATIONS (字符串的运算)
# =============================================================================

def string_operations():
    """Demonstrate concatenation, repetition, comparison, membership, indexing."""
    print("\n" + "=" * 60)
    print("2. STRING OPERATIONS")
    print("=" * 60)

    # Concatenation (+) and repetition (*)
    s1 = 'hello' + ', ' + 'world'
    print(f"Concatenation: {s1}")
    s2 = '!' * 3
    print(f"Repetition:    {s2}")
    s1 += s2
    print(f"Augmented +=:  {s1}")
    s1 *= 2
    print(f"Augmented *=:  {s1}")

    # Comparison -- compares Unicode code points character by character
    print("\n--- Comparison ---")
    print(f"'A' < 'a'  => {ord('A')} < {ord('a')}  => {'A' < 'a'}")
    print(f"'boy' < 'bad' => compares 2nd char: 'o'({ord('o')}) vs 'a'({ord('a')}) => {'boy' < 'bad'}")

    # Membership testing (in / not in)
    s3 = 'hello, world'
    print(f"\n--- Membership ---")
    print(f"'wo' in 'hello, world'     => {'wo' in s3}")
    print(f"'xyz' not in 'hello, world' => {'xyz' not in s3}")

    # Length
    print(f"\nlen('hello, world') = {len(s3)}")

    # Indexing and slicing (索引和切片)
    print("\n--- Indexing & Slicing ---")
    s4 = 'abc123456'
    n = len(s4)
    print(f"String: {s4!r}  (len={n})")
    print(f"s4[0]={s4[0]}, s4[-n]={s4[-n]}")
    print(f"s4[n-1]={s4[n-1]}, s4[-1]={s4[-1]}")
    print(f"s4[2:5]   = {s4[2:5]!r}")
    print(f"s4[-7:-4] = {s4[-7:-4]!r}")
    print(f"s4[2:]    = {s4[2:]!r}")
    print(f"s4[:2]    = {s4[:2]!r}")
    print(f"s4[::2]   = {s4[::2]!r}   (every 2nd char)")
    print(f"s4[::-1]  = {s4[::-1]!r}  (reversed)")

    # NOTE: Strings are IMMUTABLE -- s4[0] = 'X' would raise TypeError
    # C++ comparison: std::string s = "abc"; s[0] = 'X'; // perfectly valid in C++


# =============================================================================
# 3. TRAVERSING STRINGS (字符的遍历)
# =============================================================================

def string_traversal():
    """Show two ways to iterate over string characters."""
    print("\n" + "=" * 60)
    print("3. STRING TRAVERSAL")
    print("=" * 60)

    s = 'hello'

    # Method 1: Index-based iteration
    print("Method 1 (index-based):")
    for i in range(len(s)):
        print(f"  s[{i}] = {s[i]!r}")

    # Method 2: Direct element iteration (preferred, Pythonic)
    print("Method 2 (direct iteration):")
    for ch in s:
        print(f"  {ch!r}")


# =============================================================================
# 4. STRING METHODS (字符串的方法)
# =============================================================================

def string_methods():
    """Demonstrate core string methods: case, find, predicate, strip, replace, split/join."""
    print("\n" + "=" * 60)
    print("4. STRING METHODS")
    print("=" * 60)

    # --- Case transformations (大小写) ---
    print("\n--- Case Methods ---")
    s1 = 'hello, world!'
    print(f"Original:     {s1!r}")
    print(f"capitalize(): {s1.capitalize()!r}")
    print(f"title():      {s1.title()!r}")
    print(f"upper():      {s1.upper()!r}")
    s2 = 'GOODBYE'
    print(f"lower():      {s2.lower()!r}")
    # NOTE: Original strings unchanged -- immutability
    print(f"s1 still:     {s1!r}")
    print(f"s2 still:     {s2!r}")

    # --- Find / Index (查找) ---
    print("\n--- Find & Index ---")
    s3 = 'hello, world!'
    print(f"s3.find('or')    = {s3.find('or')}")
    print(f"s3.find('or', 9) = {s3.find('or', 9)}  (not found => -1)")
    print(f"s3.rfind('o')    = {s3.rfind('o')}")
    # s3.index('or', 9) would raise ValueError

    # --- Predicates (性质判断) ---
    print("\n--- Predicates ---")
    s4 = 'abc123456'
    print(f"'{s4}'.startswith('abc') => {s4.startswith('abc')}")
    print(f"'{s4}'.endswith('456')   => {s4.endswith('456')}")
    print(f"'{s4}'.isdigit()         => {s4.isdigit()}")
    print(f"'{s4}'.isalpha()         => {s4.isalpha()}")
    print(f"'{s4}'.isalnum()         => {s4.isalnum()}")

    # --- Strip / Replace ---
    print("\n--- Strip & Replace ---")
    s5 = '   jackfrued@126.com  '
    print(f"strip():  {s5.strip()!r}")
    s6 = '~你好，世界~'
    print(f"lstrip('~'): {s6.lstrip('~')!r}")
    print(f"rstrip('~'): {s6.rstrip('~')!r}")

    s7 = 'hello, good world'
    print(f"replace('o', '@'):     {s7.replace('o', '@')!r}")
    print(f"replace('o', '@', 1):  {s7.replace('o', '@', 1)!r}")

    # --- Split & Join (拆分与合并) ---
    print("\n--- Split & Join ---")
    s8 = 'I love you'
    words = s8.split()
    print(f"split():       {words}")
    print(f"'~'.join():    {'~'.join(words)!r}")

    s9 = 'I#love#you#so#much'
    print(f"split('#'):    {s9.split('#')}")
    print(f"split('#', 2): {s9.split('#', 2)}  (max 2 splits)")


# =============================================================================
# 5. STRING FORMATTING (字符串格式化)
# =============================================================================

def string_formatting():
    """
    Demonstrate all three formatting approaches: %, str.format(), f-string.

    C++ Comparison:
        - Python f-string evaluates arbitrary expressions at runtime.
        - C++20 std::format resolves format specs at compile time with type safety.
        - Python: f"{x:.2f}"  |  C++20: std::format("{:.2f}", x)
    """
    print("\n" + "=" * 60)
    print("5. STRING FORMATTING (% / format / f-string)")
    print("=" * 60)

    a, b = 321, 123

    # %-formatting (oldest style, similar to C printf)
    print(f"\n--- %-format ---")
    print('%d * %d = %d' % (a, b, a * b))

    # str.format()
    print(f"\n--- str.format() ---")
    print('{0} * {1} = {2}'.format(a, b, a * b))

    # f-string (Python 3.6+)
    print(f"\n--- f-string ---")
    print(f'{a} * {b} = {a * b}')

    # Advanced f-string format specifiers
    print(f"\n--- f-string Format Specifiers ---")
    pi = 3.1415926
    print(f"pi = {pi:.2f}       (2 decimal places)")
    print(f"pi = {pi:+.2f}      (with sign)")
    neg = -1
    print(f"neg = {neg:+.2f}     (negative with sign)")
    print(f"pi = {pi:.0f}       (no decimals)")

    num = 123
    print(f"{num:0>10d}   (zero-padded to 10)")
    print(f"{num:x<10d}   (right-padded with x)")
    print(f"{num:>10d}    (right-aligned)")
    print(f"{num:<10d}    (left-aligned)")

    big = 123456789
    print(f"{big:,}      (comma-separated)")
    print(f"{0.123:.2%}     (percent)")
    print(f"{big:.2e}    (scientific)")

    # Alignment helpers: center, ljust, rjust, zfill
    print(f"\n--- Alignment Methods ---")
    s = 'hello, world'
    print(s.center(20, '*'))
    print(s.rjust(20))
    print(s.ljust(20, '~'))
    print('33'.zfill(5))
    print('-33'.zfill(5))


# =============================================================================
# 6. ENCODING & DECODING (编码和解码)
# =============================================================================

def string_encoding():
    """
    Demonstrate encode/decode between str and bytes.

    C++ Comparison:
        - Python str is always Unicode; encode() produces bytes for I/O.
        - C++ std::string is just bytes; you must manually handle encoding.
        - Python: s.encode('utf-8')  |  C++: requires iconv or codecvt
    """
    print("\n" + "=" * 60)
    print("6. ENCODING & DECODING")
    print("=" * 60)

    a = '骆昊'
    b = a.encode('utf-8')
    c = a.encode('gbk')
    print(f"Original:       {a!r}")
    print(f"UTF-8 bytes:    {b}")
    print(f"GBK bytes:      {c}")
    print(f"UTF-8 decode:   {b.decode('utf-8')!r}")
    print(f"GBK decode:     {c.decode('gbk')!r}")

    # Demonstrate encoding/decoding mismatch
    print(f"\n--- Encoding Mismatch ---")
    try:
        c.decode('utf-8')  # GBK bytes decoded as UTF-8 -- will fail
    except UnicodeDecodeError as e:
        print(f"Expected error: {e}")

    # Practical: encode to various formats
    text = 'Hello, 世界!'
    for enc in ('ascii', 'utf-8', 'utf-16', 'latin-1'):
        try:
            encoded = text.encode(enc)
            print(f"  {enc:10s} => {encoded}")
        except UnicodeEncodeError as e:
            print(f"  {enc:10s} => EncodingError: {e}")


# =============================================================================
# 7. ENTERPRISE EXAMPLES (企业级示例)
# =============================================================================

def enterprise_log_formatting():
    """
    Enterprise Example 1: Structured Log Formatting.

    In production systems, log lines must follow a strict format for
    downstream parsing (ELK stack, Splunk, CloudWatch, etc.).
    """
    print("\n" + "=" * 60)
    print("7a. ENTERPRISE: Log Formatting")
    print("=" * 60)

    import datetime

    def format_log_line(level: str, module: str, message: str,
                        user_id: int | None = None,
                        request_id: str | None = None) -> str:
        """Format a structured log line for a log aggregation system."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            '%Y-%m-%dT%H:%M:%S.%fZ'
        )
        parts = [
            f"[{timestamp}]",
            f"[{level.upper():8s}]",
            f"[{module}]",
        ]
        if request_id:
            parts.append(f"[req:{request_id}]")
        if user_id is not None:
            parts.append(f"[user:{user_id}]")
        parts.append(message)
        return ' '.join(parts)

    # Simulate log output
    print(format_log_line('INFO', 'auth', 'User login successful',
                          user_id=42, request_id='abc-123'))
    print(format_log_line('WARN', 'payment', 'Retry attempt 2/3',
                          request_id='pay-456'))
    print(format_log_line('ERROR', 'db', 'Connection timeout after 30s'))
    print(format_log_line('DEBUG', 'cache', 'Cache hit for key=user:42'))


def enterprise_template_engine():
    """
    Enterprise Example 2: Simple Template Engine.

    Many systems use template strings for emails, notifications, and
    report generation. This demonstrates a custom template renderer
    using Python's string methods and f-string concepts.
    """
    print("\n" + "=" * 60)
    print("7b. ENTERPRISE: Template Engine")
    print("=" * 60)

    # Simple template engine using str.format_map and dict
    EMAIL_TEMPLATE = """\
Dear {customer_name},

Thank you for your order #{order_id} placed on {order_date}.

Order Summary:
{order_items}

Total: ${total:.2f}

{promo_message}

Best regards,
{company_name} Support Team"""

    order_data = {
        'customer_name': 'Alice Zhang',
        'order_id': 'ORD-20260602-7891',
        'order_date': '2026-06-02',
        'order_items': '\n'.join([
            '  - Widget Pro x2    $59.98',
            '  - Cable Kit x1     $12.99',
            '  - USB Hub x1       $24.99',
        ]),
        'total': 97.96,
        'promo_message': 'Use code SUMMER20 for 20% off your next purchase!',
        'company_name': 'TechGear',
    }

    rendered = EMAIL_TEMPLATE.format_map(order_data)
    print(rendered)

    # Demonstrate safe template substitution with missing keys
    print("\n--- Safe Template with Defaults ---")

    def safe_format(template: str, defaults: dict, **kwargs) -> str:
        """Format a template, filling missing keys with defaults."""
        merged = {**defaults, **kwargs}
        # Use a custom dict that returns a placeholder for missing keys
        class SafeDict(dict):
            def __missing__(self, key):
                return f'[{key}]'
        return template.format_map(SafeDict(merged))

    notification = "Hello {name}, your {item} is {status}. Ref: {ref}"
    result = safe_format(notification,
                         defaults={'ref': 'N/A', 'status': 'pending'},
                         name='Bob', item='order')
    print(result)


def enterprise_input_sanitization():
    """
    Enterprise Example 3: Input Sanitization.

    User input must be sanitized before use in SQL, HTML, or shell commands.
    This demonstrates string-based sanitization patterns.
    """
    print("\n" + "=" * 60)
    print("7c. ENTERPRISE: Input Sanitization")
    print("=" * 60)

    def sanitize_username(raw_input: str) -> str:
        """Sanitize a username: strip whitespace, remove dangerous chars."""
        s = raw_input.strip()
        # Only allow alphanumeric, underscore, hyphen, dot
        allowed = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-')
        sanitized = ''.join(ch for ch in s if ch in allowed)
        return sanitized[:32]  # enforce max length

    def sanitize_html(raw_input: str) -> str:
        """Basic HTML entity escaping to prevent XSS."""
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
        }
        result = raw_input
        for char, entity in replacements.items():
            result = result.replace(char, entity)
        return result

    # Test sanitization
    test_inputs = [
        '  alice_bob  ',
        'admin<script>alert(1)</script>',
        'user"name"; DROP TABLE--',
        'a' * 100,
    ]

    print("--- Username Sanitization ---")
    for raw in test_inputs:
        clean = sanitize_username(raw)
        print(f"  {raw!r:50s} => {clean!r}")

    print("\n--- HTML Sanitization ---")
    html_tests = [
        '<b>Hello</b>',
        'user@example.com',
        'Tom & Jerry',
        '<img src=x onerror=alert(1)>',
    ]
    for raw in html_tests:
        clean = sanitize_html(raw)
        print(f"  {raw!r:45s} => {clean!r}")


def enterprise_url_parsing():
    """
    Enterprise Example 4: URL Parsing and Manipulation.

    Demonstrates string splitting, joining, and manipulation for
    URL construction and parameter handling.
    """
    print("\n" + "=" * 60)
    print("7d. ENTERPRISE: URL Parsing")
    print("=" * 60)

    def parse_url(url: str) -> dict:
        """Parse a URL into its components using string methods."""
        result = {
            'scheme': '', 'host': '', 'port': '', 'path': '',
            'query': '', 'fragment': '', 'params': {},
        }

        # Split fragment
        if '#' in url:
            url, result['fragment'] = url.split('#', 1)

        # Split scheme
        if '://' in url:
            result['scheme'], url = url.split('://', 1)

        # Split query string
        if '?' in url:
            url, query_str = url.split('?', 1)
            result['query'] = query_str
            # Parse query parameters
            for pair in query_str.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    result['params'][key] = value

        # Split host:port and path
        if '/' in url:
            host_port, result['path'] = url.split('/', 1)
            result['path'] = '/' + result['path']
        else:
            host_port = url

        if ':' in host_port:
            result['host'], result['port'] = host_port.split(':', 1)
        else:
            result['host'] = host_port

        return result

    def build_url(scheme: str, host: str, path: str = '/',
                  port: str = '', params: dict | None = None,
                  fragment: str = '') -> str:
        """Build a URL from components."""
        url = f"{scheme}://{host}"
        if port:
            url += f":{port}"
        url += path
        if params:
            query = '&'.join(f"{k}={v}" for k, v in params.items())
            url += f"?{query}"
        if fragment:
            url += f"#{fragment}"
        return url

    # Parse example URLs
    test_urls = [
        'https://api.example.com:8443/v1/users?page=1&limit=20#section1',
        'http://localhost:3000/dashboard',
        'https://search.example.org/q?term=python+strings&lang=en',
    ]

    print("--- URL Parsing ---")
    for url in test_urls:
        parsed = parse_url(url)
        print(f"  URL: {url}")
        for key in ('scheme', 'host', 'port', 'path', 'params', 'fragment'):
            print(f"    {key:10s}: {parsed[key]}")
        print()

    # Build URL
    print("--- URL Building ---")
    built = build_url(
        scheme='https',
        host='api.myservice.com',
        path='/v2/orders',
        port='443',
        params={'status': 'active', 'page': '3'},
        fragment='results',
    )
    print(f"  Built: {built}")


# =============================================================================
# 8. C++ COMPARISON SUMMARY
# =============================================================================

def cpp_comparison_summary():
    """
    Summarize key differences between Python strings and C++ std::string.
    """
    print("\n" + "=" * 60)
    print("8. C++ COMPARISON SUMMARY")
    print("=" * 60)

    comparisons = [
        ("Mutability",
         "Python str is IMMUTABLE -- every modification creates a new object.",
         "C++ std::string is MUTABLE -- characters can be changed in-place via operator[] or at()."),

        ("Formatting",
         "Python f-string (3.6+) evaluates expressions at runtime: f'{x:.2f}'",
         "C++20 std::format uses compile-time type-checked specs: std::format(\"{:.2f}\", x)"),

        ("Unicode",
         "Python str is always Unicode internally; encoding is explicit via .encode().",
         "C++ std::string is a byte container; encoding is the programmer's responsibility."),

        ("Concatenation",
         "Python: s1 + s2 creates a new string (O(n+m)). Use ''.join() for efficiency.",
         "C++: s1 += s2 appends in-place (amortized O(1) per char with SSO)."),

        ("Slicing",
         "Python: s[2:5] returns a new substring (O(k) copy).",
         "C++: s.substr(2, 3) returns a new string (O(k) copy)."),

        ("Immutability Workaround",
         "Python: convert to list, modify, then ''.join(list).",
         "C++: direct mutation is native; no workaround needed."),
    ]

    for topic, py_note, cpp_note in comparisons:
        print(f"\n  [{topic}]")
        print(f"    Python: {py_note}")
        print(f"    C++:    {cpp_note}")


# =============================================================================
# 9. ADDITIONAL PRACTICAL EXAMPLES
# =============================================================================

def practical_extras():
    """Additional practical patterns for real-world Python string usage."""
    print("\n" + "=" * 60)
    print("9. ADDITIONAL PRACTICAL PATTERNS")
    print("=" * 60)

    # 9a. String building efficiency: join vs concatenation
    print("\n--- Efficient String Building ---")
    # Bad: O(n^2) due to immutability
    # result = ''
    # for i in range(1000):
    #     result += str(i)  # creates a new string each time

    # Good: O(n) using join
    parts = [str(i) for i in range(10)]
    result = ', '.join(parts)
    print(f"Join result: {result}")

    # 9b. Multi-line alignment for reports
    print("\n--- Report Table Formatting ---")
    header = f"{'Name':<15} {'Department':<12} {'Salary':>10}"
    separator = '-' * len(header)
    rows = [
        ('Alice Zhang', 'Engineering', 125000),
        ('Bob Li', 'Marketing', 98000),
        ('Charlie Wu', 'Engineering', 132000),
        ('Diana Chen', 'Sales', 87000),
    ]
    print(header)
    print(separator)
    for name, dept, salary in rows:
        print(f"{name:<15} {dept:<12} ${salary:>9,}")
    print(separator)

    # 9c. Password strength checker using string methods
    print("\n--- Password Strength Checker ---")

    def check_password_strength(password: str) -> tuple[bool, list[str]]:
        issues = []
        if len(password) < 8:
            issues.append("Too short (minimum 8 characters)")
        if not any(c.isupper() for c in password):
            issues.append("Missing uppercase letter")
        if not any(c.islower() for c in password):
            issues.append("Missing lowercase letter")
        if not any(c.isdigit() for c in password):
            issues.append("Missing digit")
        special = set('!@#$%^&*()_+-=[]{}|;:,.<>?')
        if not any(c in special for c in password):
            issues.append("Missing special character")
        return (len(issues) == 0, issues)

    test_passwords = ['abc', 'abcdefgh', 'Abc12345', 'Abc123!@', 'Str0ng!Pass#2026']
    for pwd in test_passwords:
        strong, issues = check_password_strength(pwd)
        status = 'STRONG' if strong else f'WEAK: {"; ".join(issues)}'
        print(f"  {pwd!r:22s} => {status}")

    # 9d. CSV-like parsing with split
    print("\n--- CSV-like Parsing ---")
    csv_line = 'Alice,30,Engineer,"New York, NY",active'
    # Simple CSV parser (doesn't handle all edge cases -- use csv module in production)
    def simple_csv_split(line: str, delimiter: str = ',') -> list[str]:
        fields = []
        current = []
        in_quotes = False
        for ch in line:
            if ch == '"':
                in_quotes = not in_quotes
            elif ch == delimiter and not in_quotes:
                fields.append(''.join(current))
                current = []
            else:
                current.append(ch)
        fields.append(''.join(current))
        return fields

    parsed = simple_csv_split(csv_line)
    print(f"  Input:  {csv_line}")
    print(f"  Fields: {parsed}")


# =============================================================================
# MAIN GUARD
# =============================================================================

if __name__ == '__main__':
    string_definition()
    string_operations()
    string_traversal()
    string_methods()
    string_formatting()
    string_encoding()
    enterprise_log_formatting()
    enterprise_template_engine()
    enterprise_input_sanitization()
    enterprise_url_parsing()
    cpp_comparison_summary()
    practical_extras()
