"""
Chat class: builds a LangGraph agent from a provider (LLM), tools, and system prompt.
Exposes ask(message) -> str with no HTTP or app state.
"""

from langchain.agents import create_agent


def _content_to_str(content):
    """Normalize message content (str or list of blocks) to a single string."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            else:
                parts.append(str(block))
        return " ".join(parts).strip() if parts else ""
    return str(content)


class Chat:
    """
    Wraps a LangChain chat model and tools in a LangGraph ReAct agent.
    """

    def __init__(self, provider, tools, system_prompt: str):
        """
        Args:
            provider: LangChain chat model (BaseChatModel), e.g. from ChatProvider.create_provider(...).
            tools: List of LangChain tools (from langchain.tools or tools.py).
            system_prompt: System prompt string for the agent.
        """
        self._agent = create_agent(provider, tools, system_prompt=system_prompt)

    def ask(self, message: str) -> str:
        """
        Invoke the agent with the given message and return the final response as a string.

        Must use tools to answer the user's question.
        Args:
            message: User message (may include short-term memory and query).

        Returns:
            The assistant's reply as a plain string.
        """
        result = self._agent.invoke({"messages": [("user", message)]})
        last_message = result["messages"][-1]
        content = getattr(last_message, "content", None) or getattr(last_message, "text", None)
        return _content_to_str(content) if content is not None else ""

