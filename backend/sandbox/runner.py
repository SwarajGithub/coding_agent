import os
import subprocess
import logging
from typing import Dict, Any

logger = logging.getLogger("agent.sandbox.runner")

BASE_WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), "workspace"))
TARGET_CODE_FILE = os.path.join(BASE_WORKSPACE, "solution.py")
TARGET_TEST_FILE = os.path.join(BASE_WORKSPACE, "test_solution.py")


def ensure_workspace_exists() -> None:
    if not os.path.exists(BASE_WORKSPACE):
        os.makedirs(BASE_WORKSPACE, exist_ok=True)

    init_file = os.path.join(BASE_WORKSPACE, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("")

    if not os.path.exists(TARGET_CODE_FILE):
        with open(TARGET_CODE_FILE, "w", encoding="utf-8") as f:
            f.write("# Placeholder for autonomous agent code generation pipeline\n")


def run_code_in_sandbox(code: str, tests: str, timeout_seconds: int = 5) -> Dict[str, Any]:
    ensure_workspace_exists()

    with open(TARGET_CODE_FILE, "w", encoding="utf-8") as f:
        f.write(code)

    with open(TARGET_TEST_FILE, "w", encoding="utf-8") as f:
        f.write(tests)

    logger.info("Executing pytest runner...")

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", TARGET_TEST_FILE, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=BASE_WORKSPACE
        )

        if result.returncode == 0:
            output_logs = "PASSED\n" + result.stdout
        else:
            output_logs = f"FAILED\n---STDOUT---\n{result.stdout}\n---STDERR---\n{result.stderr}"

    except subprocess.TimeoutExpired:
        logger.error(f"Execution runtime exceeded timeout: {timeout_seconds}s")
        output_logs = f"FAILED\nRuntime Execution Timeout Error: The test suite exceeded the {timeout_seconds} second limit."
    except Exception as e:
        logger.critical(f"System tracking error encountered inside workspace processing runtime: {str(e)}")
        output_logs = f"FAILED\nInternal Sandbox Execution Fault: {str(e)}"

    return {
        "output_logs": output_logs
    }
