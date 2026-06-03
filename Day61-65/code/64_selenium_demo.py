"""
Day 64 - 使用Selenium抓取网页动态内容 (Scraping Dynamic Web Content with Selenium)

This module demonstrates comprehensive Selenium WebDriver usage for automating
web browsers, finding elements, handling waits, executing JavaScript, and
building enterprise-grade scraping and automation tools.

Requirements:
    pip install selenium requests
    Chrome browser + matching ChromeDriver installed and on PATH

Topics Covered:
    1. Selenium basics and WebDriver setup
    2. Locating elements (By.ID, By.CSS_SELECTOR, By.XPATH, etc.)
    3. Implicit and explicit waits
    4. Executing JavaScript in the browser
    5. Anti-detection techniques
    6. Headless browsing
    7. Enterprise examples: dynamic page scraper, form automation, screenshot tool

================================================================================
Python Selenium vs C++ Selenium WebDriver Bindings
================================================================================

| Aspect                   | Python Selenium                         | C++ Selenium (via WebDriver bindings)    |
|--------------------------|-----------------------------------------|------------------------------------------|
| Language ecosystem       | Rich (requests, pandas, bs4, scrapy)    | Limited; must link C++ HTTP/JSON libs    |
| Ease of use              | Concise, dynamic typing, rapid dev      | Verbose, manual memory management        |
| Performance              | Adequate for I/O-bound web scraping     | Faster CPU-bound processing              |
| Binding maturity         | Official Selenium client, well-maintained| Community-maintained; less documentation |
| Async support            | Via selenium-wire, asyncio wrappers     | Possible but requires manual event loops |
| Setup complexity         | pip install selenium                    | Build system (CMake), link headers, etc. |
| Integration              | Easy with data science / ML pipelines   | Better for embedded / system-level tools |
| Typical use case         | Web scraping, testing, automation       | Performance-critical browser automation  |

Python is the dominant choice for Selenium automation due to its concise syntax,
massive ecosystem, and rapid prototyping ability. C++ bindings exist but are
rarely used for web scraping -- they appear mainly in performance-critical
testing frameworks or when embedding a browser controller in a C++ application.

Key Python Selenium advantages:
    - One-liner element interactions vs multi-line C++ equivalents
    - Built-in support for expected conditions and wait strategies
    - Seamless integration with data processing libraries
    - Extensive community examples and StackOverflow coverage

Key C++ Selenium advantages:
    - Lower latency per WebDriver command (negligible in practice)
    - Direct memory control for long-running browser pools
    - Integration into C++ desktop applications
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =========================================================================
# Section 1: Selenium Basics - Browser Setup and Configuration
# =========================================================================

def create_chrome_driver(
    headless: bool = False,
    driver_path: Optional[str] = None,
    window_size: tuple[int, int] = (1280, 900),
    anti_detect: bool = False,
    download_dir: Optional[str] = None,
) -> webdriver.Chrome:
    """Create and configure a Chrome WebDriver instance.

    Args:
        headless: Run Chrome without a visible browser window.
        driver_path: Explicit path to chromedriver executable.
            If None, Selenium looks on the system PATH.
        window_size: (width, height) for the browser window.
        anti_detect: Apply stealth options to avoid bot detection.
        download_dir: Directory for automatic file downloads.

    Returns:
        A configured Chrome WebDriver instance.

    Example (C++ equivalent):
        // C++ requires explicit Service creation and option structs
        // WebDriver* driver = new ChromeDriver(service, options);
        // driver->Get("https://example.com");
    """
    options = ChromeOptions()

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")

    options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Anti-detection: hide "Chrome is being controlled by automated software"
    if anti_detect:
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

    # Custom download directory
    if download_dir:
        prefs = {
            "download.default_directory": os.path.abspath(download_dir),
            "download.prompt_for_download": False,
        }
        options.add_experimental_option("prefs", prefs)

    service = ChromeService(executable_path=driver_path) if driver_path else None

    driver = webdriver.Chrome(service=service, options=options)

    # Apply anti-detection CDP command after driver creation
    if anti_detect:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'},
        )

    logger.info("Chrome WebDriver created (headless=%s, anti_detect=%s)", headless, anti_detect)
    return driver


# =========================================================================
# Section 2: Element Finding Strategies
# =========================================================================

class ElementFinder:
    """Utility class demonstrating all Selenium element-finding strategies.

    Selenium supports multiple locator strategies via the By class:
        By.ID, By.NAME, By.CLASS_NAME, By.TAG_NAME,
        By.CSS_SELECTOR, By.XPATH, By.LINK_TEXT, By.PARTIAL_LINK_TEXT

    In Python:
        element = driver.find_element(By.ID, "my-id")

    In C++ (Selenium bindings):
        WebElement element = driver->FindElement(By::Id("my-id"));
        // Note: C++ uses By::Id() function calls, not enum constants.
    """

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver

    def by_id(self, element_id: str) -> WebElement:
        """Find element by its HTML id attribute."""
        return self._driver.find_element(By.ID, element_id)

    def by_name(self, name: str) -> WebElement:
        """Find element by its name attribute."""
        return self._driver.find_element(By.NAME, name)

    def by_class_name(self, class_name: str) -> WebElement:
        """Find element by CSS class name."""
        return self._driver.find_element(By.CLASS_NAME, class_name)

    def by_tag_name(self, tag: str) -> WebElement:
        """Find element by HTML tag name (e.g. 'div', 'input')."""
        return self._driver.find_element(By.TAG_NAME, tag)

    def by_css(self, selector: str) -> WebElement:
        """Find element by CSS selector."""
        return self._driver.find_element(By.CSS_SELECTOR, selector)

    def by_xpath(self, xpath: str) -> WebElement:
        """Find element by XPath expression."""
        return self._driver.find_element(By.XPATH, xpath)

    def by_link_text(self, text: str) -> WebElement:
        """Find <a> element by its exact visible text."""
        return self._driver.find_element(By.LINK_TEXT, text)

    def by_partial_link_text(self, text: str) -> WebElement:
        """Find <a> element by partial visible text."""
        return self._driver.find_element(By.PARTIAL_LINK_TEXT, text)

    def all_by_css(self, selector: str) -> list[WebElement]:
        """Find all elements matching a CSS selector."""
        return self._driver.find_elements(By.CSS_SELECTOR, selector)

    def all_by_xpath(self, xpath: str) -> list[WebElement]:
        """Find all elements matching an XPath expression."""
        return self._driver.find_elements(By.XPATH, xpath)


# =========================================================================
# Section 3: Implicit and Explicit Waits
# =========================================================================

class WaitHelper:
    """Demonstrates Selenium wait strategies.

    Two types of waits in Selenium:
        1. Implicit wait: driver.implicitly_wait(seconds)
           - Sets a global timeout for all find_element calls.
           - Polls the DOM for the specified duration if element not found.

        2. Explicit wait: WebDriverWait(driver, timeout).until(condition)
           - Waits for a specific condition to be true.
           - More flexible and recommended for dynamic content.

    C++ comparison:
        driver->manage().timeouts().implicitlyWait(seconds);
        // Explicit waits in C++ require manual polling loops or
        // third-party libraries; no built-in WebDriverWait equivalent
        // in some C++ bindings.
    """

    # Common expected conditions mapped to readable names
    CONDITIONS: dict[str, Callable] = {
        "title_is": EC.title_is,
        "title_contains": EC.title_contains,
        "presence_of_element": EC.presence_of_element_located,
        "visibility_of_element": EC.visibility_of_element_located,
        "invisibility_of_element": EC.invisibility_of_element_located,
        "presence_of_all_elements": EC.presence_of_all_elements_located,
        "text_to_be_present": EC.text_to_be_present_in_element,
        "element_to_be_clickable": EC.element_to_be_clickable,
        "alert_is_present": EC.alert_is_present,
        "frame_to_be_available": EC.frame_to_be_available_and_switch_to_it,
    }

    def __init__(self, driver: WebDriver, default_timeout: float = 10) -> None:
        self._driver = driver
        self._default_timeout = default_timeout

    def set_implicit_wait(self, seconds: float) -> None:
        """Set the implicit wait timeout for all element lookups.

        After this call, every find_element / find_elements call will
        poll for up to `seconds` before raising NoSuchElementException.
        """
        self._driver.implicitly_wait(seconds)
        logger.info("Implicit wait set to %.1f seconds", seconds)

    def wait_for_element(
        self,
        locator: tuple[str, str],
        timeout: Optional[float] = None,
        condition: str = "presence_of_element",
    ) -> WebElement:
        """Explicitly wait until a condition is met for the given locator.

        Args:
            locator: A (By.X, "value") tuple, e.g. (By.ID, "kw").
            timeout: Max seconds to wait. Uses default if None.
            condition: Name of the expected condition to use.

        Returns:
            The WebElement once the condition is satisfied.

        Raises:
            TimeoutException: If the condition is not met within timeout.
        """
        timeout = timeout or self._default_timeout
        cond_func = self.CONDITIONS.get(condition)
        if cond_func is None:
            raise ValueError(f"Unknown wait condition: {condition}")

        wait = WebDriverWait(self._driver, timeout)
        element = wait.until(cond_func(locator))
        logger.debug("Wait condition '%s' satisfied for %s", condition, locator)
        return element

    def wait_for_clickable(
        self, locator: tuple[str, str], timeout: Optional[float] = None
    ) -> WebElement:
        """Wait until an element is both present and clickable."""
        return self.wait_for_element(locator, timeout, condition="element_to_be_clickable")

    def wait_for_text(
        self,
        locator: tuple[str, str],
        text: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """Wait until the specified text appears inside the element."""
        timeout = timeout or self._default_timeout
        wait = WebDriverWait(self._driver, timeout)
        result = wait.until(EC.text_to_be_present_in_element(locator, text))
        logger.debug("Text '%s' found in %s", text, locator)
        return result

    def wait_for_title(self, title: str, timeout: Optional[float] = None) -> bool:
        """Wait until the page title matches exactly."""
        timeout = timeout or self._default_timeout
        wait = WebDriverWait(self._driver, timeout)
        return wait.until(EC.title_is(title))

    def wait_for_js_condition(
        self, js_expression: str, timeout: Optional[float] = None
    ) -> Any:
        """Wait until a JavaScript expression returns a truthy value.

        Useful for custom conditions not covered by expected_conditions.
        Example: "return document.readyState === 'complete'"
        """
        timeout = timeout or self._default_timeout
        wait = WebDriverWait(self._driver, timeout)
        return wait.until(lambda driver: driver.execute_script(js_expression))


# =========================================================================
# Section 4: JavaScript Execution
# =========================================================================

class JSExecutor:
    """Utility for executing JavaScript within the browser context.

    Selenium's execute_script() runs synchronous JS in the page context.
    Use this for:
        - Scrolling (infinite scroll / lazy loading)
        - Modifying DOM elements
        - Extracting data not accessible via WebElement
        - Overriding browser properties (anti-detection)

    C++ comparison:
        driver->ExecuteScript("return document.title;");
        // Same API in C++, but return values must be cast manually.
    """

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver

    def execute(self, script: str, *args: Any) -> Any:
        """Execute synchronous JavaScript and return the result.

        Args:
            script: JavaScript code to execute.
            *args: Arguments accessible as arguments[0], arguments[1], etc.

        Returns:
            The value returned by the JavaScript code.
        """
        return self._driver.execute_script(script, *args)

    def scroll_to_bottom(self) -> None:
        """Scroll the page to the very bottom (useful for infinite scroll)."""
        self.execute(
            "document.documentElement.scrollTop = document.documentElement.scrollHeight"
        )
        logger.debug("Scrolled to page bottom")

    def scroll_to_element(self, element: WebElement) -> None:
        """Scroll the viewport to bring an element into view."""
        self.execute("arguments[0].scrollIntoView(true);", element)

    def scroll_by(self, x: int = 0, y: int = 500) -> None:
        """Scroll the page by (x, y) pixels."""
        self.execute(f"window.scrollBy({x}, {y});")

    def get_page_height(self) -> int:
        """Return total scrollable page height in pixels."""
        return int(self.execute("return document.documentElement.scrollHeight"))

    def remove_attribute(self, element: WebElement, attribute: str) -> None:
        """Remove an attribute from a DOM element."""
        self.execute(f"arguments[0].removeAttribute('{attribute}');", element)

    def set_attribute(self, element: WebElement, attr: str, value: str) -> None:
        """Set an attribute on a DOM element."""
        self.execute(
            f"arguments[0].setAttribute('{attr}', '{value}');", element
        )

    def highlight_element(self, element: WebElement, color: str = "yellow") -> None:
        """Highlight an element with a colored border (debugging aid)."""
        self.execute(
            f"arguments[0].style.border='3px solid {color}';", element
        )

    def get_inner_text(self) -> str:
        """Return all visible text on the page."""
        return str(self.execute("return document.body.innerText;"))

    def override_webdriver_property(self) -> None:
        """Set navigator.webdriver to undefined (anti-detection)."""
        self._driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'},
        )
        logger.info("navigator.webdriver set to undefined")


# =========================================================================
# Section 5: Enterprise Example - Dynamic Page Scraper
# =========================================================================

@dataclass
class ScrapedItem:
    """Represents a single item scraped from a dynamic web page."""
    title: str
    url: str
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())


class DynamicPageScraper:
    """Enterprise-grade scraper for JavaScript-rendered pages.

    Features:
        - Handles infinite scroll / pagination
        - Configurable wait strategies
        - Anti-detection options
        - Structured data output
        - Error handling and retry logic

    C++ comparison:
        Building this in C++ would require:
        1. Linking Selenium C++ WebDriver library
        2. Manual HTTP session management
        3. JSON parsing library (e.g., nlohmann/json)
        4. String encoding handling (UTF-8 conversion)
        Python handles all of this natively with minimal code.
    """

    def __init__(
        self,
        base_url: str,
        headless: bool = True,
        anti_detect: bool = True,
        max_scroll_attempts: int = 20,
        scroll_pause: float = 1.5,
    ) -> None:
        self.base_url = base_url
        self.headless = headless
        self.anti_detect = anti_detect
        self.max_scroll_attempts = max_scroll_attempts
        self.scroll_pause = scroll_pause
        self._driver: Optional[WebDriver] = None
        self._items: list[ScrapedItem] = []

    def __enter__(self) -> DynamicPageScraper:
        self._driver = create_chrome_driver(
            headless=self.headless, anti_detect=self.anti_detect
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Quit the browser and release resources."""
        if self._driver:
            self._driver.quit()
            self._driver = None
            logger.info("Browser closed")

    @property
    def driver(self) -> WebDriver:
        if self._driver is None:
            raise RuntimeError("Scraper not initialized. Use 'with' statement or call start().")
        return self._driver

    def load_page(self, url: Optional[str] = None) -> None:
        """Navigate to the target URL and wait for initial load."""
        target = url or self.base_url
        self.driver.get(target)
        self.driver.implicitly_wait(10)
        logger.info("Loaded page: %s (title: %s)", target, self.driver.title)

    def scroll_and_load_all(self) -> None:
        """Scroll down repeatedly to trigger lazy-loaded content."""
        js = JSExecutor(self.driver)
        prev_height = 0

        for attempt in range(self.max_scroll_attempts):
            js.scroll_to_bottom()
            time.sleep(self.scroll_pause)
            new_height = js.get_page_height()
            logger.debug(
                "Scroll attempt %d: height %d -> %d", attempt + 1, prev_height, new_height
            )
            if new_height == prev_height:
                logger.info("No new content after scroll attempt %d", attempt + 1)
                break
            prev_height = new_height

    def extract_items(
        self,
        container_selector: str,
        title_selector: str = "h2",
        link_selector: str = "a",
        desc_selector: str = "p",
    ) -> list[ScrapedItem]:
        """Extract structured data from loaded page content.

        Args:
            container_selector: CSS selector for each item container.
            title_selector: CSS selector (relative to container) for the title.
            link_selector: CSS selector (relative to container) for the link.
            desc_selector: CSS selector (relative to container) for description.

        Returns:
            List of ScrapedItem objects.
        """
        finder = ElementFinder(self.driver)
        containers = finder.all_by_css(container_selector)
        items: list[ScrapedItem] = []

        for container in containers:
            try:
                title_el = container.find_element(By.CSS_SELECTOR, title_selector)
                title = title_el.text.strip()

                link_el = container.find_element(By.CSS_SELECTOR, link_selector)
                url = link_el.get_attribute("href") or ""

                desc = ""
                try:
                    desc_el = container.find_element(By.CSS_SELECTOR, desc_selector)
                    desc = desc_el.text.strip()
                except Exception:
                    pass  # Description is optional

                items.append(ScrapedItem(title=title, url=url, description=desc))
            except Exception as e:
                logger.warning("Failed to extract item: %s", e)

        self._items = items
        logger.info("Extracted %d items from page", len(items))
        return items

    def save_results(self, output_path: str) -> None:
        """Save scraped items to a JSON file."""
        data = [
            {
                "title": item.title,
                "url": item.url,
                "description": item.description,
                "metadata": item.metadata,
                "scraped_at": item.scraped_at,
            }
            for item in self._items
        ]
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Saved %d items to %s", len(data), output_path)


