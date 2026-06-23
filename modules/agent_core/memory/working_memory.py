from typing import Any, Dict
from .base import BaseMemory


class WorkingMemory(BaseMemory):
    def __init__(self):
        self.state: Dict[str, Any] = {
            "current_task": "",
            "steps_completed": [],
            "intermediate_results": {},
            "todo": [],
            "context": {}
        }

    def add(self, key: str, value: Any, **kwargs) -> None:
        if key == "task":
            self.state["current_task"] = value
        elif key == "step":
            self.state["steps_completed"].append(value)
        elif key == "result":
            step = kwargs.get("step", "unknown")
            self.state["intermediate_results"][step] = value
        elif key == "todo":
            self.state["todo"] = value
        else:
            self.state["context"][key] = value

    def get(self, key: str, **kwargs) -> Any:
        if key == "task":
            return self.state["current_task"]
        elif key == "steps":
            return self.state["steps_completed"]
        elif key == "results":
            return self.state["intermediate_results"]
        elif key == "todo":
            return self.state["todo"]
        return self.state["context"].get(key)

    def search(self, query: str, top_k: int = 5, **kwargs) -> list:
        return []

    def clear(self) -> None:
        self.state = {
            "current_task": "",
            "steps_completed": [],
            "intermediate_results": {},
            "todo": [],
            "context": {}
        }

    def to_prompt_context(self) -> str:
        import json
        lines = [
            f"Current Task: {self.state['current_task']}",
            f"Steps Completed: {', '.join(self.state['steps_completed'])}",
            f"Intermediate Results: {json.dumps(self.state['intermediate_results'], ensure_ascii=False)}",
            f"TODO: {', '.join(self.state['todo'])}"
        ]
        return "\n".join(lines)