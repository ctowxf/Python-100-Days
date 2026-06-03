"""
Day 21 - File I/O and Exception Handling
=========================================

Covers:
    - Text and binary file read/write
    - try / except / else / finally / raise
    - Context managers (__enter__, __exit__, contextlib)
    - Custom exception hierarchies
    - "Python with vs C++ RAII" - resource management comparison
    - Enterprise patterns: config parser, log processor

C++ RAII comparison note:
    In C++, resources are tied to object lifetimes via constructors/
    destructors (RAII). The destructor runs automatically when the object
    goes out of scope -- even during stack unwinding from an exception.
    Python's `with` statement provides a similar guarantee: __exit__ is
    called when the block exits, whether normally or via exception.
    However, Python's GC does NOT guarantee deterministic destruction
    the way C++ does, so `with` / context managers are the idiomatic
    replacement for RAII in Python.
"""

from __future__ import annotations

import configparser
import contextlib
import csv
import io
import json
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, TextIO


# ---------------------------------------------------------------------------
# 1. Custom Exception Hierarchy
# ---------------------------------------------------------------------------

class AppError(Exception):
    """Base exception for application-level errors."""

    def __init__(self, message: str, *, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


class ConfigError(AppError):
    """Raised when configuration is missing or invalid."""


class LogParseError(AppError):
    """Raised when a log line cannot be parsed."""


# ---------------------------------------------------------------------------
# 2. Context Manager Demo: Python `with` vs C++ RAII
# ---------------------------------------------------------------------------

class ManagedFile:
    """
    A manual context manager that mirrors C++ RAII semantics.

    C++ RAII pattern (for comparison):
        class FileGuard {
            FILE* fp;
        public:
            FileGuard(const char* path) : fp(fopen(path, "r")) {
                if (!fp) throw std::runtime_error("open failed");
            }
            ~FileGuard() { if (fp) fclose(fp); }   // destructor = cleanup
        };
        // Usage -- destructor runs automatically at scope exit:
        {
            FileGuard guard("data.txt");
            // ... work with file ...
        }   // ~FileGuard() called here, even if exception was thrown

    Python equivalent -- __exit__ is the destructor analogue:
        with ManagedFile("data.txt") as f:
            ...work with file...
        # __exit__ called here, even if exception was thrown
    """

    def __init__(self, path: str, mode: str = "r",
                 encoding: str | None = "utf-8") -> None:
        self._path = path
        self._mode = mode
        self._encoding = encoding
        self._file: TextIO | None = None

    def __enter__(self) -> TextIO:
        """Called at the start of the `with` block (like a C++ constructor)."""
        self._file = open(
            self._path, self._mode, encoding=self._encoding,
        )
        return self._file

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc_val: BaseException | None,
                 exc_tb: Any) -> bool:
        """
        Called when the `with` block exits (like a C++ destructor).

        Return True  to suppress the exception (swallow it).
        Return False to let it propagate (the default).
        """
        if self._file is not None:
            self._file.close()
            self._file = None
        return False  # never suppress


# ---------------------------------------------------------------------------
# 3. contextlib-based Context Manager
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def open_temp_file(mode: str = "w+",
                   encoding: str = "utf-8",
                   suffix: str = ".txt",
                   delete: bool = True) -> Iterator[TextIO]:
    """
    Yield a writable/readable temporary file.

    The file is automatically deleted when the block exits unless
    ``delete=False``.  This is the lightweight alternative to writing
    a full __enter__/__exit__ class.
    """
    tf = tempfile.NamedTemporaryFile(
        mode=mode, encoding=encoding, suffix=suffix,
        delete=delete, newline="",
    )
    try:
        yield tf
    finally:
        tf.close()


# ---------------------------------------------------------------------------
# 4. Basic Text File I/O with try/except/else/finally
# ---------------------------------------------------------------------------