# =========================================================================
# Section 6: Enterprise Example - Form Automation
# =========================================================================

@dataclass
class FormField:
    """Describes a field in a web form for automated filling."""
    locator: tuple[str, str]
    value: str
    field_type: str = "text"  # text, select, checkbox, radio, file


class FormAutomator:
    """Automates filling and submitting web forms.

    Supports text inputs, dropdowns, checkboxes, radio buttons,
    and file uploads. Designed for repeated form submissions
    (e.g., registration flows, data entry, testing).

    C++ comparison:
        In C++, each send_keys / click / select call maps to:
            element->SendKeys("value");
            element->Click();
        Select dropdown handling requires the Select helper class
        which exists in C++ but with less ergonomic API.
    """

    def __init__(self, driver: WebDriver) -> None:
        self._driver = driver
        self._wait = WaitHelper(driver)
        self._finder = ElementFinder(driver)

    def fill_field(self, field: FormField) -> None:
        """Fill a single form field based on its type.

        Args:
            field: FormField describing the locator, value, and type.

        Raises:
            ValueError: If field_type is not supported.
        """
        element = self._wait.wait_for_element(
            field.locator, condition="element_to_be_clickable"
        )

        if field.field_type == "text":
            element.clear()
            element.send_keys(field.value)
        elif field.field_type == "select":
            from selenium.webdriver.support.ui import Select
            select = Select(element)
            select.select_by_visible_text(field.value)
        elif field.field_type == "checkbox":
            if field.value.lower() in ("true", "1", "yes"):
                if not element.is_selected():
                    element.click()
            else:
                if element.is_selected():
                    element.click()
        elif field.field_type == "radio":
            element.click()
        elif field.field_type == "file":
            element.send_keys(os.path.abspath(field.value))
        else:
            raise ValueError(f"Unsupported field type: {field.field_type}")

        logger.debug("Filled field %s (%s)", field.locator, field.field_type)

    def fill_form(self, fields: Sequence[FormField]) -> None:
        """Fill multiple form fields in order."""
        for i, field in enumerate(fields, 1):
            try:
                self.fill_field(field)
                logger.info("Field %d/%d filled successfully", i, len(fields))
            except Exception as e:
                logger.error("Failed to fill field %d: %s", i, e)
                raise

    def submit(self, submit_locator: tuple[str, str] = (By.CSS_SELECTOR, "button[type=submit], input[type=submit]")) -> None:
        """Click the submit button."""
        button = self._wait.wait_for_clickable(submit_locator)
        button.click()
        logger.info("Form submitted")

    def get_validation_errors(self, error_selector: str = ".error, .invalid-feedback, [class*=error]") -> list[str]:
        """Collect validation error messages displayed after submission."""
        errors = self._finder.all_by_css(error_selector)
        messages = [el.text.strip() for el in errors if el.text.strip()]
        logger.info("Found %d validation errors", len(messages))
        return messages


