"""
Day 34-35: Linux System Administration with Python
===================================================

This module demonstrates how Python interacts with Linux systems for:
  - Running shell commands via subprocess (vs C++ system()/popen())
  - File/directory operations via os, shutil, pathlib (vs C++ std::filesystem)
  - Enterprise system administration: health checks, log rotation,
    backup automation, and process management

C++ Comparison Notes:
  Python subprocess  vs C++ system()/popen():
    - subprocess.run() returns a CompletedProcess with returncode/stdout/stderr
    - C system() only returns an int exit code; popen() returns a FILE* stream
    - subprocess supports timeout, encoding, pipes natively

  Python pathlib     vs C++ std::filesystem (C++17):
    - pathlib uses / operator for path joining; C++ uses std::filesystem::path /
    - Both support iterating dirs, checking existence, renaming
    - Python pathlib is pure-Python; C++ filesystem requires linking <filesystem>
"""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
import socket
import time
import gzip
import tarfile
import logging
import tempfile
import signal as _signal
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Sequence, Union

# ---------------------------------------------------------------------------
# Configure logging for all enterprise modules
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================
# 1. SUBPROCESS -- Running Shell Commands from Python
# ============================================================
#
# C++ equivalent:  system("ls -l") returns only an int exit code.
#                  popen("ls -l", "r") returns a FILE* you fread().
#
# Python subprocess.run() returns a CompletedProcess with:
#   .returncode  (int)
#   .stdout      (str or bytes)
#   .stderr      (str or bytes)
#   .args        (the original command)
# ============================================================


