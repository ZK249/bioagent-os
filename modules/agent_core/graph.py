from typing import Dict, Any
from langgraph.graph import StateGraph, END

from .state import AgentState
from .agents.router_agent import RouterAgent
from .agents.research_agent import ResearchAgent
from .agents.data_agent import DataAgent
from .agents.memory_agent import MemoryAgent
from .memory.memory_manager import MemoryManager
from .llm_client import LLMClient


class BioAgentWorkflow:
    def __init__(self, memory_manager: MemoryManager, llm_client: LLMClient):
        self.memory = memory_manager
        self.llm = llm_client

        self.router = RouterAgent(llm_client)
        self.research = ResearchAgent(memory_manager, llm_client)
        self.data = DataAgent(memory_manager, llm_client)
        self.memory_agent = MemoryAgent(memory_manager, llm_client)

        self.workflow = StateGraph(AgentState)

        self.workflow.add_node("router", self._route)
        self.workflow.add_node("research", self._run_research)
        self.workflow.add_node("data", self._run_data)
        self.workflow.add_node("memory_update", self._update_memory)
        self.workflow.add_node("synthesize", self._synthesize)

        self.workflow.set_entry_point("router")
        self.workflow.add_conditional_edges(
            "router",
            lambda state: state["agent_type"],
            {
                "research": "research",
                "data": "data",
                "direct": "synthesize"
            }
        )
        self.workflow.add_edge("research", "memory_update")
        self.workflow.add_edge("data", "memory_update")
        self.workflow.add_edge("memory_update", "synthesize")
        self.workflow.add_edge("synthesize", END)

        self.app = self.workflow.compile()

    def _route(self, state: AgentState) -> AgentState:
        state["agent_type"] = self.router.route(state["query"])
        state["memory_context"] = self.memory.build_prompt_context(state["query"])
        return state

    def _run_research(self, state: AgentState) -> AgentState:
        result = self.research.run(state["query"], state["memory_context"])
        state["agent_response"] = result["response"]
        state["tools_called"] = result.get("tools_used", [])
        return state

    def _run_data(self, state: AgentState) -> AgentState:
        result = self.data.run(state["query"], state["memory_context"])
        state["agent_response"] = result["response"]
        state["tools_called"] = result.get("tools_used", [])
        return state

    def _update_memory(self, state: AgentState) -> AgentState:
        self.memory_agent.update(state["query"], state["agent_response"])
        return state

    def _synthesize(self, state: AgentState) -> AgentState:
        state["final_answer"] = state["agent_response"]
        state["iteration"] = state.get("iteration", 0) + 1
        return state

    def run(self, query: str) -> Dict[str, Any]:
        initial_state = AgentState(
            query=query,
            agent_type="",
            memory_context="",
            agent_response="",
            tools_called=[],
            final_answer="",
            iteration=0,
            max_iterations=3
        )
        return self.app.invoke(initial_state)