
const API = "http://127.0.0.1:8000";
let TOKEN = "";

function nav(el, name) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('page-' + name).classList.add('active');
    el.classList.add('active');
    // Auto-close sidebar on mobile after nav
    if (window.innerWidth <= 768) {
        document.getElementById('sidebar').classList.remove('open');
        document.getElementById('overlay').classList.remove('show');
    }
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('overlay').classList.toggle('show');
}

// Close sidebar on resize to desktop
window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
        document.getElementById('sidebar').classList.remove('open');
        document.getElementById('overlay').classList.remove('show');
    }
});

function authH() { return { "Authorization": "Bearer " + TOKEN }; }

function showResp(id, st, d) {
    const b = document.getElementById(id);
    b.classList.add('show');
    const ok = st >= 200 && st < 300;
    let body = '';
    if (typeof d === 'string') {
        body = d;
    } else {
        const json = JSON.stringify(d, null, 2);
        body = json.replace(/"(id|user_id|role_id|document_id|uploaded_by|access_token)":\s*"([^"]+)"/g,
            (match, key, val) => `"${key}": "${val}" <button class="btn-copy" onclick="navigator.clipboard.writeText('${val}');this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1000)" style="position:relative;top:-1px">Copy</button>`
        );
    }
    b.innerHTML = `<div class="response-header">
        <span class="status-badge ${ok ? 'status-ok' : 'status-err'}">${st}</span>
        <span style="font-size:11px;color:var(--text-secondary)">${ok ? 'Success' : 'Error'}</span>
    </div><div class="response-body">${body}</div>`;
}

async function api(m, p, body, rid) {
    if (!TOKEN && !p.startsWith('/auth/')) { alert('Please login first!'); return null; }
    const o = { method: m, headers: { ...authH() } };
    if (body instanceof FormData) o.body = body;
    else if (body) { o.headers["Content-Type"] = "application/json"; o.body = JSON.stringify(body); }
    try {
        const r = await fetch(API + p, o);
        const d = await r.json().catch(() => "No body");
        if (rid) showResp(rid, r.status, d);
        return { status: r.status, data: d };
    } catch (e) {
        if (rid) showResp(rid, 0, "Network error: " + e.message);
        return null;
    }
}

function updateAuth() {
    const bar = document.getElementById('tokenBar');
    const badge = document.getElementById('userBadge');
    const lb = document.getElementById('logoutBtn');
    if (TOKEN) {
        bar.classList.add('show');
        document.getElementById('tokenPreview').textContent = TOKEN.substring(0, 25) + '...';
        badge.classList.add('active');
        lb.style.display = '';
    } else {
        bar.classList.remove('show');
        badge.classList.remove('active');
        lb.style.display = 'none';
    }
}

function copyTk() {
    navigator.clipboard.writeText(TOKEN);
    const b = event.currentTarget;
    b.textContent = 'Copied!';
    setTimeout(() => b.textContent = 'Copy Token', 1200);
}

function copyId(val, btn) {
    navigator.clipboard.writeText(val);
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy', 1000);
}

function logout() {
    TOKEN = "";
    updateAuth();
    document.getElementById('userLabel').textContent = '';
    document.querySelector('.nav-item').click();
}

async function doLogin() {
    const r = await api('POST', '/auth/login', {
        email: document.getElementById('loginEmail').value,
        password: document.getElementById('loginPass').value
    }, 'resp-login');
    if (r && r.status === 200) {
        TOKEN = r.data.access_token;
        document.getElementById('userLabel').textContent = document.getElementById('loginEmail').value;
        updateAuth();
    }
}

async function doRegister() {
    await api('POST', '/auth/register', {
        email: document.getElementById('regEmail').value,
        username: document.getElementById('regUser').value,
        password: document.getElementById('regPass').value
    }, 'resp-register');
}

async function doCreateRole() {
    await api('POST', '/roles/create', {
        name: document.getElementById('roleName').value,
        permission: document.getElementById('rolePerm').value
    }, 'resp-createrole');
}

async function doAssignRole() {
    await api('POST', '/users/assign-role', {
        user_id: document.getElementById('assignUserId').value,
        role_id: document.getElementById('assignRoleId').value
    }, 'resp-assignrole');
}

