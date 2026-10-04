"""
rag.py
------
A tiny Retrieval-Augmented Generation (RAG) component.

What it does:
  1. Reads the three Markdown policy files at startup.
  2. Splits them into small overlapping text chunks.
  3. Embeds the chunks using OpenAI embeddings and stores them in an
     in-memory FAISS vector store (no external database required).
  4. Exposes retrieve_policy(query) which returns the top-2 most relevant
     chunks as a single string — ready to be injected into the LLM prompt.

Why RAG here?
  The LLM needs accurate policy text to give correct answers about refund
  windows, chargeback procedures, and payment failure steps. RAG ensures
  it reads from our actual policy documents rather than making things up.
"""

from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.documents import Document

POLICIES_DIR = Path(__file__).parent.parent / "policies"

# How many top chunks to return for each query
TOP_K = 2

# ---------------------------------------------------------------------------
# Build the in-memory vector store (called once at startup)
# ---------------------------------------------------------------------------


def _load_policy_documents() -> list[Document]:
    """Read all .md files from the policies directory into LangChain Documents."""
    docs = []
    for md_file in sorted(POLICIES_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        docs.append(Document(
            page_content=text,
            metadata={"source": md_file.name}
        ))
    return docs


def build_vector_store() -> FAISS:
    """
    Split policy documents into chunks, embed them, and return a FAISS store.
    Called once when the agent starts up.
    """
    raw_docs = _load_policy_documents()

    # Split into overlapping chunks so long rules are not cut mid-sentence
    splitter = CharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separator="\n",
    )
    chunks = splitter.split_documents(raw_docs)

    # Use a local sentence-transformers model — no API key required
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store


# ---------------------------------------------------------------------------
# Public retrieval function
# ---------------------------------------------------------------------------


def retrieve_policy(query: str, vector_store: FAISS) -> str:
    """
    Retrieve the most relevant policy chunks for a given user query.

    Args:
        query:        The user's question or the current conversation context.
        vector_store: The pre-built FAISS store (built once at startup).

    Returns:
        A formatted string containing the top-K most relevant policy chunks,
        each labelled with its source file. Returns a default message if
        no policies are loaded.
    """
    if vector_store is None:
        return "No policy documents available."

    results = vector_store.similarity_search(query, k=TOP_K)

    if not results:
        return "No relevant policy information found."

    formatted_chunks = []
    for doc in results:
        source = doc.metadata.get("source", "unknown")
        formatted_chunks.append(f"[Source: {source}]\n{doc.page_content.strip()}")

    return "\n\n---\n\n".join(formatted_chunks)
