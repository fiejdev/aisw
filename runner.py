import json
import subprocess
from json import JSONDecodeError
from typing import Any, Dict


IMAGE_NAME = "dt-sandbox:py313"


def run_in_container(user_code: str, timeout_seconds: int = 420) -> Dict[str, Any]:
    docker_cmd = ["docker", "run", "--rm", "-i", IMAGE_NAME]
    completed = subprocess.run(
        docker_cmd,
        input=user_code,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        timeout=timeout_seconds,
        check=False,
    )
    stdout_text = completed.stdout.strip()
    if stdout_text:
        try:
            return json.loads(stdout_text)
        except JSONDecodeError:
            pass
    return {
        "success": False,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "duration_ms": 0,
        "trace": [],
        "exception": {
            "type": "ContainerExecutionError",
            "message": f"invalid harness output (exit {completed.returncode})",
            "frames": [],
        },
    }
