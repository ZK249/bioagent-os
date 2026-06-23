import os
from typing import List, Dict, Optional
from openai import OpenAI


PROVIDER_CONFIG = {
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "env_key": "KIMI_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen2.5-14b-instruct",
        "env_key": "DASHSCOPE_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-3-haiku-20240307",
        "env_key": "ANTHROPIC_API_KEY",
    },
}


class LLMClient:
    def __init__(
        self,
        provider: str = "kimi",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        provider = provider.lower().strip()
        if provider not in PROVIDER_CONFIG:
            raise ValueError(
                f"Unknown provider '{provider}'. Supported: {list(PROVIDER_CONFIG.keys())}"
            )

        cfg = PROVIDER_CONFIG[provider]
        self.provider = provider

        # 优先级：传入 api_key > 环境变量
        _api_key = api_key or os.getenv(cfg["env_key"])
        if not _api_key:
            raise RuntimeError(
                f"{cfg['env_key']} not set. "
                f"Export it: export {cfg['env_key']}=your_key"
            )

        self.client = OpenAI(
            api_key=_api_key,
            base_url=base_url or cfg["base_url"],
        )
        self.model = model or cfg["default_model"]

    def generate(self, messages: List[Dict], max_tokens: int = 2000, temperature: float = 0.3) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content

    def generate_with_tools(self, messages: List[Dict], tools: List[Dict], max_tokens: int = 2000) -> Dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message

    @classmethod
    def list_providers(cls) -> List[str]:
        return list(PROVIDER_CONFIG.keys())

    @classmethod
    def get_provider_info(cls, provider: str) -> Dict:
        return PROVIDER_CONFIG.get(provider, {})