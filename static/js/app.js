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

function toggleThemeDropdown(e) {
    if (e) e.stopPropagation();
    const menu = document.getElementById('theme-dropdown-menu');
    const container = document.getElementById('theme-dropdown-container');
    if (!menu) return;

    const isOpen = menu.style.display !== 'none';
    if (isOpen) {
        menu.style.display = 'none';
        container?.classList.remove('open');
    } else {
        menu.style.display = 'flex';
        container?.classList.add('open');
    }
}

// Global outside-click closer for theme dropdown
document.addEventListener('click', (e) => {
    const container = document.getElementById('theme-dropdown-container');
    const menu = document.getElementById('theme-dropdown-menu');
    if (container && menu && !container.contains(e.target)) {
        menu.style.display = 'none';
        container.classList.remove('open');
    }
});

function applyThemeUI(themePref) {
    const effectiveTheme = resolveEffectiveTheme(themePref);
    
    // Apply dataset attribute on <html> element
    document.documentElement.setAttribute('data-theme', effectiveTheme);
    document.documentElement.setAttribute('data-theme-preference', themePref);

    // Dynamically update theme-aware logos and favicon across sidebar and main-content
    const logoUrl = `/static/images/logo-${effectiveTheme}.png`;
    window.getThemeLogoSrc = function() {
        return logoUrl;
    };
    document.querySelectorAll('.sidebar-logo, .theme-aware-logo, .main-content-logo, #app-logo-img, #dashboard-logo-img, #workspace-logo-img').forEach(img => {
        img.src = logoUrl;
    });
    const fav = document.getElementById('app-favicon');
    if (fav) {
        fav.href = logoUrl;
    }

    // Update active highlight on theme items in dropdown, collapsed bar & settings
    document.querySelectorAll('.theme-menu-item, .theme-pick-btn, .collapsed-theme-btn').forEach(btn => {
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

    // Update indicator icon and text in sidebar dropdown trigger
    const icons = {
        'system': '🖥️',
        'light': '☀️',
        'dark': '🌙',
        'grey': '🩶'
    };
    const labels = {
        'system': 'System Default',
        'light': 'Light Theme',
        'dark': 'Dark Theme',
        'grey': 'Grey (Zinc)'
    };
    const activeIconEl = document.getElementById('theme-active-icon');
    if (activeIconEl) {
        activeIconEl.textContent = icons[themePref] || '🌓';
    }
    const activeLabelEl = document.getElementById('theme-active-label');
    if (activeLabelEl) {
        activeLabelEl.textContent = labels[themePref] || 'Dark Theme';
    }

    // Close theme menu if open
    const themeMenu = document.getElementById('theme-dropdown-menu');
    const themeContainer = document.getElementById('theme-dropdown-container');
    if (themeMenu) themeMenu.style.display = 'none';
    if (themeContainer) themeContainer.classList.remove('open');

    // Update Monaco editor theme if active
    if (window.monacoEditorInstance && window.monaco) {
        const monacoTheme = effectiveTheme === 'light' ? 'vs' : 'vs-dark';
        window.monaco.editor.setTheme(monacoTheme);
    }
}

// Sidebar Collapse / Expand Controller
function initSidebar() {
    const rawVal = localStorage.getItem('ch_sidebar_collapsed');
    // By default: OPEN (not collapsed) on first launch or when null/unset
    const isCollapsed = rawVal === 'true';
    const sidebar = document.getElementById('app-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');

    if (!sidebar) return;

    if (isCollapsed) {
        sidebar.classList.add('collapsed');
        document.documentElement.classList.add('sidebar-is-collapsed');
        if (toggleBtn) toggleBtn.textContent = '▶';
    } else {
        sidebar.classList.remove('collapsed');
        document.documentElement.classList.remove('sidebar-is-collapsed');
        if (toggleBtn) toggleBtn.textContent = '◀';
    }

    // Enable smooth slide transitions only AFTER initial paint to prevent opening/minimizing flicker on refresh
    requestAnimationFrame(() => {
        setTimeout(() => {
            sidebar.classList.add('sidebar-animated');
        }, 50);
    });
}

function toggleSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle-btn');
    if (!sidebar) return;

    // Ensure transition animation is enabled on user click
    sidebar.classList.add('sidebar-animated');

    const isCurrentlyCollapsed = sidebar.classList.contains('collapsed');
    const nextState = !isCurrentlyCollapsed;

    if (nextState) {
        sidebar.classList.add('collapsed');
        document.documentElement.classList.add('sidebar-is-collapsed');
        if (toggleBtn) toggleBtn.textContent = '▶';
    } else {
        sidebar.classList.remove('collapsed');
        document.documentElement.classList.remove('sidebar-is-collapsed');
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

// Global In-App Modal Dialog Controller (Replaces window.confirm & window.prompt)
let appConfirmResolve = null;
let appPromptResolve = null;

function showAppConfirm({ title = 'Confirm Action', message = 'Are you sure?', confirmText = 'Confirm', isDanger = true, icon = '⚠️' } = {}) {
    return new Promise((resolve) => {
        const modal = document.getElementById('app-confirm-modal');
        if (!modal) {
            resolve(window.confirm(message));
            return;
        }

        document.getElementById('app-confirm-title').textContent = title;
        document.getElementById('app-confirm-message').textContent = message;
        document.getElementById('app-confirm-icon').textContent = icon;
        
        const confirmBtn = document.getElementById('app-confirm-btn');
        confirmBtn.textContent = confirmText;
        confirmBtn.className = isDanger ? 'btn btn-danger' : 'btn btn-primary';

        appConfirmResolve = resolve;
        modal.style.display = 'flex';
        confirmBtn.focus();
    });
}

function closeAppConfirm(result) {
    const modal = document.getElementById('app-confirm-modal');
    if (modal) modal.style.display = 'none';
    if (appConfirmResolve) {
        appConfirmResolve(result);
        appConfirmResolve = null;
    }
}

function showAppPrompt({ title = 'Input Required', message = 'Please enter a value:', defaultValue = '', placeholder = '', icon = '✏️' } = {}) {
    return new Promise((resolve) => {
        const modal = document.getElementById('app-prompt-modal');
        if (!modal) {
            resolve(window.prompt(message, defaultValue));
            return;
        }

        document.getElementById('app-prompt-title').textContent = title;
        document.getElementById('app-prompt-message').textContent = message;
        document.getElementById('app-prompt-icon').textContent = icon;
        
        const input = document.getElementById('app-prompt-input');
        input.value = defaultValue;
        input.placeholder = placeholder;

        appPromptResolve = resolve;
        modal.style.display = 'flex';
        setTimeout(() => {
            input.focus();
            input.select();
        }, 80);

        input.onkeydown = (e) => {
            if (e.key === 'Enter') {
                closeAppPrompt(input.value.trim());
            }
        };
    });
}

function closeAppPrompt(val) {
    const modal = document.getElementById('app-prompt-modal');
    if (modal) modal.style.display = 'none';
    if (appPromptResolve) {
        appPromptResolve(val);
        appPromptResolve = null;
    }
}

// Global Shortcuts & Escape Key Handling
document.addEventListener('keydown', (e) => {
    // Ctrl+K or Cmd+K: Open Search
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openSearchModal();
        return;
    }

    // Escape Key: Priority Hierarchy (Close Modal -> Restore Maximized Editor -> Exit Fullscreen)
    if (e.key === 'Escape') {
        // 1. Close open in-app prompt or confirm modals
        const confirmModal = document.getElementById('app-confirm-modal');
        if (confirmModal && confirmModal.style.display === 'flex') {
            closeAppConfirm(false);
            return;
        }
        const promptModal = document.getElementById('app-prompt-modal');
        if (promptModal && promptModal.style.display === 'flex') {
            closeAppPrompt(null);
            return;
        }

        // 2. Close any generic open modals (search, create-db, explorer, history)
        let closedAnyModal = false;
        document.querySelectorAll('.modal-overlay').forEach(m => {
            if (m.style.display === 'flex' || m.style.display === 'block') {
                m.style.display = 'none';
                closedAnyModal = true;
            }
        });
        if (closedAnyModal) return;

        // 3. Restore Maximized Editor (Zen Mode) if active
        const workspacePage = document.querySelector('.workspace-page');
        if (workspacePage && workspacePage.classList.contains('editor-maximized')) {
            if (typeof toggleMaximizeEditor === 'function') {
                toggleMaximizeEditor();
                return;
            }
        }

        // 4. Exit Browser Fullscreen if active
        if (isFullScreenActive()) {
            toggleFullScreen();
            return;
        }
    }
});

// Fullscreen API Controller
function isFullScreenActive() {
    return !!(document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement);
}

function toggleFullScreen() {
    try {
        if (!isFullScreenActive()) {
            const docEl = document.documentElement;
            if (docEl.requestFullscreen) {
                docEl.requestFullscreen();
            } else if (docEl.webkitRequestFullscreen) {
                docEl.webkitRequestFullscreen();
            } else if (docEl.mozRequestFullScreen) {
                docEl.mozRequestFullScreen();
            } else if (docEl.msRequestFullscreen) {
                docEl.msRequestFullscreen();
            }
            showToast('Entered Fullscreen (Press F11 or Esc to exit)', 'info', 1800);
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            showToast('Exited Fullscreen', 'info', 1500);
        }
    } catch (err) {
        console.warn('Fullscreen error:', err);
    }
}

function updateFullScreenUI() {
    const isFs = isFullScreenActive();
    document.querySelectorAll('.btn-fullscreen-trigger').forEach(btn => {
        const icon = btn.querySelector('.fullscreen-icon');
        const text = btn.querySelector('.fullscreen-text');
        if (isFs) {
            btn.classList.add('active');
            if (icon) icon.textContent = '🗗';
            if (text) text.textContent = 'Exit Fullscreen';
            btn.title = 'Exit Fullscreen (F11 / Esc)';
        } else {
            btn.classList.remove('active');
            if (icon) icon.textContent = '⛶';
            if (text) text.textContent = 'Fullscreen';
            btn.title = 'Toggle Fullscreen (F11)';
        }
    });

    setTimeout(() => {
        if (window.monacoEditorInstance) {
            window.monacoEditorInstance.layout();
        }
    }, 150);
}

document.addEventListener('fullscreenchange', updateFullScreenUI);
document.addEventListener('webkitfullscreenchange', updateFullScreenUI);
document.addEventListener('mozfullscreenchange', updateFullScreenUI);
document.addEventListener('MSFullscreenChange', updateFullScreenUI);

// Tactile Click Ripple & Press Animation Engine
function initClickAnimations() {
    document.addEventListener('pointerdown', (e) => {
        const target = e.target.closest(
            '.btn, .file-tab, .sidebar-link, .sidebar-tech-btn, .theme-dropdown-trigger, .theme-menu-item, .collapsed-theme-btn, .custom-modal-btn, .btn-new-file, .btn-open-files, .btn-file-explorer-toggle, .stat-card, .dashboard-tech-card, .btn-icon, .modal-close-btn'
        );
        if (!target) return;

        const rect = target.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * 1.6;
        const x = (e.clientX || (rect.left + rect.width / 2)) - rect.left - size / 2;
        const y = (e.clientY || (rect.top + rect.height / 2)) - rect.top - size / 2;

        const ripple = document.createElement('span');
        ripple.className = 'ripple-effect';
        ripple.style.width = `${size}px`;
        ripple.style.height = `${size}px`;
        ripple.style.left = `${x}px`;
        ripple.style.top = `${y}px`;

        target.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 550);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initSidebar();
    initClickAnimations();

    const searchInput = document.getElementById('global-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearchInput);
    }
});
