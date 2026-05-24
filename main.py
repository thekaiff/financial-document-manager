import os
import uuid
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import engine, Base, SessionLocal
from models import User, Role, Document
from schemas import (
    UserRegister, UserLogin, TokenResponse, UserOut,
    RoleCreate, RoleOut, AssignRole, DocumentOut, SearchRequest,
)
from auth import hash_password, verify_password, create_token, verify_token
import vector_store
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


Base.metadata.create_all(bind=engine)

# App setup: 
app = FastAPI(
    title="Financial Document Management API",
    description="""
## About
A system to **store, manage, and search** financial documents using AI-powered semantic search.

## How to use
1. Register or login to get a JWT token
2. Click the **Authorize 🔒** button (top right) and paste your token
3. Now you can use all the protected endpoints

## Roles & Permissions
| Role    | Permission   | Can do                            |
|---------|-------------|-----------------------------------|
| admin   | full_access | Everything                        |
| analyst | upload_edit | Upload, edit, view documents      |
| auditor | review      | Review and view documents         |
| client  | view        | View documents only               |
    """,
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/ui", StaticFiles(directory="static", html=True), name="ui")


security = HTTPBearer()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

VALID_ROLES = ["admin", "analyst", "auditor", "client"]
VALID_DOC_TYPES = ["invoice", "report", "contract"]
VALID_PERMISSIONS = ["full_access", "upload_edit", "review", "view"]
ROLE_LEVELS = {"view": 1, "review": 2, "upload_edit": 3, "full_access": 4}



# helper func:

def get_db():
    return SessionLocal()


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Extract user from JWT token. Swagger sends the token automatically after you Authorize."""
    token = creds.credentials
    user_id = verify_token(token)

    db = get_db()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def check_permission(user: User, min_permission: str):
    """Check if user's role has enough permission level."""
    db = get_db()
    role = db.query(Role).filter(Role.id == user.role_id).first()
    db.close()

    if not role:
        raise HTTPException(status_code=403, detail="No role assigned. Ask an admin to assign you a role.")

    user_level = ROLE_LEVELS.get(role.permission, 0)
    required_level = ROLE_LEVELS.get(min_permission, 0)

    if user_level < required_level:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Your permission: {role.permission}. Required: {min_permission}",
        )


def extract_text(file_path: str) -> str:
    """Read text from .txt or .pdf files."""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".txt":
            with open(file_path, "r") as f:
                return f.read()
        elif ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return "\n".join(
                page.extract_text() for page in reader.pages if page.extract_text()
            )
        return ""
    except Exception:
        return ""



# auth:

@app.post("/auth/register", response_model=UserOut, status_code=201, tags=["Auth"])
def register(data: UserRegister):
    """Register a new user. New users start with no role (ask admin to assign one)."""
    db = get_db()

    if db.query(User).filter(User.email == data.email).first():
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(User).filter(User.username == data.username).first():
        db.close()
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(data: UserLogin):
    """Login with email and password. Returns a JWT token to use for all other APIs."""
    db = get_db()
    user = db.query(User).filter(User.email == data.email).first()
    db.close()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user_id=user.id)
    return TokenResponse(access_token=token)



# roles:

@app.post("/roles/create", response_model=RoleOut, status_code=201, tags=["Roles"])
def create_role(data: RoleCreate, current_user: User = Depends(get_current_user)):
    """Create a new role. Only admins can do this."""
    check_permission(current_user, "full_access")

    if data.permission not in VALID_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid permission. Choose: {VALID_PERMISSIONS}")

    db = get_db()

    if db.query(Role).filter(Role.name == data.name).first():
        db.close()
        raise HTTPException(status_code=400, detail="Role already exists")

    role = Role(name=data.name, permission=data.permission)
    db.add(role)
    db.commit()
    db.refresh(role)
    db.close()
    return role

@app.get("/roles", tags=["Roles"])
def list_roles(current_user: User = Depends(get_current_user)):
    """List all available roles with their IDs."""
    db = get_db()
    roles = db.query(Role).all()
    db.close()
    return [{"id": r.id, "name": r.name, "permission": r.permission} for r in roles]

@app.get("/users", tags=["Roles"])
def list_users(current_user: User = Depends(get_current_user)):
    """List all users. Admin only."""
    check_permission(current_user, "full_access")

    db = get_db()
    users = db.query(User).all()
    db.close()
    return [{"id": u.id, "username": u.username, "email": u.email, "role_id": u.role_id} for u in users]

@app.post("/users/assign-role", tags=["Roles"])
def assign_role(data: AssignRole, current_user: User = Depends(get_current_user)):
    """Assign a role to a user. Only admins can do this."""
    check_permission(current_user, "full_access")

    db = get_db()

    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        db.close()
        raise HTTPException(status_code=404, detail="Role not found")

    user.role_id = role.id
    role_name = role.name
    username = user.username
    db.commit()
    db.close()
    return {"message": f"Role '{role_name}' assigned to '{username}'"}

@app.get("/users/{user_id}/roles", tags=["Roles"])
def get_user_role(user_id: str, current_user: User = Depends(get_current_user)):
    """Get the role assigned to a user."""
    db = get_db()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == user.role_id).first() if user.role_id else None
    db.close()

    return {
        "user_id": user.id,
        "username": user.username,
        "role": {"id": role.id, "name": role.name, "permission": role.permission} if role else None,
    }


