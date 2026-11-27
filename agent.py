import os
from typing import Annotated, TypedDict

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from tools import get_price_summary, simple_screener

SYSTEM_PROMPT = (
    "You are StockScout, a stock-screening assistant. Use the simple_screener tool "
    "to find stocks or funds and get_price_summary for recent price moves. "
    "Never invent prices or tickers: only report what the tools return. "
    "If the user asks for 'more' results, call the screener again with the next offset. "
    "This is information, not financial advice."
)


class State(TypedDict):
    messages: Annotated[list, add_messages]


def make_llm(provider: str | None = None, api_key: str | None = None):
    """Local Ollama model by default; Anthropic API when provider='anthropic'."""
    provider = provider or os.getenv("LLM_PROVIDER", "ollama")
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model="claude-haiku-5-5",
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
        )
    from langchain_ollama import ChatOllama

    return ChatOllama(model="qwen2.5:3b")


def build_graph(llm=None):
    tools = [simple_screener, get_price_summary]
    llm_with_tools = (llm or make_llm()).bind_tools(tools)

    def chatbot(state: State):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}

    def router(state: State):
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else END

    builder = StateGraph(State)
    builder.add_node("chatbot", chatbot)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "chatbot")
    builder.add_conditional_edges("chatbot", router)
    builder.add_edge("tools", "chatbot")
    return builder.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    graph = build_graph()
    config = {"configurable": {"thread_id": "cli"}}
    while True:
        prompt = input("Ask StockScout: ")
        result = graph.invoke({"messages": [{"role": "user", "content": prompt}]}, config=config)
        print(result["messages"][-1].content)