def demo_text_file_basics(write_path: str) -> None:
    """Demonstrate writing and reading a text file with full exception
    handling (the verbose way, before introducing `with`)."""

    # --- WRITE ---
    file = None
    try:
        file = open(write_path, "w", encoding="utf-8")
        file.write("Line 1: Hello, file I/O!\n")
        file.write("Line 2: Exception handling in action.\n")
        file.write("Line 3: Context managers are next.\n")
    except PermissionError:
        print(f"[ERROR] No permission to write to {write_path}")
    except OSError as exc:
        print(f"[ERROR] OS error while writing: {exc}")
    else:
        print(f"[OK] Successfully wrote to {write_path}")
    finally:
        if file is not None:
            file.close()

    # --- READ ---
    file = None
    try:
        file = open(write_path, "r", encoding="utf-8")
        content = file.read()
    except FileNotFoundError:
        print(f"[ERROR] File not found: {write_path}")
    except LookupError:
        print("[ERROR] Unknown encoding specified.")
    except UnicodeDecodeError:
        print("[ERROR] Could not decode the file with the given encoding.")
    else:
        print(f"[OK] File contents:\n{content}")
    finally:
        if file is not None:
            file.close()


# ---------------------------------------------------------------------------
# 5. Context Manager version (the Pythonic way)
# ---------------------------------------------------------------------------

