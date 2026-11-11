from typing import TypedDict, List
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """Tracks global workspace context through loop execution."""
    messages: List[BaseMessage]      # Full chat history transcript (System prompts, errors, updates)
    requirement: str                 # Original core coding task instruction
    code_draft: str                  # Current raw string iteration of python code file
    test_suite: str                  # Core pytest suite provided to track verification
    test_results: str                # Latest stdout/stderr string output from the runner
    retry_count: int                 # Loop circuit breaker monitoring iteration index
    max_retries: int                 # Absolute boundary capping infinite looping
