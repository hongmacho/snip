// API Configuration
const API = '/api';

// State
let snippets = [];
let selectedId = null;
let currentFilters = {
    lang: '',
    tag: '',
    query: ''
};

// ============================================================================
// HELPERS
// ============================================================================

function normalizeSnippet(s) {
    return {
        ...s,
        id: String(s.id),
        tags: s.tags ? s.tags.split(',').map(t => t.trim()).filter(Boolean) : []
    };
}

// ============================================================================
// API CALLS
// ============================================================================

async function fetchSnippets(lang = '', tag = '') {
    try {
        const params = new URLSearchParams();
        if (lang) params.append('lang', lang);
        if (tag) params.append('tag', tag);

        const url = params.toString() ? `${API}/snippets?${params}` : `${API}/snippets`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch snippets');

        const data = await response.json();
        snippets = (Array.isArray(data) ? data : []).map(normalizeSnippet);
        return snippets;
    } catch (error) {
        showToast('스니펫 로딩 실패', 'error');
        return [];
    }
}

async function createSnippet(data) {
    try {
        const response = await fetch(`${API}/snippets`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to create snippet');

        const result = await response.json();
        showToast('Snippet created successfully');
        return result.data;
    } catch (error) {
        console.error('Error creating snippet:', error);
        showToast('Failed to create snippet', 'error');
        throw error;
    }
}

async function deleteSnippet(id) {
    try {
        const response = await fetch(`${API}/snippets/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete snippet');

        showToast('Snippet deleted successfully');
        return true;
    } catch (error) {
        console.error('Error deleting snippet:', error);
        showToast('Failed to delete snippet', 'error');
        throw error;
    }
}

async function searchSnippets(q) {
    try {
        const params = new URLSearchParams({ q });
        const response = await fetch(`${API}/snippets/search?${params}`);
        if (!response.ok) throw new Error('Failed to search snippets');

        const data = await response.json();
        snippets = (Array.isArray(data) ? data : []).map(normalizeSnippet);
        return snippets;
    } catch (error) {
        showToast('검색 실패', 'error');
        return [];
    }
}

async function fetchStats() {
    try {
        const response = await fetch(`${API}/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');

        return await response.json();
    } catch (error) {
        return {};
    }
}

// ============================================================================
// RENDER FUNCTIONS
// ============================================================================

function renderSnippetList(snippetsList) {
    const container = document.getElementById('snippets-container');
    const emptyState = document.getElementById('empty-state');

    if (!snippetsList || snippetsList.length === 0) {
        container.innerHTML = '';
        emptyState.style.display = 'block';
        return;
    }

    emptyState.style.display = 'none';
    container.innerHTML = snippetsList.map(snippet => `
        <div class="snippet-card" data-id="${snippet.id}">
            <div class="snippet-card-header">
                <h3 class="snippet-title">${escapeHtml(snippet.title)}</h3>
                <button class="snippet-delete" data-id="${snippet.id}" aria-label="Delete snippet">
                    🗑
                </button>
            </div>
            <span class="lang-badge">${escapeHtml(snippet.language)}</span>
            ${snippet.description ? `<p class="snippet-description">${escapeHtml(snippet.description)}</p>` : ''}
            ${snippet.tags && snippet.tags.length > 0 ? `
                <div class="snippet-tags">
                    ${snippet.tags.map(tag => `<span class="tag-badge">${escapeHtml(tag)}</span>`).join('')}
                </div>
            ` : ''}
        </div>
    `).join('');

    // Add event listeners to cards
    container.querySelectorAll('.snippet-card').forEach(card => {
        card.addEventListener('click', (e) => {
            if (!e.target.closest('.snippet-delete')) {
                const id = card.getAttribute('data-id');
                showDetail(snippets.find(s => s.id === id));
            }
        });
    });

    // Add event listeners to delete buttons
    container.querySelectorAll('.snippet-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = btn.getAttribute('data-id');
            const snippet = snippets.find(s => s.id === id);
            if (confirm(`Delete "${snippet.title}"?`)) {
                handleDeleteSnippet(id);
            }
        });
    });
}

function renderStats(stats) {
    document.getElementById('stat-total').textContent = stats.total || 0;

    const langStatsContainer = document.getElementById('stats-by-lang');
    if (stats.languages && Object.keys(stats.languages).length > 0) {
        langStatsContainer.innerHTML = Object.entries(stats.languages)
            .map(([lang, count]) => `
                <div class="stat-item">
                    <span class="stat-label">${escapeHtml(lang)}</span>
                    <span class="stat-value">${count}</span>
                </div>
            `).join('');
    }
}

function renderFilters() {
    const uniqueLangs = [...new Set(snippets.map(s => s.language))].sort();
    const uniqueTags = [...new Set(snippets.flatMap(s => s.tags || []))].sort();

    const langContainer = document.getElementById('lang-filter');
    langContainer.innerHTML = uniqueLangs.map(lang => `
        <button class="filter-item ${currentFilters.lang === lang ? 'active' : ''}" data-filter="lang" data-value="${escapeHtml(lang)}">
            ${escapeHtml(lang)}
        </button>
    `).join('');

    const tagContainer = document.getElementById('tag-filter');
    tagContainer.innerHTML = uniqueTags.map(tag => `
        <button class="filter-item ${currentFilters.tag === tag ? 'active' : ''}" data-filter="tag" data-value="${escapeHtml(tag)}">
            ${escapeHtml(tag)}
        </button>
    `).join('');
}

