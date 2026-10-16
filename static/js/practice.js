// Practice Workspace Controller

let activePracticeId = null;
let activeTechnology = null;
let monacoEditor = null;
let isDirty = false;
let autoSaveTimer = null;
let practicesMap = {}; // id -> practice object

// Helper: Map tech to Monaco language
function getMonacoLanguage(tech, subtype) {
    if (tech === 'SQL') return 'sql';
    if (tech === 'System Design') return 'markdown';
    if (tech === 'Databricks' && subtype === 'SQL') return 'sql';
    return 'python';
}

// Initialize Monaco Editor
function initMonaco() {
    return new Promise((resolve) => {
        if (window.monaco) {
            resolve();
            return;
        }

        require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs' }});
        require(['vs/editor/editor.main'], function() {
            resolve();
        });
    });
}

function createOrUpdateEditor(code, language) {
    const container = document.getElementById('monaco-editor-container');
    if (!container) return;

    const currentTheme = document.documentElement.getAttribute('data-theme') === 'light' ? 'vs' : 'vs-dark';

    if (!monacoEditor) {
        monacoEditor = monaco.editor.create(container, {
            value: code,
            language: language,
            theme: currentTheme,
            automaticLayout: true,
            fontSize: 14,
            tabSize: 4,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineNumbers: 'on',
            folding: true,
            renderLineHighlight: 'all'
        });

        window.monacoEditorInstance = monacoEditor;

        monacoEditor.onDidChangeModelContent(() => {
            isDirty = true;
            scheduleAutosave();
        });

        // Ctrl+Enter: Run Code
        monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
            runCurrentCode();
        });

        // Ctrl+S: Save
        monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
            saveCurrentPractice(false);
        });
    } else {
        const model = monacoEditor.getModel();
        monaco.editor.setModelLanguage(model, language);
        if (monacoEditor.getValue() !== code) {
            monacoEditor.setValue(code);
        }
    }
}