def run_command(
    cmd: Union[Sequence[str], str],
    *,
    timeout: int = 30,
    capture: bool = True,
    shell: bool = False,
) -> subprocess.CompletedProcess[str]:
    """
    Wrapper around subprocess.run with sensible defaults.

    Parameters
    ----------
    cmd : list[str] or str
        The command to execute.  When *shell=False* (default) this must be
        a list of arguments.  When *shell=True* it can be a single string.
    timeout : int
        Maximum seconds to wait before raising TimeoutExpired.
    capture : bool
        Whether to capture stdout/stderr (default True).
    shell : bool
        Whether to invoke via the system shell (default False for safety).

    Returns
    -------
    subprocess.CompletedProcess[str]

    Examples
    --------
    >>> result = run_command(["echo", "hello"])
    >>> result.returncode
    0
    >>> "hello" in result.stdout
    True
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            shell=shell,
        )
        return result
    except subprocess.TimeoutExpired:
        logger.error("Command timed out after %ds: %s", timeout, cmd)
        raise
    except FileNotFoundError:
        logger.error("Command not found: %s", cmd)
        raise


def command_exists(name: str) -> bool:
    """
    Check whether a program is available on PATH (like ``which`` on Linux).

    Internally uses shutil.which, which searches PATH the same way the
    shell would.

    >>> command_exists("python")
    True
    """
    return shutil.which(name) is not None


# ============================================================
# 2. OS MODULE -- Low-level OS Interface
# ============================================================


def show_environment_info() -> dict[str, str]:
    """Gather basic environment information via the os module."""
    info: dict[str, str] = {
        "platform": sys.platform,
        "python_version": sys.version.split()[0],
        "cwd": os.getcwd(),
        "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
        "home": os.path.expanduser("~"),
        "hostname": socket.gethostname(),
        "cpu_count": str(os.cpu_count() or "N/A"),
        "pid": str(os.getpid()),
    }
    return info


def get_directory_tree(root: str, max_depth: int = 2) -> list[str]:
    """
    Walk a directory tree up to *max_depth* levels and return a formatted
    list of paths.

    Uses os.walk() -- the Python equivalent of ``find . -maxdepth 2``.
    """
    lines: list[str] = []
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.replace(root, "").count(os.sep)
        if depth >= max_depth:
            dirnames.clear()  # stop descending further
            continue
        indent = "  " * depth
        basename = os.path.basename(dirpath) or dirpath
        lines.append(f"{indent}{basename}/")
        for fname in filenames:
            lines.append(f"{indent}  {fname}")
    return lines


# ============================================================
# 3. PATHLIB -- Object-oriented Filesystem Paths
# ============================================================
#
# C++17 std::filesystem::path comparison:
#   C++:   std::filesystem::path p = "/tmp"; p /= "subdir";
#   Py:    p = Path("/tmp") / "subdir"
#
# Both support: exists(), is_file(), is_dir(), rename(), remove(),
#               parent, stem, suffix, iterdir()
# ============================================================


def pathlib_demo(base: str = "") -> None:
    """Demonstrate pathlib features with C++ equivalents noted in comments."""
    if not base:
        base = os.path.join(tempfile.gettempdir(), "pathlib_demo")

    root = Path(base)

    # Create directory tree
    # C++ equivalent: std::filesystem::create_directories(root / "sub1");
    (root / "sub1").mkdir(parents=True, exist_ok=True)
    (root / "sub2").mkdir(parents=True, exist_ok=True)

    # Create files
    # C++ equivalent: std::ofstream(root / "sub1" / "hello.txt") << "data";
    (root / "sub1" / "hello.txt").write_text("Hello, pathlib!\n", encoding="utf-8")
    (root / "sub2" / "data.csv").write_text("a,b,c\n1,2,3\n", encoding="utf-8")

    # Iterate directory
    # C++ equivalent: for (auto& e : std::filesystem::directory_iterator(root))
    entries: list[str] = [str(e.relative_to(root)) for e in root.iterdir()]
    logger.info("pathlib iterdir: %s", entries)

    # Path properties
    p = root / "sub1" / "hello.txt"
    logger.info(
        "name=%s  stem=%s  suffix=%s  parent=%s", p.name, p.stem, p.suffix, p.parent
    )

    # Glob pattern matching (recursive)
    # C++ equivalent: std::filesystem::recursive_directory_iterator + regex
    csv_files = [str(f.relative_to(root)) for f in root.rglob("*.csv")]
    logger.info("Glob *.csv: %s", csv_files)

    # File stats
    # C++ equivalent: std::filesystem::file_size(p)
    size = p.stat().st_size
    logger.info("File size of %s: %d bytes", p.name, size)

    # Cleanup
    shutil.rmtree(root, ignore_errors=True)
    logger.info("Cleaned up %s", root)


# ============================================================
# 4. SHUTIL -- High-level File Operations
# ============================================================


def archive_directory(src: str, dest: str) -> str:
    """
    Create a .tar.gz archive of *src* at *dest*.

    This mirrors the Linux workflow::

        tar -czf dest.tar.gz src/

    Parameters
    ----------
    src : str
        Source directory to archive.
    dest : str
        Destination tar.gz path.

    Returns
    -------
    str
        The absolute path to the created archive.
    """
    src_path = Path(src)
    if not src_path.is_dir():
        raise FileNotFoundError(f"Source directory not found: {src}")

    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(dest_path, "w:gz") as tar:
        tar.add(src, arcname=src_path.name)

    logger.info(
        "Archived %s -> %s (%.2f MB)", src, dest, dest_path.stat().st_size / 1e6
    )
    return str(dest_path)


def safe_copy(src: str, dst: str) -> str:
    """
    Copy a file or directory.  Uses shutil.copy2 (preserves metadata) for
    files and shutil.copytree for directories.
    """
    src_path = Path(src)
    if src_path.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    logger.info("Copied %s -> %s", src, dst)
    return dst


# ============================================================
# 5. ENTERPRISE: Server Health Check
# ============================================================


@dataclass
class HealthReport:
    """Structured report from a server health check."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    hostname: str = ""
    uptime: str = ""
    cpu_load_1m: float = 0.0
    cpu_load_5m: float = 0.0
    cpu_load_15m: float = 0.0
    mem_total_mb: float = 0.0
    mem_used_mb: float = 0.0
    mem_percent: float = 0.0
    disk_percent: float = 0.0
    warnings: list[str] = field(default_factory=list)
    healthy: bool = True

    def summary(self) -> str:
        status = "HEALTHY" if self.healthy else "DEGRADED"
        lines = [
            f"=== Health Report [{status}] ===",
            f"  Host:   {self.hostname}",
            f"  Time:   {self.timestamp}",
            f"  Uptime: {self.uptime}",
            f"  CPU Load (1/5/15m): "
            f"{self.cpu_load_1m:.2f} / {self.cpu_load_5m:.2f} / {self.cpu_load_15m:.2f}",
            f"  Memory: {self.mem_used_mb:.0f}/{self.mem_total_mb:.0f} MB "
            f"({self.mem_percent:.1f}%)",
            f"  Disk:   {self.disk_percent:.1f}% used",
        ]
        if self.warnings:
            lines.append("  Warnings:")
            for w in self.warnings:
                lines.append(f"    - {w}")
        return "\n".join(lines)


