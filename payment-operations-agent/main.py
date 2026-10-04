"""
main.py
-------
CLI entry point for the Payment Operations Agent.

Usage:
    python main.py

The agent maintains conversation history across turns in the same session.
Type 'quit', 'exit', or 'q' to stop. Type 'clear' to reset the conversation.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env before importing LangChain modules
load_dotenv()

from langchain_core.messages import HumanMessage
from agent.graph import build_graph

BANNER = """
╔══════════════════════════════════════════════════════════╗
║         💳  Payment Operations Agent  💳                 ║
║                                                          ║
║  Ask me about payments, refunds, chargebacks, or         ║
║  payment failures. I use real policy documents to        ║
║  give you accurate, deterministic answers.               ║
║                                                          ║
║  Commands:  'clear' = new conversation                   ║
║             'quit'  = exit                               ║
╚══════════════════════════════════════════════════════════╝
"""

EXAMPLE_QUESTIONS = """
💡 Example questions to try:
   1. "Can I get a refund for payment PAY-001?"
   2. "What happened with customer CUST-003's recent support cases?"
   3. "My payment failed — what should I do?"
"""


def run_cli():
    # Validate API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY is not set.")
        print("   Copy .env.example to .env and add your key.")
        return

    print(BANNER)
    print(EXAMPLE_QUESTIONS)

    # Build the graph once (loads RAG vector store at startup)
    graph = build_graph()

    # Conversation history — persists across turns in a session
    conversation_messages = []

    print("Ready! Type your question below.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit", "q"}:
            print("👋 Goodbye!")
            break

        if user_input.lower() == "clear":
            conversation_messages = []
            print("🔄 Conversation cleared. Starting fresh.\n")
            continue

        # Append new user message to history
        conversation_messages.append(HumanMessage(content=user_input))

        # Invoke the graph with the full conversation history
        print("\n🤔 Thinking...\n")
        try:
            result = graph.invoke(
                {"messages": conversation_messages, "policy_context": ""}
            )
        except Exception as e:
            print(f"❌ Error during agent execution: {e}\n")
            continue

        # Extract all messages from the result and update history
        result_messages = result.get("messages", [])
        conversation_messages = result_messages  # graph returns full updated history

        # Print the final assistant response (last message)
        if result_messages:
            final_answer = result_messages[-1].content
            print(f"Agent: {final_answer}\n")
        else:
            print("Agent: (no response)\n")

        print("-" * 60)


if __name__ == "__main__":
    run_cli()
