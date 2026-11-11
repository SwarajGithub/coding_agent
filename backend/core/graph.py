import logging
import re

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from core.state import AgentState
from config.settings import get_configured_llm
from sandbox.runner import run_code_in_sandbox
from evaluators.judge import evaluate_code_quality

logger = logging.getLogger("agent.core.graph")


def extract_clean_python(raw_text: str) -> str:
    """Strips Qwen3 <think> tags and extracts the main Python code block."""
    # 1. Remove Qwen3 thinking blocks so they don't pollute code or context
    cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()

    # 2. Find all ```python ... ``` or ``` ... ``` blocks
    blocks = re.findall(r"```(?:python)?\n(.*?)```", cleaned, flags=re.DOTALL)
    if blocks:
        # Return the longest code block (ignores small 1-line import snippets)
        return max(blocks, key=len).strip()

    return cleaned

def verify_test_syntax_node(state: AgentState) -> dict:

    import subprocess
    from sandbox.runner import TARGET_TEST_FILE, ensure_workspace_exists

    ensure_workspace_exists()
    with open(TARGET_TEST_FILE, "w", encoding="utf-8") as f:
        f.write(state["test_suite"])

    result = subprocess.run(
        ["python", "-m", "py_compile", TARGET_TEST_FILE],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        logger.warning("Structural error detected inside user-provided test suite!")
        return {"test_results": f"TEST_SYNTAX_ERROR\n{result.stderr}"}

    return {"test_results": "TEST_SYNTAX_OK"}


def fix_test_suite_node(state: AgentState) -> dict:
    llm = get_configured_llm(temperature=0.0)

    system_prompt = SystemMessage(
        content="You are an expert QA and automation engineer.\n"
                "The test suite provided has a compilation or structural error.\n"
                "Fix the test code syntax so it compiles successfully. Return ONLY valid Python code inside markdown blocks."
    )

    conversation = [
        system_prompt,
        HumanMessage(
            content=f"Original broken test file:\n{state['test_suite']}\n\nCompilation Error:\n{state['test_results']}")
    ]

    response = llm.invoke(conversation)
    extracted_code = extract_clean_python(response.content)
    fixed_tests = extracted_code
    if "```python" in fixed_tests:
        fixed_tests = fixed_tests.split("```python")[1].split("```")[0].strip()

    return {
        "test_suite": fixed_tests,
        "retry_count": state["retry_count"] + 1
    }


def generate_code_node(state: AgentState) -> dict:
    llm = get_configured_llm(temperature=0.0)

    system_prompt = SystemMessage(
        content="You are an elite autonomous TDD software engineer.\n"
                "Generate ONLY execution-ready Python code. Do not wrap code in extra explanations.\n"
                "Always wrap python blocks inside proper markdown blocks."
    )

    conversation = [system_prompt] + state["messages"]

    if state["test_results"] and "FAILED" in state["test_results"]:
        feedback_msg = HumanMessage(
            content=f"Your previous attempt failed the test suite with this trace:\n"
                    f"{state['test_results']}\n"
                    f"Analyze the failures, identify bugs, and rewrite the fixed code."
        )
        conversation.append(feedback_msg)
    else:
        init_msg = HumanMessage(
            content=f"Write code matching this specification:\n{state['requirement']}\n"
                    f"It must pass this test layout:\n{state['test_suite']}"
        )
        conversation.append(init_msg)

    response = llm.invoke(conversation)
    extracted_code = extract_clean_python(response.content)
    if "```python" in extracted_code:
        extracted_code = extracted_code.split("```python")[1].split("```")[0].strip()

    return {
        "code_draft": extracted_code,
        "messages": state["messages"] + [AIMessage(content=response.content)],
        "retry_count": state["retry_count"] + 1
    }


def run_tests_node(state: AgentState) -> dict:
    runner_output = run_code_in_sandbox(code=state["code_draft"], tests=state["test_suite"])
    return {"test_results": runner_output["output_logs"]}


# --- Routing Gates ---

def test_gate(state: AgentState) -> str:
    """Routes based on whether the test suite itself is syntactically correct."""
    if "TEST_SYNTAX_ERROR" in state["test_results"]:
        return "fix_test_suite"
    return "generate_code"


def execution_gate(state: AgentState) -> str:
    """Routes based on unit test outcomes."""
    if "PASSED" in state["test_results"]:
        return "evaluate_quality"
    if state["retry_count"] >= state["max_retries"]:
        return "graceful_exit"
    return "generate_code"


def evaluate_quality_node(state: AgentState) -> dict:
    """Applies the LLM quality gate check on top of passing code."""
    review_report = evaluate_code_quality(
        requirement=state["requirement"],
        code_draft=state["code_draft"]
    )

    # Append the judge results to the test logs or track via messages
    report_summary = (
        f"\n\n--- QUALITY GATE RESULT: {review_report.status} ---\n"
        f"Readability Score: {review_report.readability_score}/10\n"
        f"Complexity: {review_report.complexity_rating}\n"
        f"Critique: {review_report.critique}\n"
        f"Vulnerabilities Found: {', '.join(review_report.security_vulnerabilities) if review_report.security_vulnerabilities else 'None'}"
    )

    return {"test_results": state["test_results"] + report_summary}



# --- Assemble the Dual-Healing Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("verify_test_syntax", verify_test_syntax_node)
workflow.add_node("fix_test_suite", fix_test_suite_node)
workflow.add_node("generate_code", generate_code_node)
workflow.add_node("run_tests", run_tests_node)
workflow.add_node("evaluate_quality", evaluate_quality_node)

# Execution Flow Routing
workflow.set_entry_point("verify_test_syntax")

workflow.add_conditional_edges("verify_test_syntax", test_gate, {
    "fix_test_suite": "fix_test_suite",
    "generate_code": "generate_code"
})

# If we fix the test suite, re-verify its syntax immediately
workflow.add_edge("fix_test_suite", "verify_test_syntax")

workflow.add_edge("generate_code", "run_tests")

workflow.add_conditional_edges("run_tests", execution_gate, {
    "generate_code": "generate_code",
    "evaluate_quality": "evaluate_quality",
    "graceful_exit": END
})
workflow.add_edge("evaluate_quality", END)

agent_graph = workflow.compile()
