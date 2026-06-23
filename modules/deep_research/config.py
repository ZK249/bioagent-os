import yaml
from pathlib import Path


class DeepResearchConfig:
    def __init__(self, config_path: str = "configs/deep_research.yaml"):
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)

    @property
    def arxiv_max_results(self) -> int:
        return self.cfg.get("arxiv", {}).get("max_results", 10)

    @property
    def pubmed_max_results(self) -> int:
        return self.cfg.get("pubmed", {}).get("max_results", 10)

    @property
    def review_model(self) -> str:
        return self.cfg.get("synthesis", {}).get("model", "moonshot-v1-8k")

    @property
    def review_max_tokens(self) -> int:
        return self.cfg.get("synthesis", {}).get("max_tokens", 3000)