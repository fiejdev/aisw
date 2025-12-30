from typing import Any, Dict

from config import get_azure_openai_client, get_azure_deployment


def build_input_text(query: str, code: str, run_result: Dict[str, Any] | None = None) -> str:
    if not code.strip():
        # Code generation scenario
        return ("You are a senior Python coding assistant. Follow user request."
            "The code must be complete and executable.\n\n"
            f"User request: {query}\n\n"
            "Respond with JSON containing:\n"
            "- problem: Brief description of what needs to be implemented\n"
            "- root_cause: Why this code is needed\n"
            "- fix: Approach taken to implement the solution\n"
            "- code: Complete executable Python code"
        )
    else:
        # Code debugging scenario
        error_context = ""
        if run_result and not run_result.get("success"):
            error_context = (
                f"Execution failed with:\n"
                f"stdout: {run_result.get('stdout', '')}\n"
                f"stderr: {run_result.get('stderr', '')}\n"
                f"exception: {run_result.get('exception', {}).get('message', '') if run_result.get('exception') else ''}\n\n"
            )

        return (
            "You are a senior Python debugging assistant. Fix the Current code to work as per the Original request."
            "The fixed code must be complete and executable.\n\n"
            f"Original request: {query}\n"
            f"{error_context}"
            "Current code:\n"
            f"{code}\n\n"
            "Respond with JSON containing:\n"
            "- problem: What's wrong with the current code\n"
            "- root_cause: Why the issue occurred\n"
            "- fix: How you fixed it\n"
            "- code: Complete corrected Python code"
        )


def create_response_schema() -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "CodeResponse",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "problem": {"type": "string"},
                    "root_cause": {"type": "string"},
                    "fix": {"type": "string"},
                    "code": {"type": "string"}
                },
                "required": ["problem", "root_cause", "fix", "code"]
            },
        },
    }


def call_llm(input_text: str) -> str:
    client = get_azure_openai_client()
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "Output only valid JSON that adheres to the provided schema."
                    "The JSON must be valid and complete."
                    "Beyond python's native libraries, only use numpy pandas requests bs4."
                    "Keep the code minimal and aligned with best practices. No extra comments."
                ),
            },
            {"role": "user", "content": input_text},
        ],
        response_format=create_response_schema(),
        max_completion_tokens=16000,
        model=get_azure_deployment(),
    )

    return response.choices[0].message.content or ""