# =========================================================================
# Section 7: Enterprise Example - Screenshot Tool
# =========================================================================

class ScreenshotTool:
    """Captures screenshots of web pages with various options.

    Supports full-page screenshots, element-specific captures,
    viewport-only screenshots, and batch screenshot workflows.

    C++ comparison:
        driver->GetScreenshotAs(OutputType::FILE, "screenshot.png");
        element->GetScreenshotAs(OutputType::FILE, "element.png");
        // Same concept in C++, but Python's file I/O is simpler.
    """

    def __init__(self, driver: WebDriver, output_dir: str = "screenshots") -> None:
        self._driver = driver
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def capture_viewport(self, filename: Optional[str] = None) -> str:
        """Take a screenshot of the current viewport.

        Returns:
            Path to the saved screenshot file.
        """
        filename = filename or f"viewport_{self._timestamp()}.png"
        filepath = self._output_dir / filename
        self._driver.save_screenshot(str(filepath))
        logger.info("Viewport screenshot saved: %s", filepath)
        return str(filepath)

    def capture_element(
        self, element: WebElement, filename: Optional[str] = None
    ) -> str:
        """Take a screenshot of a specific element.

        Returns:
            Path to the saved screenshot file.
        """
        filename = filename or f"element_{self._timestamp()}.png"
        filepath = self._output_dir / filename
        element.screenshot(str(filepath))
        logger.info("Element screenshot saved: %s", filepath)
        return str(filepath)

    def capture_full_page(self, filename: Optional[str] = None) -> str:
        """Capture the full page by stitching viewport-sized screenshots.

        Scrolls through the page, captures each viewport, and returns
        the path to the final stitched image (requires Pillow for true
        stitching; this version saves the last viewport as a placeholder).

        Returns:
            Path to the saved screenshot file.
        """
        js = JSExecutor(self._driver)
        filename = filename or f"fullpage_{self._timestamp()}.png"

        # Scroll to top first
        js.execute("window.scrollTo(0, 0)")
        time.sleep(0.5)

        # For a true full-page capture, we would need Pillow to stitch images.
        # Here we use Chrome DevTools Protocol for full-page capture.
        metrics = self._driver.execute_cdp_cmd(
            "Page.getLayoutMetrics", {}
        )
        content_size = metrics.get("contentSize", metrics.get("cssContentSize", {}))
        width = content_size.get("width", 1280)
        height = content_size.get("height", 800)

        self._driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "mobile": False,
                "width": width,
                "height": height,
                "deviceScaleFactor": 1,
            },
        )

        filepath = self._output_dir / filename
        screenshot_data = self._driver.execute_cdp_cmd(
            "Page.captureScreenshot",
            {"format": "png", "captureBeyondViewport": True},
        )

        import base64
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(screenshot_data["data"]))

        # Reset viewport
        self._driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})

        logger.info("Full page screenshot saved: %s", filepath)
        return str(filepath)

    def capture_pages(self, urls: list[str], prefix: str = "page") -> list[str]:
        """Capture screenshots of multiple pages.

        Args:
            urls: List of URLs to screenshot.
            prefix: Filename prefix for each screenshot.

        Returns:
            List of file paths to saved screenshots.
        """
        paths: list[str] = []
        for i, url in enumerate(urls, 1):
            try:
                self._driver.get(url)
                time.sleep(2)  # Allow page to render
                path = self.capture_viewport(f"{prefix}_{i}_{self._timestamp()}.png")
                paths.append(path)
            except Exception as e:
                logger.error("Failed to capture %s: %s", url, e)
        return paths

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")


