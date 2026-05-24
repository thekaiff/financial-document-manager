<div align="center">
  <img width="80px" src="https://img.icons8.com/fluency/96/document.png" />
</div>

<h1 align="center">FastAPI Financial Document Management with Semantic Analysis</h1>

<h3 align="center">Industry: FinTech | AI-Powered Document Intelligence</h3>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" />
  <img src="https://img.shields.io/badge/RAG-Pipeline-blueviolet?style=for-the-badge" />
</p>

---

<table align="center">
  <tr>
    <td width="1440">
<h2 align="center">Project Overview</h2>

<p>
Financial organizations handle thousands of documents — reports, invoices, contracts — but finding specific information across them is painful. Traditional keyword search fails when users search "debt problems" but the document says "high leverage ratio."
</p>

<p>
This project solves that problem by building a <strong>FastAPI-based document management system</strong> with <strong>AI-powered semantic search</strong>. It combines a relational database (SQLite) for structured metadata with a vector database (ChromaDB) for meaning-based retrieval, enabling users to find relevant financial information by <em>meaning</em>, not just keywords.
</p>

<p>
The system implements <strong>JWT authentication</strong>, <strong>Role-Based Access Control (RBAC)</strong> with 4 permission levels, a complete <strong>document CRUD pipeline</strong>, and a full <strong>RAG (Retrieval Augmented Generation) pipeline</strong> with text extraction, chunking, embedding, vector search, and keyword-overlap reranking.
</p>

<strong>Key Capabilities:</strong>
<ul>
  <li>Secure user authentication with JWT tokens and bcrypt password hashing</li>
  <li>Role-Based Access Control: Admin, Financial Analyst, Auditor, Client</li>
  <li>Document upload with automatic text extraction (PDF & TXT)</li>
  <li>AI-powered semantic search using embedding similarity + reranking</li>
  <li>Clean web UI dashboard for end-to-end testing and demo</li>
</ul>

  </td>
  </tr>
</table>

---

<table align="center">
  <tr>
    <td align="center">
      <img src="preview/financial_doc_manager.gif" style="max-width:100%; height:auto; border-radius:10px;" />
      <p><strong>Preview</strong></p>
    </td>
  </tr>

</table>

---

<h2 align="center">Executive Summary</h2>
<table align="center">
  <tr>
    <td width="1440">

Traditional keyword search on financial documents has a fundamental limitation: it only finds exact word matches. This system introduces <strong>semantic search</strong> — understanding the <em>meaning</em> behind queries — combined with a <strong>reranking pipeline</strong> that refines results for maximum relevance.

<br>

<strong>High-Level Technical Impact:</strong>
<ul>
  <li><strong>Semantic Understanding:</strong> Query "company debt problems" successfully retrieves sections about "leverage ratio" and "credit facility refinancing" — zero keyword overlap, pure meaning-based matching (score: 0.5391)</li>
  <li><strong>4-Stage RAG Pipeline:</strong> Query → Embedding (384-dim vector via all-MiniLM-L6-v2) → Vector Search (top 20 candidates) → Reranking (keyword overlap + vector score) → Top K results</li>
  <li><strong>Complete RBAC System:</strong> 4 roles with hierarchical permissions (view → review → upload_edit → full_access), enforced on every protected endpoint</li>
  <li><strong>Production-Ready Auth:</strong> JWT tokens with 1-hour expiry, bcrypt password hashing, stateless authentication</li>
</ul>

<strong>Final Output:</strong> A fully functional REST API with 17 endpoints + a web UI dashboard that demonstrates the complete document management and semantic search workflow.

  </td>
  </tr>
</table>

---

<h2 align="center">System Architecture</h2>

<table align="center">
  <tr>
    <td align="center" width="1440">

