"""
Day 91 - Team Development: Problems and Solutions
==================================================

This module demonstrates enterprise-grade team development practices in Python,
covering code style (PEP 8), linting, type checking, documentation standards,
virtual environment management, and automated code quality pipelines.

Topics covered:
    1. PEP 8 code style enforcement and comparison with C++ Google Style Guide
    2. Virtual environments (venv) and comparison with C++ package managers
    3. Project scaffolding / setup automation
    4. Pre-commit hook configuration
    5. Code quality checker (lint, type check, docstring validation)

C++ Comparison Notes:
    - Python PEP 8 vs C++ Google Style Guide:
        * PEP 8 recommends 4-space indentation; Google C++ uses 2-space.
        * PEP 8 limits lines to 79 chars; Google C++ allows 80.
        * PEP 8 uses snake_case for functions/variables; Google C++ uses
          snake_case for functions but camelCase for variables.
        * Both mandate consistent naming and discourage abbreviations.
    - Python venv vs C++ Conan/vcpkg:
        * Python venv isolates interpreter + pip packages per project.
        * Conan and vcpkg manage C/C++ compiled libraries and toolchains.
        * venv is built-in to Python (stdlib); Conan/vcpkg are third-party.
        * All three use a lockfile or manifest to pin dependency versions.

Author: Python-100-Days Contributors
License: MIT
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger: logging.Logger = logging.getLogger(__name__)


# ===================================================================
# Section 1: Code Style Constants and Comparison Data
# ===================================================================

class StyleGuide(Enum):
    """Supported style guides for code style comparison."""
    PEP8 = auto()
    GOOGLE_CPP = auto()


@dataclass(frozen=True)
class StyleRule:
    """A single coding-style rule."""
    category: str
    python_pep8: str
    cpp_google: str


STYLE_COMPARISON: List[StyleRule] = [
    StyleRule(
        category="Indentation",
        python_pep8="4 spaces per indentation level",
        cpp_google="2 spaces per indentation level",
    ),
    StyleRule(
        category="Line Length",
        python_pep8="79 characters (docstrings/comments: 72)",
        cpp_google="80 characters",
    ),
    StyleRule(
        category="Function Naming",
        python_pep8="snake_case (e.g. calculate_total)",
        cpp_google="PascalCase (e.g. CalculateTotal)",
    ),
    StyleRule(
        category="Variable Naming",
        python_pep8="snake_case (e.g. user_count)",
        cpp_google="snake_case for locals, kConstant for constants",
    ),
    StyleRule(
        category="Class Naming",
        python_pep8="PascalCase (e.g. UserService)",
        cpp_google="PascalCase (e.g. UserService)",
    ),
    StyleRule(
        category="Import Order",
        python_pep8="stdlib -> third-party -> local (PEP 8 / isort)",
        cpp_google="Related header, C system, C++ std, other libs",
    ),
    StyleRule(
        category="Docstrings",
        python_pep8="Triple-quoted strings per PEP 257",
        cpp_google="Doxygen-style /** */ comments",
    ),
    StyleRule(
        category="Braces / Blocks",
        python_pep8="No braces; indentation defines blocks",
        cpp_google="Opening brace on same line; closing brace on own line",
    ),
]

PACKAGE_MANAGER_COMPARISON: Dict[str, Dict[str, str]] = {
    "Isolation": {
        "python_venv": "venv creates isolated Python interpreter + site-packages",
        "cpp_conan": "Conan uses profiles to isolate compiler/settings per project",
        "cpp_vcpkg": "vcpkg installs per-triplet; no full interpreter isolation",
    },
    "Manifest": {
        "python_venv": "requirements.txt or pyproject.toml",
        "cpp_conan": "conanfile.py or conanfile.txt",
        "cpp_vcpkg": "vcpkg.json (manifest mode)",
    },
    "Lock File": {
        "python_venv": "pip freeze > requirements.txt or poetry.lock",
        "cpp_conan": "conan.lock (auto-generated)",
        "cpp_vcpkg": "versions/ directory in registry",
    },
    "Scope": {
        "python_venv": "Python packages only (pure Python / wheels)",
        "cpp_conan": "C/C++ libraries, build systems, toolchains",
        "cpp_vcpkg": "C/C++ libraries (focuses on Windows/Linux/macOS)",
    },
}


# ===================================================================
# Section 2: PEP 8 Code Style Checker (simplified)
# ===================================================================

@dataclass
class StyleViolation:
    """Represents a single PEP 8 style violation."""
    file_path: str
    line_number: int
    column: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number}:{self.column}: {self.code} {self.message}"


class PEP8Checker:
    """
    A simplified PEP 8 style checker that validates common rules.

    This is a teaching example -- production projects should use
    ``flake8``, ``ruff``, or ``pycodestyle`` directly.

    Attributes:
        max_line_length: Maximum allowed line width.
        violations: Accumulated violations after ``check_file`` or
            ``check_source`` is called.
    """

    # Regex patterns for common PEP 8 checks
    _TRAILING_WHITESPACE_RE: re.Pattern[str] = re.compile(r"[ \t]+$")
    _INDENTATION_RE: re.Pattern[str] = re.compile(r"^( {1,3}|\t+)")
    _MISSING_SPACE_AFTER_COMMA_RE: re.Pattern[str] = re.compile(
        r",[^\s\n\]\)]"
    )
    _MISSING_BLANK_BEFORE_DEF_RE: re.Pattern[str] = re.compile(
        r"^(    )*(def |class )"
    )

    def __init__(self, max_line_length: int = 79) -> None:
        self.max_line_length: int = max_line_length
        self.violations: List[StyleViolation] = []

    def check_source(
        self, source: str, file_path: str = "<string>"
    ) -> List[StyleViolation]:
        """Check a string of Python source for PEP 8 violations."""
        violations: List[StyleViolation] = []
        lines: List[str] = source.splitlines(keepends=True)
        prev_was_blank: bool = True  # treat start-of-file as "blank"

        for line_no, line in enumerate(lines, start=1):
            stripped: str = line.rstrip("\n\r")

            # W291 - trailing whitespace
            match: Optional[re.Match[str]] = self._TRAILING_WHITESPACE_RE.search(
                line
            )
            if match:
                violations.append(
                    StyleViolation(
                        file_path=file_path,
                        line_number=line_no,
                        column=match.start() + 1,
                        code="W291",
                        message="trailing whitespace",
                    )
                )

            # E501 - line too long
            if len(stripped) > self.max_line_length:
                violations.append(
                    StyleViolation(
                        file_path=file_path,
                        line_number=line_no,
                        column=self.max_line_length + 1,
                        code="E501",
                        message=(
                            f"line too long "
                            f"({len(stripped)} > {self.max_line_length})"
                        ),
                    )
                )

            # E302 - expected 2 blank lines before a top-level def/class
            if not line.startswith(" ") and not line.startswith("\t"):
                indent_match: Optional[re.Match[str]] = (
                    self._MISSING_BLANK_BEFORE_DEF_RE.match(line)
                )
                if indent_match and not prev_was_blank:
                    violations.append(
                        StyleViolation(
                            file_path=file_path,
                            line_number=line_no,
                            column=1,
                            code="E302",
                            message="expected 2 blank lines before def/class",
                        )
                    )

            # E231 - missing whitespace after ','
            comma_match: Optional[re.Match[str]] = (
                self._MISSING_SPACE_AFTER_COMMA_RE.search(stripped)
            )
            if comma_match:
                violations.append(
                    StyleViolation(
                        file_path=file_path,
                        line_number=line_no,
                        column=comma_match.start() + 1,
                        code="E231",
                        message="missing whitespace after ','",
                    )
                )

            prev_was_blank = stripped.strip() == ""

        self.violations.extend(violations)
        return violations

    def check_file(self, file_path: Union[str, Path]) -> List[StyleViolation]:
        """Check a Python file on disk for PEP 8 violations."""
        path: Path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")
        source: str = path.read_text(encoding="utf-8")
        return self.check_source(source, file_path=str(path))


# ===================================================================
# Section 3: Docstring Validator
# ===================================================================

class DocstringValidator:
    """
    Validates that public modules, classes, and functions have docstrings
    conforming to PEP 257 conventions.

    Only performs static text inspection (not AST-based) for portability.
    """

    _CLASS_RE: re.Pattern[str] = re.compile(r"^class\s+(\w+)")
    _DEF_RE: re.Pattern[str] = re.compile(r"^(\s*)def\s+(\w+)\s*\(")
    _DOCSTRING_RE: re.Pattern[str] = re.compile(r'^\s*(""".*?"""|\'\'\'.*?\'\'\')', re.DOTALL)

    @dataclass
    class DocstringIssue:
        file_path: str
        line_number: int
        name: str
        kind: str  # "module", "class", "function"

    def validate_file(
        self, file_path: Union[str, Path]
    ) -> List["DocstringValidator.DocstringIssue"]:
        """Return a list of missing-docstring issues for *file_path*."""
        path: Path = Path(file_path)
        source: str = path.read_text(encoding="utf-8")
        lines: List[str] = source.splitlines()
        issues: List[DocstringValidator.DocstringIssue] = []

        # Module-level docstring
        stripped_first: str = lines[0].strip() if lines else ""
        if not stripped_first.startswith(('"""', "'''")):
            issues.append(
                self.DocstringIssue(
                    file_path=str(path),
                    line_number=1,
                    name=path.stem,
                    kind="module",
                )
            )

        # Scan for class / function definitions
        for idx, line in enumerate(lines):
            class_match: Optional[re.Match[str]] = self._CLASS_RE.match(line)
            def_match: Optional[re.Match[str]] = self._DEF_RE.match(line)

            if class_match:
                name: str = class_match.group(1)
                if name.startswith("_"):
                    continue
                # Expect a docstring on the very next non-blank line
                if not self._has_docstring(lines, idx + 1):
                    issues.append(
                        self.DocstringIssue(
                            file_path=str(path),
                            line_number=idx + 1,
                            name=name,
                            kind="class",
                        )
                    )

            elif def_match:
                indent: str = def_match.group(1)
                func_name: str = def_match.group(2)
                if func_name.startswith("_") and func_name != "__init__":
                    continue
                if not self._has_docstring(lines, idx + 1):
                    issues.append(
                        self.DocstringIssue(
                            file_path=str(path),
                            line_number=idx + 1,
                            name=func_name,
                            kind="function",
                        )
                    )

        return issues

    @staticmethod
    def _has_docstring(lines: List[str], start_idx: int) -> bool:
        """Check whether a docstring appears at or after *start_idx*."""
        for line in lines[start_idx : start_idx + 3]:
            stripped: str = line.strip()
            if stripped == "":
                continue
            return stripped.startswith(('"""', "'''"))
        return False