# =========================================================================
# Section 8: Practical Demo Functions
# =========================================================================

def demo_baidu_search() -> None:
    """Demonstrate basic Selenium: open Baidu, search, and screenshot.

    This mirrors the example from the Day 64 tutorial document.
    """
    driver = create_chrome_driver(headless=False, anti_detect=True)
    wait = WaitHelper(driver)
    js = JSExecutor(driver)

    try:
        driver.set_window_size(1200, 800)
        driver.get("https://www.baidu.com/")

        # Find search input and type query
        kw_input = wait.wait_for_element((By.ID, "kw"), condition="element_to_be_clickable")
        kw_input.send_keys("Python")

        # Find and click search button
        su_button = wait.wait_for_clickable((By.CSS_SELECTOR, "#su"))
        su_button.click()

        # Wait for search results to appear
        wait.wait_for_element(
            (By.CSS_SELECTOR, "#content_left"),
            condition="presence_of_element",
        )

        # Scroll down to load more results
        js.scroll_to_bottom()

        # Take screenshot of results
        screenshot_tool = ScreenshotTool(driver)
        path = screenshot_tool.capture_viewport("baidu_python_results.png")
        logger.info("Baidu search demo complete. Screenshot: %s", path)

    finally:
        driver.quit()


def demo_form_filling() -> None:
    """Demonstrate form automation with FormAutomator.

    Uses a public test form for safe demonstration.
    """
    driver = create_chrome_driver(headless=True, anti_detect=True)

    try:
        driver.get("https://httpbin.org/forms/post")

        automator = FormAutomator(driver)
        fields = [
            FormField(locator=(By.NAME, "custname"), value="Zhang San", field_type="text"),
            FormField(locator=(By.NAME, "custtel"), value="13800138000", field_type="text"),
            FormField(locator=(By.NAME, "custemail"), value="zhangsan@example.com", field_type="text"),
            FormField(locator=(By.NAME, "size"), value="medium", field_type="radio"),
            FormField(locator=(By.NAME, "topping"), value="cheese", field_type="checkbox"),
            FormField(locator=(By.NAME, "delivery"), value="11:00", field_type="text"),
            FormField(locator=(By.NAME, "comments"), value="No onions please", field_type="text"),
        ]

        automator.fill_form(fields)
        logger.info("Form filling demo complete")

    finally:
        driver.quit()


