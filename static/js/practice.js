// Practice Workspace Controller - With Multi-File Python & Multi-Database SQL Support

let activePracticeId = null;
let activeTechnology = null;
let monacoEditor = null;
let isDirty = false;
let autoSaveTimer = null;
let practicesMap = {}; // id -> practice object

// Multi-File Project State (For Python / DSA / Databricks)
let currentProjectFiles = { "main.py": "" };
let activeFileName = "main.py";

// Database Context State (For DuckDB SQL)
let activeDatabaseName = "main";
let availableDatabases = [];
let cachedExplorerSchemas = [];

// Helper: Map extension or tech to Monaco language
function getLanguageForFile(filename, tech, subtype) {
    if (filename.endsWith('.py')) return 'python';
    if (filename.endsWith('.sql')) return 'sql';
    if (filename.endsWith('.json')) return 'json';
    if (filename.endsWith('.md')) return 'markdown';

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
            // Update active file buffer for all technologies
            currentProjectFiles[activeFileName] = monacoEditor.getValue();
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

// Multi-File Project Workspace Helpers (Enabled for ALL technologies)
function renderMultiFileTabs() {
    const bar = document.getElementById('multi-file-tabs-bar');
    if (!bar) return;

    bar.style.display = 'flex';
    bar.innerHTML = '';

    Object.keys(currentProjectFiles).forEach(fname => {
        const tab = document.createElement('div');
        tab.className = `file-tab ${fname === activeFileName ? 'active' : ''}`;
        
        const titleSpan = document.createElement('span');
        titleSpan.textContent = fname;
        titleSpan.onclick = () => switchActiveFile(fname);
        tab.appendChild(titleSpan);

        // Close/delete file button (don't delete if it's the only file or main.py)
        if (Object.keys(currentProjectFiles).length > 1) {
            const closeBtn = document.createElement('span');
            closeBtn.className = 'file-tab-close';
            closeBtn.innerHTML = '&times;';
            closeBtn.title = `Delete ${fname}`;
            closeBtn.onclick = (e) => {
                e.stopPropagation();
                deleteProjectFile(fname);
            };
            tab.appendChild(closeBtn);
        }

        bar.appendChild(tab);
    });

    // "+ New File" Button
    const newBtn = document.createElement('button');
    newBtn.className = 'btn-new-file';
    newBtn.innerHTML = '+ New File';
    newBtn.onclick = promptNewFile;
    bar.appendChild(newBtn);
}

function switchActiveFile(targetFileName) {
    if (activeFileName === targetFileName) return;

    // Save current content in buffer
    if (monacoEditor) {
        currentProjectFiles[activeFileName] = monacoEditor.getValue();
    }

    activeFileName = targetFileName;
    const code = currentProjectFiles[activeFileName] || '';
    const lang = getLanguageForFile(activeFileName, activeTechnology);

    if (monacoEditor) {
        createOrUpdateEditor(code, lang);
    }

    renderMultiFileTabs();
}

async function promptNewFile() {
    let defaultSuggest = 'utils.py';
    let defaultExt = '.py';
    if (activeTechnology === 'SQL') {
        defaultSuggest = 'tables.sql';
        defaultExt = '.sql';
    } else if (activeTechnology === 'System Design') {
        defaultSuggest = 'architecture_notes.md';
        defaultExt = '.md';
    }

    const name = await showAppPrompt({
        title: 'Create New File',
        message: `Enter new file name for your ${activeTechnology} workspace:`,
        defaultValue: defaultSuggest,
        placeholder: `e.g. ${defaultSuggest}`,
        icon: '📄'
    });

    if (!name || !name.trim()) return;
    let cleanName = name.trim();

    if (!cleanName.includes('.')) {
        cleanName += defaultExt;
    }

    if (cleanName in currentProjectFiles) {
        showToast(`File '${cleanName}' already exists. Switched to it.`, 'info');
        switchActiveFile(cleanName);
        return;
    }

    let defaultContent = `-- ${cleanName}\n`;
    if (cleanName.endsWith('.py')) {
        defaultContent = `# ${cleanName}\n\ndef example_function():\n    return "Hello from ${cleanName}"\n`;
    } else if (cleanName.endsWith('.sql')) {
        defaultContent = `-- ${cleanName}\nSELECT 1 AS status;\n`;
    } else if (cleanName.endsWith('.md')) {
        defaultContent = `# ${cleanName}\n\nDocument architecture notes here.\n`;
    } else if (cleanName.endsWith('.json')) {
        defaultContent = `{\n  "name": "${cleanName}"\n}\n`;
    }

    currentProjectFiles[cleanName] = defaultContent;
    switchActiveFile(cleanName);
    isDirty = true;
    scheduleAutosave();
    showToast(`Created ${cleanName}`, 'success');
}

async function deleteProjectFile(filename) {
    const isConfirmed = await showAppConfirm({
        title: 'Delete File',
        message: `Are you sure you want to delete '${filename}' from this practice? This action cannot be undone.`,
        confirmText: 'Delete File',
        isDanger: true,
        icon: '🗑️'
    });

    if (!isConfirmed) return;

    delete currentProjectFiles[filename];
    const remaining = Object.keys(currentProjectFiles);
    activeFileName = remaining[0] || (activeTechnology === 'SQL' ? 'query.sql' : 'main.py');
    if (!currentProjectFiles[activeFileName]) {
        currentProjectFiles[activeFileName] = '';
    }
    
    const code = currentProjectFiles[activeFileName] || '';
    const lang = getLanguageForFile(activeFileName, activeTechnology);
    createOrUpdateEditor(code, lang);
    renderMultiFileTabs();
    isDirty = true;
    scheduleAutosave();
    showToast(`Deleted ${filename}`, 'info');
}

// Database Selector & Creation (For DuckDB SQL)
async function loadDatabasesList() {
    try {
        const res = await fetch('/api/practice/databases');
        const data = await res.json();
        if (data.success && data.databases) {
            availableDatabases = data.databases;
            const selectEl = document.getElementById('sql-active-db-select');
            if (selectEl) {
                selectEl.innerHTML = '';
                availableDatabases.forEach(db => {
                    const opt = document.createElement('option');
                    opt.value = db.name;
                    opt.textContent = `${db.name === 'main' ? 'practice (main / default)' : db.name}`;
                    if (db.name === activeDatabaseName) opt.selected = true;
                    selectEl.appendChild(opt);
                });

                selectEl.onchange = (e) => {
                    activeDatabaseName = e.target.value;
                    showToast(`Switched active database context to '${activeDatabaseName}'`, 'info');
                };
            }
        }
    } catch (e) {
        console.error('Error loading databases:', e);
    }
}

// In-App Database Creation Modal Controller
function openCreateDatabaseModal() {
    const modal = document.getElementById('create-db-modal');
    const input = document.getElementById('new-db-name-input');
    const err = document.getElementById('create-db-error');
    if (!modal) return;

    if (err) {
        err.style.display = 'none';
        err.textContent = '';
    }
    if (input) {
        input.value = '';
    }
    modal.style.display = 'flex';
    setTimeout(() => input?.focus(), 120);
}

function closeCreateDatabaseModal() {
    const modal = document.getElementById('create-db-modal');
    if (modal) modal.style.display = 'none';
}

async function submitCreateDatabaseModal() {
    const input = document.getElementById('new-db-name-input');
    const err = document.getElementById('create-db-error');
    const submitBtn = document.getElementById('btn-submit-create-db');
    const rawName = (input?.value || '').trim();

    if (!rawName) {
        if (err) {
            err.textContent = 'Please enter a database name.';
            err.style.display = 'block';
        }
        input?.focus();
        return;
    }

    const safeName = rawName.replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase();

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Creating...';
    }

    try {
        const res = await fetch('/api/practice/database/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: safeName })
        });
        const data = await res.json();

        if (data.success) {
            showToast(`Database '${data.database}' created and attached! 🎉`, 'success');
            activeDatabaseName = data.database;
            await loadDatabasesList();
            await refreshExplorerList();
            closeCreateDatabaseModal();
        } else {
            if (err) {
                err.textContent = data.error || 'Failed to create database';
                err.style.display = 'block';
            }
        }
    } catch (e) {
        if (err) {
            err.textContent = 'Server error creating database: ' + e.message;
            err.style.display = 'block';
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>+ Create Database</span>';
        }
    }
}

