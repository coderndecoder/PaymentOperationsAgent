"""
state.py
--------
Defines the AgentState TypedDict that flows through every node in the LangGraph graph.

Fields:
  - messages:       Full conversation history (HumanMessage, AIMessage, ToolMessage, etc.)
  - policy_context: Text retrieved from the RAG component for the current turn.
                    Injected as extra context into the LLM system prompt.
"""

from typing import TypedDict
from langgraph.graph.message import add_messages
from typing import Annotated
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    # Annotated with add_messages so LangGraph automatically appends
    # new messages instead of overwriting the list.
    messages: Annotated[list[BaseMessage], add_messages]

    # Policy text retrieved by the RAG node for the current user question.
    # Starts as an empty string and is populated by rag_node each turn.
    policy_context: str