@app.get("/users/{user_id}/permissions", tags=["Roles"])
def get_user_permissions(user_id: str, current_user: User = Depends(get_current_user)):
    """View what a user is allowed to do based on their role."""
    db = get_db()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == user.role_id).first() if user.role_id else None
    db.close()

    permission_map = {
        "full_access": ["upload", "edit", "delete", "view", "manage_users", "manage_roles"],
        "upload_edit": ["upload", "edit", "view"],
        "review": ["view", "review"],
        "view": ["view"],
    }

    perms = permission_map.get(role.permission, []) if role else []

    return {
        "user_id": user.id,
        "username": user.username,
        "role": role.name if role else None,
        "permissions": perms,
    }


# docs:


@app.post("/documents/upload", response_model=DocumentOut, status_code=201, tags=["Documents"])
def upload_document(
    title: str = Form(...),
    company_name: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a financial document (.txt or .pdf). Text is extracted automatically."""
    check_permission(current_user, "upload_edit")

    if document_type not in VALID_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid type. Choose: {VALID_DOC_TYPES}")

    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    text = extract_text(file_path)

    db = get_db()
    doc = Document(
        title=title,
        company_name=company_name,
        document_type=document_type,
        file_path=file_path,
        content_text=text,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.close()
    return doc


@app.get("/documents", response_model=list[DocumentOut], tags=["Documents"])
def get_all_documents(current_user: User = Depends(get_current_user)):
    """Get all uploaded documents."""
    db = get_db()
    docs = db.query(Document).all()
    db.close()
    return docs


@app.get("/documents/search", response_model=list[DocumentOut], tags=["Documents"])
def search_by_metadata(
    title: str = Query(None),
    company_name: str = Query(None),
    document_type: str = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Search documents by title, company name, or type (keyword search, not AI)."""
    db = get_db()
    q = db.query(Document)

    if title:
        q = q.filter(Document.title.ilike(f"%{title}%"))
    if company_name:
        q = q.filter(Document.company_name.ilike(f"%{company_name}%"))
    if document_type:
        q = q.filter(Document.document_type == document_type)

    results = q.all()
    db.close()
    return results


@app.get("/documents/{document_id}", response_model=DocumentOut, tags=["Documents"])
def get_document(document_id: str, current_user: User = Depends(get_current_user)):
    """Get a single document by its ID."""
    db = get_db()
    doc = db.query(Document).filter(Document.id == document_id).first()
    db.close()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.delete("/documents/{document_id}", tags=["Documents"])
def delete_document(document_id: str, current_user: User = Depends(get_current_user)):
    """Delete a document. Admin only."""
    check_permission(current_user, "full_access")

    db = get_db()
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        db.close()
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    db.close()
    return {"message": f"Document '{doc.title}' deleted"}

@app.delete("/users/{user_id}", tags=["Roles"])
def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    """Delete a user. Admin only."""
    check_permission(current_user, "full_access")

    db = get_db()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")

    username = user.username
    db.delete(user)
    db.commit()
    db.close()
    return {"message": f"User '{username}' deleted"}


# RAG:

@app.post("/rag/index-document", tags=["RAG"])
def index_document(document_id: str, current_user: User = Depends(get_current_user)):
    """
    Index a document for AI search. This breaks the document into chunks
    and stores them in the vector database. Must be done before semantic search works.
    """
    check_permission(current_user, "upload_edit")

    db = get_db()
    doc = db.query(Document).filter(Document.id == document_id).first()
    db.close()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if not doc.content_text:
        raise HTTPException(status_code=400, detail="Document has no text content to index")

    count = vector_store.add_document(
        document_id=doc.id, text=doc.content_text,
        title=doc.title, company=doc.company_name,
    )
    return {"message": "Document indexed", "document_id": doc.id, "chunks_created": count}


@app.delete("/rag/remove-document/{document_id}", tags=["RAG"])
def remove_from_index(document_id: str, current_user: User = Depends(get_current_user)):
    """Remove a document from the AI search index."""
    check_permission(current_user, "full_access")

    vector_store.remove_document(document_id)
    return {"message": "Removed from index", "document_id": document_id}


@app.post("/rag/search", tags=["RAG"])
def semantic_search(data: SearchRequest, current_user: User = Depends(get_current_user)):
    """
    AI-powered semantic search. Finds document chunks by meaning, not just keywords.
    Example: searching 'debt problems' also finds text about 'high leverage ratio'.
    """
    candidates = vector_store.search_documents(query=data.query, top_k=20)
    results = vector_store.rerank_results(query=data.query, results=candidates, top_k=data.top_k)
    return {"query": data.query, "results": results}


@app.get("/rag/context/{document_id}", tags=["RAG"])
def get_context(document_id: str, current_user: User = Depends(get_current_user)):
    """See all indexed chunks of a specific document."""
    chunks = vector_store.get_chunks(document_id)
    return {"document_id": document_id, "total_chunks": len(chunks), "chunks": chunks}



# heath:

@app.get("/", tags=["Health"])
def health():
    """Check if the API is running."""
    return {"status": "running", "docs": "/docs"}



@app.get("/debug/text/{document_id}", tags=["Health"])
def debug_text(document_id: str, current_user: User = Depends(get_current_user)):
    """Temporary: see extracted text of a document."""
    db = get_db()
    doc = db.query(Document).filter(Document.id == document_id).first()
    db.close()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": doc.id, "text_length": len(doc.content_text), "text_preview": doc.content_text[:500]}