def demo_screenshot_collection() -> None:
    """Demonstrate batch screenshot capture of multiple pages."""
    urls = [
        "https://www.python.org",
        "https://selenium.dev",
        "https://pypi.org",
    ]

    driver = create_chrome_driver(headless=True)

    try:
        tool = ScreenshotTool(driver, output_dir="screenshots/demo")
        paths = tool.capture_pages(urls, prefix="demo")
        logger.info("Captured %d screenshots: %s", len(paths), paths)
    finally:
        driver.quit()


def demo_infinite_scroll_scraping() -> None:
    """Demonstrate scraping a page with infinite scroll behavior.

    This pattern is common for social media feeds, image galleries,
    and news sites that load content as the user scrolls.
    """
    driver = create_chrome_driver(headless=True, anti_detect=True)
    js = JSExecutor(driver)

    try:
        driver.get("https://quotes.toscrape.com/js/")
        driver.implicitly_wait(10)

        quotes_data: list[dict[str, str]] = []
        prev_count = 0

        for scroll_round in range(5):
            js.scroll_to_bottom()
            time.sleep(1.5)

            quotes = driver.find_elements(By.CSS_SELECTOR, ".quote")
            for quote in quotes[prev_count:]:
                text_el = quote.find_element(By.CSS_SELECTOR, ".text")
                author_el = quote.find_element(By.CSS_SELECTOR, ".author")
                quotes_data.append({
                    "text": text_el.text,
                    "author": author_el.text,
                })

            prev_count = len(quotes)
            logger.info("Scroll %d: %d quotes collected", scroll_round + 1, len(quotes_data))

        logger.info("Total quotes scraped: %d", len(quotes_data))

    finally:
        driver.quit()