def _read_proc_loadavg() -> tuple[float, float, float]:
    """Read /proc/loadavg on Linux, fall back to os.getloadavg()."""
    try:
        loadavg_path = Path("/proc/loadavg")
        if loadavg_path.exists():
            parts = loadavg_path.read_text().split()[:3]
            return float(parts[0]), float(parts[1]), float(parts[2])
    except (OSError, ValueError):
        pass
    # Fallback for non-Linux (macOS, Windows)
    if hasattr(os, "getloadavg"):
        return os.getloadavg()
    # Windows: use CPU count as a rough proxy (not a real load metric)
    cpu = os.cpu_count() or 1
    return (0.0, 0.0, 0.0)


def _read_proc_meminfo() -> tuple[float, float, float]:
    """Return (total_mb, used_mb, percent).  Reads /proc/meminfo on Linux."""
    try:
        meminfo_path = Path("/proc/meminfo")
        if meminfo_path.exists():
            data: dict[str, float] = {}
            for line in meminfo_path.read_text().splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    data[key] = float(parts[1])  # values in kB
            total = data.get("MemTotal", 0) / 1024
            available = data.get("MemAvailable", data.get("MemFree", 0)) / 1024
            used = total - available
            pct = (used / total * 100) if total > 0 else 0.0
            return total, used, pct
    except (OSError, ValueError):
        pass
    return 0.0, 0.0, 0.0


def _get_disk_usage_percent(path: Optional[str] = None) -> float:
    """Return disk usage percentage for the given mount point."""
    if path is None:
        # Default to root "/" on Unix, current drive "C:\\" on Windows
        path = "\\" if sys.platform == "win32" else "/"
    try:
        usage = shutil.disk_usage(path)
        return usage.used / usage.total * 100 if usage.total > 0 else 0.0
    except OSError:
        return 0.0