```
┌──────────────────────────────────────────────────────────┐
│                    CLIENT (Web UI / Swagger)              │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP + JWT Token
┌──────────────────────▼───────────────────────────────────┐
│                    FastAPI Server                         │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────────┐ │
│  │ Auth Routes  │ │ Doc Routes   │ │   RAG Routes       │ │
│  │ /auth/*      │ │ /documents/* │ │   /rag/*           │ │
│  └──────┬──────┘ └──────┬───────┘ └────────┬───────────┘ │
│         │               │                  │             │
│  ┌──────▼──────┐ ┌──────▼───────┐ ┌────────▼───────────┐│
│  │JWT + bcrypt │ │Text Extractor│ │ Embedding Service  ││
│  │ (auth.py)   │ │(pypdf)       │ │ (vector_store.py)  ││
│  └──────┬──────┘ └──────┬───────┘ └────────┬───────────┘│
└─────────┼───────────────┼──────────────────┼────────────┘
          │               │                  │
   ┌──────▼───────┐       │         ┌────────▼──────────┐
   │   SQLite DB   │◄─────┘         │    ChromaDB       │
   │  (Users,Roles │                │  (Embeddings,     │
   │   Documents)  │                │   Chunks,Search)  │
   └───────────────┘                └───────────────────┘
```

   </td>
  </tr>
</table>

---

<h2 align="center">RAG Retrieval Pipeline</h2>

<table align="center">
  <tr>
    <td width="1440">

The semantic search follows a multi-stage retrieval pipeline as specified in the requirements:

<br><br>

```
Document Processing (Indexing Phase):
  Document Upload → Text Extraction (PDF/TXT) → Chunking (~500 chars)
       → Embedding (all-MiniLM-L6-v2, 384 dimensions) → ChromaDB Storage

Query Processing (Search Phase):
  User Query
       ↓
  Embedding (same model: all-MiniLM-L6-v2)
       ↓
  Vector Search (ChromaDB, cosine similarity)
       ↓
  Top 20 Candidates
       ↓
  Reranking (70% vector score + 30% keyword overlap)
       ↓
  Top K Most Relevant Results (with scores)
```

<strong>Why this approach?</strong>
<ul>
  <li><strong>Chunking (~500 chars):</strong> Documents are split into focused pieces so search returns the <em>exact relevant paragraph</em>, not the entire 50-page document. Too small (100 chars) loses context; too large (2000 chars) dilutes relevance.</li>
  <li><strong>all-MiniLM-L6-v2:</strong> A lightweight sentence-transformer model that runs locally without API keys. Produces 384-dimensional embeddings where semantically similar texts have similar vector representations.</li>
  <li><strong>Reranking:</strong> Vector search is fast but approximate. The reranker re-scores the top 20 results by combining semantic similarity (70%) with keyword overlap (30%), improving final result ordering.</li>
</ul>

   </td>
  </tr>
</table>

---

<h2 align="center">API Endpoints</h2>

<table align="center">
  <tr>
    <td width="1440">

<h3>Authentication</h3>

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|:---:|
| POST | `/auth/register` | Register a new user | ❌ |
| POST | `/auth/login` | Login, get JWT token | ❌ |

<h3>Role-Based Access Control</h3>

| Method | Endpoint | Description | Min Permission |
|--------|----------|-------------|:---:|
| GET | `/roles` | List all roles | view |
| POST | `/roles/create` | Create a new role | full_access |
| POST | `/users/assign-role` | Assign role to user | full_access |
| GET | `/users/{id}/roles` | Get user's role | view |
| GET | `/users/{id}/permissions` | View user permissions | view |
| DELETE | `/users/{user_id}` | Delete a user | full_access |

<h3>Document Management</h3>

| Method | Endpoint | Description | Min Permission |
|--------|----------|-------------|:---:|
| POST | `/documents/upload` | Upload document (PDF/TXT) | upload_edit |
| GET | `/documents` | List all documents | view |
| GET | `/documents/search` | Search by metadata | view |
| GET | `/documents/{id}` | Get single document | view |
| DELETE | `/documents/{id}` | Delete document | full_access |

<h3>RAG - Semantic Search</h3>

| Method | Endpoint | Description | Min Permission |
|--------|----------|-------------|:---:|
| POST | `/rag/index-document` | Index document for AI search | upload_edit |
| DELETE | `/rag/remove-document/{id}` | Remove from search index | full_access |
| POST | `/rag/search` | Semantic search with reranking | view |
| GET | `/rag/context/{id}` | View indexed chunks | view |

<h3>Permission Hierarchy</h3>

