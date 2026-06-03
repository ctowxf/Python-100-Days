"""
Day 67 - 环境准备 (Environment Setup)

本模块提供 Python 数据科学环境的自动化检测、验证和诊断功能。
涵盖 Anaconda/Miniconda 环境检测、JupyterLab 可用性检查、
核心数据分析库（NumPy, Pandas, Matplotlib）版本验证，
以及企业级依赖检查器和环境验证器。

对应文档: Day66-80/67.环境准备.md
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional


# ============================================================================
# 1. 基础版本与导入检查
# ============================================================================

class CheckStatus(Enum):
    """检查项的执行状态。"""
    PASS = auto()
    FAIL = auto()
    WARN = auto()
    SKIP = auto()


@dataclass
class CheckResult:
    """单项检查的结果。"""
    name: str
    status: CheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        icon = {
            CheckStatus.PASS: "[PASS]",
            CheckStatus.FAIL: "[FAIL]",
            CheckStatus.WARN: "[WARN]",
            CheckStatus.SKIP: "[SKIP]",
        }[self.status]
        return f"{icon} {self.name}: {self.message}"


def check_python_version(min_version: tuple[int, ...] = (3, 8)) -> CheckResult:
    """
    检查当前 Python 版本是否满足最低要求。

    Args:
        min_version: 最低版本号元组，默认 (3, 8)。

    Returns:
        CheckResult 对象。
    """
    current = sys.version_info[:len(min_version)]
    current_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    min_str = ".".join(str(v) for v in min_version)

    if current >= min_version:
        return CheckResult(
            name="Python 版本",
            status=CheckStatus.PASS,
            message=f"当前版本 {current_str} >= 最低要求 {min_str}",
            details={"current": current_str, "minimum": min_str},
        )
    return CheckResult(
        name="Python 版本",
        status=CheckStatus.FAIL,
        message=f"当前版本 {current_str} < 最低要求 {min_str}",
        details={"current": current_str, "minimum": min_str},
    )


def check_module_importable(module_name: str, display_name: str | None = None) -> CheckResult:
    """
    检查指定模块是否可以成功导入。

    Args:
        module_name: 模块的导入名（如 'numpy'）。
        display_name: 用于展示的友好名称，默认使用 module_name。

    Returns:
        CheckResult 对象。
    """
    label = display_name or module_name
    try:
        mod = __import__(module_name)
        version = getattr(mod, "__version__", "未知")
        return CheckResult(
            name=f"模块导入: {label}",
            status=CheckStatus.PASS,
            message=f"已安装，版本 {version}",
            details={"module": module_name, "version": version},
        )
    except ImportError:
        return CheckResult(
            name=f"模块导入: {label}",
            status=CheckStatus.FAIL,
            message=f"未安装或无法导入 '{module_name}'",
            details={"module": module_name},
        )


def check_module_version(
    module_name: str,
    min_version: str,
    display_name: str | None = None,
) -> CheckResult:
    """
    检查指定模块的版本是否满足最低要求。

    Args:
        module_name: 模块的导入名。
        min_version: 最低版本字符串（如 '1.24.0'）。
        display_name: 展示名称。

    Returns:
        CheckResult 对象。
    """
    from packaging.version import Version

    label = display_name or module_name
    try:
        mod = __import__(module_name)
        current: str = getattr(mod, "__version__", "0.0.0")
        if Version(current) >= Version(min_version):
            return CheckResult(
                name=f"版本检查: {label}",
                status=CheckStatus.PASS,
                message=f"{current} >= {min_version}",
                details={"current": current, "minimum": min_version},
            )
        return CheckResult(
            name=f"版本检查: {label}",
            status=CheckStatus.WARN,
            message=f"{current} < {min_version}，建议升级",
            details={"current": current, "minimum": min_version},
        )
    except ImportError:
        return CheckResult(
            name=f"版本检查: {label}",
            status=CheckStatus.FAIL,
            message=f"模块 '{module_name}' 未安装",
            details={"module": module_name},
        )
    except Exception as exc:
        return CheckResult(
            name=f"版本检查: {label}",
            status=CheckStatus.WARN,
            message=f"版本比较失败: {exc}",
            details={"error": str(exc)},
        )


# ============================================================================
# 2. Anaconda / Conda 环境检测
# ============================================================================

@dataclass
class CondaInfo:
    """Conda 环境信息。"""
    available: bool = False
    version: str = ""
    is_conda_env: bool = False
    env_name: str = ""
    env_location: str = ""
    default_packages: list[str] = field(default_factory=list)


def detect_conda() -> CondaInfo:
    """
    检测当前环境中 conda 的可用性和状态。

    Returns:
        CondaInfo 对象，包含 conda 的详细信息。
    """
    info = CondaInfo()

    # 检查 conda 命令是否可用
    conda_path = shutil.which("conda")
    if conda_path is None:
        return info

    info.available = True

    # 获取 conda 版本
    try:
        result = subprocess.run(
            ["conda", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            info.version = result.stdout.strip().replace("conda ", "")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # 检查是否在 conda 虚拟环境中运行
    conda_default_env = os.environ.get("CONDA_DEFAULT_ENV", "")
    conda_prefix = os.environ.get("CONDA_PREFIX", "")
    if conda_default_env:
        info.is_conda_env = True
        info.env_name = conda_default_env
        info.env_location = conda_prefix

    return info


def get_conda_env_list() -> list[dict[str, str]]:
    """
    获取 conda 所有虚拟环境列表。

    Returns:
        环境信息字典列表，每项包含 'name' 和 'path'。
    """
    envs: list[dict[str, str]] = []
    try:
        result = subprocess.run(
            ["conda", "env", "list"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return envs

        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2 and not line.startswith("base"):
                # 格式: env_name  /path/to/env
                envs.append({"name": parts[0], "path": parts[-1]})
            elif line.startswith("base") and len(parts) >= 2:
                envs.append({"name": "base", "path": parts[-1]})
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return envs


# ============================================================================
# 3. Jupyter 环境检测
# ============================================================================

@dataclass
class JupyterInfo:
    """Jupyter 环境信息。"""
    notebook_available: bool = False
    lab_available: bool = False
    lab_version: str = ""
    notebook_version: str = ""
    ipython_available: bool = False
    ipython_version: str = ""


def detect_jupyter() -> JupyterInfo:
    """
    检测 Jupyter 相关组件的可用性。

    Returns:
        JupyterInfo 对象。
    """
    info = JupyterInfo()

    # 检查 jupyter lab
    if shutil.which("jupyter") is not None:
        info.lab_available = shutil.which("jupyter-lab") is not None
        info.notebook_available = shutil.which("jupyter-notebook") is not None

    # 通过导入获取版本
    try:
        import jupyterlab
        info.lab_version = getattr(jupyterlab, "__version__", "未知")
        info.lab_available = True
    except ImportError:
        pass

    try:
        import notebook
        info.notebook_version = getattr(notebook, "__version__", "未知")
        info.notebook_available = True
    except ImportError:
        pass

    try:
        import IPython
        info.ipython_available = True
        info.ipython_version = getattr(IPython, "__version__", "未知")
    except ImportError:
        pass

    return info


# ============================================================================
# 4. 系统与平台信息收集
# ============================================================================

@dataclass
class PlatformReport:
    """当前运行平台的详细报告。"""
    system: str = ""
    release: str = ""
    version: str = ""
    machine: str = ""
    processor: str = ""
    python_implementation: str = ""
    python_compiler: str = ""
    executable_path: str = ""
    working_directory: str = ""
    encoding: str = ""
    env_conda: bool = False
    env_virtualenv: bool = False


def collect_platform_info() -> PlatformReport:
    """
    收集当前系统的平台与运行环境信息。

    Returns:
        PlatformReport 对象。
    """
    report = PlatformReport(
        system=platform.system(),
        release=platform.release(),
        version=platform.version(),
        machine=platform.machine(),
        processor=platform.processor(),
        python_implementation=platform.python_implementation(),
        python_compiler=platform.python_compiler(),
        executable_path=sys.executable,
        working_directory=os.getcwd(),
        encoding=sys.getdefaultencoding(),
        env_conda=bool(os.environ.get("CONDA_DEFAULT_ENV")),
        env_virtualenv=bool(
            os.environ.get("VIRTUAL_ENV")
            or os.environ.get("PYENV_VERSION")
        ),
    )
    return report


# ============================================================================
# 5. 数据科学核心库检查
# ============================================================================

# 核心数据科学库及其建议最低版本
DATASCIENCE_PACKAGES: dict[str, dict[str, str]] = {
    "numpy": {"display": "NumPy", "min_version": "1.24.0"},
    "pandas": {"display": "Pandas", "min_version": "2.0.0"},
    "matplotlib": {"display": "Matplotlib", "min_version": "3.7.0"},
    "scipy": {"display": "SciPy", "min_version": "1.10.0"},
    "sklearn": {"display": "scikit-learn", "min_version": "1.2.0"},
    "seaborn": {"display": "Seaborn", "min_version": "0.12.0"},
    "jupyterlab": {"display": "JupyterLab", "min_version": "4.0.0"},
    "ipython": {"display": "IPython", "min_version": "8.0.0"},
}


def check_datasience_packages() -> list[CheckResult]:
    """
    批量检查数据科学核心库的安装状态和版本。

    Returns:
        CheckResult 列表。
    """
    results: list[CheckResult] = []
    for module_name, meta in DATASCIENCE_PACKAGES.items():
        # 先检查是否可导入
        import_result = check_module_importable(module_name, meta["display"])
        results.append(import_result)

        # 如果已安装，再检查版本
        if import_result.status == CheckStatus.PASS:
            version_result = check_module_version(
                module_name, meta["min_version"], meta["display"]
            )
            results.append(version_result)

    return results


# ============================================================================
# 6. 企业级依赖检查器
# ============================================================================

@dataclass
class DependencySpec:
    """依赖项规格定义。"""
    name: str
    import_name: str
    min_version: str = ""
    max_version: str = ""
    required: bool = True
    extras: list[str] = field(default_factory=list)
    description: str = ""


class DependencyChecker:
    """
    企业级依赖检查器。

    支持从依赖规格列表中系统地检查所有依赖项，
    并生成结构化的检查报告。

    用法示例:
        checker = DependencyChecker()
        checker.add(DependencySpec("NumPy", "numpy", min_version="1.24.0"))
        checker.add(DependencySpec("Pandas", "pandas", min_version="2.0.0"))
        report = checker.run_all()
        checker.print_report(report)
    """

    def __init__(self) -> None:
        self._specs: list[DependencySpec] = []

    def add(self, spec: DependencySpec) -> None:
        """添加一个依赖项规格。"""
        self._specs.append(spec)

    def add_bulk(self, specs: Iterable[DependencySpec]) -> None:
        """批量添加依赖项规格。"""
        self._specs.extend(specs)

    def _check_one(self, spec: DependencySpec) -> CheckResult:
        """检查单个依赖项。"""
        try:
            mod = __import__(spec.import_name)
        except ImportError:
            status = CheckStatus.WARN if not spec.required else CheckStatus.FAIL
            return CheckResult(
                name=spec.name,
                status=status,
                message=f"未安装 ({spec.description})" if spec.description else "未安装",
                details={"import_name": spec.import_name, "required": spec.required},
            )

        current_version: str = getattr(mod, "__version__", "未知")
        details: dict[str, Any] = {
            "import_name": spec.import_name,
            "current_version": current_version,
            "required": spec.required,
        }

        # 版本范围检查
        if spec.min_version or spec.max_version:
            try:
                from packaging.version import Version
                ver = Version(current_version)
                if spec.min_version and ver < Version(spec.min_version):
                    return CheckResult(
                        name=spec.name,
                        status=CheckStatus.WARN,
                        message=f"版本 {current_version} 低于最低要求 {spec.min_version}",
                        details=details,
                    )
                if spec.max_version and ver > Version(spec.max_version):
                    return CheckResult(
                        name=spec.name,
                        status=CheckStatus.WARN,
                        message=f"版本 {current_version} 高于最高限制 {spec.max_version}",
                        details=details,
                    )
            except Exception:
                pass  # packaging 不可用时跳过精确版本比较

        # 检查 extras 子模块
        missing_extras: list[str] = []
        for extra in spec.extras:
            try:
                __import__(extra)
            except ImportError:
                missing_extras.append(extra)

        if missing_extras:
            return CheckResult(
                name=spec.name,
                status=CheckStatus.WARN,
                message=f"已安装 {current_version}，但缺少子模块: {', '.join(missing_extras)}",
                details={**details, "missing_extras": missing_extras},
            )

        return CheckResult(
            name=spec.name,
            status=CheckStatus.PASS,
            message=f"已安装 {current_version}",
            details=details,
        )

    def run_all(self) -> list[CheckResult]:
        """
        执行所有依赖项检查。

        Returns:
            CheckResult 列表。
        """
        return [self._check_one(spec) for spec in self._specs]

    @staticmethod
    def print_report(results: list[CheckResult]) -> None:
        """
        将检查结果格式化输出到控制台。

        Args:
            results: CheckResult 列表。
        """
        passed = sum(1 for r in results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in results if r.status == CheckStatus.FAIL)
        warned = sum(1 for r in results if r.status == CheckStatus.WARN)

        print("=" * 60)
        print("  依赖检查报告")
        print("=" * 60)
        for r in results:
            print(f"  {r}")
        print("-" * 60)
        print(f"  通过: {passed}  |  失败: {failed}  |  警告: {warned}")
        print(f"  总计: {len(results)} 项")
        print("=" * 60)

    def get_summary(self, results: list[CheckResult]) -> dict[str, int]:
        """返回统计摘要。"""
        return {
            "total": len(results),
            "passed": sum(1 for r in results if r.status == CheckStatus.PASS),
            "failed": sum(1 for r in results if r.status == CheckStatus.FAIL),
            "warned": sum(1 for r in results if r.status == CheckStatus.WARN),
            "skipped": sum(1 for r in results if r.status == CheckStatus.SKIP),
        }


# ============================================================================
# 7. 企业级环境验证器
# ============================================================================

@dataclass
class EnvironmentReport:
    """完整的环境验证报告。"""
    platform: PlatformReport
    conda: CondaInfo
    jupyter: JupyterInfo
    python_check: CheckResult
    core_packages: list[CheckResult]
    dependency_results: list[CheckResult]
    all_passed: bool = False

    def summary(self) -> str:
        """生成人类可读的摘要。"""
        lines: list[str] = []
        lines.append("=" * 64)
        lines.append("  Python 数据科学环境验证报告")
        lines.append("=" * 64)

        # 平台
        lines.append("\n--- 系统平台 ---")
        lines.append(f"  系统:       {self.platform.system} {self.platform.release}")
        lines.append(f"  架构:       {self.platform.machine}")
        lines.append(f"  Python:     {self.platform.python_implementation}")
        lines.append(f"  可执行文件: {self.platform.executable_path}")
        lines.append(f"  工作目录:   {self.platform.working_directory}")

        # Conda
        lines.append("\n--- Conda 环境 ---")
        if self.conda.available:
            lines.append(f"  Conda 版本: {self.conda.version}")
            if self.conda.is_conda_env:
                lines.append(f"  当前环境:   {self.conda.env_name}")
                lines.append(f"  环境路径:   {self.conda.env_location}")
            else:
                lines.append("  当前环境:   非 conda 虚拟环境")
        else:
            lines.append("  Conda:      未检测到")

        # Jupyter
        lines.append("\n--- Jupyter 环境 ---")
        lines.append(f"  JupyterLab:   {'可用' if self.jupyter.lab_available else '不可用'}"
                      + (f" (v{self.jupyter.lab_version})" if self.jupyter.lab_version else ""))
        lines.append(f"  Notebook:     {'可用' if self.jupyter.notebook_available else '不可用'}"
                      + (f" (v{self.jupyter.notebook_version})" if self.jupyter.notebook_version else ""))
        lines.append(f"  IPython:      {'可用' if self.jupyter.ipython_available else '不可用'}"
                      + (f" (v{self.jupyter.ipython_version})" if self.jupyter.ipython_version else ""))

        # Python 版本
        lines.append(f"\n--- Python 版本检查 ---\n  {self.python_check}")

        # 核心库
        lines.append("\n--- 核心数据科学库 ---")
        for r in self.core_packages:
            lines.append(f"  {r}")

        # 额外依赖
        if self.dependency_results:
            lines.append("\n--- 额外依赖检查 ---")
            for r in self.dependency_results:
                lines.append(f"  {r}")

        # 总结
        all_results = [self.python_check] + self.core_packages + self.dependency_results
        passed = sum(1 for r in all_results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in all_results if r.status == CheckStatus.FAIL)
        warned = sum(1 for r in all_results if r.status == CheckStatus.WARN)
        self.all_passed = (failed == 0)

        lines.append("\n" + "=" * 64)
        lines.append(f"  结果: 通过 {passed} / 失败 {failed} / 警告 {warned}")
        verdict = "环境就绪" if self.all_passed else "环境存在问题，请检查上述失败项"
        lines.append(f"  结论: {verdict}")
        lines.append("=" * 64)

        return "\n".join(lines)


class EnvironmentValidator:
    """
    企业级环境验证器。

    将平台信息收集、Conda/Jupyter 检测、Python 版本检查、
    核心库检查和自定义依赖检查整合为一次完整验证流程。

    用法示例:
        validator = EnvironmentValidator()
        validator.add_dependency(DependencySpec("Flask", "flask", min_version="2.0"))
        report = validator.validate()
        print(report.summary())
    """

    def __init__(
        self,
        *,
        min_python: tuple[int, ...] = (3, 8),
        check_core_packages: bool = True,
    ) -> None:
        self._min_python = min_python
        self._check_core = check_core_packages
        self._extra_deps: list[DependencySpec] = []

    def add_dependency(self, spec: DependencySpec) -> None:
        """添加额外的依赖项规格。"""
        self._extra_deps.append(spec)

    def validate(self) -> EnvironmentReport:
        """
        执行完整环境验证。

        Returns:
            EnvironmentReport 对象。
        """
        platform_info = collect_platform_info()
        conda_info = detect_conda()
        jupyter_info = detect_jupyter()
        python_check = check_python_version(self._min_python)

        core_results: list[CheckResult] = []
        if self._check_core:
            core_results = check_datasience_packages()

        dep_results: list[CheckResult] = []
        if self._extra_deps:
            checker = DependencyChecker()
            checker.add_bulk(self._extra_deps)
            dep_results = checker.run_all()

        return EnvironmentReport(
            platform=platform_info,
            conda=conda_info,
            jupyter=jupyter_info,
            python_check=python_check,
            core_packages=core_results,
            dependency_results=dep_results,
        )


# ============================================================================
# 8. 快速诊断工具函数
# ============================================================================

def quick_diagnose() -> None:
    """
    快速诊断当前环境并输出报告到控制台。
    适合在终端中直接运行或在 Notebook 中调用。
    """
    validator = EnvironmentValidator()
    report = validator.validate()
    print(report.summary())


def check_pip_packages() -> list[str]:
    """
    获取通过 pip 安装的所有包列表。

    Returns:
        包名列表。
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=freeze"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return [
                line.split("==")[0]
                for line in result.stdout.splitlines()
                if "==" in line
            ]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def suggest_missing_packages() -> list[str]:
    """
    根据当前环境，建议安装缺失的数据科学包。

    Returns:
        建议安装的包名列表，可直接用于 pip install。
    """
    installed = set(check_pip_packages())
    suggestions: list[str] = []
    for module_name, meta in DATASCIENCE_PACKAGES.items():
        # 检查是否已安装
        pip_name = module_name if module_name != "sklearn" else "scikit-learn"
        if pip_name not in installed:
            try:
                __import__(module_name)
            except ImportError:
                suggestions.append(pip_name)
    return suggestions


