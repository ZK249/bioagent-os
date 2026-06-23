
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any
import yaml
from pathlib import Path

from modules.agent_core.llm_client import LLMClient
from modules.agent_core.memory.memory_manager import MemoryManager
from modules.agent_core.graph import BioAgentWorkflow
from modules.data_engine.vectorizers.dnabert_vectorizer import DNABERT_Vectorizer

app = FastAPI(title="BioAgent-OS")
BASE_DIR = Path(__file__).parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR/ "modules" / "agent_core" / "templates"))

_workflow = None
_memory = None


def get_workflow():
    global _workflow, _memory
    if _workflow is None:
        # 读取配置
        cfg_path = BASE_DIR / "configs" / "agent_core.yaml"
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f)
        llm_cfg = cfg.get("llm", {})
        provider = llm_cfg.get("provider", "kimi")

        # 先建立 Milvus 连接（MemoryManager 的 LongTermMemory / EntityMemory 需要）
        from pymilvus import connections
        import os
        os.makedirs("data", exist_ok=True)
        try:
            connections.disconnect("default")
        except Exception:
            pass
        connections.connect(alias="default", uri=str(BASE_DIR / "data" / "milvus_demo.db"))

        llm = LLMClient(
            provider=provider,
            api_key=llm_cfg.get("api_key") or None,
            model=llm_cfg.get("model") or None,
        )
        print(f"[LLM] Provider: {provider}, Model: {llm.model}")

        vectorizer = DNABERT_Vectorizer(
            model_name="~/projects/bioagent-os/models/dnabert-2",
            device="cpu"
        )
        _memory = MemoryManager(vectorizer=vectorizer)
        _memory.entity.add("relation", {
            "head": "TP53", "relation": "regulates", "tail": "CDKN1A",
            "confidence": 0.95, "metadata": {"source": "KEGG"}
        })
        _memory.entity.add("relation", {
            "head": "CRISPR-Cas9", "relation": "used_for", "tail": "gene_knockout",
            "confidence": 0.98, "metadata": {"source": "literature"}
        })
        _workflow = BioAgentWorkflow(_memory, llm)
    return _workflow, _memory


class ChatRequest(BaseModel):
    query: str


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # FastAPI 0.138 / Starlette 0.40+ 语法：
    # 第一个参数是 request 对象，第二个是模板文件名
    return templates.TemplateResponse(request, "index.html")

@app.post("/api/chat")
async def chat(req: ChatRequest):
    workflow, memory = get_workflow()
    result = workflow.run(req.query)
    recall = memory.recall(req.query)
    
    # 标准化 tools_called 数据格式（兼容 DeepResearchTool / DeepResearchPipeline 两种返回值）
    raw_tools = result.get("tools_called", [])
    standardized_tools = []
    for tool in raw_tools:
        if tool:
            # 兼容两种数据结构：
            # DeepResearchTool 返回: {papers_found, top_papers, review, query, tool}
            # DeepResearchPipeline 返回: {total_papers, papers, review, query, sources}
            standardized_tools.append({
                "tool": tool.get("tool", "deep_research"),
                "query": tool.get("query", ""),
                "papers_found": tool.get("papers_found", tool.get("total_papers", 0)),
                "review": tool.get("review", "")[:500],
                "top_papers": tool.get("top_papers", tool.get("papers", [])[:5])
            })
    
    return {
        "query": req.query,
        "agent_type": result["agent_type"],
        "response": result["final_answer"],
        "tools_called": standardized_tools,
        "memory": {
            "short_term": recall["short_term"][-6:],
            "long_term": recall["long_term"],
            "entities": recall["entities"],
            "working": recall["working"]
        }
    }


@app.post("/api/clear")
async def clear_memory():
    _, memory = get_workflow()
    memory.clear_all()
    return {"status": "cleared"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}