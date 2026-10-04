"""
smoke_test.py
-------------
Non-interactive test that runs all three example questions through the agent
and prints the responses. Used to verify the agent works end-to-end.
Run with:  python3 smoke_test.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from agent.graph import build_graph

QUESTIONS = [
    "Can I get a refund for payment PAY-005?",
    "What happened with customer CUST-003's recent support cases?",
    "My payment failed — what should I do?",
]

def main():
    print("\n" + "="*65)
    print("  Payment Operations Agent — Smoke Test")
    print("="*65 + "\n")

    graph = build_graph()

    for i, question in enumerate(QUESTIONS, 1):
        print(f"\n{'─'*65}")
        print(f"  Example {i}: {question}")
        print(f"{'─'*65}")

        result = graph.invoke({
            "messages": [HumanMessage(content=question)],
            "policy_context": ""
        })

        messages = result.get("messages", [])
        answer = messages[-1].content if messages else "(no response)"
        print(f"\nAgent:\n{answer}\n")

    print("="*65)
    print("  Smoke test complete!")
    print("="*65 + "\n")

if __name__ == "__main__":
    main()
