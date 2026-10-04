"""
graph.py
--------
Builds and compiles the LangGraph state graph for the Payment Operations Agent.

Graph layout:
  START → rag_node → llm_node → (conditional) → tool_node → llm_node → ...
                                              ↘ END

Nodes:
  rag_node  : Retrieves relevant policy text, stores in policy_context.
  llm_node  : Calls the LLM with tools bound and policy context as system message.
  tool_node : Auto-executes any tool calls the LLM requested (LangGraph built-in).
"""

import os
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from agent.state import AgentState
from agent.tools import (
    get_payment, get_customer,
    search_support_cases, check_refund_eligibility
)
from agent.rag import build_vector_store, retrieve_policy

TOOLS = [get_payment, get_customer, search_support_cases, check_refund_eligibility]

BASE_SYSTEM_PROMPT = """You are a Payment Operations support agent. Your job is to help
customers and support staff understand payment statuses, refund eligibility, and policy rules.

IMPORTANT RULES:
1. For refund eligibility, you MUST use the check_refund_eligibility tool and relay its
   verdict exactly. Never invent or override a refund decision.
2. Always look up actual data using the provided tools before answering questions about
   specific payments, customers, or support cases.
3. Use the policy context provided to answer questions about rules and procedures.
4. Be concise, factual, and helpful. Do not speculate beyond what the data and policy say.

When policy context is provided below, use it to inform your answer.
"""


def build_graph():
    """
    Construct and compile the LangGraph state graph.
    Returns the compiled graph ready for invocation.
    """
    print("📚 Loading policy documents into vector store...")
    vector_store = build_vector_store()
    print("✅ Vector store ready.\n")

    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(
            model=model_name,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0,
            max_tokens=2048,
        )
        print(f"🤖 Using Anthropic model: {model_name}\n")
    else:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=model_name, temperature=0)
        print(f"🤖 Using OpenAI model: {model_name}\n")

    llm_with_tools = llm.bind_tools(TOOLS)

    # --- Node: RAG retrieval ---
    def rag_node(state: AgentState) -> dict:
        """Retrieve relevant policy chunks for the latest user message."""
        last_human_msg = ""
        for msg in reversed(state["messages"]):
            if msg.type == "human":
                last_human_msg = msg.content
                break
        policy_text = retrieve_policy(last_human_msg, vector_store)
        return {"policy_context": policy_text}

    # --- Node: LLM call ---
    def llm_node(state: AgentState) -> dict:
        """Call the LLM, injecting policy context as part of the system message."""
        policy_context = state.get("policy_context", "")
        system_content = BASE_SYSTEM_PROMPT
        if policy_context:
            system_content += (
                f"\n\n=== RELEVANT POLICY CONTEXT ===\n"
                f"{policy_context}\n"
                f"================================"
            )
        system_msg = SystemMessage(content=system_content)
        messages_with_system = [system_msg] + list(state["messages"])
        response = llm_with_tools.invoke(messages_with_system)
        return {"messages": [response]}

    # --- Conditional edge: tool call or end? ---
    def should_continue(state: AgentState) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    # --- Assemble graph ---
    tool_node = ToolNode(TOOLS)
    builder = StateGraph(AgentState)

    builder.add_node("rag_node", rag_node)
    builder.add_node("llm_node", llm_node)
    builder.add_node("tool_node", tool_node)

    builder.add_edge(START, "rag_node")
    builder.add_edge("rag_node", "llm_node")
    builder.add_conditional_edges(
        "llm_node",
        should_continue,
        {"tools": "tool_node", "end": END},
    )
    builder.add_edge("tool_node", "llm_node")

    return builder.compile()