def demo_text_file_with(write_path: str) -> None:
    """Same task as above, but using `with` -- the idiomatic approach."""

    # Write
    try:
        with open(write_path, "w", encoding="utf-8") as f:
            f.write("Line 1: Written via context manager.\n")
            f.write("Line 2: No explicit close() needed.\n")
    except OSError as exc:
        print(f"[ERROR] {exc}")
        return

    # Read line-by-line (iterator protocol)
    try:
        with open(write_path, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                print(f"  {lineno}: {line}", end="")
    except FileNotFoundError:
        print(f"[ERROR] File not found: {write_path}")


# ---------------------------------------------------------------------------
# 6. Binary File I/O (chunked copy)
# ---------------------------------------------------------------------------

def copy_file_binary(src: str, dst: str, chunk_size: int = 512) -> int:
    """Copy a binary file in chunks.  Returns total bytes copied."""
    total = 0
    try:
        with open(src, "rb") as fin, open(dst, "wb") as fout:
            while chunk := fin.read(chunk_size):
                fout.write(chunk)
                total += len(chunk)
    except FileNotFoundError:
        print(f"[ERROR] Source not found: {src}")
        raise
    except IOError as exc:
        print(f"[ERROR] I/O error during copy: {exc}")
        raise
    return total


# ---------------------------------------------------------------------------
# 7. Enterprise Pattern -- Config Parser
# ---------------------------------------------------------------------------

@dataclass
class AppConfig:
    """Typed application configuration."""
    host: str = "127.0.0.1"
    port: int = 8080
    debug: bool = False
    log_file: str = "app.log"
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])

    @classmethod
    def from_ini(cls, path: str | Path) -> "AppConfig":
        """Load configuration from an INI file.

        Raises ConfigError if the file is missing or contains
        invalid values.
        """
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}", code=10)

        parser = configparser.ConfigParser()
        try:
            parser.read(path, encoding="utf-8")
        except configparser.Error as exc:
            raise ConfigError(f"Failed to parse config: {exc}", code=11) from exc

        section = "app" if parser.has_section("app") else "DEFAULT"
        try:
            host = parser.get(section, "host", fallback="127.0.0.1")
            port = parser.getint(section, "port", fallback=8080)
            debug = parser.getboolean(section, "debug", fallback=False)
            log_file = parser.get(section, "log_file", fallback="app.log")
            origins_raw = parser.get(
                section, "allowed_origins", fallback="*",
            )
        except (configparser.Error, ValueError) as exc:
            raise ConfigError(
                f"Invalid config value: {exc}", code=12,
            ) from exc

        allowed_origins = [
            o.strip() for o in origins_raw.split(",") if o.strip()
        ]

        return cls(
            host=host,
            port=port,
            debug=debug,
            log_file=log_file,
            allowed_origins=allowed_origins,
        )

    def to_json(self, path: str | Path) -> None:
        """Serialize config to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, path: str | Path) -> "AppConfig":
        """Load config from a JSON file."""
        with open(path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        return cls(**{k: v for k, v in data.items()
                      if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# 8. Enterprise Pattern -- Log Processor
# ---------------------------------------------------------------------------

# A simple log format:
#   2025-01-15 08:30:12 [INFO] Application started
#   2025-01-15 08:31:05 [ERROR] Connection refused

_LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})"
    r"\s+\[(?P<level>\w+)\]\s+(?P<message>.+)$",
)


@dataclass
class LogEntry:
    timestamp: str
    level: str
    message: str


class LogProcessor:
    """Read and filter structured log files.

    Demonstrates:
        - Reading files line-by-line with enumeration
        - Custom exceptions (LogParseError)
        - Generator-based iteration (lazy processing)
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def iter_entries(self, *,
                     min_level: str | None = None) -> Iterator[LogEntry]:
        """Yield parsed log entries, optionally filtering by minimum level.

        Levels are compared lexicographically which works for the
        standard DEBUG < INFO < WARNING < ERROR < CRITICAL ordering.
        """
        level_order = {
            "DEBUG": 0, "INFO": 1, "WARNING": 2,
            "ERROR": 3, "CRITICAL": 4,
        }
        min_rank = level_order.get(min_level.upper(), 0) if min_level else 0

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for lineno, raw_line in enumerate(f, start=1):
                    line = raw_line.rstrip("\n\r")
                    if not line:
                        continue
                    match = _LOG_PATTERN.match(line)
                    if match is None:
                        raise LogParseError(
                            f"Line {lineno}: cannot parse '{line}'",
                            code=20,
                        )
                    entry = LogEntry(
                        timestamp=match.group("timestamp"),
                        level=match.group("level"),
                        message=match.group("message"),
                    )
                    rank = level_order.get(entry.level.upper(), -1)
                    if rank >= min_rank:
                        yield entry
        except FileNotFoundError:
            raise ConfigError(
                f"Log file not found: {self._path}", code=21,
            )

    def count_by_level(self) -> dict[str, int]:
        """Return a count of log entries grouped by level."""
        counts: dict[str, int] = {}
        for entry in self.iter_entries():
            counts[entry.level] = counts.get(entry.level, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# 9. Custom Context Manager Class: FileLock (illustrative)
# ---------------------------------------------------------------------------

class FileLock:
    """
    A trivial advisory lock using a .lock sentinel file.

    Mirrors the C++ RAII idiom: the lock is acquired in __enter__
    (constructor) and released in __exit__ (destructor), guaranteeing
    cleanup even if the body raises an exception.
    """

    def __init__(self, lock_path: str) -> None:
        self._lock_path = lock_path

    def __enter__(self) -> "FileLock":
        if os.path.exists(self._lock_path):
            raise AppError(f"Lock already held: {self._lock_path}", code=30)
        with open(self._lock_path, "w") as f:
            f.write(str(os.getpid()))
        return self

    def __exit__(self, exc_type: type[BaseException] | None,
                 exc_val: BaseException | None,
                 exc_tb: Any) -> bool:
        with contextlib.suppress(OSError):
            os.remove(self._lock_path)
        return False


# ---------------------------------------------------------------------------
# 10. Demonstration Helpers
# ---------------------------------------------------------------------------

def _create_sample_ini(path: Path) -> None:
    """Write a sample INI config file for demonstration."""
    content = (
        "[app]\n"
        "host = 0.0.0.0\n"
        "port = 9090\n"
        "debug = true\n"
        "log_file = /var/log/myapp.log\n"
        "allowed_origins = https://example.com, https://api.example.com\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _create_sample_log(path: Path) -> None:
    """Write a sample log file for demonstration."""
    lines = [
        "2025-01-15 08:30:12 [INFO] Application started",
        "2025-01-15 08:31:05 [DEBUG] Loading configuration",
        "2025-01-15 08:31:06 [INFO] Config loaded successfully",
        "2025-01-15 08:32:00 [WARNING] Connection pool running low",
        "2025-01-15 08:33:45 [ERROR] Connection refused to database",
        "2025-01-15 08:33:46 [CRITICAL] Shutting down due to DB failure",
        "2025-01-15 08:34:00 [INFO] Shutdown complete",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# 11. Main Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all demonstrations."""

    # Use a temporary directory so we leave no artifacts.
    with tempfile.TemporaryDirectory(prefix="day21_demo_") as tmpdir:
        tmp = Path(tmpdir)

        # --- 1. Text file basics (verbose try/except/else/finally) ---
        print("=" * 60)
        print("1. Text file I/O -- verbose try/except/else/finally")
        print("=" * 60)
        demo_text_file_basics(str(tmp / "basics.txt"))
        print()

        # --- 2. Text file with context manager ---
        print("=" * 60)
        print("2. Text file I/O -- context manager (`with`)")
        print("=" * 60)
        demo_text_file_with(str(tmp / "with_demo.txt"))
        print()

        # --- 3. Binary file copy ---
        print("=" * 60)
        print("3. Binary file I/O -- chunked copy")
        print("=" * 60)
        # Create a small binary file to copy
        src_bin = tmp / "source.bin"
        dst_bin = tmp / "dest.bin"
        with open(src_bin, "wb") as f:
            f.write(bytes(range(256)) * 4)  # 1024 bytes
        copied = copy_file_binary(str(src_bin), str(dst_bin))
        print(f"[OK] Copied {copied} bytes from {src_bin.name} "
              f"-> {dst_bin.name}")
        print()

        # --- 4. Custom ManagedFile context manager ---
        print("=" * 60)
        print("4. Custom context manager (ManagedFile -- C++ RAII analogy)")
        print("=" * 60)
        managed_path = tmp / "managed.txt"
        with ManagedFile(str(managed_path), "w") as f:
            f.write("Written via ManagedFile context manager.\n")
        with ManagedFile(str(managed_path), "r") as f:
            print(f"  {f.readline().rstrip()}")
        print()

        # --- 5. contextlib.temp_file ---
        print("=" * 60)
        print("5. @contextlib.contextmanager -- temp file")
        print("=" * 60)
        with open_temp_file() as tf:
            tf.write("Hello from a temporary file!\n")
            tf.seek(0)
            print(f"  {tf.readline().rstrip()}")
        print("  (temp file cleaned up automatically)")
        print()

        # --- 6. Enterprise: Config Parser ---
        print("=" * 60)
        print("6. Enterprise pattern -- Config Parser (INI + JSON)")
        print("=" * 60)
        ini_path = tmp / "app.ini"
        json_path = tmp / "app.json"
        _create_sample_ini(ini_path)

        config = AppConfig.from_ini(ini_path)
        print(f"  Loaded from INI : {config}")
        config.to_json(json_path)
        print(f"  Serialized to   : {json_path}")

        config2 = AppConfig.from_json(json_path)
        print(f"  Loaded from JSON: {config2}")
        print()

        # Demonstrate ConfigError on missing file
        try:
            AppConfig.from_ini(tmp / "nonexistent.ini")
        except ConfigError as exc:
            print(f"  Expected error  : {exc} (code={exc.code})")
        print()

        # --- 7. Enterprise: Log Processor ---
        print("=" * 60)
        print("7. Enterprise pattern -- Log Processor")
        print("=" * 60)
        log_path = tmp / "app.log"
        _create_sample_log(log_path)

        processor = LogProcessor(log_path)

        print("  All entries:")
        for entry in processor.iter_entries():
            print(f"    {entry.timestamp} [{entry.level}] {entry.message}")
        print()

        print("  ERROR+ only:")
        for entry in processor.iter_entries(min_level="ERROR"):
            print(f"    {entry.timestamp} [{entry.level}] {entry.message}")
        print()

        print("  Count by level:")
        for level, count in sorted(processor.count_by_level().items()):
            print(f"    {level}: {count}")
        print()

        # --- 8. FileLock context manager ---
        print("=" * 60)
        print("8. FileLock context manager (RAII-style resource guard)")
        print("=" * 60)
        lock_path = str(tmp / "demo.lock")
        try:
            with FileLock(lock_path):
                print("  Lock acquired, doing critical work...")
            print("  Lock released (automatic cleanup).")
        except AppError as exc:
            print(f"  Lock error: {exc}")

        # Demonstrate double-lock
        try:
            with FileLock(lock_path):
                with FileLock(lock_path):  # should fail
                    pass
        except AppError as exc:
            print(f"  Expected double-lock error: {exc}")
        print()

    print("=" * 60)
    print("All temporary files cleaned up. Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
