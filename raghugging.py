from pathlib import Path
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

# 🔹 Fix: Ensure asyncio event loop exists (needed for grpc.aio in Streamlit)
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# CONFIG
DOCS_PATH = Path("./Train.pdf")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 🔹 Change HuggingFace model here
CHAT_MODEL = "gemini-1.5-flash"
TOP_K = 8
SEARCH_TYPE = "similarity"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def find_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    exts = {".txt", ".md", ".pdf"}
    return [p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in exts]


def load_documents(paths: list[Path]) -> list[Document]:
    docs: list[Document] = []
    for p in paths:
        try:
            if p.suffix.lower() in (".txt", ".md"):
                docs.extend(TextLoader(str(p), encoding="utf-8").load())
            elif p.suffix.lower() == ".pdf":
                docs.extend(PyPDFLoader(str(p)).load())
        except Exception as e:
            print(f"[WARN] Failed to load {p}: {e}")
    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(docs)


def build_faiss_in_memory(chunks: list[Document]) -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)  # 🔹 Hugging Face instead of Google
    return FAISS.from_documents(chunks, embeddings)


def make_retriever(vectorstore: FAISS):
    return vectorstore.as_retriever(
        search_type=SEARCH_TYPE,
        search_kwargs={"k": TOP_K}
    )


def make_rag_chain(retriever):
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a helpful train ticket assistant which gives solution in bullet points to the user based on ticket content and ticket category "
         "Be as direct and clear as possible. "
         "If the exact answer is not found, provide the closest relevant information from context. "),
        ("human", "Question:\n{input}\n\nContext:\n{context}"),
    ])
    llm = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0.2)
    doc_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, doc_chain)


def format_sources(ctx: list[Document]) -> str:
    lines = []
    for d in ctx:
        src = d.metadata.get("source") or d.metadata.get("file_path") or "unknown"
        page = d.metadata.get("page")
        name = Path(src).name
        lines.append(f"- {name}" + (f" (page {page})" if page is not None else ""))
    return "\n".join(lines)


# 🔹 Build pipeline once when module is imported
_files = find_files(DOCS_PATH)
_docs = load_documents(_files)
_chunks = split_documents(_docs)
_vectorstore = build_faiss_in_memory(_chunks)
_retriever = make_retriever(_vectorstore)
_rag_chain = make_rag_chain(_retriever)


def get_answer(question: str) -> dict:
    """Answer a question using the pre-built RAG pipeline."""
    result = _rag_chain.invoke({"input": question})
    answer = result.get("answer") or result.get("output") or str(result)
    ctx = result.get("context", [])
    return {
        "answer": answer.strip(),
        "sources": format_sources(ctx) if ctx else None
    }