# =========================================================================
# Section 9: WebElement Interaction Reference
# =========================================================================

def element_interaction_reference(element: WebElement) -> None:
    """Reference guide for common WebElement interactions.

    This function documents the full WebElement API for quick reference.
    It is not meant to be called directly.

    WebElement Attributes:
        element.text             - Visible text content
        element.tag_name         - HTML tag (e.g., 'div', 'input')
        element.id               - Internal Selenium element ID
        element.location         - {'x': int, 'y': int} position
        element.size             - {'width': int, 'height': int}
        element.rect             - Combined location + size

    WebElement Methods:
        element.click()                         - Click the element
        element.clear()                         - Clear input field
        element.send_keys("text")               - Type text into element
        element.submit()                        - Submit the containing form
        element.get_attribute("href")           - Get HTML attribute value
        element.get_property("checked")         - Get DOM property value
        element.get_dom_attribute("class")      - Get original HTML attribute
        element.value_of_css_property("color")  - Get computed CSS value
        element.is_displayed()                  - True if visible to user
        element.is_enabled()                    - True if interactive
        element.is_selected()                   - True if checked/selected
        element.screenshot("el.png")            - Save element screenshot

    Child Element Finding:
        element.find_element(By.ID, "child")        - Find single child
        element.find_elements(By.TAG_NAME, "li")    - Find all children
    """
    # This function exists as documentation; no executable code needed.
    pass


