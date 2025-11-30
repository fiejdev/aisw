import io
import json
import sys
import time
from collections import deque
from contextlib import redirect_stdout, redirect_stderr

MAX_LOCALS = 30
MAX_REPR = 256
MAX_EVENTS = 200


def to_jsonable(value: object) -> object:
    try:
        json.dumps(value)
        return value
    except Exception:
        representation = repr(value)
        truncated = representation[:MAX_REPR]
        if len(representation) > MAX_REPR:
            truncated += "…"
        return {"__repr__": truncated, "__type__": type(value).__name__}


def serialize_locals(locals_dict: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    count = 0
    for key, val in locals_dict.items():
        if key.startswith("__"):
            continue
        result[key] = to_jsonable(val)
        count += 1
        if count >= MAX_LOCALS:
            break
    return result


def capture_exception(exc: BaseException) -> dict[str, object]:
    tb = exc.__traceback__
    frames: list[dict[str, object]] = []
    while tb is not None:
        frame = tb.tb_frame
        frames.append(
            {
                "file": frame.f_code.co_filename,
                "line": tb.tb_lineno,
                "func": frame.f_code.co_name,
                "locals": serialize_locals(frame.f_locals),
            }
        )
        tb = tb.tb_next
    return {"type": type(exc).__name__, "message": str(exc), "frames": frames}


def main() -> None:
    code = sys.stdin.read()
    
    events: deque[dict[str, object]] = deque(maxlen=MAX_EVENTS)
    
    def tracer(frame, event, arg):
        if event == "line" and frame.f_code.co_filename == "<string>":
            events.append(
                {
                    "file": frame.f_code.co_filename,
                    "line": frame.f_lineno,
                    "func": frame.f_code.co_name,
                    "locals": serialize_locals(frame.f_locals),
                }
            )
        return tracer

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    start = time.perf_counter()
    sys.settrace(tracer)
    success = True
    exc_info = None
    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(code, {"__name__": "__main__"})
    except BaseException as exc:
        success = False
        exc_info = capture_exception(exc)
    finally:
        sys.settrace(None)
        duration_ms = int((time.perf_counter() - start) * 1000)

    result = {
        "success": success,
        "stdout": stdout_buf.getvalue(),
        "stderr": stderr_buf.getvalue(),
        "duration_ms": duration_ms,
        "trace": list(events),
    }
    if not success:
        result["exception"] = exc_info

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
