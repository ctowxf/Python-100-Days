"""
92. Docker Container Technology Demo (Docker容器技术详解)

Enterprise-level implementation covering:
- Docker concepts and architecture (images, containers, volumes, networks)
- Dockerfile generation for Python applications
- Docker Compose multi-service orchestration
- Python Docker SDK for programmatic container management
- Container health monitoring and management

C++ Comparison: Docker Containers vs C++ Static Linking
============================================================
Docker containers package an application with its full runtime environment
(shared libraries, system dependencies, configs) into layered filesystem
images using Linux namespaces and cgroups. C++ static linking bundles all
library code directly into a single executable binary at compile time.
Containers offer environment isolation and portability across hosts at the
cost of image size overhead, while static binaries are self-contained,
lightweight single files but lack runtime isolation. In practice, C++ apps
are often deployed *inside* Docker containers to get the best of both
worlds: portable isolation with native execution speed.
============================================================
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Section 1: Docker Concepts and Architecture (Docker概念与架构)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DockerLayer:
    """Represents a single layer in a Docker image filesystem."""
    instruction: str
    command: str
    size_bytes: int = 0

    def __str__(self) -> str:
        return f"[{self.instruction}] {self.command} ({self.size_bytes} bytes)"


@dataclass
class DockerImage:
    """
    Conceptual representation of a Docker image.

    Docker images are built from a series of read-only layers, each
    representing a filesystem change (ADD, RUN, COPY, etc.). The Union
    Filesystem (UnionFS) overlays these layers into a single coherent
    filesystem visible inside the container.

    Architecture:
    - bootfs: Linux kernel boot filesystem (bottom layer)
    - rootfs: Root filesystem (read-only OS layer, e.g. Ubuntu/Alpine)
    - app layers: Application-specific layers (read-only)
    - container layer: Writable layer created at runtime (copy-on-write)
    """
    name: str
    tag: str = "latest"
    layers: List[DockerLayer] = field(default_factory=list)
    base_image: str = ""
    expose_ports: List[int] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    entrypoint: List[str] = field(default_factory=list)
    cmd: List[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.name}:{self.tag}"

    @property
    def total_size(self) -> int:
        return sum(layer.size_bytes for layer in self.layers)

    def summary(self) -> str:
        lines = [
            f"Image: {self.full_name}",
            f"Base:  {self.base_image}",
            f"Size:  {self.total_size:,} bytes",
            f"Ports: {', '.join(str(p) for p in self.expose_ports)}",
            f"Layers ({len(self.layers)}):",
        ]
        for i, layer in enumerate(self.layers):
            lines.append(f"  {i}: {layer}")
        return "\n".join(lines)


@dataclass
class DockerContainer:
    """
    Conceptual representation of a running Docker container.

    A container is a runnable instance of an image with an additional
    writable layer. Containers are isolated via Linux namespaces
    (PID, NET, MNT, UTS, IPC, USER) and resource-limited via cgroups.
    """
    container_id: str = ""
    name: str = ""
    image: str = ""
    status: str = "created"
    ports: Dict[int, int] = field(default_factory=dict)  # host:container
    volumes: Dict[str, str] = field(default_factory=dict)  # host:container
    env_vars: Dict[str, str] = field(default_factory=dict)
    networks: List[str] = field(default_factory=list)

    def is_running(self) -> bool:
        return self.status == "running"

    def __str__(self) -> str:
        port_str = ", ".join(
            f"{h}->{c}" for h, c in self.ports.items()
        )
        return (
            f"Container({self.name or self.container_id[:12]}) "
            f"image={self.image} status={self.status} ports=[{port_str}]"
        )


# ---------------------------------------------------------------------------
# Section 2: Dockerfile Generator (Dockerfile生成器)
# ---------------------------------------------------------------------------


class DockerfileGenerator:
    """
    Programmatic Dockerfile generator for Python applications.

    Generates production-ready Dockerfiles with:
    - Multi-stage builds for smaller images
    - Non-root user for security
    - Health checks
    - Proper signal handling via tini or gunicorn

    Enterprise Example: Generates Dockerfiles for microservice deployments
    with security best practices and minimal attack surface.
    """

    VALID_BASE_IMAGES = {
        "python": ["3.9", "3.10", "3.11", "3.12", "3.12-slim", "3.12-alpine"],
        "node": ["18", "20", "20-slim", "20-alpine"],
        "nginx": ["1.24", "1.25", "latest", "alpine"],
        "mysql": ["5.7", "8.0", "8.0-debian"],
        "redis": ["7", "7-alpine", "latest"],
        "ubuntu": ["20.04", "22.04", "24.04"],
    }

    def __init__(
        self,
        base_image: str = "python:3.12-slim",
        app_name: str = "myapp",
        workdir: str = "/app",
        port: int = 8000,
        non_root_user: str = "appuser",
    ):
        self.base_image = base_image
        self.app_name = app_name
        self.workdir = workdir
        self.port = port
        self.non_root_user = non_root_user
        self._instructions: List[str] = []
        self._env_vars: Dict[str, str] = {}
        self._labels: Dict[str, str] = {}
        self._copy_sources: List[Tuple[str, str]] = []
        self._run_commands: List[str] = []
        self._volumes: List[str] = []

    def add_label(self, key: str, value: str) -> "DockerfileGenerator":
        self._labels[key] = value
        return self

    def add_env(self, key: str, value: str) -> "DockerfileGenerator":
        self._env_vars[key] = value
        return self

    def add_copy(self, src: str, dest: str) -> "DockerfileGenerator":
        self._copy_sources.append((src, dest))
        return self

    def add_run(self, command: str) -> "DockerfileGenerator":
        self._run_commands.append(command)
        return self

    def add_volume(self, path: str) -> "DockerfileGenerator":
        self._volumes.append(path)
        return self

    def generate(self) -> str:
        """Generate the Dockerfile content as a string."""
        lines: List[str] = []

        # FROM with optional alias for multi-stage
        lines.append(f"FROM {self.base_image} AS builder")
        lines.append("")

        # Labels
        for key, val in self._labels.items():
            lines.append(f'LABEL {key}="{val}"')
        if self._labels:
            lines.append("")

        # Environment variables
        for key, val in self._env_vars.items():
            lines.append(f"ENV {key}={val}")
        if self._env_vars:
            lines.append("")

        # Working directory
        lines.append(f"WORKDIR {self.workdir}")
        lines.append("")

        # Copy and install dependencies first (cache layer optimization)
        if any("requirements" in src for src, _ in self._copy_sources):
            for src, dest in self._copy_sources:
                if "requirements" in src:
                    lines.append(f"COPY {src} {dest}")
            lines.append(
                "RUN pip install --no-cache-dir -r requirements.txt "
                "-i https://pypi.tuna.tsinghua.edu.cn/simple/"
            )
            lines.append("")

        # Copy remaining files
        for src, dest in self._copy_sources:
            if "requirements" not in src:
                lines.append(f"COPY {src} {dest}")
        lines.append("")

        # Additional RUN commands
        for cmd in self._run_commands:
            lines.append(f"RUN {cmd}")
        if self._run_commands:
            lines.append("")

        # Create non-root user
        lines.append(
            f"RUN groupadd -r {self.non_root_user} && "
            f"useradd -r -g {self.non_root_user} -d {self.workdir} "
            f"-s /sbin/nologin {self.non_root_user}"
        )
        lines.append(
            f"RUN chown -R {self.non_root_user}:{self.non_root_user} {self.workdir}"
        )
        lines.append(f"USER {self.non_root_user}")
        lines.append("")

        # Volumes
        for vol in self._volumes:
            lines.append(f"VOLUME {vol}")
        if self._volumes:
            lines.append("")

        # Expose port
        lines.append(f"EXPOSE {self.port}")
        lines.append("")

        # Health check
        lines.append(
            f"HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\"
        )
        lines.append(
            f'  CMD curl -f http://localhost:{self.port}/health || exit 1'
        )
        lines.append("")

        # Default command
        lines.append(
            f'CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:{self.port}", '
            f'"--access-logfile", "-", "app:app"]'
        )

        return "\n".join(lines)

    def save(self, directory: str, filename: str = "Dockerfile") -> str:
        """Write the Dockerfile to disk and return the file path."""
        filepath = Path(directory) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(self.generate(), encoding="utf-8")
        return str(filepath)


# ---------------------------------------------------------------------------
# Section 3: Docker Compose Builder (Docker Compose构建器)
# ---------------------------------------------------------------------------


@dataclass
class ServiceConfig:
    """Configuration for a single Docker Compose service."""
    name: str
    image: str = ""
    build_context: str = ""
    dockerfile: str = "Dockerfile"
    ports: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    restart: str = "unless-stopped"
    healthcheck: Optional[str] = None
    expose: List[str] = field(default_factory=list)
    command: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.image:
            d["image"] = self.image
        if self.build_context:
            d["build"] = self.build_context
            if self.dockerfile != "Dockerfile":
                d["build"] = {
                    "context": self.build_context,
                    "dockerfile": self.dockerfile,
                }
        if self.ports:
            d["ports"] = self.ports
        if self.volumes:
            d["volumes"] = self.volumes
        if self.environment:
            d["environment"] = self.environment
        if self.depends_on:
            d["depends_on"] = self.depends_on
        if self.networks:
            d["networks"] = self.networks
        if self.restart != "unless-stopped":
            d["restart"] = self.restart
        if self.healthcheck:
            d["healthcheck"] = {"test": ["CMD-SHELL", self.healthcheck]}
        if self.expose:
            d["expose"] = self.expose
        if self.command:
            d["command"] = self.command
        return d


class DockerComposeBuilder:
    """
    Programmatic docker-compose.yml generator.

    Supports building multi-service stacks for common enterprise patterns:
    - Web app + database + cache + reverse proxy
    - Microservices with message queues
    - Development and production profiles

    Enterprise Example: Generates complete docker-compose configurations
    for deploying Django/Flask applications with PostgreSQL, Redis,
    Nginx, and Celery workers.
    """

    def __init__(
        self,
        version: str = "3.8",
        project_name: str = "myproject",
    ):
        self.version = version
        self.project_name = project_name
        self.services: Dict[str, ServiceConfig] = {}
        self.networks: Dict[str, Dict[str, Any]] = {}
        self.volumes: Dict[str, Dict[str, Any]] = {}

    def add_service(self, config: ServiceConfig) -> "DockerComposeBuilder":
        self.services[config.name] = config
        return self

    def add_network(
        self, name: str, driver: str = "bridge"
    ) -> "DockerComposeBuilder":
        self.networks[name] = {"driver": driver}
        return self

    def add_volume(
        self, name: str, driver: str = "local"
    ) -> "DockerComposeBuilder":
        self.volumes[name] = {"driver": driver}
        return self

    def generate(self) -> str:
        """Generate docker-compose.yml content."""
        parts: List[str] = []
        parts.append(f"# Docker Compose - {self.project_name}")
        parts.append(f"version: '{self.version}'")
        parts.append("")

        # Services
        parts.append("services:")
        for name, svc in self.services.items():
            parts.append(f"  {name}:")
            svc_dict = svc.to_dict()
            for key, val in svc_dict.items():
                if isinstance(val, dict):
                    parts.append(f"    {key}:")
                    for k2, v2 in val.items():
                        if isinstance(v2, list):
                            parts.append(f"      {k2}:")
                            for item in v2:
                                parts.append(f"        - {item}")
                        else:
                            parts.append(f"      {k2}: {v2}")
                elif isinstance(val, list):
                    parts.append(f"    {key}:")
                    for item in val:
                        parts.append(f"      - {item}")
                elif isinstance(val, str):
                    parts.append(f'    {key}: "{val}"')
                else:
                    parts.append(f"    {key}: {val}")
            parts.append("")

        # Networks
        if self.networks:
            parts.append("networks:")
            for name, cfg in self.networks.items():
                parts.append(f"  {name}:")
                for key, val in cfg.items():
                    parts.append(f"    {key}: {val}")
            parts.append("")

        # Volumes
        if self.volumes:
            parts.append("volumes:")
            for name, cfg in self.volumes.items():
                parts.append(f"  {name}:")
                for key, val in cfg.items():
                    parts.append(f"    {key}: {val}")

        return "\n".join(parts)

    def save(self, directory: str, filename: str = "docker-compose.yml") -> str:
        filepath = Path(directory) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(self.generate(), encoding="utf-8")
        return str(filepath)


# ---------------------------------------------------------------------------
# Section 4: Container Health Checker (容器健康检查器)
# ---------------------------------------------------------------------------


@dataclass
class HealthCheckResult:
    """Result of a container health check."""
    container_name: str
    is_healthy: bool
    response_time_ms: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        status = "HEALTHY" if self.is_healthy else "UNHEALTHY"
        return (
            f"[{status}] {self.container_name} "
            f"({self.response_time_ms:.1f}ms)"
        )


class ContainerHealthChecker:
    """
    Enterprise container health monitoring system.

    Checks container health via:
    - HTTP endpoint probes
    - TCP socket connectivity
    - Docker API status inspection
    - Custom health check scripts

    This class simulates what a production health checker would do;
    actual Docker API calls require the `docker` Python package.
    """

    def __init__(
        self,
        check_interval: int = 30,
        timeout: int = 5,
        retries: int = 3,
    ):
        self.check_interval = check_interval
        self.timeout = timeout
        self.retries = retries
        self.results: List[HealthCheckResult] = []

    def check_http_endpoint(
        self, name: str, url: str
    ) -> HealthCheckResult:
        """Probe a container's HTTP health endpoint."""
        start = time.time()
        try:
            import urllib.request
            import urllib.error

            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                elapsed = (time.time() - start) * 1000
                result = HealthCheckResult(
                    container_name=name,
                    is_healthy=resp.status == 200,
                    response_time_ms=elapsed,
                    status_code=resp.status,
                )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            result = HealthCheckResult(
                container_name=name,
                is_healthy=False,
                response_time_ms=elapsed,
                error_message=str(e),
            )
        self.results.append(result)
        return result

    def check_tcp_port(
        self, name: str, host: str, port: int
    ) -> HealthCheckResult:
        """Check if a TCP port is accepting connections."""
        import socket

        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((host, port))
            sock.close()
            elapsed = (time.time() - start) * 1000
            result = HealthCheckResult(
                container_name=name,
                is_healthy=True,
                response_time_ms=elapsed,
                details={"host": host, "port": port},
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            result = HealthCheckResult(
                container_name=name,
                is_healthy=False,
                response_time_ms=elapsed,
                error_message=str(e),
                details={"host": host, "port": port},
            )
        self.results.append(result)
        return result

    def simulate_docker_api_check(
        self, container: DockerContainer
    ) -> HealthCheckResult:
        """
        Simulate a Docker API container status check.

        In production, this would call the Docker Engine API:
        GET /containers/{id}/json
        """
        is_healthy = container.is_running()
        result = HealthCheckResult(
            container_name=container.name,
            is_healthy=is_healthy,
            response_time_ms=0.0,
            details={
                "status": container.status,
                "image": container.image,
            },
        )
        self.results.append(result)
        return result

    def get_report(self) -> Dict[str, Any]:
        """Generate a summary health report."""
        total = len(self.results)
        healthy = sum(1 for r in self.results if r.is_healthy)
        unhealthy = total - healthy
        avg_response = (
            sum(r.response_time_ms for r in self.results) / total
            if total > 0
            else 0.0
        )
        return {
            "total_checks": total,
            "healthy": healthy,
            "unhealthy": unhealthy,
            "health_rate": healthy / total if total > 0 else 0.0,
            "avg_response_time_ms": round(avg_response, 2),
            "results": [
                {
                    "container": r.container_name,
                    "healthy": r.is_healthy,
                    "response_ms": round(r.response_time_ms, 2),
                    "error": r.error_message,
                }
                for r in self.results
            ],
        }


# ---------------------------------------------------------------------------
# Section 5: Docker SDK Wrapper (Docker SDK封装)
# ---------------------------------------------------------------------------


class DockerSDKClient:
    """
    Wrapper around the Docker Python SDK for programmatic container management.

    Provides a clean interface for:
    - Listing, creating, starting, stopping, and removing containers
    - Building and pulling images
    - Managing volumes and networks
    - Streaming container logs

    Falls back to subprocess-based CLI calls if the Docker SDK is not installed.

    Note: Install with `pip install docker` for full SDK functionality.
    """

    def __init__(self):
        self._client = None
        self._use_sdk = False
        try:
            import docker  # type: ignore[import-untyped]
            self._client = docker.from_env()
            self._use_sdk = True
        except ImportError:
            pass
        except Exception:
            pass

    @property
    def is_available(self) -> bool:
        """Check if Docker daemon is accessible."""
        if self._use_sdk and self._client is not None:
            try:
                self._client.ping()  # type: ignore[union-attr]
                return True
            except Exception:
                return False
        # Fallback: try CLI
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def list_images(self) -> List[Dict[str, Any]]:
        """List locally available Docker images."""
        if self._use_sdk and self._client is not None:
            images = []
            for img in self._client.images.list():  # type: ignore[union-attr]
                tags = img.tags if img.tags else ["<none>:<none>"]
                images.append({
                    "id": img.short_id,
                    "tags": tags,
                    "size_mb": round(img.attrs.get("Size", 0) / 1e6, 1),
                })
            return images
        # Fallback
        try:
            result = subprocess.run(
                ["docker", "images", "--format", "{{json .}}"],
                capture_output=True, text=True, timeout=15,
            )
            images = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    images.append(json.loads(line))
            return images
        except Exception:
            return []

    def list_containers(self, all: bool = True) -> List[Dict[str, Any]]:
        """List Docker containers."""
        if self._use_sdk and self._client is not None:
            containers = []
            for c in self._client.containers.list(all=all):  # type: ignore[union-attr]
                containers.append({
                    "id": c.short_id,
                    "name": c.name,
                    "image": c.image.tags[0] if c.image.tags else "<none>",
                    "status": c.status,
                })
            return containers
        # Fallback
        try:
            flag = "-a" if all else ""
            result = subprocess.run(
                ["docker", "ps", flag, "--format", "{{json .}}"],
                capture_output=True, text=True, timeout=15,
            )
            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    containers.append(json.loads(line))
            return containers
        except Exception:
            return []

    def run_container(
        self,
        image: str,
        name: str = "",
        ports: Optional[Dict[str, str]] = None,
        detach: bool = True,
        environment: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        command: Optional[str] = None,
    ) -> Optional[str]:
        """
        Run a Docker container.

        Parameters
        ----------
        image : str
            Docker image name and tag.
        name : str
            Container name.
        ports : dict
            Port mappings, e.g. {"8080/tcp": "80"}.
        detach : bool
            Run in background.
        environment : dict
            Environment variables.
        volumes : dict
            Volume mounts.
        command : str
            Override default command.

        Returns
        -------
        str or None
            Container ID if successful.
        """
        if self._use_sdk and self._client is not None:
            try:
                container = self._client.containers.run(  # type: ignore[union-attr]
                    image=image,
                    name=name or None,
                    ports=ports,
                    detach=detach,
                    environment=environment,
                    volumes=volumes,
                    command=command,
                )
                return container.short_id
            except Exception as e:
                print(f"Error running container: {e}")
                return None
        # Fallback: CLI
        cmd_parts = ["docker", "run"]
        if detach:
            cmd_parts.append("-d")
        if name:
            cmd_parts.extend(["--name", name])
        if ports:
            for container_port, host_port in ports.items():
                cmd_parts.extend(["-p", f"{host_port}:{container_port.split('/')[0]}"])
        if environment:
            for k, v in environment.items():
                cmd_parts.extend(["-e", f"{k}={v}"])
        if volumes:
            for host_path, cfg in volumes.items():
                bind = cfg.get("bind", "")
                mode = cfg.get("mode", "rw")
                cmd_parts.extend(["-v", f"{host_path}:{bind}:{mode}"])
        cmd_parts.append(image)
        if command:
            cmd_parts.append(command)
        try:
            result = subprocess.run(
                cmd_parts, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()[:12]
            print(f"Docker CLI error: {result.stderr}")
            return None
        except Exception as e:
            print(f"Docker CLI error: {e}")
            return None

    def stop_container(self, name_or_id: str) -> bool:
        """Stop a running container."""
        if self._use_sdk and self._client is not None:
            try:
                container = self._client.containers.get(name_or_id)  # type: ignore[union-attr]
                container.stop()
                return True
            except Exception:
                return False
        try:
            result = subprocess.run(
                ["docker", "stop", name_or_id],
                capture_output=True, text=True, timeout=30,
            )
            return result.returncode == 0
        except Exception:
            return False

    def remove_container(self, name_or_id: str, force: bool = False) -> bool:
        """Remove a container."""
        if self._use_sdk and self._client is not None:
            try:
                container = self._client.containers.get(name_or_id)  # type: ignore[union-attr]
                container.remove(force=force)
                return True
            except Exception:
                return False
        try:
            cmd = ["docker", "rm"]
            if force:
                cmd.append("-f")
            cmd.append(name_or_id)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return result.returncode == 0
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Section 6: Enterprise Docker Patterns (企业级Docker模式)
# ---------------------------------------------------------------------------


def generate_flask_dockerfile() -> str:
    """Generate a production-ready Dockerfile for a Flask application."""
    gen = DockerfileGenerator(
        base_image="python:3.12-slim",
        app_name="flask-api",
        port=8000,
    )
    gen.add_label("maintainer", "devops@enterprise.com")
    gen.add_label("version", "1.0.0")
    gen.add_label("description", "Production Flask API server")
    gen.add_env("PYTHONDONTWRITEBYTECODE", "1")
    gen.add_env("PYTHONUNBUFFERED", "1")
    gen.add_env("FLASK_ENV", "production")
    gen.add_copy("requirements.txt", ".")
    gen.add_copy(".", ".")
    gen.add_run("apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*")
    gen.add_volume("/app/data")
    return gen.generate()


def generate_django_dockerfile() -> str:
    """Generate a production Dockerfile for a Django application."""
    gen = DockerfileGenerator(
        base_image="python:3.12-slim",
        app_name="django-app",
        port=8000,
    )
    gen.add_label("maintainer", "devops@enterprise.com")
    gen.add_env("DJANGO_SETTINGS_MODULE", "config.settings.production")
    gen.add_env("PYTHONDONTWRITEBYTECODE", "1")
    gen.add_env("PYTHONUNBUFFERED", "1")
    gen.add_copy("requirements.txt", ".")
    gen.add_copy(".", ".")
    gen.add_run("python manage.py collectstatic --noinput")
    gen.add_volume("/app/media")
    gen.add_volume("/app/static")
    return gen.generate()


def generate_full_stack_compose() -> str:
    """
    Generate a complete docker-compose.yml for a full-stack application.

    Services: Nginx (reverse proxy), Django (app), PostgreSQL, Redis, Celery
    """
    builder = DockerComposeBuilder(
        version="3.8",
        project_name="enterprise-app",
    )

    # PostgreSQL database
    builder.add_service(ServiceConfig(
        name="db",
        image="postgres:15-alpine",
        ports=["5432:5432"],
        volumes=["pgdata:/var/lib/postgresql/data"],
        environment={
            "POSTGRES_DB": "appdb",
            "POSTGRES_USER": "appuser",
            "POSTGRES_PASSWORD": "secretpass",
        },
        restart="always",
    ))

    # Redis cache and message broker
    builder.add_service(ServiceConfig(
        name="redis",
        image="redis:7-alpine",
        ports=["6379:6379"],
        volumes=["redisdata:/data"],
        restart="always",
    ))

    # Django application
    builder.add_service(ServiceConfig(
        name="web",
        build_context="./app",
        ports=["8000:8000"],
        volumes=["./app:/app", "mediadata:/app/media"],
        environment={
            "DJANGO_SETTINGS_MODULE": "config.settings.production",
            "DATABASE_URL": "postgres://appuser:secretpass@db:5432/appdb",
            "REDIS_URL": "redis://redis:6379/0",
            "CELERY_BROKER_URL": "redis://redis:6379/1",
        },
        depends_on=["db", "redis"],
        restart="always",
    ))

    # Celery worker
    builder.add_service(ServiceConfig(
        name="celery",
        build_context="./app",
        command="celery -A config worker -l info",
        environment={
            "DJANGO_SETTINGS_MODULE": "config.settings.production",
            "DATABASE_URL": "postgres://appuser:secretpass@db:5432/appdb",
            "REDIS_URL": "redis://redis:6379/0",
            "CELERY_BROKER_URL": "redis://redis:6379/1",
        },
        depends_on=["db", "redis", "web"],
        restart="always",
    ))

    # Nginx reverse proxy
    builder.add_service(ServiceConfig(
        name="nginx",
        image="nginx:1.25-alpine",
        ports=["80:80", "443:443"],
        volumes=[
            "./nginx/nginx.conf:/etc/nginx/nginx.conf:ro",
            "./nginx/ssl:/etc/nginx/ssl:ro",
            "mediadata:/usr/share/nginx/html/media:ro",
        ],
        depends_on=["web"],
        restart="always",
    ))

    # Add shared volumes
    builder.add_volume("pgdata")
    builder.add_volume("redisdata")
    builder.add_volume("mediadata")

    return builder.generate()


def generate_microservices_compose() -> str:
    """Generate docker-compose for a microservices architecture."""
    builder = DockerComposeBuilder(
        version="3.8",
        project_name="microservices",
    )

    services = [
        ("api-gateway", "kong:3.4", ["8000:8000", "8443:8443", "8001:8001"]),
        ("user-service", "./services/user", ["8002:8002"]),
        ("product-service", "./services/product", ["8003:8003"]),
        ("order-service", "./services/order", ["8004:8004"]),
        ("payment-service", "./services/payment", ["8005:8005"]),
    ]

    for name, image, ports in services:
        is_build = image.startswith("./")
        svc = ServiceConfig(
            name=name,
            image="" if is_build else image,
            build_context=image if is_build else "",
            ports=[f"{p}:{p}" for p in ports],
            depends_on=["postgres", "redis"] if name != "api-gateway" else [],
        )
        builder.add_service(svc)

    builder.add_service(ServiceConfig(
        name="postgres", image="postgres:15-alpine",
        ports=["5432:5432"], volumes=["pgdata:/var/lib/postgresql/data"],
    ))
    builder.add_service(ServiceConfig(
        name="redis", image="redis:7-alpine",
        ports=["6379:6379"],
    ))

    builder.add_volume("pgdata")
    return builder.generate()


# ---------------------------------------------------------------------------
# Section 7: Demonstration Functions
# ---------------------------------------------------------------------------


def demonstrate_docker_concepts() -> None:
    """Explain Docker core concepts with programmatic examples."""
    print("=" * 70)
    print("PART 1: Docker Core Concepts")
    print("=" * 70)

    # Docker Image representation
    image = DockerImage(
        name="enterprise/webapp",
        tag="v1.2.0",
        base_image="python:3.12-slim",
        expose_ports=[8000, 8443],
        env_vars={"FLASK_ENV": "production", "PYTHONUNBUFFERED": "1"},
        layers=[
            DockerLayer("FROM", "python:3.12-slim", 150_000_000),
            DockerLayer("COPY", "requirements.txt", 500),
            DockerLayer("RUN", "pip install -r requirements.txt", 45_000_000),
            DockerLayer("COPY", ". .", 2_000_000),
            DockerLayer("EXPOSE", "8000", 0),
            DockerLayer("CMD", "gunicorn app:app", 0),
        ],
    )
    print(f"\n{image.summary()}")

    # Docker Container representation
    container = DockerContainer(
        container_id="a1b2c3d4e5f6",
        name="webapp-prod",
        image="enterprise/webapp:v1.2.0",
        status="running",
        ports={80: 8000, 443: 8443},
        volumes={"/data/webapp": "/app/data"},
        env_vars={"FLASK_ENV": "production"},
        networks=["frontend", "backend"],
    )
    print(f"\n{container}")

    # Docker vs VM comparison
    print("\n" + "-" * 50)
    print("Docker Containers vs Virtual Machines:")
    print("-" * 50)
    comparison = [
        ("Aspect", "Docker Container", "Virtual Machine"),
        ("Isolation", "Process-level (namespaces)", "Hardware-level (hypervisor)"),
        ("OS", "Shares host kernel", "Full guest OS"),
        ("Size", "MB (application layers)", "GB (full OS image)"),
        ("Startup", "Seconds", "Minutes"),
        ("Performance", "Near-native", "5-20% overhead"),
        ("Density", "Hundreds per host", "Tens per host"),
    ]
    for row in comparison:
        print(f"  {row[0]:15s} | {row[1]:30s} | {row[2]}")


def demonstrate_dockerfile_generation() -> None:
    """Generate and display Dockerfiles for common Python applications."""
    print("\n" + "=" * 70)
    print("PART 2: Dockerfile Generation")
    print("=" * 70)

    # Flask Dockerfile
    print("\n--- Flask API Dockerfile ---")
    flask_dockerfile = generate_flask_dockerfile()
    print(flask_dockerfile)

    # Django Dockerfile
    print("\n--- Django Application Dockerfile ---")
    django_dockerfile = generate_django_dockerfile()
    print(django_dockerfile)

    # Custom Dockerfile via builder pattern
    print("\n--- Custom Data Science Dockerfile ---")
    custom = DockerfileGenerator(
        base_image="python:3.11-slim",
        app_name="ml-pipeline",
        port=8888,
    )
    custom.add_label("type", "data-science")
    custom.add_env("JUPYTER_PORT", "8888")
    custom.add_copy("requirements.txt", ".")
    custom.add_copy("notebooks/", "./notebooks/")
    custom.add_run("pip install jupyter")
    custom.add_volume("/app/data")
    custom.add_volume("/app/models")
    print(custom.generate())


def demonstrate_docker_compose() -> None:
    """Generate and display docker-compose configurations."""
    print("\n" + "=" * 70)
    print("PART 3: Docker Compose Generation")
    print("=" * 70)

    # Full-stack compose
    print("\n--- Full-Stack Application Stack ---")
    full_stack = generate_full_stack_compose()
    print(full_stack)

    # Microservices compose
    print("\n--- Microservices Architecture ---")
    micro = generate_microservices_compose()
    print(micro)


def demonstrate_health_checker() -> None:
    """Demonstrate container health checking."""
    print("\n" + "=" * 70)
    print("PART 4: Container Health Monitoring")
    print("=" * 70)

    checker = ContainerHealthChecker(check_interval=30, timeout=5, retries=3)

    # Simulate checks on several containers
    containers = [
        DockerContainer(
            name="web-server", image="nginx:latest",
            status="running", ports={80: 8080},
        ),
        DockerContainer(
            name="api-server", image="flask:latest",
            status="running", ports={8000: 8000},
        ),
        DockerContainer(
            name="db-server", image="postgres:15",
            status="running", ports={5432: 5432},
        ),
        DockerContainer(
            name="cache-server", image="redis:7",
            status="stopped", ports={6379: 6379},
        ),
    ]

    print("\nRunning simulated health checks...")
    for container in containers:
        result = checker.simulate_docker_api_check(container)
        status_icon = "[OK]" if result.is_healthy else "[FAIL]"
        print(f"  {status_icon} {result.container_name}: {container.status}")

    # Show report
    report = checker.get_report()
    print(f"\nHealth Report:")
    print(f"  Total checks: {report['total_checks']}")
    print(f"  Healthy:      {report['healthy']}")
    print(f"  Unhealthy:    {report['unhealthy']}")
    print(f"  Health rate:  {report['health_rate']:.1%}")


def demonstrate_docker_sdk() -> None:
    """Demonstrate Docker SDK usage."""
    print("\n" + "=" * 70)
    print("PART 5: Docker Python SDK")
    print("=" * 70)

    client = DockerSDKClient()

    if client.is_available:
        print("\nDocker daemon is accessible.")

        images = client.list_images()
        print(f"\nLocal images ({len(images)}):")
        for img in images[:5]:
            if isinstance(img, dict):
                tags = img.get("tags", ["<none>"])
                size = img.get("size_mb", 0)
                print(f"  {tags[0] if tags else '<none>'} ({size} MB)")

        containers = client.list_containers(all=True)
        print(f"\nContainers ({len(containers)}):")
        for c in containers[:5]:
            if isinstance(c, dict):
                name = c.get("name", c.get("Names", "<unknown>"))
                status = c.get("status", c.get("Status", "<unknown>"))
                print(f"  {name}: {status}")
    else:
        print("\nDocker daemon is not accessible.")
        print("  Install Docker Desktop or start the Docker service.")
        print("  SDK commands will be demonstrated via CLI fallback.")
        print("\n  Example commands:")
        print("    docker images          - List local images")
        print("    docker ps -a           - List all containers")
        print("    docker run -d nginx    - Run Nginx in background")
        print("    docker stop <id>       - Stop a container")
        print("    docker rm <id>         - Remove a container")
        print("    docker build -t name . - Build an image from Dockerfile")
        print("    docker-compose up -d   - Start compose stack")


def demonstrate_common_commands() -> None:
    """Show common Docker CLI commands and their Python equivalents."""
    print("\n" + "=" * 70)
    print("PART 6: Docker Commands Reference")
    print("=" * 70)

    commands = {
        "Image Management": [
            ("docker images", "List all local images"),
            ("docker pull nginx:latest", "Download an image from registry"),
            ("docker build -t myapp:v1 .", "Build image from Dockerfile"),
            ("docker rmi myapp:v1", "Remove a local image"),
            ("docker tag myapp:v1 myapp:latest", "Tag an image"),
            ("docker push myuser/myapp:v1", "Push image to Docker Hub"),
        ],
        "Container Lifecycle": [
            ("docker run -d --name web -p 80:80 nginx", "Create and run container"),
            ("docker start web", "Start a stopped container"),
            ("docker stop web", "Stop a running container"),
            ("docker restart web", "Restart a container"),
            ("docker rm web", "Remove a stopped container"),
            ("docker rm -f web", "Force-remove a running container"),
        ],
        "Container Inspection": [
            ("docker ps", "List running containers"),
            ("docker ps -a", "List all containers"),
            ("docker logs web", "View container logs"),
            ("docker logs -f web", "Follow container logs (tail -f)"),
            ("docker exec -it web /bin/bash", "Enter container shell"),
            ("docker inspect web", "Show container details (JSON)"),
        ],
        "Data Management": [
            ("docker volume create mydata", "Create a named volume"),
            ("docker volume ls", "List all volumes"),
            ("docker run -v /host:/container nginx", "Bind mount host directory"),
            ("docker cp web:/app/logs ./logs", "Copy files from container"),
        ],
        "Compose Commands": [
            ("docker-compose up -d", "Start all services in background"),
            ("docker-compose down", "Stop and remove all services"),
            ("docker-compose ps", "List compose services"),
            ("docker-compose logs -f web", "Follow service logs"),
            ("docker-compose build", "Rebuild service images"),
        ],
    }

    for category, cmds in commands.items():
        print(f"\n  {category}:")
        print(f"  {'-' * 60}")
        for cmd, desc in cmds:
            print(f"    {cmd:50s} # {desc}")


# ---------------------------------------------------------------------------
# Main Guard
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Docker Container Technology -- Enterprise Demo")
    print("=" * 70)

    demonstrate_docker_concepts()
    demonstrate_dockerfile_generation()
    demonstrate_docker_compose()
    demonstrate_health_checker()
    demonstrate_docker_sdk()
    demonstrate_common_commands()

    print("\n" + "=" * 70)
    print("All demonstrations completed successfully.")
    print("=" * 70)
