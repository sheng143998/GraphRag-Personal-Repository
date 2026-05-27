class BaseAgent:
    name = "base-agent"

    async def invoke(self, user_input: str) -> str:
        raise NotImplementedError
