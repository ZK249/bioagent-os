from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):
    query: str
    agent_type: str
    memory_context: str
    agent_response: str
    tools_called: List[Dict]
    final_answer: str
    iteration: int
    max_iterations: int