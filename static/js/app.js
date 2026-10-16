// Global Application Utilities, Sidebar & Theming Engine

// Theming Engine: supports 'system', 'light', 'dark', 'grey'
const AVAILABLE_THEMES = ['system', 'light', 'dark', 'grey'];

function resolveEffectiveTheme(pref) {
    if (pref === 'system') {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return pref;
}

function initTheme() {
    const savedPref = localStorage.getItem('ch_theme_preference') || 'dark';
    applyThemeUI(savedPref);

    // Watch system color scheme changes if system preference active
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            const currentPref = localStorage.getItem('ch_theme_preference');
            if (currentPref === 'system') {
                applyThemeUI('system');
            }
        });
    }
}

function setAppTheme(themePref) {
    if (!AVAILABLE_THEMES.includes(themePref)) return;
    localStorage.setItem('ch_theme_preference', themePref);
    applyThemeUI(themePref);

    // Persist setting to backend settings table asynchronously
    try {
        fetch('/api/settings/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme: themePref })
        }).catch(err => console.debug('Settings auto-save notice:', err));
    } catch (e) {}

    showToast(`Theme updated to ${themePref.toUpperCase()}`, 'info', 1800);
}

function applyThemeUI(themePref) {
    const effectiveTheme = resolveEffectiveTheme(themePref);
    
    // Apply dataset attribute on <html> element
    document.documentElement.setAttribute('data-theme', effectiveTheme);
    document.documentElement.setAttribute('data-theme-preference', themePref);

    // Update active highlight on theme buttons
    document.querySelectorAll('.theme-pick-btn').forEach(btn => {
        const val = btn.getAttribute('data-theme-value');
        if (val === themePref) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update Settings page select if present
    const settingSelect = document.getElementById('setting-theme');
    if (settingSelect && settingSelect.value !== themePref) {
        settingSelect.value = themePref;
    }

    // Update indicator icon in sidebar
    const activeIconEl = document.getElementById('theme-active-icon');
    if (activeIconEl) {
        const icons = {
            'system': '🖥️',
            'light': '☀️',
            'dark': '🌙',
            'grey': '🩶'
        };
        activeIconEl.textContent = icons[themePref] || '🌓';
    }

    // Update Monaco editor theme if active
    if (window.monacoEditorInstance && window.monaco) {
        const monacoTheme = effectiveTheme === 'light' ? 'vs' : 'vs-dark';
        window.monaco.editor.setTheme(monacoTheme);
    }
}

// Sidebar Collapse / Expand Controller
function initSidebar() {
    const isCollapsed = localStorage.getItem('ch_sidebar_collapsed') === 'true';
    const sidebar = document.getElementById('app-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');

    if (isCollapsed && sidebar) {
        sidebar.classList.add('collapsed');
        if (toggleBtn) toggleBtn.textContent = '▶';
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    if (!sidebar) return;

    const isCurrentlyCollapsed = sidebar.classList.contains('collapsed');
    const nextState = !isCurrentlyCollapsed;

    if (nextState) {
        sidebar.classList.add('collapsed');
        if (toggleBtn) toggleBtn.textContent = '▶';
    } else {
        sidebar.classList.remove('collapsed');
        if (toggleBtn) toggleBtn.textContent = '◀';
    }

    localStorage.setItem('ch_sidebar_collapsed', nextState);

    // Relayout Monaco editor smoothly after sidebar width transition
    setTimeout(() => {
        if (window.monacoEditorInstance) {
            window.monacoEditorInstance.layout();
        }
    }, 220);
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
    initSidebar();

    const searchInput = document.getElementById('global-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearchInput);
    }
});
