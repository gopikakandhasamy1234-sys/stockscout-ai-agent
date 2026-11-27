# StockScout AI

A chat assistant that screens stocks and funds from plain-English questions
("show me today's top gainers", "show me the next 5", "how has TSM moved in 3 months?").
Built with LangGraph, Yahoo Finance data (yfinance) and a Streamlit front end.

**Live demo:** coming soon

## What it does
- 15 predefined Yahoo Finance screens (stocks and funds), 5 results per page with pagination
- Remembers the conversation, so "show me the next 5" works
- Price summary tool for any ticker (change, high and low over 5 days to 1 year)
- Runs on a local model (Qwen2.5-3B through Ollama) or the Claude API

## How it works
A LangGraph state graph with a chatbot node, a tool node and a router that sends
the model's tool calls to the tools and back. Conversation memory is kept per
session with LangGraph's `InMemorySaver`.
![Agent graph]

## What I added
- Streamlit chat interface, deployable to the cloud
- Second tool (`get_price_summary`)
- Input validation and error handling (invalid screen names and network errors no longer crash the agent)
- System prompt that stops the model inventing prices
- Switchable LLM: local Ollama or the Claude API

## Run it
```
pip install -r requirements.txt
ollama pull qwen2.5:3b        # local model
streamlit run app.py
```
To use the Claude API instead, set `ANTHROPIC_API_KEY` (environment variable or Streamlit secrets).

## Deploy (Streamlit Community Cloud)
Ollama cannot run there, so add `ANTHROPIC_API_KEY` under the app's Secrets.

## Credit
Based on Nick Renotte's LangGraph crash course (MIT licence): https://github.com/nicknochnack/LanggraphCrashCourse
