from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
load_lab_env(ROOT)

from chat import run_model_tool_loop, trim_history
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ARTIFACTS_DIR = ROOT / "artifacts"

def get_tools():
    decls = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    return to_openai_tools(decls)

def get_system_prompt() -> str:
    return (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]]
    provider: str = "nvidia"
    max_tool_rounds: int = 4
    history_window: int = 5

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    provider = make_provider(req.provider)
    tools = get_tools()
    system_prompt = get_system_prompt()
    
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(req.history, req.history_window),
        {"role": "user", "content": req.message},
    ]
    
    result = run_model_tool_loop(
        provider=provider,
        messages=messages,
        tools=tools,
        model=None,
        max_tool_rounds=req.max_tool_rounds,
    )
    
    return result