def _get_uptime() -> str:
    """Read system uptime from /proc/uptime or subprocess fallback."""
    try:
        uptime_path = Path("/proc/uptime")
        if uptime_path.exists():
            seconds = float(uptime_path.read_text().split()[0])
            delta = timedelta(seconds=int(seconds))
            return str(delta)
    except (OSError, ValueError):
        pass
    try:
        result = run_command(["uptime", "-p"], timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Windows fallback: approximate uptime from boot time via ctypes
    if sys.platform == "win32":
        try:
            import ctypes
            tick_ms = ctypes.windll.kernel32.GetTickCount64()
            delta = timedelta(milliseconds=tick_ms)
            return str(delta)
        except Exception:
            pass
    return "unknown"


def server_health_check(
    *,
    mem_threshold: float = 90.0,
    disk_threshold: float = 85.0,
    load_threshold: float = 4.0,
) -> HealthReport:
    """
    Perform a comprehensive server health check.

    Collects CPU load, memory, and disk usage, then compares against the
    supplied thresholds.  Returns a :class:`HealthReport` dataclass.

    Parameters
    ----------
    mem_threshold : float
        Memory usage percentage above which a warning is issued.
    disk_threshold : float
        Disk usage percentage above which a warning is issued.
    load_threshold : float
        1-minute load average above which a warning is issued.
    """
    report = HealthReport()
    report.hostname = socket.gethostname()
    report.uptime = _get_uptime()

    # CPU load
    avg1, avg5, avg15 = _read_proc_loadavg()
    report.cpu_load_1m = avg1
    report.cpu_load_5m = avg5
    report.cpu_load_15m = avg15
    if avg1 > load_threshold:
        report.warnings.append(
            f"High CPU load: {avg1:.2f} (threshold: {load_threshold})"
        )
        report.healthy = False

    # Memory
    total, used, pct = _read_proc_meminfo()
    report.mem_total_mb = total
    report.mem_used_mb = used
    report.mem_percent = pct
    if pct > mem_threshold and total > 0:
        report.warnings.append(
            f"High memory usage: {pct:.1f}% (threshold: {mem_threshold}%)"
        )
        report.healthy = False

    # Disk
    disk_pct = _get_disk_usage_percent()
    report.disk_percent = disk_pct
    if disk_pct > disk_threshold:
        report.warnings.append(
            f"High disk usage: {disk_pct:.1f}% (threshold: {disk_threshold}%)"
        )
        report.healthy = False

    return report


# ============================================================
# 6. ENTERPRISE: Log Rotation
# ============================================================
#
# Mirrors the Linux logrotate utility described in the course.
# Compresses old logs and removes logs beyond a retention period.
# ============================================================


@dataclass
class LogRotationConfig:
    """Configuration for log rotation (analogous to /etc/logrotate.conf)."""
    log_dir: str = "/var/log"
    pattern: str = "*.log"
    max_size_bytes: int = 10 * 1024 * 1024  # 10 MB
    max_files: int = 7
    compress: bool = True


def _gzip_file(src: Path, dst: Path) -> None:
    """Compress a file using gzip."""
    with open(src, "rb") as f_in, gzip.open(dst, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)


def _cleanup_old_backups(log_dir: Path, base_name: str, max_files: int) -> None:
    """Remove rotated backups whose index exceeds max_files."""
    for backup in log_dir.glob(f"{base_name}.*"):
        suffix = backup.name[len(base_name) + 1:]
        try:
            num = int(suffix.split(".")[0])
            if num > max_files:
                backup.unlink()
                logger.debug("Removed old backup: %s", backup)
        except ValueError:
            continue


def rotate_logs(config: LogRotationConfig | None = None) -> list[str]:
    """
    Rotate log files in *config.log_dir* matching *config.pattern*.

    For each log file exceeding max_size_bytes:
      1. Rename existing rotated files: app.log.2.gz -> app.log.3.gz, etc.
      2. Compress the current file:   app.log.1 -> app.log.1.gz
      3. Rename current file:         app.log -> app.log.1

    Returns a list of rotated file names.
    """
    if config is None:
        config = LogRotationConfig()

    log_dir = Path(config.log_dir)
    if not log_dir.is_dir():
        logger.warning("Log directory does not exist: %s", log_dir)
        return []

    rotated: list[str] = []

    for log_file in log_dir.glob(config.pattern):
        if not log_file.is_file():
            continue
        if log_file.stat().st_size < config.max_size_bytes:
            continue

        logger.info(
            "Rotating %s (%.2f MB)",
            log_file.name,
            log_file.stat().st_size / 1e6,
        )

        # Shift numbered backups: .N -> .N+1
        for i in range(config.max_files - 1, 0, -1):
            src = log_dir / f"{log_file.name}.{i}"
            src_gz = log_dir / f"{log_file.name}.{i}.gz"
            dst = log_dir / f"{log_file.name}.{i + 1}"
            dst_gz = log_dir / f"{log_file.name}.{i + 1}.gz"

            if src_gz.exists():
                if i + 1 > config.max_files:
                    src_gz.unlink()
                else:
                    src_gz.rename(dst_gz)
            elif src.exists():
                if config.compress:
                    _gzip_file(src, src_gz)
                    src.unlink(missing_ok=True)
                    if i + 1 > config.max_files:
                        src_gz.unlink()
                    else:
                        src_gz.rename(dst_gz)
                else:
                    if i + 1 > config.max_files:
                        src.unlink()
                    else:
                        src.rename(dst)

        # Compress and rename current log
        first_backup = log_dir / f"{log_file.name}.1"
        if config.compress:
            _gzip_file(log_file, first_backup.with_suffix(first_backup.suffix + ".gz"))
        else:
            log_file.rename(first_backup)

        # Create fresh empty log
        log_file.write_text("")
        rotated.append(log_file.name)

        # Remove old backups beyond max_files
        _cleanup_old_backups(log_dir, log_file.name, config.max_files)

    return rotated


# ============================================================
# 7. ENTERPRISE: Backup Automation
# ============================================================
#
# Mirrors a cron-based backup workflow:
#   - Create timestamped tar.gz of source directories
#   - Prune backups older than retention_days
# ============================================================


@dataclass
class BackupJob:
    """Defines a single backup job."""
    name: str
    source_dir: str
    backup_dir: str
    retention_days: int = 30
    exclude_patterns: list[str] = field(
        default_factory=lambda: ["*.tmp", "*.pyc", "__pycache__"]
    )


def execute_backup(job: BackupJob) -> dict[str, object]:
    """
    Execute a backup job:
      1. Create a timestamped .tar.gz of *job.source_dir* in *job.backup_dir*.
      2. Prune backups older than *job.retention_days*.

    Returns a summary dict with keys: archive, size_mb, pruned, source.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{job.name}_{timestamp}.tar.gz"
    backup_root = Path(job.backup_dir)
    backup_root.mkdir(parents=True, exist_ok=True)
    archive_path = backup_root / archive_name

    source = Path(job.source_dir)
    if not source.is_dir():
        raise FileNotFoundError(f"Backup source not found: {job.source_dir}")

    with tarfile.open(archive_path, "w:gz") as tar:
        for item in source.rglob("*"):
            # Check exclusion patterns
            if any(item.match(pat) for pat in job.exclude_patterns):
                continue
            tar.add(item, arcname=str(item.relative_to(source.parent)))

    size_mb = round(archive_path.stat().st_size / 1e6, 2)
    logger.info(
        "Backup '%s' complete: %s (%.2f MB)", job.name, archive_name, size_mb
    )

    # Prune old backups
    cutoff = datetime.now() - timedelta(days=job.retention_days)
    pruned = 0
    prefix = f"{job.name}_"
    for old_backup in backup_root.glob(f"{prefix}*.tar.gz"):
        try:
            ts_str = old_backup.stem.replace(".tar", "").replace(prefix, "")
            file_dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            if file_dt < cutoff:
                old_backup.unlink()
                pruned += 1
                logger.info("Pruned old backup: %s", old_backup.name)
        except ValueError:
            continue

    return {
        "archive": archive_name,
        "size_mb": size_mb,
        "pruned": pruned,
        "source": job.source_dir,
    }


# ============================================================
# 8. ENTERPRISE: Process Manager
# ============================================================
#
# Manages long-running processes (e.g. web servers, workers).
# Comparable to a simplified supervisord or systemd unit.
#
# C++ comparison: In C++ you would use fork()+exec() or
# std::system().  Python's subprocess.Popen gives a higher-level
# handle with poll(), communicate(), send_signal(), and returncode.
# ============================================================


@dataclass
class ManagedProcess:
    """A process managed by ProcessManager."""
    name: str
    command: list[str]
    process: Optional[subprocess.Popen[str]] = None
    restart_count: int = 0
    max_restarts: int = 5
    auto_restart: bool = True


class ProcessManager:
    """
    A simple process manager that starts, monitors, and restarts processes.

    Usage::

        mgr = ProcessManager()
        mgr.register("web", ["python", "-m", "http.server", "8080"])
        mgr.start("web")
        print(mgr.status())
        mgr.stop("web")
    """

    def __init__(self) -> None:
        self._processes: dict[str, ManagedProcess] = {}

    def register(
        self,
        name: str,
        command: list[str],
        *,
        auto_restart: bool = True,
        max_restarts: int = 5,
    ) -> None:
        """Register a process definition."""
        self._processes[name] = ManagedProcess(
            name=name,
            command=command,
            auto_restart=auto_restart,
            max_restarts=max_restarts,
        )
        logger.info("Registered process '%s': %s", name, " ".join(command))

    def start(self, name: str) -> bool:
        """Start a registered process."""
        proc = self._processes.get(name)
        if proc is None:
            logger.error("Process '%s' not registered", name)
            return False
        if proc.process is not None and proc.process.poll() is None:
            logger.warning(
                "Process '%s' is already running (pid=%d)", name, proc.process.pid
            )
            return False

        try:
            proc.process = subprocess.Popen(
                proc.command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Started '%s' (pid=%d)", name, proc.process.pid)
            return True
        except FileNotFoundError:
            logger.error("Command not found for '%s': %s", name, proc.command)
            return False

    def stop(self, name: str, *, force: bool = False) -> bool:
        """Stop a running process.  SIGTERM by default, SIGKILL if *force*."""
        proc = self._processes.get(name)
        if proc is None or proc.process is None:
            logger.warning("Process '%s' is not running", name)
            return False

        if proc.process.poll() is not None:
            logger.info(
                "Process '%s' already exited (code=%d)", name, proc.process.returncode
            )
            proc.process = None
            return True

        try:
            proc.process.send_signal(
                _signal.SIGKILL if force else _signal.SIGTERM
            )
            proc.process.wait(timeout=10)
            logger.info("Stopped '%s'", name)
        except subprocess.TimeoutExpired:
            proc.process.kill()
            logger.warning("Force killed '%s' after timeout", name)
        proc.process = None
        return True

    def status(self) -> dict[str, dict[str, object]]:
        """Return status of all managed processes."""
        result: dict[str, dict[str, object]] = {}
        for name, proc in self._processes.items():
            if proc.process is None:
                state = "stopped"
                pid: Optional[int] = None
                rc: Optional[int] = None
            elif proc.process.poll() is None:
                state = "running"
                pid = proc.process.pid
                rc = None
            else:
                state = "exited"
                pid = None
                rc = proc.process.returncode

            result[name] = {
                "state": state,
                "pid": pid,
                "returncode": rc,
                "restart_count": proc.restart_count,
            }
        return result

    def watch(self, interval: float = 5.0, iterations: int = 3) -> None:
        """
        Monitor loop: check each process and auto-restart if it exited.

        In production, run this in a separate thread or use asyncio.
        Here we do a bounded number of iterations for demonstration.
        """
        for _ in range(iterations):
            for name, proc in self._processes.items():
                if proc.process is not None and proc.process.poll() is not None:
                    rc = proc.process.returncode
                    logger.warning("Process '%s' exited (code=%s)", name, rc)
                    if (
                        proc.auto_restart
                        and proc.restart_count < proc.max_restarts
                    ):
                        proc.restart_count += 1
                        logger.info(
                            "Auto-restarting '%s' (attempt %d/%d)",
                            name,
                            proc.restart_count,
                            proc.max_restarts,
                        )
                        self.start(name)
                    else:
                        logger.error(
                            "'%s' reached max restarts or auto_restart disabled",
                            name,
                        )
            time.sleep(interval)


# ============================================================
# 9. FILE PERMISSIONS (os.chmod / os.stat)
# ============================================================
#
# Mirrors the Linux chmod / chown commands from the course.
# ============================================================


def set_permissions(path: str, mode: int) -> None:
    """
    Set file/directory permissions using an octal mode (like ``chmod``).

    Parameters
    ----------
    path : str
        Target file or directory.
    mode : int
        Octal permission bits, e.g. ``0o644`` (rw-r--r--) or ``0o755``
        (rwxr-xr-x).
    """
    os.chmod(path, mode)
    logger.info("Set permissions %04o on %s", mode, path)


def describe_permissions(path: str) -> str:
    """
    Return a human-readable permission string (like ``ls -l``).

    Parameters
    ----------
    path : str
        Target file or directory.

    Returns
    -------
    str
        e.g. ``'-rw-r--r--'`` or ``'drwxr-xr-x'``
    """
    st = os.stat(path)
    mode = st.st_mode

    # File type prefix
    if os.path.isdir(path):
        ft = "d"
    elif os.path.islink(path):
        ft = "l"
    else:
        ft = "-"

    # Owner / Group / Other permissions
    perms = ""
    for shift in (6, 3, 0):
        r = "r" if mode & (0o4 << shift) else "-"
        w = "w" if mode & (0o2 << shift) else "-"
        x = "x" if mode & (0o1 << shift) else "-"
        perms += r + w + x
    return ft + perms


# ============================================================
# 10. DEMONSTRATION / MAIN
# ============================================================


def demo_subprocess() -> None:
    """Demonstrate subprocess usage."""
    print("=" * 60)
    print("DEMO: subprocess module")
    print("  (C++ equivalent: system() / popen())")
    print("=" * 60)

    # Simple command
    result = run_command(["echo", "Hello from subprocess!"])
    print(f"  echo -> returncode={result.returncode}, "
          f"stdout={result.stdout.strip()!r}")

    # Python version
    result = run_command(["python", "--version"])
    ver = result.stdout.strip() or result.stderr.strip()
    print(f"  python --version -> {ver!r}")

    # Command existence check
    for cmd in ["python", "git", "nonexistent_tool_xyz"]:
        print(f"  command_exists('{cmd}'): {command_exists(cmd)}")


def demo_os_module() -> None:
    """Demonstrate os module usage."""
    print("\n" + "=" * 60)
    print("DEMO: os module")
    print("=" * 60)

    info = show_environment_info()
    for k, v in info.items():
        print(f"  {k}: {v}")


def demo_pathlib_full() -> None:
    """Demonstrate pathlib usage."""
    print("\n" + "=" * 60)
    print("DEMO: pathlib module")
    print("  (C++ equivalent: std::filesystem, C++17)")
    print("=" * 60)
    pathlib_demo()


def demo_health_check() -> None:
    """Demonstrate server health check."""
    print("\n" + "=" * 60)
    print("DEMO: Server Health Check")
    print("=" * 60)
    report = server_health_check()
    print(report.summary())


def demo_log_rotation() -> None:
    """Demonstrate log rotation with temporary files."""
    print("\n" + "=" * 60)
    print("DEMO: Log Rotation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake log that exceeds the size threshold
        log_file = Path(tmpdir) / "app.log"
        log_file.write_text("x" * 1024 + "\n" * 100)

        config = LogRotationConfig(
            log_dir=tmpdir,
            pattern="app.log",
            max_size_bytes=512,  # small threshold for demo
            max_files=3,
            compress=True,
        )

        rotated = rotate_logs(config)
        print(f"  Rotated files: {rotated}")
        remaining = sorted(p.name for p in Path(tmpdir).iterdir())
        print(f"  Remaining files: {remaining}")


def demo_backup() -> None:
    """Demonstrate backup automation."""
    print("\n" + "=" * 60)
    print("DEMO: Backup Automation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample source directory
        src = Path(tmpdir) / "project"
        src.mkdir()
        (src / "main.py").write_text("print('hello')\n")
        (src / "utils.py").write_text("def helper(): pass\n")
        (src / "temp.tmp").write_text("temporary\n")
        sub = src / "subdir"
        sub.mkdir()
        (sub / "data.csv").write_text("a,b,c\n1,2,3\n")

        backup_dir = Path(tmpdir) / "backups"
        job = BackupJob(
            name="project_backup",
            source_dir=str(src),
            backup_dir=str(backup_dir),
            retention_days=7,
            exclude_patterns=["*.tmp"],
        )

        result = execute_backup(job)
        print(f"  Archive:  {result['archive']}")
        print(f"  Size:     {result['size_mb']} MB")
        print(f"  Pruned:   {result['pruned']} old backups")
        contents = sorted(p.name for p in backup_dir.iterdir())
        print(f"  Backup dir contents: {contents}")


def demo_process_manager() -> None:
    """Demonstrate the process manager with short-lived processes."""
    print("\n" + "=" * 60)
    print("DEMO: Process Manager")
    print("=" * 60)

    mgr = ProcessManager()

    # Register a simple process (sleeps for 1 second then exits)
    mgr.register(
        "demo_worker",
        ["python", "-c", "import time; time.sleep(1)"],
        auto_restart=False,
    )

    mgr.start("demo_worker")
    status = mgr.status()
    for name, info in status.items():
        print(f"  {name}: {info}")

    # Wait for it to finish
    time.sleep(1.5)
    status = mgr.status()
    for name, info in status.items():
        print(f"  {name} (after wait): {info}")


def demo_permissions() -> None:
    """Demonstrate file permissions."""
    print("\n" + "=" * 60)
    print("DEMO: File Permissions (os.chmod)")
    print("  (C++ equivalent: std::filesystem::permissions())")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("permission test\n")

        # rw-r--r-- (0644)
        set_permissions(str(test_file), 0o644)
        print(f"  After 0o644: {describe_permissions(str(test_file))}")

        # rwxr-xr-x (0755)
        set_permissions(str(test_file), 0o755)
        print(f"  After 0o755: {describe_permissions(str(test_file))}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Day 34-35: Linux System Administration with Python")
    print("=" * 60)
    print()

    demo_subprocess()
    demo_os_module()
    demo_pathlib_full()
    demo_health_check()
    demo_log_rotation()
    demo_backup()
    demo_process_manager()
    demo_permissions()

    print("\n" + "=" * 60)
    print("All demos completed successfully.")
    print("=" * 60)
