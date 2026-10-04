# 💳 Payment Operations Agent

A beginner-friendly demo application that uses **LangGraph** and an **LLM** to answer
payment support questions. It uses fake local JSON data, a tiny RAG system over Markdown
policy documents, and four deterministic tools — no web UI, no external database.

---

## 🗺️ Architecture

```mermaid
flowchart TD
    A([User CLI Input]) --> B[LangGraph Graph]

    B --> C[rag_node\nRetrieves relevant policy chunks\nfrom FAISS vector store]
    C --> D[llm_node\nCalls LLM with tools bound\nPolicy context injected as system msg]

    D -->|Tool call requested| E[tool_node\nAuto-executes tool calls]
    D -->|No tool calls| F([Final Answer - CLI])

    E --> D

    subgraph Tools
        T1[get_payment]
        T2[get_customer]
        T3[search_support_cases]
        T4[check_refund_eligibility\n- Deterministic Python rules -]
    end

    subgraph RAG Vector Store - FAISS in-memory
        P1[refund_policy.md]
        P2[chargeback_policy.md]
        P3[payment_failure_policy.md]
    end

    E --> Tools
    C --> RAG Vector Store - FAISS in-memory
```

**Flow summary:**
1. User types a question in the CLI.
2. **rag_node** searches the policy vector store and retrieves the most relevant snippets.
3. **llm_node** receives the conversation + policy context and decides what to do.
4. If the LLM needs data, it calls a **tool** (e.g. `get_payment`, `check_refund_eligibility`).
5. **tool_node** executes the tool and returns the result to the LLM.
6. The LLM formulates a final answer printed to the CLI.

---

## 📁 Project Structure

```
payment-operations-agent/
│
├── data/                          # Fake local JSON data (no real database)
│   ├── customers.json             # 5 customer records
│   ├── payments.json              # 10 payment records
│   └── support_cases.json         # 6 support case records
│
├── policies/                      # Source documents for the RAG component
│   ├── refund_policy.md           # Refund rules (30-day window, status checks, etc.)
│   ├── chargeback_policy.md       # Chargeback vs. refund, dispute process
│   └── payment_failure_policy.md  # Failure reasons, retry logic, escalation steps
│
├── agent/                         # Core agent code
│   ├── __init__.py
│   ├── state.py                   # AgentState TypedDict (LangGraph shared state)
│   ├── tools.py                   # 4 LangChain tools (data lookup + refund rules)
│   ├── rag.py                     # RAG: embed policy docs, retrieve relevant chunks
│   └── graph.py                   # LangGraph graph: nodes, edges, conditional routing
│
├── main.py                        # CLI entry point
├── requirements.txt               # Python dependencies
├── .env.example                   # Template for environment variables
└── README.md                      # This file
```

---

## 📄 Important Files Explained

### `agent/state.py`
Defines `AgentState` — the shared dictionary that flows through every graph node.
- `messages` — full conversation history (auto-appended by LangGraph via `add_messages`)
- `policy_context` — RAG-retrieved policy text for the current turn

### `agent/tools.py`
Four `@tool`-decorated functions the LLM can invoke:

| Tool | Input | What it does |
|---|---|---|
| `get_payment` | `payment_id` | Looks up a payment in `payments.json` |
| `get_customer` | `customer_id` | Looks up a customer in `customers.json` |
| `search_support_cases` | `query` | Keyword-searches `support_cases.json` |
| `check_refund_eligibility` | `payment_id` | **Deterministic Python rules** — 30-day window, status check, subscription check. LLM relays the verdict as-is. |

### `agent/rag.py`
Tiny RAG pipeline:
1. Reads all `.md` files from `policies/` at startup.
2. Splits them into overlapping chunks (600 chars, 100 overlap).
3. Embeds with `OpenAIEmbeddings` into an in-memory **FAISS** vector store.
4. `retrieve_policy(query)` returns the top-2 most relevant chunks.

### `agent/graph.py`
The LangGraph state graph with three nodes:
- **`rag_node`** → retrieves policy context before every LLM call
- **`llm_node`** → calls the LLM with tools bound and policy context injected as a system message
- **`tool_node`** → auto-executes tool calls using LangGraph's built-in `ToolNode`

A **conditional edge** after `llm_node` routes to `tool_node` if a tool was requested, or to `END` if the answer is ready.

### `main.py`
Simple CLI loop — builds the graph once, maintains conversation history across turns.
Special commands: `clear` (reset), `quit` (exit).

---

## 🚀 Setup & Running

### 1. Prerequisites
- Python 3.10 or higher
- An OpenAI API key

### 2. Install dependencies

```bash
cd payment-operations-agent
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 4. Run the agent

```bash
python main.py
```

---

## 💡 Example Questions & Expected Behaviour

### Example 1 — Refund eligibility check
```
You: Can I get a refund for payment PAY-005?
```
**What happens:**
1. `rag_node` retrieves refund policy chunks.
2. LLM calls `get_payment("PAY-005")` → status=completed, date=2026-09-25.
3. LLM calls `check_refund_eligibility("PAY-005")`.
4. Tool returns **ELIGIBLE** (completed, within 30 days, not a subscription).
5. LLM relays the verdict and explains next steps (5–10 business days).

---

### Example 2 — Support case lookup
```
You: What happened with customer CUST-003's recent support cases?
```
**What happens:**
1. LLM calls `get_customer("CUST-003")` → Carol White.
2. LLM calls `search_support_cases("CUST-003")` → finds CASE-003 (dispute) and CASE-004 (pending payment).
3. LLM summarises both open cases clearly.

---

### Example 3 — General policy question (RAG only, no tool call)
```
You: My payment failed — what should I do?
```
**What happens:**
1. `rag_node` retrieves the top chunks from `payment_failure_policy.md`.
2. LLM reads the policy context in its system message.
3. LLM explains failure reasons, the automatic retry schedule, and when to escalate.
4. No tool calls needed — answered from policy alone.

---

## 🔒 Key Design Decisions

| Decision | Why |
|---|---|
| **Deterministic refund rules** | `check_refund_eligibility` is pure Python — LLM cannot hallucinate eligibility. |
| **RAG at every turn** | Query-relevant policy text is always fresh and injected before the LLM responds. |
| **In-memory FAISS** | No external database. Vector store is built from `.md` files each run. |
| **LangGraph `ToolNode`** | Handles tool dispatch and error handling automatically — less boilerplate. |
| **Flat JSON files** | No database setup. Readable and editable by anyone. |
| **`add_messages` reducer** | LangGraph safely appends messages to history without overwriting. |

---

## 🛠️ Extending the Project

- **Add more tools** — e.g. `create_support_case`, `escalate_to_billing`
- **Add more policies** — drop any `.md` file into `policies/` and it is automatically embedded
- **Swap the LLM** — change `MODEL_NAME` in `.env` (e.g. `gpt-4o`, `gpt-3.5-turbo`)
- **Add persistence** — use LangGraph's checkpointing to persist conversations across sessions
- **Add more data** — extend the JSON files in `data/` freely