| Role | Permission Level | Capabilities |
|------|:---:|-------------|
| Admin | `full_access` (4) | Everything: create roles, delete users/docs, manage system |
| Financial Analyst | `upload_edit` (3) | Upload documents, index for search, edit, view |
| Auditor | `review` (2) | Review and view documents |
| Client | `view` (1) | View company documents only |

  </td>
  </tr>
</table>

---

<h2 align="center">Tech Stack & Skills</h2>
<table align="center">
  <tr>
    <td width="1440">
<ul>
  <li><strong>Backend Framework:</strong> FastAPI (Python) — async-ready, auto-generated OpenAPI docs, Pydantic validation</li>
  <li><strong>Relational Database:</strong> SQLite via SQLAlchemy ORM — stores users, roles, document metadata</li>
  <li><strong>Vector Database:</strong> ChromaDB (PersistentClient) — stores embeddings, handles similarity search</li>
  <li><strong>Embedding Model:</strong> all-MiniLM-L6-v2 (sentence-transformers) — 384-dimensional vectors, runs locally</li>
  <li><strong>Authentication:</strong> JWT tokens (python-jose) + bcrypt password hashing (passlib)</li>
  <li><strong>Text Extraction:</strong> pypdf for PDF files, built-in for TXT files</li>
  <li><strong>Frontend:</strong> Vanilla HTML/CSS/JS dashboard — no framework dependencies</li>
  <li><strong>API Documentation:</strong> Auto-generated Swagger UI at /docs</li>
</ul>
    </td>
  </tr>
</table>

---

<h2 align="center">Semantic Search Results — Real Output</h2>
<table align="center">
  <tr>
    <td width="1440">

<h3>Query: "company debt problems"</h3>

The system successfully retrieves the DEBT AND LIABILITIES section despite zero keyword overlap with "debt problems":

| Rank | Score | Matched Content | Why It Matched |
|:---:|:---:|---|---|
| 1 | **0.5391** | "Total long-term debt stands at 28 million... debt-to-equity ratio of 0.85... refinanced senior credit facility..." | Semantically related to "debt problems" — discusses debt metrics and leverage |
| 2 | **0.3488** | "Rising interest rates could increase the cost of servicing debt obligations..." | Related to debt risk — interest rate impact on debt |
| 3 | **0.2980** | "Revenue of 45.2 million... 12 percent increase..." | General financial context — lower relevance, correctly ranked last |

<h3>Query: "revenue growth analysis"</h3>

| Rank | Score | Matched Content |
|:---:|:---:|---|
| 1 | **0.5508** | EXECUTIVE SUMMARY + REVENUE ANALYSIS sections — directly about revenue and growth |
| 2 | **0.5010** | CASH FLOW + OUTLOOK sections — mentions "revenue growth of 8 to 10 percent" |
| 3 | **0.2645** | R&D investment and margin improvement — tangentially related to growth |

The reranking pipeline correctly prioritizes results that contain both semantic similarity AND keyword overlap.

  </td>
  </tr>
</table>

---

<h2 align="center">Project Structure</h2>

<table align="center">
  <tr>
    <td width="1440">

```
fin-doc-api/
├── main.py                 # FastAPI app — all 17 API routes
├── database.py             # SQLite connection via SQLAlchemy
├── models.py               # Database tables: User, Role, Document
├── schemas.py              # Pydantic request/response validation
├── auth.py                 # JWT token creation/verification + bcrypt
├── vector_store.py         # ChromaDB: chunking, embedding, search, reranking
├── seed.py                 # Initial setup: creates 4 roles + admin user
├── sample_report.txt       # Sample financial document for testing
├── static/
│   └── index.html          # Web UI dashboard
├── requirements.txt        # Python dependencies
├── .env                    # Secret key configuration
└── README.md
```

   </td>
  </tr>
</table>

---

<h2 align="center">Setup & Installation</h2>
<table align="center">
  <tr>
    <td width="1440">

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/financial-doc-management-api.git
cd financial-doc-management-api

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
echo "SECRET_KEY=mysecretkey123" > .env

# 5. Seed the database (creates admin + 4 roles)
python seed.py

# 6. Start the server
uvicorn main:app --reload

