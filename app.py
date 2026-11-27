import os
import uuid

import streamlit as st

from agent import build_graph, make_llm

st.set_page_config(page_title="StockScout AI", page_icon="📈")
st.title("📈 StockScout AI")
st.caption("Ask for stock or fund screens in plain English. Powered by LangGraph and live Yahoo Finance data.")


def get_api_key():
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY")


API_KEY = get_api_key()
PROVIDER = "anthropic" if API_KEY else "ollama"


@st.cache_resource
def get_graph(provider: str, api_key: str | None):
    return build_graph(make_llm(provider, api_key))


def reply_text(content) -> str:
    """Anthropic can return a list of content blocks; Ollama returns a string."""
    if isinstance(content, list):
        return "".join(block.get("text", "") for block in content if isinstance(block, dict))
    return content


if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.history = []

with st.sidebar:
    st.write(f"Model: {'Claude (API)' if PROVIDER == 'anthropic' else 'Qwen2.5-3B (local Ollama)'}")
    st.write("Try:")
    st.code("Show me today's top gainers")
    st.code("Show me the next 5")
    st.code("How has TSM moved in the last 3 months?")
    if st.button("New conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.history = []
        st.rerun()

for role, text in st.session_state.history:
    st.chat_message(role).write(text)

if prompt := st.chat_input("Ask about stocks or funds..."):
    st.chat_message("user").write(prompt)
    st.session_state.history.append(("user", prompt))
    try:
        graph = get_graph(PROVIDER, API_KEY)
        with st.spinner("Checking the market..."):
            result = graph.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config={"configurable": {"thread_id": st.session_state.thread_id}},
            )
        answer = reply_text(result["messages"][-1].content)
    except Exception as exc:
        answer = f"Something went wrong: {exc}"
    st.chat_message("assistant").write(answer)
    st.session_state.history.append(("assistant", answer))
