from __future__ import annotations

import json
import sys
import logging
from typing import Any, Dict, TypedDict, Annotated
import operator
import hashlib

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

import programmer
from config import load_dotenv_file
from runner import run_in_container


class GraphState(TypedDict, total=False):
	query: str
	code: str
	attempt: Annotated[int, operator.add]
	max_iters: int
	run_result: Dict[str, Any] | None


def _setup_logger() -> logging.Logger:
	logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
	return logging.getLogger("graph")


logger = _setup_logger()


def _preview(text: Any, max_chars: int = 300) -> str:
	if text is None:
		return ""
	if not isinstance(text, str):
		text = str(text)
	if len(text) <= max_chars:
		return text
	return text[:max_chars] + "…"


RESET = "\033[0m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
GRAY = "\033[90m"

_ENABLE_COLOR = sys.stdout.isatty()


def _c(text: str, color: str) -> str:
	if not _ENABLE_COLOR:
		return text
	return f"{color}{text}{RESET}"


def _label(actor: str) -> str:
	color = CYAN if actor == "programmer" else MAGENTA
	return _c(f"[{actor}]", color)


def _success(text: str = "success") -> str:
	return _c(text, GREEN)


def _failure(text: str = "failure") -> str:
	return _c(text, RED)


def _dim(text: str) -> str:
	return _c(text, GRAY)


def _log_preview(label: str, text: Any) -> None:
	logger.info(f"{label} {_dim('(preview)')}:\n{_preview(text)}")



def programmer_node(state: GraphState) -> GraphState:
	phase = "generating" if not state.get("run_result") else "repairing"
	logger.info(f"{_label('programmer')} {phase} code…")
	input_text = programmer.build_input_text(
		state.get("query", ""), 
		state.get("code", ""), 
		state.get("run_result")
	)
	try:
		response_str = programmer.call_llm(input_text)
		data = json.loads(response_str)
	except (ValueError, json.JSONDecodeError) as e:
		logger.error(f"{_label('programmer')} {_failure('LLM error')}: {e}")
		raise
	new_code = str(data.get("code", ""))
	if not new_code.strip():
		logger.error(f"{_label('programmer')} {_failure('empty code returned')}")
		raise ValueError("LLM returned empty code")
	_log_preview(f"{_label('programmer')} produced code", new_code)
	return {
		"code": new_code,
		"attempt": 1,
	}


def runner_node(state: GraphState) -> GraphState:
	logger.info(f"{_label('runner')} executing code in container…")
	result = run_in_container(state.get("code", ""))
	if result.get("success"):
		logger.info(f"{_label('runner')} {_success()}")
		_log_preview(f"{_label('runner')} stdout", result.get("stdout", ""))
		_log_preview(f"{_label('runner')} code", state.get("code", ""))
	else:
		logger.info(f"{_label('runner')} {_failure()}")
		_log_preview(f"{_label('runner')} stderr", result.get("stderr", ""))
		_log_preview(f"{_label('runner')} exception", result.get("exception"))
	return {"run_result": result}


def decide_next(state: GraphState) -> str:
	result = state.get("run_result") or {}
	max_iters = int(state.get("max_iters") or 3)
	attempt = int(state.get("attempt") or 0)
	if result.get("success"):
		return "end"
	if attempt >= max_iters:
		return "end"
	return "retry"


def build_graph():
	graph = StateGraph(GraphState)
	graph.add_node("programmer", programmer_node)
	graph.add_node("runner", runner_node)
	graph.set_entry_point("programmer")
	graph.add_edge("programmer", "runner")
	graph.add_conditional_edges(
		"runner",
		decide_next,
		{"retry": "programmer", "end": END},
	)
	checkpointer = MemorySaver()
	return graph.compile(checkpointer=checkpointer)


def main() -> None:
	query = sys.argv[1]
	max_iters: int = int(sys.argv[2]) if len(sys.argv) > 2 else 3
	load_dotenv_file()
	app = build_graph()
	state: GraphState = {"query": query, "code": "", "attempt": 0, "max_iters": max_iters, "run_result": None}
	thread_id = hashlib.sha256(query.encode("utf-8")).hexdigest()[:12]
	logger.info(f"thread_id={thread_id}")
	final_state = app.invoke(state, config={"configurable": {"thread_id": thread_id}})


if __name__ == "__main__":
	main()