// Switch Technology Tab
async function switchTech(techName) {
    if (activeTechnology === techName) return;

    // Save previous if dirty
    if (isDirty && activePracticeId) {
        await saveCurrentPractice(false);
    }

    activeTechnology = techName;

    // Update tab UI
    document.querySelectorAll('.tech-tab').forEach(btn => {
        if (btn.getAttribute('data-tech') === techName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Find practice record
    const p = Object.values(practicesMap).find(x => x.technology === techName);
    if (!p) return;

    activePracticeId = p.id;

    // Update metadata inputs
    document.getElementById('meta-title').value = p.title || '';
    document.getElementById('meta-difficulty').value = p.difficulty || 'Medium';
    document.getElementById('meta-topic').value = p.topic || '';
    document.getElementById('meta-tags').value = p.tags || '';
    document.getElementById('meta-question').value = p.question || '';
    document.getElementById('meta-notes').value = p.notes || '';
    
    // Status Badge
    updateStatusBadge(p.status);

    // Parse extra metadata if any
    let extra = {};
    try {
        extra = typeof p.extra_metadata === 'string' ? JSON.parse(p.extra_metadata || '{}') : (p.extra_metadata || {});
    } catch (e) {
        extra = {};
    }

    // Toggle Specialized UI Panes
    setupSpecializedUI(techName, extra);

    // Update Editor
    const lang = getMonacoLanguage(techName, extra.subtype);
    createOrUpdateEditor(p.code || '', lang);

    // Render Output
    renderOutput(p.latest_output, p.latest_error, p.duration_ms);

    // If System Design, trigger mermaid preview
    if (techName === 'System Design') {
        renderSystemDesignPreview(p.code || '');
    }

    isDirty = false;
}

function updateStatusBadge(status) {
    const badge = document.getElementById('practice-status-badge');
    if (badge) {
        badge.className = `badge badge-${status.replace(/\s+/g, '-')}`;
        badge.textContent = status;
    }
}

// Specialized UI settings
function setupSpecializedUI(tech, extra) {
    const dsaPanel = document.getElementById('dsa-specific-panel');
    const databricksPanel = document.getElementById('databricks-specific-panel');
    const systemDesignPreview = document.getElementById('system-design-preview-container');
    const standardOutput = document.getElementById('standard-output-container');
    const sqlExplorerBtn = document.getElementById('btn-toggle-sql-explorer');

    // Default hide all
    if (dsaPanel) dsaPanel.style.display = 'none';
    if (databricksPanel) databricksPanel.style.display = 'none';
    if (systemDesignPreview) systemDesignPreview.style.display = 'none';
    if (standardOutput) standardOutput.style.display = 'flex';
    if (sqlExplorerBtn) sqlExplorerBtn.style.display = 'none';

    if (tech === 'DSA') {
        if (dsaPanel) {
            dsaPanel.style.display = 'block';
            document.getElementById('dsa-constraints').value = extra.constraints || '';
            document.getElementById('dsa-time-complexity').value = extra.time_complexity || '';
            document.getElementById('dsa-space-complexity').value = extra.space_complexity || '';
            document.getElementById('dsa-test-cases').value = extra.test_cases || '';
        }
    } else if (tech === 'Databricks') {
        if (databricksPanel) {
            databricksPanel.style.display = 'block';
            document.getElementById('databricks-subtype').value = extra.subtype || 'PySpark';
        }
    } else if (tech === 'System Design') {
        if (systemDesignPreview) systemDesignPreview.style.display = 'block';
        if (standardOutput) standardOutput.style.display = 'none';
    } else if (tech === 'SQL') {
        if (sqlExplorerBtn) sqlExplorerBtn.style.display = 'inline-flex';
    }
}

// Gather extra metadata depending on active technology
function gatherExtraMetadata() {
    let extra = {};
    if (activeTechnology === 'DSA') {
        extra.constraints = document.getElementById('dsa-constraints')?.value || '';
        extra.time_complexity = document.getElementById('dsa-time-complexity')?.value || '';
        extra.space_complexity = document.getElementById('dsa-space-complexity')?.value || '';
        extra.test_cases = document.getElementById('dsa-test-cases')?.value || '';
    } else if (activeTechnology === 'Databricks') {
        extra.subtype = document.getElementById('databricks-subtype')?.value || 'PySpark';
    }
    return extra;
}

// Autosave Scheduler
function scheduleAutosave() {
    const indicator = document.getElementById('autosave-indicator');
    if (indicator) {
        indicator.innerHTML = '<span style="color:var(--text-muted);">● Unsaved changes</span>';
    }

    clearTimeout(autoSaveTimer);
    autoSaveTimer = setTimeout(() => {
        saveCurrentPractice(false);
    }, 15000); // 15 seconds debounce
}

// Save Practice
async function saveCurrentPractice(markCompleted = false) {
    if (!activePracticeId) return;

    const indicator = document.getElementById('autosave-indicator');
    if (indicator) indicator.textContent = 'Saving...';

    const code = monacoEditor ? monacoEditor.getValue() : '';
    const currentPractice = practicesMap[activePracticeId];
    
    let targetStatus = currentPractice.status;
    if (markCompleted) {
        targetStatus = 'COMPLETED';
    } else if (targetStatus === 'NOT STARTED' && code.trim().length > 0) {
        targetStatus = 'IN PROGRESS';
    }

    const payload = {
        id: activePracticeId,
        title: document.getElementById('meta-title').value,
        difficulty: document.getElementById('meta-difficulty').value,
        topic: document.getElementById('meta-topic').value,
        tags: document.getElementById('meta-tags').value,
        question: document.getElementById('meta-question').value,
        notes: document.getElementById('meta-notes').value,
        code: code,
        status: targetStatus,
        extra_metadata: gatherExtraMetadata()
    };

    try {
        const res = await fetch('/api/practice/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.success) {
            isDirty = false;
            // Update local cache
            Object.assign(currentPractice, payload);
            updateStatusBadge(targetStatus);
            
            // Update 6/6 counter in header
            if (data.completed_count !== undefined) {
                const countBadge = document.getElementById('session-completion-badge');
                if (countBadge) countBadge.textContent = `${data.completed_count} / 6`;
            }

            const now = new Date().toLocaleTimeString();
            if (indicator) indicator.textContent = `All changes saved (${now})`;
            if (markCompleted) showToast('Practice marked as COMPLETED! 🎉', 'success');
        } else {
            if (indicator) indicator.textContent = 'Save failed';
            showToast(data.error || 'Failed to save', 'error');
        }
    } catch (err) {
        if (indicator) indicator.textContent = 'Save error';
        console.error('Save error:', err);
    }
}

// Run Code
async function runCurrentCode() {
    if (!activePracticeId) return;

    // First ensure latest edits are saved
    await saveCurrentPractice(false);

    updateStatusBadge('RUNNING');
    const runBtn = document.getElementById('btn-run');
    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML = '⏳ Running...';
    }

    const code = monacoEditor ? monacoEditor.getValue() : '';
    const payload = {
        id: activePracticeId,
        technology: activeTechnology,
        code: code,
        extra_metadata: gatherExtraMetadata()
    };

    try {
        const res = await fetch('/api/practice/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        
        // Update local practice state
        const p = practicesMap[activePracticeId];
        p.latest_output = data.output;
        p.latest_error = data.error;
        p.status = data.practice_status;
        p.duration_ms = data.duration_ms;

        updateStatusBadge(p.status);
        renderOutput(data.output, data.error, data.duration_ms, data.structured_result);

        if (data.status === 'SUCCESS') {
            showToast(`Execution succeeded (${data.duration_ms}ms)`, 'success');
        } else {
            showToast('Execution finished with errors', 'error');
        }

    } catch (err) {
        console.error('Run error:', err);
        renderOutput('', `Client-side execution request error: ${err.message}`, 0);
        updateStatusBadge('FAILED');
    } finally {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = '▶ Run';
        }
    }
}

// Render Output Panel
function renderOutput(stdout, stderr, durationMs, structuredResult) {
    const container = document.getElementById('output-console');
    if (!container) return;

    const timerBadge = document.getElementById('output-duration-badge');
    if (timerBadge) timerBadge.textContent = durationMs ? `${durationMs} ms` : '';

    container.innerHTML = '';

    if (structuredResult && structuredResult.columns && structuredResult.columns.length > 0) {
        // Render Structured SQL Results Table
        const table = document.createElement('table');
        table.className = 'output-table';

        // Header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        structuredResult.columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');
        structuredResult.rows.forEach(row => {
            const tr = document.createElement('tr');
            row.forEach(val => {
                const td = document.createElement('td');
                td.textContent = val !== null ? val : 'NULL';
                if (val === null) td.style.color = 'var(--text-muted)';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);

        container.appendChild(table);

        const summary = document.createElement('div');
        summary.style.marginTop = '0.5rem';
        summary.style.fontSize = '0.8rem';
        summary.style.color = 'var(--text-secondary)';
        summary.textContent = `Rows returned: ${structuredResult.row_count} ${structuredResult.truncated ? '(truncated for display)' : ''}`;
        container.appendChild(summary);
    } else {
        // Plain text output
        if (stdout) {
            const outDiv = document.createElement('div');
            outDiv.textContent = stdout;
            container.appendChild(outDiv);
        }
    }

    if (stderr) {
        const errDiv = document.createElement('div');
        errDiv.className = 'output-error';
        errDiv.style.marginTop = stdout ? '0.75rem' : '0';
        errDiv.textContent = stderr;
        container.appendChild(errDiv);
    }

    if (!stdout && !stderr && (!structuredResult || !structuredResult.columns)) {
        container.innerHTML = '<span style="color:var(--text-muted);">No output yet. Click Run to execute code.</span>';
    }
}

// Render System Design Preview (Markdown + Mermaid)
function renderSystemDesignPreview(markdownText) {
    const previewEl = document.getElementById('system-design-preview-container');
    if (!previewEl) return;

    // Simple markdown renderer for headers, lists, code, mermaid
    let html = markdownText
        .replace(/^### (.*$)/gim, '<h3 style="margin-top:0.75rem; color:var(--accent-primary);">$1</h3>')
        .replace(/^## (.*$)/gim, '<h2 style="margin-top:1rem; border-bottom:1px solid var(--border-color); padding-bottom:0.25rem;">$1</h2>')
        .replace(/^# (.*$)/gim, '<h1 style="font-size:1.4rem; margin-bottom:0.5rem;">$1</h1>')
        .replace(/^\- (.*$)/gim, '<li style="margin-left:1.25rem;">$1</li>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');

    // Extract mermaid blocks
    html = html.replace(/```mermaid([\s\S]*?)```/gim, function(match, code) {
        return `<pre class="mermaid">${code.trim()}</pre>`;
    });

    previewEl.innerHTML = html;

    // Run Mermaid renderer if library loaded
    if (window.mermaid) {
        try {
            mermaid.run({ nodes: previewEl.querySelectorAll('.mermaid') });
        } catch (e) {
            console.error('Mermaid rendering error:', e);
        }
    }
}

// Open Execution History Modal
async function openExecutionHistory() {
    if (!activePracticeId) return;

    const modal = document.getElementById('history-modal');
    const container = document.getElementById('history-list-container');
    if (!modal || !container) return;

    modal.style.display = 'flex';
    container.innerHTML = '<div style="text-align:center; padding:1.5rem; color:var(--text-muted);">Loading attempts...</div>';

    try {
        const res = await fetch(`/api/practice/executions/${activePracticeId}`);
        const executions = await res.json();

        if (!executions || executions.length === 0) {
            container.innerHTML = '<div style="text-align:center; padding:1.5rem; color:var(--text-muted);">No execution history recorded for this practice yet.</div>';
            return;
        }

        container.innerHTML = executions.map((item, idx) => {
            const attemptNum = executions.length - idx;
            const dateStr = new Date(item.created_at).toLocaleString();
            return `
                <div style="background:var(--bg-tertiary); border:1px solid var(--border-color); border-radius:6px; padding:0.85rem; margin-bottom:0.75rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                        <div>
                            <span style="font-weight:700;">Execution #${attemptNum}</span>
                            <span class="badge badge-${item.status}" style="margin-left:0.5rem;">${item.status}</span>
                            <span style="font-size:0.78rem; color:var(--text-muted); margin-left:0.5rem;">${item.duration_ms} ms</span>
                        </div>
                        <div style="display:flex; gap:0.4rem;">
                            <button class="btn btn-secondary btn-sm" onclick="copyCodeSnapshot(${item.id})">📋 Copy</button>
                            <button class="btn btn-primary btn-sm" onclick="restoreCodeSnapshot(${item.id})">↺ Restore Code</button>
                        </div>
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:0.5rem;">${dateStr}</div>
                    <pre style="background:var(--editor-bg); color:var(--text-primary); padding:0.5rem; border-radius:4px; font-family:var(--font-mono); font-size:0.8rem; max-height:120px; overflow:auto;">${escapeHtml(item.code_snapshot)}</pre>
                    ${item.error_output ? `<div style="color:#f87171; font-size:0.75rem; font-family:var(--font-mono); margin-top:0.4rem; max-height:60px; overflow:auto;">${escapeHtml(item.error_output)}</div>` : ''}
                </div>
            `;
        }).join('');

        window.currentExecutionsCache = executions;
    } catch (err) {
        container.innerHTML = `<div style="color:#f87171;">Failed to load executions: ${err.message}</div>`;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function copyCodeSnapshot(execId) {
    const item = (window.currentExecutionsCache || []).find(x => x.id === execId);
    if (item && item.code_snapshot) {
        navigator.clipboard.writeText(item.code_snapshot);
        showToast('Code copied to clipboard!', 'info');
    }
}

function restoreCodeSnapshot(execId) {
    const item = (window.currentExecutionsCache || []).find(x => x.id === execId);
    if (item && monacoEditor) {
        monacoEditor.setValue(item.code_snapshot);
        document.getElementById('history-modal').style.display = 'none';
        isDirty = true;
        scheduleAutosave();
        showToast('Restored previous code snapshot into editor!', 'success');
    }
}

// Split Resizer Logic
function initResizer() {
    const resizer = document.getElementById('workspace-resizer');
    const editorPane = document.getElementById('editor-pane');
    const splitContainer = document.querySelector('.split-container');
    if (!resizer || !editorPane || !splitContainer) return;

    let isResizing = false;

    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        resizer.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
    });

    window.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const containerRect = splitContainer.getBoundingClientRect();
        const offsetLeft = e.clientX - containerRect.left;
        const totalWidth = containerRect.width;
        let percentage = (offsetLeft / totalWidth) * 100;

        // Boundaries: 30% to 85%
        if (percentage < 30) percentage = 30;
        if (percentage > 85) percentage = 85;

        editorPane.style.flex = `0 0 ${percentage}%`;
        if (monacoEditor) monacoEditor.layout();
    });

    window.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            resizer.classList.remove('resizing');
            document.body.style.cursor = '';
            if (monacoEditor) monacoEditor.layout();
        }
    });
}

// DuckDB Table Explorer Drawer
async function toggleDuckDBExplorer() {
    const modal = document.getElementById('duckdb-explorer-modal');
    if (!modal) return;

    if (modal.style.display === 'flex') {
        modal.style.display = 'none';
        return;
    }

    modal.style.display = 'flex';
    const container = document.getElementById('duckdb-explorer-list');
    container.innerHTML = '<div style="color:var(--text-muted); text-align:center; padding:1.5rem;">Loading DuckDB tables & views...</div>';

    try {
        const res = await fetch('/api/datasets/duckdb_explorer');
        const data = await res.json();
        
        if (!data.schemas || data.schemas.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted); text-align:center; padding:1.5rem;">No tables or views found. Upload a dataset in the Datasets tab to query it here!</div>';
            return;
        }

        container.innerHTML = data.schemas.map(s => `
            <div style="background:var(--bg-tertiary); border:1px solid var(--border-color); border-radius:6px; padding:0.75rem; margin-bottom:0.6rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600; font-family:var(--font-mono);">${s.name}</span>
                    <span class="badge badge-NOT-STARTED">${s.type} ${s.row_count !== null ? `(${s.row_count} rows)` : ''}</span>
                </div>
                <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:0.3rem;">
                    ${s.columns.map(c => `<code>${c.name}</code> (${c.type})`).join(', ')}
                </div>
                <button class="btn btn-secondary btn-sm" style="margin-top:0.4rem;" onclick="insertTableQuery('${s.name}')">
                    Insert SELECT query
                </button>
            </div>
        `).join('');
    } catch (err) {
        container.innerHTML = `<div style="color:#f87171;">Error loading explorer: ${err.message}</div>`;
    }
}

function insertTableQuery(tableName) {
    if (monacoEditor) {
        const currentCode = monacoEditor.getValue();
        const snippet = `\nSELECT * FROM "${tableName}" LIMIT 10;\n`;
        monacoEditor.setValue(currentCode + snippet);
        document.getElementById('duckdb-explorer-modal').style.display = 'none';
        isDirty = true;
        scheduleAutosave();
    }
}

// Warn on accidental exit with unsaved edits
window.addEventListener('beforeunload', (e) => {
    if (isDirty) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes in your practice workspace.';
    }
});

// Main Setup for Practice page
async function initPracticePage(sessionData, initialTech) {
    // Populate cache
    sessionData.practices.forEach(p => {
        practicesMap[p.id] = p;
    });

    // Wire up Metadata inputs for auto-dirty tracking
    ['meta-title', 'meta-difficulty', 'meta-topic', 'meta-tags', 'meta-question', 'meta-notes'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', () => {
                isDirty = true;
                scheduleAutosave();
            });
        }
    });

    // Specialized panel inputs
    ['dsa-constraints', 'dsa-time-complexity', 'dsa-space-complexity', 'dsa-test-cases', 'databricks-subtype'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', () => {
                isDirty = true;
                scheduleAutosave();
            });
        }
    });

    // Buttons
    document.getElementById('btn-run')?.addEventListener('click', runCurrentCode);
    document.getElementById('btn-save')?.addEventListener('click', () => saveCurrentPractice(false));
    document.getElementById('btn-save-complete')?.addEventListener('click', () => saveCurrentPractice(true));
    document.getElementById('btn-clear-output')?.addEventListener('click', () => renderOutput('', '', 0));
    document.getElementById('btn-exec-history')?.addEventListener('click', openExecutionHistory);
    document.getElementById('btn-toggle-sql-explorer')?.addEventListener('click', toggleDuckDBExplorer);

    // Reset Button
    document.getElementById('btn-reset')?.addEventListener('click', () => {
        if (confirm('Are you sure you want to reset code to empty/default? This will not delete your past execution history.')) {
            if (monacoEditor) {
                monacoEditor.setValue('-- Reset workspace\n');
                isDirty = true;
                scheduleAutosave();
            }
        }
    });

    // Resizer
    initResizer();

    // Load Monaco
    await initMonaco();

    // Select initial tab
    await switchTech(initialTech || 'SQL');
}