function promptCreateDatabase() {
    openCreateDatabaseModal();
}

function createDatabaseFromExplorer() {
    openCreateDatabaseModal();
}

// Switch Technology Tab
async function switchTech(techName) {
    if (activeTechnology === techName) return;

    // Save previous if dirty
    if (isDirty && activePracticeId) {
        await saveCurrentPractice(false);
    }

    activeTechnology = techName;

    // Update tab UI (both sidebar tech buttons and any header tabs)
    document.querySelectorAll('.sidebar-tech-btn, .tech-tab').forEach(btn => {
        if (btn.getAttribute('data-tech') === techName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update Header Active Tech Pill
    const icons = {
        'SQL': '🗄️',
        'Python': '🐍',
        'PySpark': '⚡',
        'Databricks': '🧱',
        'DSA': '🧩',
        'System Design': '📐'
    };
    const iconEl = document.getElementById('header-tech-icon');
    const nameEl = document.getElementById('header-tech-name');
    if (iconEl) iconEl.textContent = icons[techName] || '💻';
    if (nameEl) nameEl.textContent = techName;

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

    // Restore multi-file project workspace for ALL coding technologies
    const defaultEntryFiles = {
        'SQL': 'query.sql',
        'Python': 'main.py',
        'PySpark': 'pipeline.py',
        'Databricks': 'notebook.py',
        'DSA': 'solution.py',
        'System Design': 'architecture.md'
    };
    const defaultFile = defaultEntryFiles[techName] || 'main.py';

    if (extra.files && typeof extra.files === 'object' && Object.keys(extra.files).length > 0) {
        currentProjectFiles = extra.files;
        activeFileName = extra.active_file || Object.keys(extra.files)[0];
    } else {
        currentProjectFiles = { [defaultFile]: p.code || "" };
        activeFileName = defaultFile;
    }
    renderMultiFileTabs();

    // Toggle Specialized UI Panes
    setupSpecializedUI(techName, extra);

    // Update Editor
    const initialCode = currentProjectFiles[activeFileName] || p.code || '';
    const lang = getLanguageForFile(activeFileName, techName, extra.subtype);
    createOrUpdateEditor(initialCode, lang);

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

    const headerBadge = document.getElementById('header-tech-status-badge');
    if (headerBadge) {
        headerBadge.className = `badge badge-${status.replace(/\s+/g, '-')}`;
        headerBadge.textContent = status;
    }

    if (activeTechnology) {
        const dotId = `status-dot-${activeTechnology.toLowerCase().replace(/\s+/g, '-')}`;
        const dot = document.getElementById(dotId);
        if (dot) {
            dot.className = `tech-status-dot status-${status.replace(/\s+/g, '-')}`;
            dot.title = status;
        }
    }
}

// Specialized UI settings
function setupSpecializedUI(tech, extra) {
    const dsaPanel = document.getElementById('dsa-specific-panel');
    const databricksPanel = document.getElementById('databricks-specific-panel');
    const systemDesignPreview = document.getElementById('system-design-preview-container');
    const standardOutput = document.getElementById('standard-output-container');
    const sqlDbToolbar = document.getElementById('sql-db-toolbar');

    // Default hide specialized panels
    if (dsaPanel) dsaPanel.style.display = 'none';
    if (databricksPanel) databricksPanel.style.display = 'none';
    if (systemDesignPreview) systemDesignPreview.style.display = 'none';
    if (standardOutput) standardOutput.style.display = 'flex';
    if (sqlDbToolbar) sqlDbToolbar.style.display = 'none';

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
        if (sqlDbToolbar) {
            sqlDbToolbar.style.display = 'inline-flex';
            loadDatabasesList();
        }
    }
}

// Gather extra metadata
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

    // Persist multi-file project across all technologies
    if (monacoEditor) {
        currentProjectFiles[activeFileName] = monacoEditor.getValue();
    }
    extra.files = currentProjectFiles;
    extra.active_file = activeFileName;

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

    // Update active file buffer
    if (monacoEditor) {
        currentProjectFiles[activeFileName] = monacoEditor.getValue();
    }

    const code = monacoEditor ? (currentProjectFiles[activeFileName] || monacoEditor.getValue()) : '';
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
            Object.assign(currentPractice, payload);
            updateStatusBadge(targetStatus);
            
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

    // Save active editor into currentProjectFiles buffer
    if (monacoEditor) {
        currentProjectFiles[activeFileName] = monacoEditor.getValue();
    }

    await saveCurrentPractice(false);

    updateStatusBadge('RUNNING');
    const runBtn = document.getElementById('btn-run');
    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML = '⏳ Running...';
    }

    const code = monacoEditor ? (currentProjectFiles[activeFileName] || monacoEditor.getValue()) : '';
    const payload = {
        id: activePracticeId,
        technology: activeTechnology,
        code: code,
        active_db: activeDatabaseName,
        files: currentProjectFiles,
        entry_file: activeFileName,
        extra_metadata: gatherExtraMetadata()
    };

    try {
        const res = await fetch('/api/practice/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        
        const p = practicesMap[activePracticeId];
        p.latest_output = data.output;
        p.latest_error = data.error;
        p.status = data.practice_status;
        p.duration_ms = data.duration_ms;

        updateStatusBadge(p.status);
        renderOutput(data.output, data.error, data.duration_ms, data.structured_result);

        // Update live database tables if returned
        if (data.updated_schemas) {
            cachedExplorerSchemas = data.updated_schemas;
            renderExplorerSchemaList(cachedExplorerSchemas);
        }

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

// Render Output Console
function renderOutput(stdout, stderr, durationMs, structuredResult) {
    const container = document.getElementById('output-console');
    if (!container) return;

    const timerBadge = document.getElementById('output-duration-badge');
    if (timerBadge) timerBadge.textContent = durationMs ? `${durationMs} ms` : '';

    container.innerHTML = '';

    if (structuredResult && structuredResult.columns && structuredResult.columns.length > 0) {
        const table = document.createElement('table');
        table.className = 'output-table';

        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        structuredResult.columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

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
        summary.textContent = `Rows returned: ${structuredResult.row_count} ${structuredResult.truncated ? '(truncated for display)' : ''} | DB Context: ${structuredResult.active_database || 'main'}`;
        container.appendChild(summary);
    } else {
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
        container.innerHTML = '<span style="color:var(--text-muted);">Ready. Click Run to execute code.</span>';
    }
}

// Render System Design Preview
function renderSystemDesignPreview(markdownText) {
    const previewEl = document.getElementById('system-design-preview-container');
    if (!previewEl) return;

    let html = markdownText
        .replace(/^### (.*$)/gim, '<h3 style="margin-top:0.75rem; color:var(--accent-primary);">$1</h3>')
        .replace(/^## (.*$)/gim, '<h2 style="margin-top:1rem; border-bottom:1px solid var(--border-color); padding-bottom:0.25rem;">$1</h2>')
        .replace(/^# (.*$)/gim, '<h1 style="font-size:1.4rem; margin-bottom:0.5rem;">$1</h1>')
        .replace(/^\- (.*$)/gim, '<li style="margin-left:1.25rem;">$1</li>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');

    html = html.replace(/```mermaid([\s\S]*?)```/gim, function(match, code) {
        return `<pre class="mermaid">${code.trim()}</pre>`;
    });

    previewEl.innerHTML = html;

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

// Vertical Split Resizer Logic (Editor on top, Console below)
function initResizer() {
    const resizer = document.getElementById('workspace-resizer');
    const editorPane = document.getElementById('editor-pane');
    const splitContainer = document.querySelector('.split-container');
    if (!resizer || !editorPane || !splitContainer) return;

    let isResizing = false;

    resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        resizer.classList.add('resizing');
        document.body.style.cursor = 'row-resize';
    });

    window.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const containerRect = splitContainer.getBoundingClientRect();
        const offsetTop = e.clientY - containerRect.top;
        const totalHeight = containerRect.height;
        let percentage = (offsetTop / totalHeight) * 100;

        // Boundaries: 20% to 85%
        if (percentage < 20) percentage = 20;
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

// DuckDB Table & Database Explorer
async function toggleDuckDBExplorer() {
    const modal = document.getElementById('duckdb-explorer-modal');
    if (!modal) return;

    if (modal.style.display === 'flex') {
        modal.style.display = 'none';
        return;
    }

    modal.style.display = 'flex';
    await refreshExplorerList();
}

async function refreshExplorerList() {
    const container = document.getElementById('duckdb-explorer-list');
    if (!container) return;
    container.innerHTML = '<div style="color:var(--text-muted); text-align:center; padding:1.5rem;">Inspecting databases, tables & views...</div>';

    try {
        const res = await fetch('/api/datasets/duckdb_explorer');
        const data = await res.json();
        
        if (!data.schemas || data.schemas.length === 0) {
            container.innerHTML = '<div style="color:var(--text-muted); text-align:center; padding:1.5rem;">No tables or views found. Upload a dataset or run a CREATE TABLE statement to see it here!</div>';
            return;
        }

        cachedExplorerSchemas = data.schemas;
        renderExplorerSchemaList(cachedExplorerSchemas);
    } catch (err) {
        container.innerHTML = `<div style="color:#f87171;">Error loading explorer: ${err.message}</div>`;
    }
}

function renderExplorerSchemaList(schemas) {
    const container = document.getElementById('duckdb-explorer-list');
    if (!container) return;

    // Group schemas by database
    const grouped = {};
    schemas.forEach(s => {
        const dbName = s.database || 'main';
        if (!grouped[dbName]) grouped[dbName] = [];
        grouped[dbName].push(s);
    });

    let html = '<div class="explorer-tree-root">';
    let dbIndex = 0;

    for (const [db, items] of Object.entries(grouped)) {
        dbIndex++;
        const isMain = db === 'main';
        const displayName = isMain ? 'practice (main / default)' : db;

        html += `
            <div class="db-tree-node" id="db-node-${dbIndex}">
                <div class="db-tree-header" onclick="toggleDbAccordion(${dbIndex})">
                    <div class="db-tree-title">
                        <span class="db-tree-chevron expanded" id="db-chevron-${dbIndex}">▶</span>
                        <span>🗄️ Database: <code style="color:var(--accent-primary); font-size:0.88rem;">${displayName}</code></span>
                        <span class="badge ${isMain ? 'badge-COMPLETED' : 'badge-NOT-STARTED'}" style="font-size:0.65rem; margin-left:0.35rem;">
                            ${isMain ? 'DEFAULT' : 'ATTACHED'}
                        </span>
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">
                        ${items.length} table(s)/view(s)
                    </div>
                </div>
                <div class="db-tree-content" id="db-content-${dbIndex}">
                    ${items.map((s, tblIdx) => {
                        const itemKey = `${dbIndex}_${tblIdx}`;
                        const querySnippet = isMain ? `SELECT * FROM "${s.name}" LIMIT 10;` : `SELECT * FROM "${s.database}"."${s.name}" LIMIT 10;`;
                        const colCount = (s.columns && s.columns.length) ? s.columns.length : 0;
                        const rowCountStr = s.row_count !== null ? `(${s.row_count.toLocaleString()} rows)` : '';

                        return `
                            <div class="table-tree-item" id="table-tree-item-${itemKey}">
                                <div class="table-tree-header">
                                    <div class="table-tree-info" onclick="toggleTableColumns('${itemKey}')">
                                        <button type="button" class="btn-tree-expander" id="btn-tree-expander-${itemKey}" title="Expand/Collapse columns with sizes" onclick="event.stopPropagation(); toggleTableColumns('${itemKey}');">
                                            +
                                        </button>
                                        <span style="font-size:0.9rem;">${s.type === 'VIEW' ? '👁️' : '📄'}</span>
                                        <span style="font-weight:700; font-family:var(--font-mono); color:var(--text-primary); font-size:0.85rem;">${s.name}</span>
                                        <span class="badge ${s.type === 'VIEW' ? 'badge-IN-PROGRESS' : 'badge-NOT-STARTED'}" style="font-size:0.65rem;">${s.type}</span>
                                        ${rowCountStr ? `<span style="font-size:0.75rem; color:var(--text-muted);">${rowCountStr}</span>` : ''}
                                        <span style="font-size:0.72rem; color:var(--text-secondary);">• ${colCount} col(s)</span>
                                    </div>
                                    <div class="table-tree-actions">
                                        <button class="btn btn-secondary btn-sm" onclick="insertCustomQuery('${escapeJs(querySnippet)}')">
                                            Insert Query
                                        </button>
                                    </div>
                                </div>
                                <div class="table-columns-panel" id="table-columns-${itemKey}" style="display:none;">
                                    <table class="columns-data-table">
                                        <thead>
                                            <tr>
                                                <th>Column Name</th>
                                                <th>Type</th>
                                                <th>Size / Length</th>
                                                <th>Nullable</th>
                                                <th style="text-align:right;">Insert</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${(s.columns || []).map(col => `
                                                <tr>
                                                    <td>
                                                        <span class="col-name-link" onclick="insertColumnName('${escapeJs(col.name)}')" title="Click to insert column into code editor">
                                                            ${escapeHtml(col.name)}
                                                        </span>
                                                    </td>
                                                    <td><code style="color:var(--accent-primary); font-size:0.75rem;">${escapeHtml(col.type)}</code></td>
                                                    <td><span class="col-size-badge">${escapeHtml(col.size || 'dynamic')}</span></td>
                                                    <td><span style="font-size:0.72rem; color:${col.nullable === 'NO' ? '#f87171' : 'var(--text-muted)'};">${escapeHtml(col.nullable || 'YES')}</span></td>
                                                    <td style="text-align:right;">
                                                        <button class="btn btn-secondary btn-sm" style="padding:0.1rem 0.4rem; font-size:0.7rem;" onclick="insertColumnName('${escapeJs(col.name)}')">+ Add</button>
                                                    </td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }
    html += '</div>';

    container.innerHTML = html;
}

function toggleDbAccordion(dbIndex) {
    const content = document.getElementById(`db-content-${dbIndex}`);
    const chevron = document.getElementById(`db-chevron-${dbIndex}`);
    if (!content) return;

    if (content.style.display === 'none') {
        content.style.display = 'flex';
        if (chevron) chevron.classList.add('expanded');
    } else {
        content.style.display = 'none';
        if (chevron) chevron.classList.remove('expanded');
    }
}

function toggleTableColumns(itemKey) {
    const panel = document.getElementById(`table-columns-${itemKey}`);
    const btn = document.getElementById(`btn-tree-expander-${itemKey}`);
    if (!panel) return;

    if (panel.style.display === 'none' || panel.style.display === '') {
        panel.style.display = 'block';
        if (btn) btn.textContent = '−';
    } else {
        panel.style.display = 'none';
        if (btn) btn.textContent = '+';
    }
}

function insertColumnName(colName) {
    if (monacoEditor) {
        const selection = monacoEditor.getSelection();
        const id = { major: 1, minor: 1 };
        const text = colName;
        const op = { identifier: id, range: selection, text: text, forceMoveMarkers: true };
        monacoEditor.executeEdits("explorer-insert", [op]);
        monacoEditor.focus();
        isDirty = true;
        scheduleAutosave();
        showToast(`Inserted column '${colName}' into editor`, 'info');
    }
}

function escapeJs(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function insertCustomQuery(snippet) {
    if (monacoEditor) {
        const currentCode = monacoEditor.getValue();
        monacoEditor.setValue(currentCode + "\n" + snippet + "\n");
        document.getElementById('duckdb-explorer-modal').style.display = 'none';
        isDirty = true;
        scheduleAutosave();
        showToast('Query snippet inserted into editor!', 'info');
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
    sessionData.practices.forEach(p => {
        practicesMap[p.id] = p;
    });

    ['meta-title', 'meta-difficulty', 'meta-topic', 'meta-tags', 'meta-question', 'meta-notes'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', () => {
                isDirty = true;
                scheduleAutosave();
            });
        }
    });

    ['dsa-constraints', 'dsa-time-complexity', 'dsa-space-complexity', 'dsa-test-cases', 'databricks-subtype'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('input', () => {
                isDirty = true;
                scheduleAutosave();
            });
        }
    });

    document.getElementById('btn-run')?.addEventListener('click', runCurrentCode);
    document.getElementById('btn-save')?.addEventListener('click', () => saveCurrentPractice(false));
    document.getElementById('btn-save-complete')?.addEventListener('click', () => saveCurrentPractice(true));
    document.getElementById('btn-clear-output')?.addEventListener('click', () => renderOutput('', '', 0));
    document.getElementById('btn-exec-history')?.addEventListener('click', openExecutionHistory);
    document.getElementById('btn-toggle-sql-explorer')?.addEventListener('click', toggleDuckDBExplorer);

    document.getElementById('btn-reset')?.addEventListener('click', async () => {
        const ok = await showAppConfirm({
            title: 'Reset Code Workspace',
            message: 'Are you sure you want to reset the current editor code? This will not delete your past execution history snapshots.',
            confirmText: 'Reset Workspace',
            isDanger: true,
            icon: '↺'
        });
        if (ok) {
            if (monacoEditor) {
                monacoEditor.setValue('-- Reset workspace\n');
                isDirty = true;
                scheduleAutosave();
                showToast('Workspace reset', 'info');
            }
        }
    });

    // Initialize Vertical Resizer
    initResizer();

    // Load Monaco
    await initMonaco();

    // Select initial tab
    await switchTech(initialTech || 'SQL');
}

// Maximize Editor / Focus Mode Controller
function toggleMaximizeEditor() {
    const workspacePage = document.querySelector('.workspace-page');
    const maxBtn = document.getElementById('btn-maximize-editor');
    if (!workspacePage) return;

    const isMax = workspacePage.classList.toggle('editor-maximized');
    if (maxBtn) {
        if (isMax) {
            maxBtn.classList.add('active');
            maxBtn.innerHTML = '<span id="maximize-icon">🗗</span> <span id="maximize-text">Restore</span>';
            maxBtn.title = 'Restore standard layout with console and metadata (Esc)';
            showToast('Editor Maximized (Focus Mode) — Press Esc or Restore to exit', 'info', 2000);
        } else {
            maxBtn.classList.remove('active');
            maxBtn.innerHTML = '<span id="maximize-icon">🗖</span> <span id="maximize-text">Maximize</span>';
            maxBtn.title = 'Maximize Editor / Focus Mode';
            showToast('Standard View Restored', 'info', 1500);
        }
    }

    setTimeout(() => {
        if (monacoEditor) {
            monacoEditor.layout();
        }
    }, 150);
}

// Escape key closes maximized editor mode or modal dialogs
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const createDbModal = document.getElementById('create-db-modal');
        if (createDbModal && createDbModal.style.display === 'flex') {
            closeCreateDatabaseModal();
            return;
        }

        const workspacePage = document.querySelector('.workspace-page');
        if (workspacePage && workspacePage.classList.contains('editor-maximized')) {
            toggleMaximizeEditor();
            return;
        }
    }
});
