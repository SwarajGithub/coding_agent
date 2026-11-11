import json
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.graph import agent_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent.api")

app = FastAPI(title="Autonomous TDD Agent Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentExecutionRequest(BaseModel):
    requirement: str = Field(..., description="The functional feature specs for the code component.")
    test_suite: str = Field(..., description="The initial pytest suite code string.")
    max_retries: int = Field(default=5, ge=1, le=10, description="Circuit breaker turn threshold limit.")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "tdd-agent-backend"}


@app.post("/api/agent/run")
async def run_agent_loop(request: AgentExecutionRequest):
    initial_state = {
        "messages": [],
        "requirement": request.requirement,
        "code_draft": "",
        "test_suite": request.test_suite,
        "test_results": "",
        "retry_count": 0,
        "max_retries": request.max_retries
    }

    async def event_streamer():
        try:
            logger.info("Starting execution trace stream...")

            async for event_update in agent_graph.astream(initial_state, stream_mode="updates"):
                node_name = list(event_update.keys())[0] if isinstance(event_update, dict) else str(event_update)
                node_payload = event_update[node_name]
                stream_payload = {
                    "node": node_name,
                    "retry_count": node_payload.get("retry_count"),
                    "code_draft": node_payload.get("code_draft", ""),
                    "test_suite": node_payload.get("test_suite", ""),
                    "test_results": node_payload.get("test_results", "")
                }
                yield f"data: {json.dumps(stream_payload)}\n\n"
                await asyncio.sleep(0.1)

            yield "data: {\"status\": \"COMPLETED\"}\n\n"

        except Exception as stream_err:
            logger.error(f"Fatal crash inside event stream processing pipeline: {str(stream_err)}")
            yield f"data: {json.dumps({'status': 'ERROR', 'error': str(stream_err)})}\n\n"

    return StreamingResponse(event_streamer(), media_type="text/event-stream")