# 7. Open in browser
# Swagger API docs: http://localhost:8000/docs
# Web UI dashboard: http://localhost:8000/ui
```

<strong>Default Admin Credentials:</strong>
<ul>
  <li>Email: <code>admin@example.com</code></li>
  <li>Password: <code>admin123</code></li>
</ul>

  </td>
  </tr>
</table>

---

<h2 align="center">Testing Workflow</h2>
<table align="center">
  <tr>
    <td width="1440">

<strong>Step 1:</strong> Login as admin → get JWT token
<br>
<strong>Step 2:</strong> Register new users → assign roles using role IDs
<br>
<strong>Step 3:</strong> Upload a financial document (PDF or TXT)
<br>
<strong>Step 4:</strong> Index the document for AI search (generates chunks + embeddings)
<br>
<strong>Step 5:</strong> Run semantic search — try queries like:
<ul>
  <li><code>"financial risk related to high debt ratio"</code></li>
  <li><code>"company revenue growth"</code></li>
  <li><code>"cash flow and liquidity"</code></li>
</ul>
<strong>Step 6:</strong> View document chunks to see how the document was split
<br>
<strong>Step 7:</strong> Test RBAC — login as a client user and try uploading (should get 403)

   </td>
  </tr>
</table>

---

<h2 align="center">Key Learnings</h2>
<table align="center">
  <tr>
    <td width="1440">
<ul>
  <li><strong>RAG Pipeline Design:</strong> Understanding the trade-offs between chunk size, embedding model choice, and retrieval accuracy. Smaller chunks improve precision but lose context; the ~500 character sweet spot balances both.</li>
  <li><strong>Semantic vs Keyword Search:</strong> Vector similarity captures meaning (synonyms, related concepts) that keyword matching completely misses — critical for financial document analysis where terminology varies.</li>
  <li><strong>Reranking Improves Results:</strong> Pure vector search is fast but approximate. Adding a simple keyword-overlap reranker on top of vector results meaningfully improves the final ranking quality.</li>
  <li><strong>JWT Stateless Auth:</strong> Token-based authentication eliminates server-side session storage. The token itself carries the user identity, verified via cryptographic signature on every request.</li>
</ul>
    </td>
  </tr>
</table>

---

<h2 align="center">Limitations</h2>
<table align="center">
  <tr>
    <td width="1440">
<ul>
  <li><strong>No chunk overlap:</strong> Current chunking splits text at ~500 character boundaries without overlap. Sentences at chunk edges may be split across two chunks, reducing search accuracy for those sentences. Fix: add 50-character overlap between consecutive chunks.</li>
  <li><strong>Basic reranker:</strong> The keyword-overlap reranker is simple. A production system would use a cross-encoder model (e.g., ms-marco-MiniLM) for significantly better reranking accuracy.</li>
  <li><strong>Single embedding model:</strong> all-MiniLM-L6-v2 is general-purpose. A financial-domain embedding model (e.g., FinBERT) would improve semantic understanding of financial terminology.</li>
  <li><strong>SQLite limitations:</strong> SQLite is single-writer and file-based. For production with concurrent users, PostgreSQL would be the appropriate choice.</li>
</ul>
    </td>
  </tr>
</table>

---

<h2 align="center">Next Steps</h2>
<table align="center">
  <tr>
    <td width="1440">
<ul>
  <li><strong>Add LangChain integration:</strong> Connect retrieved chunks to an LLM (via LangChain) to generate natural language answers from document context, completing the full RAG pipeline.</li>
  <li><strong>Implement hybrid search:</strong> Combine BM25 keyword search with vector search for better retrieval on queries that mix specific terms with semantic intent.</li>
  <li><strong>Upgrade reranker:</strong> Replace keyword-overlap reranker with a cross-encoder model for production-grade result quality.</li>
  <li><strong>Deploy with Docker:</strong> Containerize the application with Docker Compose (FastAPI + PostgreSQL + Qdrant) for production deployment.</li>
</ul>
    </td>
  </tr>
</table>

---

<h3 align="center">📊 This project demonstrates how FastAPI, vector databases, and semantic search can transform financial document management from keyword-dependent to meaning-aware intelligence.</h3>