async function doGetUserRole() { await api('GET', `/users/${document.getElementById('viewRoleUserId').value}/roles`, null, 'resp-userrole'); }
async function doGetUserPerms() { await api('GET', `/users/${document.getElementById('viewRoleUserId').value}/permissions`, null, 'resp-userrole'); }
async function doDeleteUser() {
    if (!confirm('Delete this user permanently?')) return;
    await api('DELETE', `/users/${document.getElementById('deleteUserId').value}`, null, 'resp-deleteuser');
}

async function doListRoles() {
    const r = await api('GET', '/roles', null, null);
    const el = document.getElementById('rolesList');
    if (!r || !r.data || r.data.length === 0) { el.innerHTML = '<div class="empty-state">No roles found</div>'; return; }
    let h = '<table class="doc-table"><thead><tr><th>Name</th><th>Permission</th><th>Role ID</th></tr></thead><tbody>';
    r.data.forEach(role => {
        h += `<tr><td><strong>${role.name}</strong></td>
        <td><span class="type-badge type-report">${role.permission}</span></td>
        <td><span class="id-display">${role.id.substring(0,10)}… <button class="btn-copy" onclick="copyId('${role.id}',this)">Copy</button></span></td></tr>`;
    });
    h += '</tbody></table>';
    el.innerHTML = h;
}

async function doUpload() {
    const fd = new FormData();
    fd.append('title', document.getElementById('docTitle').value);
    fd.append('company_name', document.getElementById('docCompany').value);
    fd.append('document_type', document.getElementById('docType').value);
    fd.append('file', document.getElementById('docFile').files[0]);
    await api('POST', '/documents/upload', fd, 'resp-upload');
}

async function doGetDocs() {
    const r = await api('GET', '/documents', null, null);
    const el = document.getElementById('docsTable');
    if (!r || !r.data || r.data.length === 0) { el.innerHTML = '<div class="empty-state">No documents found</div>'; return; }
    let h = `<table class="doc-table"><thead><tr><th>Title</th><th>Company</th><th>Type</th><th>Document ID</th><th>Date</th><th></th></tr></thead><tbody>`;
    r.data.forEach(d => {
        h += `<tr>
        <td><strong>${d.title}</strong></td>
        <td>${d.company_name}</td>
        <td><span class="type-badge type-${d.document_type}">${d.document_type}</span></td>
        <td><span class="id-display">${d.id.substring(0,10)}… <button class="btn-copy" onclick="copyId('${d.id}',this)">Copy</button></span></td>
        <td style="font-size:11px;color:var(--text-secondary);white-space:nowrap">${new Date(d.created_at).toLocaleDateString()}</td>
        <td><button class="btn btn-danger btn-sm" onclick="doDelDoc('${d.id}')">Del</button></td></tr>`;
    });
    h += '</tbody></table>';
    el.innerHTML = h;
}

async function doDelDoc(id) {
    if (!confirm('Delete?')) return;
    await api('DELETE', `/documents/${id}`, null, 'resp-docs');
    doGetDocs();
}

async function doGetSingleDoc() { await api('GET', `/documents/${document.getElementById('getDocId').value}`, null, 'resp-singledoc'); }

async function doMetaSearch() {
    const p = new URLSearchParams();
    const t = document.getElementById('msTitle').value;
    const c = document.getElementById('msCompany').value;
    const tp = document.getElementById('msType').value;
    if (t) p.append('title', t);
    if (c) p.append('company_name', c);
    if (tp) p.append('document_type', tp);
    const r = await api('GET', '/documents/search?' + p.toString(), null, null);
    const el = document.getElementById('metaResults');
    if (!r || !r.data || r.data.length === 0) { el.innerHTML = '<div class="empty-state">No results</div>'; return; }
    let h = '';
    r.data.forEach(d => {
        h += `<div class="result-card">
        <div class="result-meta"><span class="result-tag">${d.document_type}</span><strong>${d.title}</strong> — ${d.company_name}</div>
        <div style="font-size:11px;color:var(--text-secondary)">ID: <span class="id-display">${d.id.substring(0,10)}… <button class="btn-copy" onclick="copyId('${d.id}',this)">Copy</button></span></div>
        </div>`;
    });
    el.innerHTML = h;
}

