from app.services.adapters.base import AdapterCallContext, LLMAdapter


class BaseGenerator:
    async def generate(self, *, prompt: str, context: AdapterCallContext) -> str:
        raise NotImplementedError


class SimpleGenerator(BaseGenerator):
    def __init__(self, *, llm_adapter: LLMAdapter) -> None:
        self.llm_adapter = llm_adapter

    async def generate(self, *, prompt: str, context: AdapterCallContext) -> str:
        return await self.llm_adapter.generate(prompt=prompt, context=context)