# =========================================================================
# Main Entry Point
# =========================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Day 64: Selenium Web Scraping Demonstrations")
    print("=" * 70)
    print()
    print("Available demos:")
    print("  1. demo_baidu_search()         - Search Baidu and screenshot")
    print("  2. demo_form_filling()          - Automated form submission")
    print("  3. demo_screenshot_collection() - Batch page screenshots")
    print("  4. demo_infinite_scroll_scraping() - Infinite scroll handling")
    print()
    print("Key classes:")
    print("  - ElementFinder: All By.* locator strategies")
    print("  - WaitHelper:    Implicit and explicit wait utilities")
    print("  - JSExecutor:    JavaScript execution helpers")
    print("  - DynamicPageScraper: Enterprise scraper with scroll support")
    print("  - FormAutomator: Multi-field form filling")
    print("  - ScreenshotTool: Viewport, element, and full-page captures")
    print()
    print("To run a demo, call the function directly, e.g.:")
    print("  python 64_selenium_demo.py")
    print()
    print("Note: Demos require Chrome browser and chromedriver on PATH.")
    print("Some demos use headless mode; Baidu demo opens a visible window.")
    print()
    print("C++ comparison: Python Selenium bindings offer concise syntax,")
    print("rich ecosystem integration, and faster development time.")
    print("C++ bindings are suited for performance-critical or embedded use.")