async function doIndex() { await api('POST', `/rag/index-document?document_id=${document.getElementById('indexDocId').value}`, null, 'resp-index'); }
async function doRemoveIndex() { await api('DELETE', `/rag/remove-document/${document.getElementById('removeDocId').value}`, null, 'resp-removeindex'); }

async function doSearch() {
    const q = document.getElementById('searchQuery').value;
    const k = parseInt(document.getElementById('searchTopK').value);
    const r = await api('POST', '/rag/search', { query: q, top_k: k }, null);
    const el = document.getElementById('searchResults');
    if (!r || !r.data || !r.data.results || r.data.results.length === 0) {
        el.innerHTML = '<div class="empty-state">No results. Index a document first.</div>';
        return;
    }
    let h = `<div style="background:var(--code-bg);border:1px solid var(--border);border-radius:7px;padding:12px 16px;margin-bottom:12px;font-size:12px;line-height:2">
    <strong>Retrieval Pipeline</strong><br>
    <span style="color:var(--accent)">❶ Query:</span> "${r.data.query}"
    → <span style="color:var(--accent)">❷ Embedding</span> (all-MiniLM-L6-v2, 384-dim vector)
    → <span style="color:var(--accent)">❸ Vector Search</span> (ChromaDB, cosine similarity, top 20 candidates)
    → <span style="color:var(--accent)">❹ Reranking</span> (keyword overlap + vector score)
    → <span style="color:var(--accent)">❺ Top ${r.data.results.length} Results</span> returned
    </div>`;
    r.data.results.forEach(res => {
        const sc = res.score > 0.5 ? 'score-high' : res.score > 0.25 ? 'score-mid' : 'score-low';
        h += `<div class="result-card">
        <div class="result-meta">
            <span class="result-score ${sc}">${res.score.toFixed(4)}</span>
            <span class="result-tag">${res.title}</span>
            <span class="result-tag">${res.company_name}</span>
        </div>
        <div class="result-text">${hl(res.chunk_text, q)}</div>
        </div>`;
    });
    el.innerHTML = h;
}

function hl(t, q) {
    const ws = q.toLowerCase().split(/\s+/);
    let r = t;
    ws.forEach(w => {
        if (w.length > 2) r = r.replace(new RegExp(`(${w})`, 'gi'), '<mark style="background:#fef08a;padding:0 1px;border-radius:2px">$1</mark>');
    });
    return r;
}

async function doGetContext() {
    const r = await api('GET', `/rag/context/${document.getElementById('contextDocId').value}`, null, null);
    const el = document.getElementById('contextResults');
    if (!r || !r.data || !r.data.chunks || r.data.chunks.length === 0) {
        el.innerHTML = '<div class="empty-state">No chunks. Index the document first.</div>';
        return;
    }
    let h = `<div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px">${r.data.total_chunks} chunks indexed</div>`;
    r.data.chunks.forEach(c => {
        h += `<div class="result-card">
        <div class="result-meta"><span class="result-tag">Chunk ${c.chunk_index}</span></div>
        <div class="result-text">${c.text}</div>
        </div>`;
    });
    el.innerHTML = h;
}

async function doListUsers() {
    const r = await api('GET', '/users', null, null);
    const el = document.getElementById('usersList');
    if (!r || !r.data || r.data.length === 0) { el.innerHTML = '<div class="empty-state">No users</div>'; return; }
    let h = '<table class="doc-table"><thead><tr><th>Username</th><th>Email</th><th>User ID</th><th>Role ID</th></tr></thead><tbody>';
    r.data.forEach(u => {
        h += `<tr>
        <td><strong>${u.username}</strong></td>
        <td>${u.email}</td>
        <td><span class="id-display">${u.id.substring(0,10)}… <button class="btn-copy" onclick="copyId('${u.id}',this)">Copy</button></span></td>
        <td>${u.role_id
            ? `<span class="id-display">${u.role_id.substring(0,10)}… <button class="btn-copy" onclick="copyId('${u.role_id}',this)">Copy</button></span>`
            : '<em style="color:var(--text-secondary)">none</em>'
        }</td></tr>`;
    });
    h += '</tbody></table>';
    el.innerHTML = h;
}