def generate_pip_install_command() -> str:
    """
    生成一条完整的 pip install 命令，用于安装所有缺失的数据科学包。

    Returns:
        pip install 命令字符串。
    """
    missing = suggest_missing_packages()
    if not missing:
        return "# 所有核心数据科学包均已安装，无需额外操作"
    return f"pip install {' '.join(missing)}"


# ============================================================================
# 9. __main__ 入口 - 独立运行时执行完整环境检查
# ============================================================================

if __name__ == "__main__":
    print("Day 67 - Python 数据科学环境检查工具")
    print()

    # 第一部分：快速诊断
    quick_diagnose()

    # 第二部分：缺失包建议
    print("\n--- 安装建议 ---")
    missing = suggest_missing_packages()
    if missing:
        print(f"  建议安装以下缺失的包:")
        for pkg in missing:
            print(f"    - {pkg}")
        print(f"\n  完整安装命令:")
        print(f"    {generate_pip_install_command()}")
    else:
        print("  所有核心数据科学包均已安装。")

    # 第三部分：Conda 虚拟环境列表
    print("\n--- Conda 虚拟环境 ---")
    conda = detect_conda()
    if conda.available:
        envs = get_conda_env_list()
        if envs:
            for env in envs:
                marker = " * " if env["name"] == conda.env_name else "   "
                print(f"  {marker}{env['name']:20s} {env['path']}")
        else:
            print("  未检测到 conda 虚拟环境。")
    else:
        print("  Conda 未安装。如需使用 conda 管理环境，")
        print("  请从 https://www.anaconda.com/ 下载安装 Anaconda 或 Miniconda。")
