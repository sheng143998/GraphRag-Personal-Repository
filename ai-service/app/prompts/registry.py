from pathlib import Path


class PromptRegistry:
    def __init__(self) -> None:
        self.prompt_dir = Path(__file__).resolve().parent

    def render(self, *, name: str, version: str, variables: dict[str, object]) -> str:
        template_path = self.prompt_dir / f"{name}.{version}.txt"
        template = template_path.read_text(encoding="utf-8")
        return template.format(**variables)


prompt_registry = PromptRegistry()