# ===================================================================
# Section 4: Virtual Environment Manager
# ===================================================================

@dataclass
class VenvConfig:
    """Configuration for a Python virtual environment."""
    project_dir: Path
    venv_name: str = ".venv"
    python_executable: str = sys.executable
    requirements_file: Optional[str] = "requirements.txt"
    upgrade_pip: bool = True


class VenvManager:
    """
    Manages creation and inspection of Python virtual environments.

    Usage::

        config = VenvConfig(project_dir=Path("/my/project"))
        manager = VenvManager(config)
        manager.create()
        manager.install_requirements()
        manager.show_info()

    Comparison with C++ package managers:
        +------------------+-------------------+-------------------+
        | Feature          | Python venv       | Conan / vcpkg     |
        +------------------+-------------------+-------------------+
        | Isolation        | Per-project venv  | Profile / triplet |
        | Manifest         | requirements.txt  | conanfile / vcpkg |
        | Lock file        | poetry.lock       | conan.lock        |
        | Language scope   | Python only       | C/C++ libraries   |
        | Built into lang  | Yes (stdlib)      | No (third-party)  |
        +------------------+-------------------+-------------------+
    """

    def __init__(self, config: VenvConfig) -> None:
        self.config: VenvConfig = config
        self.venv_path: Path = config.project_dir / config.venv_name

    def create(self) -> Path:
        """Create a new virtual environment. Returns the venv path."""
        logger.info("Creating virtual environment at %s", self.venv_path)
        subprocess.run(
            [self.config.python_executable, "-m", "venv", str(self.venv_path)],
            check=True,
        )
        if self.config.upgrade_pip:
            pip_exe: str = self._pip_path()
            logger.info("Upgrading pip inside the new venv...")
            subprocess.run(
                [pip_exe, "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
            )
        logger.info("Virtual environment ready at %s", self.venv_path)
        return self.venv_path

    def install_requirements(self) -> None:
        """Install packages from the requirements file."""
        req: Optional[str] = self.config.requirements_file
        if req is None:
            logger.warning("No requirements file configured; skipping.")
            return
        req_path: Path = self.config.project_dir / req
        if not req_path.exists():
            logger.warning("Requirements file %s not found; skipping.", req_path)
            return
        pip_exe: str = self._pip_path()
        logger.info("Installing dependencies from %s ...", req_path)
        subprocess.run(
            [pip_exe, "install", "-r", str(req_path)],
            check=True,
        )

    def show_info(self) -> Dict[str, str]:
        """Return information about the virtual environment."""
        info: Dict[str, str] = {
            "venv_path": str(self.venv_path),
            "python": self._python_path(),
            "pip": self._pip_path(),
            "exists": str(self.venv_path.exists()),
            "platform": platform.platform(),
        }
        for key, value in info.items():
            logger.info("  %s: %s", key, value)
        return info

    def _python_path(self) -> str:
        """Return the path to the venv's Python executable."""
        if platform.system() == "Windows":
            return str(self.venv_path / "Scripts" / "python.exe")
        return str(self.venv_path / "bin" / "python")

    def _pip_path(self) -> str:
        """Return the path to the venv's pip executable."""
        if platform.system() == "Windows":
            return str(self.venv_path / "Scripts" / "pip.exe")
        return str(self.venv_path / "bin" / "pip")


# ===================================================================
# Section 5: Project Scaffolding / Setup Script
# ===================================================================

@dataclass
class ProjectTemplate:
    """Defines the structure of a new Python project."""
    name: str
    root_dir: Path
    author: str = "Team"
    license_: str = "MIT"
    python_requires: str = ">=3.10"
    create_venv: bool = True
    init_git: bool = True
    directories: List[str] = field(default_factory=list)
    files: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Populate sensible defaults for directories and files."""
        if not self.directories:
            self.directories = [
                f"src/{self.name}",
                "tests",
                "docs",
                "scripts",
            ]
        if not self.files:
            pkg: str = self.name
            self.files = {
                "pyproject.toml": self._pyproject_toml(pkg),
                "README.md": f"# {self.name}\n\nProject description.\n",
                ".gitignore": self._default_gitignore(),
                "Makefile": self._default_makefile(pkg),
                ".pre-commit-config.yaml": self._default_precommit(),
                f"src/{pkg}/__init__.py": '"""Package initializer."""\n',
                f"src/{pkg}/__main__.py": self._main_template(pkg),
                "tests/__init__.py": "",
                "tests/test_sample.py": self._sample_test(pkg),
            }

    # -- Template generators -----------------------------------------------

    @staticmethod
    def _pyproject_toml(pkg: str) -> str:
        return textwrap.dedent(f"""\
            [build-system]
            requires = ["setuptools>=68.0", "wheel"]
            build-backend = "setuptools.build_meta"

            [project]
            name = "{pkg}"
            version = "0.1.0"
            requires-python = ">=3.10"
            dependencies = []

            [project.optional-dependencies]
            dev = [
                "flake8",
                "mypy",
                "ruff",
                "pytest",
                "pre-commit",
            ]

            [tool.mypy]
            python_version = "3.10"
            warn_return_any = true
            warn_unused_configs = true
            disallow_untyped_defs = true

            [tool.ruff]
            line-length = 79
            select = ["E", "F", "W", "I"]
        """)

    @staticmethod
    def _default_gitignore() -> str:
        return textwrap.dedent("""\
            __pycache__/
            *.py[cod]
            *.egg-info/
            dist/
            build/
            .venv/
            .mypy_cache/
            .pytest_cache/
            .ruff_cache/
            *.egg
        """)

    @staticmethod
    def _default_makefile(pkg: str) -> str:
        return textwrap.dedent(f"""\
            .PHONY: lint typecheck test clean

            lint:
            \t@echo "Running linter (ruff)..."
            \truff check src/ tests/

            typecheck:
            \t@echo "Running type checker (mypy)..."
            \tmypy src/{pkg}/

            test:
            \t@echo "Running tests (pytest)..."
            \tpytest tests/ -v

            clean:
            \trm -rf build/ dist/ *.egg-info __pycache__
        """)

    @staticmethod
    def _default_precommit() -> str:
        return textwrap.dedent("""\
            repos:
              - repo: https://github.com/pre-commit/pre-commit-hooks
                rev: v4.6.0
                hooks:
                  - id: trailing-whitespace
                  - id: end-of-file-fixer
                  - id: check-yaml
                  - id: check-added-large-files

              - repo: https://github.com/astral-sh/ruff-pre-commit
                rev: v0.4.8
                hooks:
                  - id: ruff
                    args: [--fix]

              - repo: https://github.com/pre-commit/mirrors-mypy
                rev: v1.10.0
                hooks:
                  - id: mypy
                    additional_dependencies: []
        """)

    @staticmethod
    def _main_template(pkg: str) -> str:
        return textwrap.dedent(f'''\
            """CLI entry point for {pkg}."""

            from __future__ import annotations

            import sys


            def main() -> int:
                """Run the application and return an exit code."""
                print("Hello from {pkg}!")
                return 0


            if __name__ == "__main__":
                sys.exit(main())
        ''')

    @staticmethod
    def _sample_test(pkg: str) -> str:
        return textwrap.dedent(f'''\
            """Sample test module for {pkg}."""

            from {pkg}.__main__ import main


            def test_main_returns_zero() -> None:
                """``main`` should return 0 on success."""
                assert main() == 0
        ''')


class ProjectScaffolder:
    """
    Creates a new Python project from a :class:`ProjectTemplate`.

    This replaces manual ``mkdir`` + ``touch`` workflows and ensures every
    new repository starts with consistent tooling (linting, typing, tests,
    pre-commit hooks, and a Makefile).

    Example::

        template = ProjectTemplate(
            name="myapp",
            root_dir=Path("/tmp/myapp"),
        )
        scaffolder = ProjectScaffolder(template)
        scaffolder.scaffold()
    """

    def __init__(self, template: ProjectTemplate) -> None:
        self.template: ProjectTemplate = template

    def scaffold(self) -> Path:
        """Create all directories and files defined in the template."""
        root: Path = self.template.root_dir
        logger.info("Scaffolding project '%s' at %s", self.template.name, root)

        # Create directories
        for directory in self.template.directories:
            dir_path: Path = root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug("  Created directory: %s", dir_path)

        # Create files
        for relative_path, content in self.template.files.items():
            file_path: Path = root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            logger.debug("  Created file: %s", file_path)

        # Optionally initialize a git repository
        if self.template.init_git:
            self._init_git(root)

        # Optionally create a virtual environment
        if self.template.create_venv:
            venv_config = VenvConfig(project_dir=root)
            VenvManager(venv_config).create()

        logger.info("Project '%s' scaffolded successfully.", self.template.name)
        return root

    @staticmethod
    def _init_git(directory: Path) -> None:
        """Initialize a git repository in *directory*."""
        if (directory / ".git").exists():
            logger.info("Git repository already exists at %s", directory)
            return
        logger.info("Initializing git repository at %s", directory)
        subprocess.run(
            ["git", "init", str(directory)],
            check=True,
            capture_output=True,
        )


# ===================================================================
# Section 6: Pre-Commit Hook Manager
# ===================================================================

class PreCommitManager:
    """
    Manages pre-commit hooks for a Python project.

    This class wraps the ``pre-commit`` CLI to install, run, and
    update hooks defined in ``.pre-commit-config.yaml``.

    Attributes:
        project_dir: Root directory of the project.
    """

    def __init__(self, project_dir: Union[str, Path]) -> None:
        self.project_dir: Path = Path(project_dir)

    def install(self) -> bool:
        """Install pre-commit hooks into the .git/hooks directory."""
        logger.info("Installing pre-commit hooks...")
        try:
            subprocess.run(
                ["pre-commit", "install"],
                cwd=str(self.project_dir),
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("Pre-commit hooks installed successfully.")
            return True
        except FileNotFoundError:
            logger.error(
                "pre-commit is not installed. "
                "Install it with: pip install pre-commit"
            )
            return False
        except subprocess.CalledProcessError as exc:
            logger.error("Failed to install hooks: %s", exc.stderr)
            return False

    def run_all(self, all_files: bool = False) -> Tuple[bool, str]:
        """Run all pre-commit hooks and return (success, output)."""
        cmd: List[str] = ["pre-commit", "run"]
        if all_files:
            cmd.append("--all-files")
        try:
            result: subprocess.CompletedProcess[str] = subprocess.run(
                cmd,
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
            )
            success: bool = result.returncode == 0
            output: str = result.stdout + result.stderr
            if success:
                logger.info("All pre-commit hooks passed.")
            else:
                logger.warning("Some pre-commit hooks failed.")
            return success, output
        except FileNotFoundError:
            logger.error("pre-commit is not installed.")
            return False, "pre-commit not found"

    def update(self) -> bool:
        """Update pre-commit hooks to the latest versions."""
        logger.info("Updating pre-commit hooks...")
        try:
            subprocess.run(
                ["pre-commit", "autoupdate"],
                cwd=str(self.project_dir),
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("Pre-commit hooks updated.")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            logger.error("Failed to update hooks: %s", exc)
            return False


# ===================================================================
# Section 7: Unified Code Quality Checker
# ===================================================================

@dataclass
class QualityReport:
    """Aggregated report from all quality checks."""
    file_path: str
    style_violations: List[StyleViolation] = field(default_factory=list)
    docstring_issues: List[Any] = field(default_factory=list)
    type_check_passed: bool = True
    lint_passed: bool = True
    overall_passed: bool = True

    def summary(self) -> str:
        """Return a human-readable summary of the report."""
        lines: List[str] = [
            f"Quality Report for: {self.file_path}",
            "=" * 50,
            f"  Style violations  : {len(self.style_violations)}",
            f"  Docstring issues  : {len(self.docstring_issues)}",
            f"  Type check passed : {self.type_check_passed}",
            f"  Lint passed       : {self.lint_passed}",
            f"  Overall passed    : {self.overall_passed}",
        ]
        if self.style_violations:
            lines.append("\n  Style Violations:")
            for v in self.style_violations[:10]:
                lines.append(f"    {v}")
            if len(self.style_violations) > 10:
                lines.append(
                    f"    ... and {len(self.style_violations) - 10} more"
                )
        if self.docstring_issues:
            lines.append("\n  Docstring Issues:")
            for issue in self.docstring_issues[:10]:
                lines.append(
                    f"    Line {issue.line_number}: "
                    f"{issue.kind} '{issue.name}' missing docstring"
                )
        return "\n".join(lines)


class QualityChecker:
    """
    Runs multiple quality checks against Python source files.

    Checks performed:
        1. PEP 8 style (via :class:`PEP8Checker`)
        2. Docstring presence (via :class:`DocstringValidator`)
        3. External lint (``ruff`` or ``flake8``) if available
        4. External type checking (``mypy``) if available

    Example::

        checker = QualityChecker()
        report = checker.run(Path("src/myapp/__main__.py"))
        print(report.summary())
    """

    def __init__(
        self,
        max_line_length: int = 79,
        use_ruff: bool = True,
        use_mypy: bool = True,
    ) -> None:
        self.style_checker: PEP8Checker = PEP8Checker(
            max_line_length=max_line_length
        )
        self.docstring_validator: DocstringValidator = DocstringValidator()
        self.use_ruff: bool = use_ruff
        self.use_mypy: bool = use_mypy

    def run(self, file_path: Union[str, Path]) -> QualityReport:
        """Run all quality checks on a single file."""
        path: Path = Path(file_path)
        report = QualityReport(file_path=str(path))

        # 1. Style check
        logger.info("Checking style for %s ...", path.name)
        report.style_violations = self.style_checker.check_file(path)

        # 2. Docstring check
        logger.info("Checking docstrings for %s ...", path.name)
        report.docstring_issues = self.docstring_validator.validate_file(path)

        # 3. External lint
        if self.use_ruff:
            report.lint_passed = self._run_external_lint(path)

        # 4. Type check
        if self.use_mypy:
            report.type_check_passed = self._run_mypy(path)

        # Overall
        report.overall_passed = (
            len(report.style_violations) == 0
            and len(report.docstring_issues) == 0
            and report.lint_passed
            and report.type_check_passed
        )

        logger.info(
            "Quality check complete for %s: %s",
            path.name,
            "PASSED" if report.overall_passed else "FAILED",
        )
        return report

    def run_directory(
        self, directory: Union[str, Path], glob_pattern: str = "**/*.py"
    ) -> List[QualityReport]:
        """Run quality checks on all matching files in a directory."""
        root: Path = Path(directory)
        reports: List[QualityReport] = []
        for py_file in sorted(root.glob(glob_pattern)):
            reports.append(self.run(py_file))
        return reports

    # -- External tool runners ---------------------------------------------

    @staticmethod
    def _run_external_lint(path: Path) -> bool:
        """Run ``ruff check`` on a file. Returns True if clean."""
        for tool in (["ruff", "check"], ["flake8"]):
            try:
                result: subprocess.CompletedProcess[str] = subprocess.run(
                    [*tool, str(path)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return True
                logger.warning(
                    "%s reported issues:\n%s",
                    tool[0],
                    result.stdout.strip(),
                )
                return False
            except FileNotFoundError:
                continue
        logger.warning("Neither ruff nor flake8 found; skipping lint.")
        return True  # no tool -> assume OK

    @staticmethod
    def _run_mypy(path: Path) -> bool:
        """Run ``mypy`` on a file. Returns True if clean."""
        try:
            result: subprocess.CompletedProcess[str] = subprocess.run(
                ["mypy", "--ignore-missing-imports", str(path)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return True
            logger.warning("mypy reported issues:\n%s", result.stdout.strip())
            return False
        except FileNotFoundError:
            logger.warning("mypy not found; skipping type check.")
            return True


# ===================================================================
# Section 8: Git Workflow Helpers (educational reference)
# ===================================================================

class GitWorkflow(Enum):
    """Supported Git branching strategies."""
    GITHUB_FLOW = "github-flow"
    GIT_FLOW = "git-flow"


@dataclass
class GitBranchInfo:
    """Represents a branch in a Git workflow."""
    name: str
    is_protected: bool = False
    upstream: Optional[str] = None
    description: str = ""


GIT_FLOW_BRANCHES: Dict[str, GitBranchInfo] = {
    "master": GitBranchInfo(
        name="master",
        is_protected=True,
        description="Production-ready code; tagged on release.",
    ),
    "develop": GitBranchInfo(
        name="develop",
        is_protected=True,
        description="Integration branch for next release.",
    ),
    "feature/*": GitBranchInfo(
        name="feature/<name>",
        description="Short-lived branches for new features; merge into develop.",
    ),
    "release/*": GitBranchInfo(
        name="release/<version>",
        description="Release preparation; merge into master and develop.",
    ),
    "hotfix/*": GitBranchInfo(
        name="hotfix/<version>",
        description="Emergency fixes branched from master; merge back to master and develop.",
    ),
}


def print_git_flow_summary() -> str:
    """Return a human-readable summary of the Git-flow branching model."""
    lines: List[str] = [
        "Git-Flow Branching Model",
        "=" * 40,
    ]
    for branch_name, info in GIT_FLOW_BRANCHES.items():
        lines.append(f"  {branch_name:<15}  {'[protected]' if info.is_protected else ''}")
        lines.append(f"  {'':15}  {info.description}")
    return "\n".join(lines)


# ===================================================================
# Section 9: Comparison Printer (utility)
# ===================================================================

def print_style_comparison() -> None:
    """Print a formatted table comparing PEP 8 and Google C++ Style Guide."""
    print("\n" + "=" * 78)
    print("  Python PEP 8  vs  C++ Google Style Guide")
    print("=" * 78)
    header: str = f"{'Category':<20} {'Python PEP 8':<28} {'C++ Google Style':<28}"
    print(header)
    print("-" * 78)
    for rule in STYLE_COMPARISON:
        print(f"{rule.category:<20} {rule.python_pep8:<28} {rule.cpp_google:<28}")
    print()


def print_package_manager_comparison() -> None:
    """Print a formatted table comparing Python venv with Conan/vcpkg."""
    print("\n" + "=" * 78)
    print("  Python venv  vs  C++ Conan / vcpkg")
    print("=" * 78)
    for aspect, details in PACKAGE_MANAGER_COMPARISON.items():
        print(f"\n  [{aspect}]")
        print(f"    Python venv : {details['python_venv']}")
        print(f"    C++ Conan   : {details['cpp_conan']}")
        print(f"    C++ vcpkg   : {details['cpp_vcpkg']}")
    print()


# ===================================================================
# Section 10: Main Entry Point
# ===================================================================

def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="91_team_dev",
        description=(
            "Day 91: Team development tools -- code style checking, "
            "project scaffolding, pre-commit hooks, and quality reports."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # -- compare -----------------------------------------------------------
    compare_parser = subparsers.add_parser(
        "compare",
        help="Print style-guide and package-manager comparisons.",
    )
    compare_parser.add_argument(
        "--style",
        action="store_true",
        help="Show PEP 8 vs C++ Google Style Guide comparison.",
    )
    compare_parser.add_argument(
        "--packages",
        action="store_true",
        help="Show Python venv vs C++ Conan/vcpkg comparison.",
    )

    # -- scaffold ----------------------------------------------------------
    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="Scaffold a new Python project with best-practice tooling.",
    )
    scaffold_parser.add_argument(
        "name",
        help="Project name (used as the package name).",
    )
    scaffold_parser.add_argument(
        "--dir",
        dest="root_dir",
        default=None,
        help="Root directory (defaults to ./<name>).",
    )
    scaffold_parser.add_argument(
        "--no-venv",
        action="store_true",
        help="Skip virtual environment creation.",
    )
    scaffold_parser.add_argument(
        "--no-git",
        action="store_true",
        help="Skip git init.",
    )

    # -- check -------------------------------------------------------------
    check_parser = subparsers.add_parser(
        "check",
        help="Run code quality checks on a file or directory.",
    )
    check_parser.add_argument(
        "path",
        help="File or directory to check.",
    )
    check_parser.add_argument(
        "--max-line-length",
        type=int,
        default=79,
        help="Maximum allowed line length (default: 79).",
    )
    check_parser.add_argument(
        "--no-mypy",
        action="store_true",
        help="Skip mypy type checking.",
    )

    # -- precommit ---------------------------------------------------------
    precommit_parser = subparsers.add_parser(
        "precommit",
        help="Manage pre-commit hooks.",
    )
    precommit_parser.add_argument(
        "action",
        choices=["install", "run", "update"],
        help="Action to perform.",
    )
    precommit_parser.add_argument(
        "--dir",
        dest="project_dir",
        default=".",
        help="Project directory (default: current directory).",
    )

    # -- gitflow -----------------------------------------------------------
    subparsers.add_parser(
        "gitflow",
        help="Print a summary of the Git-flow branching model.",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Returns 0 on success, non-zero on failure."""
    parser: argparse.ArgumentParser = _build_parser()
    args: argparse.Namespace = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    # -- compare -----------------------------------------------------------
    if args.command == "compare":
        if args.style or not args.packages:
            print_style_comparison()
        if args.packages or not args.style:
            print_package_manager_comparison()
        return 0

    # -- scaffold ----------------------------------------------------------
    if args.command == "scaffold":
        root: Path = Path(args.root_dir) if args.root_dir else Path(args.name)
        template = ProjectTemplate(
            name=args.name,
            root_dir=root,
            create_venv=not args.no_venv,
            init_git=not args.no_git,
        )
        scaffolder = ProjectScaffolder(template)
        scaffolder.scaffold()
        print(f"\nProject '{args.name}' created at {root.resolve()}")
        return 0

    # -- check -------------------------------------------------------------
    if args.command == "check":
        checker = QualityChecker(
            max_line_length=args.max_line_length,
            use_mypy=not args.no_mypy,
        )
        target: Path = Path(args.path)
        if target.is_dir():
            reports: List[QualityReport] = checker.run_directory(target)
        else:
            reports = [checker.run(target)]

        all_passed: bool = True
        for report in reports:
            print(report.summary())
            print()
            if not report.overall_passed:
                all_passed = False

        return 0 if all_passed else 1

    # -- precommit ---------------------------------------------------------
    if args.command == "precommit":
        manager = PreCommitManager(args.project_dir)
        if args.action == "install":
            success: bool = manager.install()
            return 0 if success else 1
        if args.action == "run":
            ok, output = manager.run_all(all_files=True)
            print(output)
            return 0 if ok else 1
        if args.action == "update":
            ok = manager.update()
            return 0 if ok else 1
        return 0

    # -- gitflow -----------------------------------------------------------
    if args.command == "gitflow":
        print(print_git_flow_summary())
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
