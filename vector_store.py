import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="./chroma_data")

# Use sentence-transformers instead of ChromaDB's built-in (more reliable)
embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name="financial_docs",
    embedding_function=embed_fn,
)

def chunk_text(text: str) -> list[str]:
    """Break text into ~500 character pieces."""
    chunks = []
    words = text.split()
    current = ""

    for word in words:
        if len(current) + len(word) + 1 > 500:
            if current:
                chunks.append(current.strip())
            current = word
        else:
            current += " " + word

    if current.strip():
        chunks.append(current.strip())

    return chunks


def add_document(document_id: str, text: str, title: str, company: str) -> int:
    """Split text into chunks and store in ChromaDB."""
    chunks = chunk_text(text)
    if not chunks:
        return 0

    ids = [f"{document_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "title": title, "company_name": company, "chunk_index": i}
        for i in range(len(chunks))
    ]

    collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


def search_documents(query: str, top_k: int = 5) -> list[dict]:
    """Semantic search - find chunks similar in meaning to query."""
    results = collection.query(query_texts=[query], n_results=top_k)

    output = []
    if results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            output.append({
                "document_id": results["metadatas"][0][i]["document_id"],
                "chunk_text": results["documents"][0][i],
                "score": round(1 - results["distances"][0][i], 4),
                "title": results["metadatas"][0][i]["title"],
                "company_name": results["metadatas"][0][i]["company_name"],
            })
    return output


def remove_document(document_id: str):
    results = collection.get(where={"document_id": document_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])


def get_chunks(document_id: str) -> list[dict]:
    results = collection.get(where={"document_id": document_id})
    chunks = []
    for i in range(len(results["documents"])):
        chunks.append({
            "chunk_index": results["metadatas"][i]["chunk_index"],
            "text": results["documents"][i],
        })
    chunks.sort(key=lambda x: x["chunk_index"])
    return chunks


# def rerank_results(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
#     """
#     Simple reranking: re-score results based on keyword overlap with query.
    
#     Why rerank?
#     Vector search finds semantically similar chunks (good but approximate).
#     Reranking looks more carefully at the top results to improve ordering.
    
#     How this works:
#     - Take the top 20 results from vector search
#     - For each result, count how many query words appear in the chunk
#     - Combine the vector score with keyword overlap score
#     - Re-sort by the combined score
#     """
#     query_words = set(query.lower().split())

#     for result in results:
#         chunk_words = set(result["chunk_text"].lower().split())
#         # Count how many query words appear in the chunk
#         overlap = len(query_words & chunk_words)
#         # Combined score: 70% vector similarity + 30% keyword overlap
#         keyword_score = overlap / max(len(query_words), 1)
#         result["score"] = round(0.7 * result["score"] + 0.3 * keyword_score, 4)

#     # Re-sort by new combined score (highest first)
#     results.sort(key=lambda x: x["score"], reverse=True)
#     return results[:top_k]

def rerank_results(query, results, top_k=5):
    query_words = set(query.lower().split())
    for result in results:
        chunk_words = set(result["chunk_text"].lower().split())
        overlap = len(query_words & chunk_words)
        keyword_score = overlap / max(len(query_words), 1)
        result["score"] = round(0.7 * result["score"] + 0.3 * keyword_score, 4)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]