function showDetail(snippet) {
    if (!snippet) return;

    selectedId = snippet.id;

    const modal = document.getElementById('detail-modal');
    document.getElementById('detail-title').textContent = snippet.title;
    document.getElementById('detail-lang').textContent = snippet.language;
    document.getElementById('detail-description').textContent = snippet.description || '';

    const tagsContainer = document.getElementById('detail-tags');
    if (snippet.tags && snippet.tags.length > 0) {
        tagsContainer.innerHTML = snippet.tags
            .map(tag => `<span class="tag-badge">${escapeHtml(tag)}</span>`)
            .join('');
    } else {
        tagsContainer.innerHTML = '';
    }

    const codeElement = document.getElementById('detail-code');
    codeElement.textContent = snippet.code;
    codeElement.className = `hljs language-${snippet.language}`;

    // Highlight code
    hljs.highlightElement(codeElement);

    modal.style.display = 'flex';
}

function showAddModal() {
    selectedId = null;
    document.getElementById('form-title').textContent = 'Add Snippet';
    document.getElementById('snippet-form').reset();
    document.getElementById('form-modal').style.display = 'flex';
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type !== 'success' ? type : ''}`;
    toast.style.display = 'block';

    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

async function handleSearch(query) {
    currentFilters.query = query;

    if (query.trim()) {
        await searchSnippets(query);
    } else {
        await loadSnippets();
    }

    renderSnippetList(snippets);
}

async function handleFilterChange(filterType, value) {
    if (currentFilters[filterType] === value) {
        currentFilters[filterType] = '';
    } else {
        currentFilters[filterType] = value;
    }

    await loadSnippets();
    renderFilters();
    renderSnippetList(snippets);
}

async function handleDeleteSnippet(id) {
    try {
        await deleteSnippet(id);
        snippets = snippets.filter(s => s.id !== id);
        renderSnippetList(snippets);
        renderFilters();

        const stats = await fetchStats();
        renderStats(stats);

        document.getElementById('detail-modal').style.display = 'none';
    } catch (error) {
        console.error('Error in handleDeleteSnippet:', error);
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const formData = {
        title: document.getElementById('form-title-input').value,
        language: document.getElementById('form-lang').value,
        description: document.getElementById('form-description').value,
        code: document.getElementById('form-code').value,
        tags: document.getElementById('form-tags').value
            .split(',')
            .map(tag => tag.trim())
            .filter(tag => tag)
            .join(',')
    };

    try {
        await createSnippet(formData);
        document.getElementById('form-modal').style.display = 'none';

        await loadSnippets();
        renderFilters();
        renderSnippetList(snippets);

        const stats = await fetchStats();
        renderStats(stats);
    } catch (error) {
        console.error('Error in handleFormSubmit:', error);
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

async function loadSnippets() {
    let lang = currentFilters.lang;
    let tag = currentFilters.tag;

    if (currentFilters.query.trim()) {
        snippets = await searchSnippets(currentFilters.query);
    } else {
        snippets = await fetchSnippets(lang, tag);
    }
}

async function loadStats() {
    const stats = await fetchStats();
    renderStats(stats);
}

async function init() {
    // Load initial data
    await loadSnippets();
    await loadStats();

    renderSnippetList(snippets);
    renderFilters();

    // Event: Search input
    const searchInput = document.getElementById('search');
    searchInput.addEventListener('input', debounce((e) => {
        handleSearch(e.target.value);
    }, 300));

    // Event: Add button
    document.getElementById('add-btn').addEventListener('click', showAddModal);

    // Event: Form submission
    document.getElementById('snippet-form').addEventListener('submit', handleFormSubmit);

    // Event: Form close
    document.getElementById('form-close').addEventListener('click', () => {
        document.getElementById('form-modal').style.display = 'none';
    });

    document.getElementById('form-cancel').addEventListener('click', () => {
        document.getElementById('form-modal').style.display = 'none';
    });

    // Event: Detail modal close
    document.getElementById('detail-close').addEventListener('click', () => {
        document.getElementById('detail-modal').style.display = 'none';
    });

    // Event: Copy button
    document.getElementById('copy-btn').addEventListener('click', () => {
        const code = document.getElementById('detail-code').textContent;
        navigator.clipboard.writeText(code).then(() => {
            showToast('Code copied to clipboard');
        }).catch(err => {
            console.error('Failed to copy:', err);
            showToast('Failed to copy code', 'error');
        });
    });

    // Event: Delete button in detail modal
    document.getElementById('delete-btn').addEventListener('click', async () => {
        if (selectedId && confirm('Delete this snippet?')) {
            await handleDeleteSnippet(selectedId);
        }
    });

    // Event: Filter buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('filter-item')) {
            const filterType = e.target.getAttribute('data-filter');
            const value = e.target.getAttribute('data-value');
            handleFilterChange(filterType, value);
        }
    });

    // Event: Close modals on background click
    document.getElementById('detail-modal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            e.currentTarget.style.display = 'none';
        }
    });

    document.getElementById('form-modal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            e.currentTarget.style.display = 'none';
        }
    });
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);
