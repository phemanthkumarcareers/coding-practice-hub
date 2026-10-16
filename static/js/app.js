// Global Application Utilities & Shortcuts

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('ch_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('ch_theme', next);
    updateThemeIcon(next);
    
    // Notify Monaco editor if active
    if (window.monacoEditorInstance && window.monaco) {
        window.monaco.editor.setTheme(next === 'dark' ? 'vs-dark' : 'vs');
    }
}

function updateThemeIcon(theme) {
    const btn = document.getElementById('theme-toggle-btn');
    if (btn) {
        btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
        btn.title = `Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`;
    }
}

// Global Toast Notifications
function showToast(message, type = 'info', duration = 3000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'error') toast.style.borderColor = '#ef4444';
    if (type === 'success') toast.style.borderColor = '#10b981';
    toast.textContent = message;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Global Search
function openSearchModal() {
    const modal = document.getElementById('search-modal');
    if (modal) {
        modal.style.display = 'flex';
        const input = document.getElementById('global-search-input');
        if (input) {
            input.value = '';
            input.focus();
        }
        document.getElementById('search-results-list').innerHTML = '<div style="color:var(--text-muted); text-align:center; padding:1.5rem;">Type anything to search across all practices...</div>';
    }
}

function closeSearchModal() {
    const modal = document.getElementById('search-modal');
    if (modal) modal.style.display = 'none';
}

let searchDebounceTimer = null;
function handleSearchInput(e) {
    clearTimeout(searchDebounceTimer);
    const query = e.target.value.trim();
    if (!query) {
        document.getElementById('search-results-list').innerHTML = '';
        return;
    }

    searchDebounceTimer = setTimeout(async () => {
        try {
            const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            const listEl = document.getElementById('search-results-list');
            
            if (!data.results || data.results.length === 0) {
                listEl.innerHTML = '<div style="color:var(--text-muted); text-align:center; padding:1.5rem;">No matching practices found.</div>';
                return;
            }

            listEl.innerHTML = data.results.map(item => `
                <a href="/practice?practice_id=${item.id}&tech=${encodeURIComponent(item.technology)}" class="search-item">
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.25rem;">
                        <span style="font-weight:600; color:var(--text-primary);">${item.title || item.technology + ' Practice'}</span>
                        <span class="badge badge-${item.status.replace(/\s+/g, '-')}">${item.status}</span>
                    </div>
                    <div style="font-size:0.8rem; color:var(--text-secondary); display:flex; gap:0.75rem;">
                        <span>📅 ${item.session_date}</span>
                        <span>⚙️ ${item.technology}</span>
                        <span>⭐ ${item.difficulty}</span>
                        ${item.topic ? `<span>📌 ${item.topic}</span>` : ''}
                    </div>
                    ${item.question ? `<div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.3rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${item.question}</div>` : ''}
                </a>
            `).join('');
        } catch (err) {
            console.error('Search error:', err);
        }
    }, 250);
}

// Global Shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+K or Cmd+K: Open Search
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openSearchModal();
    }
    // Escape: Close modals
    if (e.key === 'Escape') {
        closeSearchModal();
        const genericModals = document.querySelectorAll('.modal-overlay');
        genericModals.forEach(m => m.style.display = 'none');
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
    }

    const searchInput = document.getElementById('global-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearchInput);
    }
});
