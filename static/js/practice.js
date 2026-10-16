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

        // Ctrl+Enter: Run Statement / Selection
        monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
            runCurrentCode(false);
        });

        // Ctrl+Shift+Enter: Run Entire File
        monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter, () => {
            runCurrentCode(true);
        });

        // Ctrl+S: Save
        monacoEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
            saveCurrentPractice(false);
        });

        // Monaco Context Menu Actions
        monacoEditor.addAction({
            id: 'run-statement-or-selection',
            label: 'Run Statement at Cursor / Selected Code (Ctrl+Enter)',
            keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
            contextMenuGroupId: 'navigation',
            contextMenuOrder: 1,
            run: () => runCurrentCode(false)
        });

        monacoEditor.addAction({
            id: 'run-entire-file',
            label: 'Run All Statements / Entire File (Ctrl+Shift+Enter)',
            keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter],
            contextMenuGroupId: 'navigation',
            contextMenuOrder: 2,
            run: () => runCurrentCode(true)
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
let inlineRenamingFile = null;
let openTabFileNames = ["main.py"];
let isEditorExplorerOpen = false;
let cachedFilesTree = null;

function ensureOpenTabsConsistent() {
    const existingFiles = Object.keys(currentProjectFiles);
    if (existingFiles.length === 0) {
        const defaultName = activeTechnology === 'SQL' ? 'query.sql' : (activeTechnology === 'System Design' ? 'architecture.md' : 'main.py');
        currentProjectFiles[defaultName] = '';
        openTabFileNames = [defaultName];
        activeFileName = defaultName;
        return;
    }

    // Filter open tabs to only valid existing files
    openTabFileNames = openTabFileNames.filter(fname => fname in currentProjectFiles);

    if (openTabFileNames.length > 0) {
        if (!activeFileName || !openTabFileNames.includes(activeFileName)) {
            activeFileName = openTabFileNames[openTabFileNames.length - 1];
        }
    } else {
        activeFileName = null;
    }
}

function renderMultiFileTabs() {
    const bar = document.getElementById('file-tabs-list') || document.getElementById('multi-file-tabs-bar');
    if (!bar) return;

    ensureOpenTabsConsistent();
    bar.innerHTML = '';

    // Toggle Editor vs Empty State
    const editorContainer = document.getElementById('monaco-editor-container');
    const emptyState = document.getElementById('editor-empty-state');
    if (openTabFileNames.length === 0) {
        if (editorContainer) editorContainer.style.display = 'none';
        if (emptyState) emptyState.style.display = 'flex';
    } else {
        if (editorContainer) editorContainer.style.display = 'block';
        if (emptyState) emptyState.style.display = 'none';
        if (monacoEditor) {
            setTimeout(() => monacoEditor.layout(), 30);
        }
    }

    const getFileIcon = (fname) => {
        if (fname.endsWith('.py')) return '🐍';
        if (fname.endsWith('.sql')) return '🗄️';
        if (fname.endsWith('.md')) return '📝';
        if (fname.endsWith('.json')) return '⚙️';
        return '📄';
    };

    // 1. "📁 Files" Toggle Button (Opens/Closes Left Folder Explorer Drawer)
    const explorerBtn = document.createElement('button');
    explorerBtn.type = 'button';
    explorerBtn.className = `btn-file-explorer-toggle ${isEditorExplorerOpen ? 'active' : ''}`;
    explorerBtn.innerHTML = '<span>📁 Files</span>';
    explorerBtn.title = 'Toggle Folder-wise Files Explorer (View past sessions, saved files & templates)';
    explorerBtn.onclick = toggleEditorExplorer;
    bar.appendChild(explorerBtn);

    // 2. Open Tab Pills
    openTabFileNames.forEach(fname => {
        const tab = document.createElement('div');
        tab.className = `file-tab ${fname === activeFileName ? 'active' : ''}`;
        tab.title = `${fname} (Click name to rename inline | Right-click for options)`;
        tab.setAttribute('data-filename', fname);

        const iconSpan = document.createElement('span');
        iconSpan.className = 'file-tab-icon';
        iconSpan.textContent = getFileIcon(fname);
        tab.appendChild(iconSpan);

        const titleSpan = document.createElement('span');
        titleSpan.className = 'file-tab-name';
        titleSpan.textContent = fname;

        // Clicking tab switches active file
        tab.onclick = (e) => {
            if (e.target.tagName === 'INPUT') return;
            if (activeFileName !== fname) {
                switchActiveFile(fname);
            }
        };

        // Inline rename
        titleSpan.onclick = (e) => {
            e.stopPropagation();
            if (activeFileName !== fname) {
                switchActiveFile(fname);
            }
            startInlineTabRename(fname, titleSpan, tab);
        };

        tab.appendChild(titleSpan);

        // Remove Tab Button "×" (Removes tab from workspace, does NOT delete file)
        const closeBtn = document.createElement('span');
        closeBtn.className = 'file-tab-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.title = `Close tab (File remains saved in workspace)`;
        closeBtn.onclick = (e) => {
            e.stopPropagation();
            removeTabFromWorkspace(fname);
        };
        tab.appendChild(closeBtn);

        // Right-click context menu: Close Tab or Permanently Delete File
        tab.oncontextmenu = (e) => {
            e.preventDefault();
            showTabContextMenu(e, fname);
        };

        bar.appendChild(tab);

        if (inlineRenamingFile === fname) {
            setTimeout(() => {
                startInlineTabRename(fname, titleSpan, tab);
            }, 10);
        }
    });

    // 3. "+ New File" Button
    const newBtn = document.createElement('button');
    newBtn.type = 'button';
    newBtn.className = 'btn-new-file';
    newBtn.innerHTML = '<span>+ New File</span>';
    newBtn.title = 'Create new file directly in workspace';
    newBtn.onclick = createNewFileTabDirect;
    bar.appendChild(newBtn);
}

// Remove Tab from editor view (File remains saved in currentProjectFiles)
function removeTabFromWorkspace(filename) {
    if (monacoEditor && activeFileName === filename) {
        currentProjectFiles[filename] = monacoEditor.getValue();
    }

    openTabFileNames = openTabFileNames.filter(f => f !== filename);

    if (activeFileName === filename) {
        if (openTabFileNames.length > 0) {
            activeFileName = openTabFileNames[openTabFileNames.length - 1];
            const code = currentProjectFiles[activeFileName] || '';
            const lang = getLanguageForFile(activeFileName, activeTechnology);
            createOrUpdateEditor(code, lang);
        } else {
            activeFileName = null;
        }
    }

    renderMultiFileTabs();
    refreshFilesTree();
    isDirty = true;
    scheduleAutosave();
    showToast(`Closed tab '${filename}'. File remains saved in 📁 Files.`, 'info', 2500);
}

// Permanently Delete File with in-app confirmation popup
async function deleteProjectFilePermanently(filename, targetPracticeId = null) {
    const practiceId = targetPracticeId || activePracticeId;
    const isConfirmed = await showAppConfirm({
        title: 'Delete File Permanently',
        message: `Are you sure you want to permanently delete '${filename}'? This action cannot be undone.`,
        confirmText: 'Delete Permanently',
        isDanger: true,
        icon: '🗑️'
    });

    if (!isConfirmed) return;

    try {
        if (practiceId) {
            const resp = await fetch('/api/practice/files/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ practice_id: practiceId, filename: filename })
            });
            const result = await resp.json();
            if (!result.success) {
                showToast(`Failed to delete file: ${result.error || 'Unknown error'}`, 'error');
                return;
            }
        }

        delete currentProjectFiles[filename];
        openTabFileNames = openTabFileNames.filter(f => f !== filename);
        ensureOpenTabsConsistent();

        if (activeFileName === filename) {
            if (openTabFileNames.length > 0) {
                activeFileName = openTabFileNames[openTabFileNames.length - 1];
            } else if (Object.keys(currentProjectFiles).length > 0) {
                activeFileName = Object.keys(currentProjectFiles)[0];
                openTabFileNames = [activeFileName];
            } else {
                activeFileName = null;
            }
        }

        if (activeFileName && currentProjectFiles[activeFileName]) {
            const code = currentProjectFiles[activeFileName] || '';
            const lang = getLanguageForFile(activeFileName, activeTechnology);
            createOrUpdateEditor(code, lang);
        }

        renderMultiFileTabs();
        refreshFilesTree();
        showToast(`Permanently deleted '${filename}'.`, 'info', 2200);
    } catch (err) {
        console.error('Delete file error:', err);
        showToast(`Error deleting file: ${err.message}`, 'error');
    }
}

// Load / Open a saved file into an editor tab
function openFileInTab(filename) {
    if (!(filename in currentProjectFiles)) {
        showToast(`File '${filename}' not found.`, 'error');
        return;
    }

    if (!openTabFileNames.includes(filename)) {
        openTabFileNames.push(filename);
    }

    switchActiveFile(filename);
    closeOpenFilesDropdown();
    showToast(`Loaded '${filename}' into editor tab`, 'info', 1600);
}

// Dropdown to load saved files or import external files
function toggleOpenFilesDropdown(container) {
    const existing = container.querySelector('.open-files-menu');
    if (existing) {
        existing.remove();
        return;
    }

    // Close any other open dropdowns
    document.querySelectorAll('.open-files-menu').forEach(el => el.remove());

    const menu = document.createElement('div');
    menu.className = 'open-files-menu';

    // Header
    const hdr = document.createElement('div');
    hdr.className = 'open-files-menu-header';
    hdr.textContent = 'Saved Files in Current Practice';
    menu.appendChild(hdr);

    const allFiles = Object.keys(currentProjectFiles);
    if (allFiles.length === 0) {
        const empty = document.createElement('div');
        empty.style.padding = '0.4rem 0.6rem';
        empty.style.color = 'var(--text-muted)';
        empty.style.fontSize = '0.78rem';
        empty.textContent = 'No files created yet.';
        menu.appendChild(empty);
    } else {
        allFiles.forEach(fname => {
            const item = document.createElement('button');
            item.type = 'button';
            const isOpen = openTabFileNames.includes(fname);
            item.className = `open-files-item ${isOpen ? 'is-open' : ''}`;
            item.innerHTML = `
                <span>📄 ${fname}</span>
                <span class="open-files-item-badge">${isOpen ? 'Open Tab' : '+ Open'}</span>
            `;
            item.onclick = (e) => {
                e.stopPropagation();
                openFileInTab(fname);
                menu.remove();
            };
            menu.appendChild(item);
        });
    }

    // Library & Import Actions
    const actHdr = document.createElement('div');
    actHdr.className = 'open-files-menu-header';
    actHdr.style.marginTop = '0.4rem';
    actHdr.textContent = 'Folders & Computer';
    menu.appendChild(actHdr);

    const folderLibBtn = document.createElement('button');
    folderLibBtn.type = 'button';
    folderLibBtn.className = 'open-files-item';
    folderLibBtn.innerHTML = '<span>📁 Browse Folder Library</span><span class="open-files-item-badge">Explorer</span>';
    folderLibBtn.onclick = (e) => {
        e.stopPropagation();
        menu.remove();
        if (!isEditorExplorerOpen) toggleEditorExplorer();
    };
    menu.appendChild(folderLibBtn);

    const importDiskBtn = document.createElement('button');
    importDiskBtn.type = 'button';
    importDiskBtn.className = 'open-files-item';
    importDiskBtn.innerHTML = '<span>📥 Import File from Computer...</span><span class="open-files-item-badge">Browse</span>';
    importDiskBtn.onclick = (e) => {
        e.stopPropagation();
        menu.remove();
        document.getElementById('local-file-importer')?.click();
    };
    menu.appendChild(importDiskBtn);

    container.appendChild(menu);

    const closer = (e) => {
        if (!container.contains(e.target)) {
            menu.remove();
            document.removeEventListener('click', closer);
        }
    };
    setTimeout(() => document.addEventListener('click', closer), 20);
}

function closeOpenFilesDropdown() {
    document.querySelectorAll('.open-files-menu').forEach(el => el.remove());
}

// Right-click context menu on tabs
function showTabContextMenu(e, filename) {
    document.querySelectorAll('.tab-context-menu').forEach(el => el.remove());

    const menu = document.createElement('div');
    menu.className = 'open-files-menu tab-context-menu';
    menu.style.position = 'fixed';
    menu.style.top = `${e.clientY + 4}px`;
    menu.style.left = `${e.clientX}px`;
    menu.style.minWidth = '180px';
    menu.style.zIndex = '9999';

    const closeItem = document.createElement('button');
    closeItem.type = 'button';
    closeItem.className = 'open-files-item';
    closeItem.innerHTML = '<span>✕ Close Tab (Keep Saved)</span>';
    closeItem.onclick = () => {
        menu.remove();
        removeTabFromWorkspace(filename);
    };
    menu.appendChild(closeItem);

    const delItem = document.createElement('button');
    delItem.type = 'button';
    delItem.className = 'open-files-item';
    delItem.style.color = '#ef4444';
    delItem.innerHTML = '<span>🗑️ Delete File Permanently...</span>';
    delItem.onclick = () => {
        menu.remove();
        deleteProjectFilePermanently(filename);
    };
    menu.appendChild(delItem);

    document.body.appendChild(menu);

    const removeMenu = (evt) => {
        if (!menu.contains(evt.target)) {
            menu.remove();
            document.removeEventListener('click', removeMenu);
        }
    };
    setTimeout(() => document.addEventListener('click', removeMenu), 20);
}

// Handle manual file import from disk
function handleLocalFileImport(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        let fname = file.name;

        // Avoid overwrite if duplicate
        let counter = 1;
        while (fname in currentProjectFiles) {
            const dot = file.name.lastIndexOf('.');
            const base = dot > 0 ? file.name.substring(0, dot) : file.name;
            const ext = dot > 0 ? file.name.substring(dot) : '';
            fname = `${base}_${counter}${ext}`;
            counter++;
        }

        currentProjectFiles[fname] = content;
        if (!openTabFileNames.includes(fname)) {
            openTabFileNames.push(fname);
        }
        switchActiveFile(fname);
        isDirty = true;
        scheduleAutosave();
        showToast(`Imported '${fname}' from computer!`, 'success');
        event.target.value = '';
    };
    reader.readAsText(file);
}

// Toggle folder-wise explorer inside the editor
function toggleEditorExplorer() {
    const drawer = document.getElementById('editor-explorer-drawer');
    const headerBtn = document.getElementById('btn-toggle-file-explorer');
    if (!drawer) return;

    isEditorExplorerOpen = drawer.style.display === 'none' || !drawer.style.display;
    if (isEditorExplorerOpen) {
        drawer.style.display = 'flex';
        headerBtn?.classList.add('active');
        refreshFilesTree();
    } else {
        drawer.style.display = 'none';
        headerBtn?.classList.remove('active');
    }

    renderMultiFileTabs();

    setTimeout(() => {
        if (monacoEditor) {
            monacoEditor.layout();
        }
    }, 60);
}

// Folder-wise Files Explorer Loader & Renderer
async function refreshFilesTree() {
    const container = document.getElementById('explorer-tree-content');
    if (!container || !isEditorExplorerOpen) return;

    try {
        const res = await fetch(`/api/practice/files/tree?tech=${encodeURIComponent(activeTechnology || 'SQL')}&practice_id=${activePracticeId || ''}`);
        const data = await res.json();
        cachedFilesTree = data;
        renderFilesTreeDOM(data);
    } catch (e) {
        if (container) {
            container.innerHTML = `<div style="padding:1rem; color:#ef4444; font-size:0.8rem;">Failed to load folder library: ${e.message}</div>`;
        }
    }
}

function renderFilesTreeDOM(treeData) {
    const container = document.getElementById('explorer-tree-content');
    if (!container) return;

    container.innerHTML = '';

    // Folder 1: Current Practice Files
    const currentFolder = document.createElement('div');
    currentFolder.className = 'folder-tree-node';
    currentFolder.innerHTML = `
        <div class="folder-tree-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'flex' : 'none'; this.querySelector('.folder-tree-chevron').classList.toggle('expanded');">
            <div class="folder-tree-title">
                <span class="folder-tree-chevron expanded">▸</span>
                <span>📁 Current Practice Files (${Object.keys(currentProjectFiles).length})</span>
            </div>
            <button type="button" class="drawer-mini-btn" onclick="event.stopPropagation(); createNewFileTabDirect();" title="Add File">+ File</button>
        </div>
        <div class="folder-tree-items">
            ${Object.keys(currentProjectFiles).map(fname => {
                const isOpen = openTabFileNames.includes(fname);
                const isActive = activeFileName === fname;
                return `
                    <div class="tree-file-row ${isActive ? 'is-active-tab' : ''}" onclick="openFileInTab('${fname}')">
                        <div class="tree-file-left">
                            <span>📄</span>
                            <span>${fname}</span>
                        </div>
                        <div class="tree-file-actions">
                            <span style="font-size:0.7rem; color:var(--text-muted);">${isOpen ? 'Open' : 'Saved'}</span>
                            <button type="button" class="tree-file-action-icon" title="Permanently delete file" onclick="event.stopPropagation(); deleteProjectFilePermanently('${fname}');">🗑️</button>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
    container.appendChild(currentFolder);

    // Folder 2: Past Sessions & History (Folder per date)
    if (treeData && treeData.past_sessions && treeData.past_sessions.length > 0) {
        const pastParent = document.createElement('div');
        pastParent.className = 'folder-tree-node';
        pastParent.innerHTML = `
            <div class="folder-tree-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'flex' : 'none'; this.querySelector('.folder-tree-chevron').classList.toggle('expanded');">
                <div class="folder-tree-title">
                    <span class="folder-tree-chevron">▸</span>
                    <span>📁 Past ${activeTechnology} Sessions (${treeData.past_sessions.length})</span>
                </div>
            </div>
            <div class="folder-tree-items" style="display:none;">
                ${treeData.past_sessions.map(sess => `
                    <div style="border-bottom:1px solid var(--border-subtle); padding-bottom:0.3rem; margin-bottom:0.3rem;">
                        <div style="font-size:0.76rem; font-weight:700; color:var(--text-primary); margin-bottom:0.2rem; display:flex; justify-content:space-between;">
                            <span>📅 ${sess.date}</span>
                            <span style="font-weight:normal; color:var(--text-muted);">${sess.title}</span>
                        </div>
                        ${sess.files.map(f => `
                            <div class="tree-file-row" onclick="importFileFromPastSession(${sess.practice_id}, '${f.name}')" title="Click to load this file into your workspace">
                                <div class="tree-file-left">
                                    <span>🗄️</span>
                                    <span>${f.name}</span>
                                </div>
                                <div class="tree-file-actions">
                                    <button type="button" class="tree-file-action-icon open-icon" title="Import/Load to current workspace">+ Load</button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `).join('')}
            </div>
        `;
        container.appendChild(pastParent);
    }

    // Folder 3: Starter Templates & Snippets
    if (treeData && treeData.starter_templates && treeData.starter_templates.length > 0) {
        const tplParent = document.createElement('div');
        tplParent.className = 'folder-tree-node';
        tplParent.innerHTML = `
            <div class="folder-tree-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'flex' : 'none'; this.querySelector('.folder-tree-chevron').classList.toggle('expanded');">
                <div class="folder-tree-title">
                    <span class="folder-tree-chevron">▸</span>
                    <span>📁 Starter Templates & Snippets (${treeData.starter_templates.length})</span>
                </div>
            </div>
            <div class="folder-tree-items" style="display:none;">
                ${treeData.starter_templates.map(tpl => `
                    <div class="tree-file-row" onclick="loadStarterTemplate('${tpl.name}')" title="${tpl.description} - Click to load">
                        <div class="tree-file-left">
                            <span>⭐</span>
                            <div>
                                <div style="font-weight:600;">${tpl.name}</div>
                                <div style="font-size:0.7rem; color:var(--text-muted);">${tpl.description}</div>
                            </div>
                        </div>
                        <div class="tree-file-actions">
                            <button type="button" class="tree-file-action-icon open-icon" title="Load into workspace">+ Load</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        container.appendChild(tplParent);
    }
}

// Import a file from past session into current workspace
async function importFileFromPastSession(sourcePracticeId, fileName) {
    try {
        const res = await fetch('/api/practice/files/get_content', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_practice_id: sourcePracticeId,
                file_name: fileName,
                tech: activeTechnology
            })
        });
        const data = await res.json();
        if (data.success) {
            let targetName = fileName;
            let counter = 1;
            while (targetName in currentProjectFiles) {
                const dot = fileName.lastIndexOf('.');
                const base = dot > 0 ? fileName.substring(0, dot) : fileName;
                const ext = dot > 0 ? fileName.substring(dot) : '';
                targetName = `${base}_copy${counter}${ext}`;
                counter++;
            }
            currentProjectFiles[targetName] = data.content;
            if (!openTabFileNames.includes(targetName)) {
                openTabFileNames.push(targetName);
            }
            switchActiveFile(targetName);
            refreshFilesTree();
            isDirty = true;
            scheduleAutosave();
            showToast(`Loaded '${targetName}' from past session!`, 'success');
        } else {
            showToast(`Could not load file: ${data.error}`, 'error');
        }
    } catch (e) {
        showToast(`Error importing file: ${e.message}`, 'error');
    }
}

// Load a starter template
async function loadStarterTemplate(templateName) {
    try {
        const res = await fetch('/api/practice/files/get_content', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                template_name: templateName,
                tech: activeTechnology
            })
        });
        const data = await res.json();
        if (data.success) {
            let targetName = templateName;
            let counter = 1;
            while (targetName in currentProjectFiles) {
                const dot = templateName.lastIndexOf('.');
                const base = dot > 0 ? templateName.substring(0, dot) : templateName;
                const ext = dot > 0 ? templateName.substring(dot) : '';
                targetName = `${base}_${counter}${ext}`;
                counter++;
            }
            currentProjectFiles[targetName] = data.content;
            if (!openTabFileNames.includes(targetName)) {
                openTabFileNames.push(targetName);
            }
            switchActiveFile(targetName);
            refreshFilesTree();
            isDirty = true;
            scheduleAutosave();
            showToast(`Loaded template '${targetName}'!`, 'success');
        } else {
            showToast(`Could not load template: ${data.error}`, 'error');
        }
    } catch (e) {
        showToast(`Error loading template: ${e.message}`, 'error');
    }
}

function filterExplorerTree(query) {
    const q = (query || '').toLowerCase().trim();
    document.querySelectorAll('.tree-file-row').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = (!q || text.includes(q)) ? 'flex' : 'none';
    });
}

function switchActiveFile(targetFileName) {
    if (activeFileName === targetFileName) return;

    // Save current content in buffer
    if (monacoEditor && activeFileName) {
        currentProjectFiles[activeFileName] = monacoEditor.getValue();
    }

    activeFileName = targetFileName;
    if (!openTabFileNames.includes(targetFileName)) {
        openTabFileNames.push(targetFileName);
    }

    const code = currentProjectFiles[activeFileName] || '';
    const lang = getLanguageForFile(activeFileName, activeTechnology);

    if (monacoEditor) {
        createOrUpdateEditor(code, lang);
    }

    renderMultiFileTabs();
    refreshFilesTree();
}

// Instant file creation: generates file directly with intelligent defaults, no modal popup
function createNewFileTabDirect() {
    let defaultExt = '.py';
    let basePrefix = 'module';
    if (activeTechnology === 'SQL') {
        defaultExt = '.sql';
        basePrefix = 'query';
    } else if (activeTechnology === 'System Design') {
        defaultExt = '.md';
        basePrefix = 'notes';
    } else if (activeTechnology === 'PySpark') {
        defaultExt = '.py';
        basePrefix = 'spark';
    } else if (activeTechnology === 'Databricks') {
        defaultExt = '.py';
        basePrefix = 'notebook';
    } else if (activeTechnology === 'DSA') {
        defaultExt = '.py';
        basePrefix = 'solution';
    }

    let counter = 2;
    let newName = `${basePrefix}_${counter}${defaultExt}`;
    while (newName in currentProjectFiles) {
        counter++;
        newName = `${basePrefix}_${counter}${defaultExt}`;
    }

    let defaultContent = `-- ${newName}\n`;
    if (newName.endsWith('.py')) {
        defaultContent = `# ${newName}\n\ndef helper():\n    return "Helper logic"\n`;
    } else if (newName.endsWith('.sql')) {
        defaultContent = `-- ${newName}\nSELECT 1 AS status;\n`;
    } else if (newName.endsWith('.md')) {
        defaultContent = `# ${newName}\n\nDocument architecture notes here.\n`;
    } else if (newName.endsWith('.json')) {
        defaultContent = `{\n  "filename": "${newName}"\n}\n`;
    }

    // Save current active buffer first
    if (monacoEditor && activeFileName) {
        currentProjectFiles[activeFileName] = monacoEditor.getValue();
    }

    currentProjectFiles[newName] = defaultContent;
    if (!openTabFileNames.includes(newName)) {
        openTabFileNames.push(newName);
    }
    inlineRenamingFile = newName;
    switchActiveFile(newName);
    isDirty = true;
    scheduleAutosave();
    showToast(`Created ${newName} — click anywhere or press Enter to rename`, 'info', 2200);
}

// Inline tab renaming: transforms tab label into input, saves on blur (click anywhere) or Enter (no icons needed)
function startInlineTabRename(oldFileName, titleSpan, tab) {
    if (tab.querySelector('.file-tab-inline-input')) return;

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'file-tab-inline-input';
    input.value = oldFileName;
    input.spellcheck = false;

    titleSpan.style.display = 'none';
    tab.insertBefore(input, titleSpan);

    input.focus();
    // Select base filename before the extension for convenient typing
    const dotIdx = oldFileName.lastIndexOf('.');
    if (dotIdx > 0) {
        input.setSelectionRange(0, dotIdx);
    } else {
        input.select();
    }

    let isCommitted = false;

    const commitChange = () => {
        if (isCommitted) return;
        isCommitted = true;
        inlineRenamingFile = null;

        let rawVal = input.value.trim();
        if (!rawVal || rawVal === oldFileName) {
            input.remove();
            titleSpan.style.display = '';
            return;
        }

        // Auto-append original extension if omitted
        if (!rawVal.includes('.')) {
            const originalExt = oldFileName.includes('.') ? oldFileName.substring(oldFileName.lastIndexOf('.')) : '';
            rawVal += originalExt;
        }

        const newFileName = rawVal;
        if (newFileName === oldFileName) {
            input.remove();
            titleSpan.style.display = '';
            return;
        }

        if (newFileName in currentProjectFiles) {
            showToast(`File '${newFileName}' already exists!`, 'error', 2500);
            input.remove();
            titleSpan.style.display = '';
            return;
        }

        // Rename key in currentProjectFiles and openTabFileNames
        const content = currentProjectFiles[oldFileName] || (monacoEditor ? monacoEditor.getValue() : '');
        currentProjectFiles[newFileName] = content;
        delete currentProjectFiles[oldFileName];

        openTabFileNames = openTabFileNames.map(f => f === oldFileName ? newFileName : f);

        if (activeFileName === oldFileName) {
            activeFileName = newFileName;
        }

        // Update editor language if extension changed
        if (monacoEditor) {
            const newLang = getLanguageForFile(newFileName, activeTechnology);
            createOrUpdateEditor(monacoEditor.getValue(), newLang);
        }

        isDirty = true;
        scheduleAutosave();
        showToast(`Renamed to '${newFileName}'`, 'success', 1800);
        renderMultiFileTabs();
        refreshFilesTree();
    };

    // Clicking anywhere on the screen fires blur and automatically saves
    input.onblur = commitChange;

    input.onkeydown = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            input.blur();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            isCommitted = true;
            inlineRenamingFile = null;
            input.remove();
            titleSpan.style.display = '';
        }
    };
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
        if (Array.isArray(extra.open_tabs) && extra.open_tabs.length > 0) {
            openTabFileNames = extra.open_tabs.filter(f => f in currentProjectFiles);
        } else {
            openTabFileNames = Object.keys(extra.files);
        }
        if (openTabFileNames.length === 0) {
            openTabFileNames = [Object.keys(extra.files)[0]];
        }
        activeFileName = (extra.active_file && (extra.active_file in currentProjectFiles))
            ? extra.active_file
            : openTabFileNames[0];
    } else {
        currentProjectFiles = { [defaultFile]: p.code || "" };
        openTabFileNames = [defaultFile];
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
    if (monacoEditor && activeFileName) {
        currentProjectFiles[activeFileName] = monacoEditor.getValue();
    }
    extra.files = currentProjectFiles;
    extra.open_tabs = openTabFileNames;
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

    // Update active file buffer if active
    if (monacoEditor && activeFileName) {
        currentProjectFiles[activeFileName] = monacoEditor.getValue();
    }

    const code = (activeFileName && currentProjectFiles[activeFileName])
        ? currentProjectFiles[activeFileName]
        : (Object.values(currentProjectFiles)[0] || (monacoEditor ? monacoEditor.getValue() : ''));
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

// Flash statement or selection highlight in Monaco editor
let statementDecorations = [];
function flashExecutionRange(startLine, endLine) {
    if (!monacoEditor) return;
    try {
        const model = monacoEditor.getModel();
        if (!model) return;
        const maxLine = model.getLineCount();
        const sLine = Math.max(1, Math.min(startLine, maxLine));
        const eLine = Math.max(sLine, Math.min(endLine, maxLine));
        const maxCol = model.getLineMaxColumn(eLine);

        statementDecorations = monacoEditor.deltaDecorations(statementDecorations, [
            {
                range: new monaco.Range(sLine, 1, eLine, maxCol),
                options: {
                    isWholeLine: true,
                    className: 'executing-statement-highlight',
                    overviewRuler: {
                        color: 'rgba(59, 130, 246, 0.7)',
                        position: monaco.editor.OverviewRulerLane.Full
                    }
                }
            }
        ]);

        setTimeout(() => {
            if (monacoEditor) {
                statementDecorations = monacoEditor.deltaDecorations(statementDecorations, []);
            }
        }, 1200);
    } catch (e) {
        console.warn('flashExecutionRange decoration error:', e);
    }
}

// Parse SQL script into individual statements separated by semicolon (;)
function splitSqlStatements(sqlText) {
    if (!sqlText || !sqlText.trim()) return [];

    const statements = [];
    let currentStart = 0;
    let inSingleQuote = false;
    let inDoubleQuote = false;
    let inLineComment = false;
    let inBlockComment = false;
    const len = sqlText.length;

    // Precompute line break indices
    const lineStarts = [0];
    for (let i = 0; i < len; i++) {
        if (sqlText[i] === '\n') {
            lineStarts.push(i + 1);
        }
    }
    function getLineNumber(offset) {
        let low = 0, high = lineStarts.length - 1;
        while (low <= high) {
            const mid = Math.floor((low + high) / 2);
            if (lineStarts[mid] <= offset) {
                if (mid === lineStarts.length - 1 || lineStarts[mid + 1] > offset) {
                    return mid + 1;
                }
                low = mid + 1;
            } else {
                high = mid - 1;
            }
        }
        return 1;
    }

    function addStatement(rawStart, rawEnd) {
        const rawChunk = sqlText.slice(rawStart, rawEnd);
        const nonWsMatch = rawChunk.match(/\S/);
        if (!nonWsMatch) return;

        const actualStart = rawStart + nonWsMatch.index;
        const actualEnd = rawEnd;
        const trimmed = sqlText.slice(actualStart, actualEnd).trim();

        // Check if trimmed text has actual SQL code beyond comments
        const noComments = trimmed
            .replace(/--.*$/gm, '')
            .replace(/\/\*[\s\S]*?\*\//g, '')
            .trim();
        if (!noComments) return;

        const startLine = getLineNumber(actualStart);
        const endLine = getLineNumber(Math.max(actualStart, actualEnd - 1));

        statements.push({
            text: trimmed,
            cleanSql: trimmed.endsWith(';') ? trimmed.slice(0, -1).trim() : trimmed,
            startIndex: actualStart,
            endIndex: actualEnd,
            startLine: startLine,
            endLine: endLine
        });
    }

    for (let i = 0; i < len; i++) {
        const ch = sqlText[i];
        const next = i + 1 < len ? sqlText[i + 1] : '';

        if (inLineComment) {
            if (ch === '\n') inLineComment = false;
            continue;
        }
        if (inBlockComment) {
            if (ch === '*' && next === '/') {
                inBlockComment = false;
                i++;
            }
            continue;
        }
        if (inSingleQuote) {
            if (ch === "'") {
                if (next === "'") {
                    i++;
                } else {
                    inSingleQuote = false;
                }
            }
            continue;
        }
        if (inDoubleQuote) {
            if (ch === '"') {
                if (next === '"') {
                    i++;
                } else {
                    inDoubleQuote = false;
                }
            }
            continue;
        }

        if (ch === '-' && next === '-') {
            inLineComment = true;
            i++;
            continue;
        }
        if (ch === '/' && next === '*') {
            inBlockComment = true;
            i++;
            continue;
        }
        if (ch === "'") {
            inSingleQuote = true;
            continue;
        }
        if (ch === '"') {
            inDoubleQuote = true;
            continue;
        }

        if (ch === ';') {
            addStatement(currentStart, i + 1);
            currentStart = i + 1;
        }
    }

    if (currentStart < len) {
        addStatement(currentStart, len);
    }

    return statements;
}

// Find SQL statement at the given line number (1-indexed)
function getSqlStatementAtCursor(fullCode, cursorLine) {
    const statements = splitSqlStatements(fullCode);
    if (!statements || statements.length === 0) return null;

    // 1. Direct match: cursor line is inside statement span [startLine, endLine]
    for (const stmt of statements) {
        if (cursorLine >= stmt.startLine && cursorLine <= stmt.endLine) {
            return stmt;
        }
    }

    // 2. Cursor is before first statement
    if (cursorLine < statements[0].startLine) {
        return statements[0];
    }

    // 3. Cursor is between statements: choose the next one
    for (const stmt of statements) {
        if (stmt.startLine >= cursorLine) {
            return stmt;
        }
    }

    // 4. Fallback to the last statement
    return statements[statements.length - 1];
}

// Run Code (supports selection, statement under cursor, or full file)
async function runCurrentCode(runAll = false) {
    if (!activePracticeId) return;

    // Ensure console is visible when user runs code
    showConsolePane();

    // If no tab is currently open, load the first available file or warn
    if (!activeFileName || openTabFileNames.length === 0) {
        const availableFiles = Object.keys(currentProjectFiles);
        if (availableFiles.length > 0) {
            openFileInTab(availableFiles[0]);
        } else {
            showToast("No active file in editor. Click '+ New File' or open a file to run code.", 'warning', 2500);
            return;
        }
    }

    // Save active editor into currentProjectFiles buffer
    if (monacoEditor && activeFileName) {
        currentProjectFiles[activeFileName] = monacoEditor.getValue();
    }

    await saveCurrentPractice(false);

    updateStatusBadge('RUNNING');
    const runBtn = document.getElementById('btn-run');
    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML = '⏳ Running...';
    }

    const fullCode = (activeFileName && currentProjectFiles[activeFileName])
        ? currentProjectFiles[activeFileName]
        : (monacoEditor ? monacoEditor.getValue() : '');

    let codeToExecute = fullCode;
    let executionNote = '';

    // Check for user-selected text in Monaco editor
    if (monacoEditor) {
        const selection = monacoEditor.getSelection();
        if (selection && !selection.isEmpty()) {
            const selectedText = monacoEditor.getModel()?.getValueInRange(selection);
            if (selectedText && selectedText.trim().length > 0) {
                codeToExecute = selectedText.trim();
                flashExecutionRange(selection.startLineNumber, selection.endLineNumber);
                executionNote = `(lines ${selection.startLineNumber}-${selection.endLineNumber})`;
            }
        }
    }

    // If no selection was made and runAll is not requested, check if it's SQL to run statement at cursor
    const isSql = (activeTechnology === 'SQL') ||
                  (activeTechnology === 'Databricks' && gatherExtraMetadata().subtype === 'SQL') ||
                  (activeFileName && activeFileName.endsWith('.sql'));

    if (codeToExecute === fullCode && !runAll && isSql && monacoEditor) {
        const position = monacoEditor.getPosition();
        const cursorLine = position ? position.lineNumber : 1;
        const stmt = getSqlStatementAtCursor(fullCode, cursorLine);
        if (stmt && stmt.text) {
            codeToExecute = stmt.text;
            flashExecutionRange(stmt.startLine, stmt.endLine);
            executionNote = `query at line ${cursorLine} (lines ${stmt.startLine}-${stmt.endLine})`;
        }
    }

    if (executionNote) {
        showToast(`Running ${executionNote}`, 'info', 1800);
    }

    const payload = {
        id: activePracticeId,
        technology: activeTechnology,
        code: fullCode,
        selected_code: codeToExecute !== fullCode ? codeToExecute : null,
        active_db: activeDatabaseName,
        files: currentProjectFiles,
        entry_file: activeFileName || Object.keys(currentProjectFiles)[0] || '',
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

// Render Output Console with Sticky Table Header in Scroll Wrapper
function renderOutput(stdout, stderr, durationMs, structuredResult) {
    const container = document.getElementById('output-console');
    if (!container) return;

    const timerBadge = document.getElementById('output-duration-badge');
    if (timerBadge) timerBadge.textContent = durationMs ? `${durationMs} ms` : '';

    container.innerHTML = '';

    if (structuredResult && structuredResult.columns && structuredResult.columns.length > 0) {
        const scrollWrapper = document.createElement('div');
        scrollWrapper.className = 'table-scroll-wrapper';

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

        scrollWrapper.appendChild(table);
        container.appendChild(scrollWrapper);

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
        errDiv.className = 'output-error shake-error';
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

// Output / Console Pane Visibility & Controls
function hideConsolePane() {
    const outputPane = document.getElementById('output-pane');
    const resizer = document.getElementById('workspace-resizer');
    const editorPane = document.getElementById('editor-pane');
    const toggleBtn = document.getElementById('btn-toggle-console');

    if (!outputPane) return;

    outputPane.style.display = 'none';
    if (resizer) resizer.style.display = 'none';
    if (editorPane) {
        editorPane.dataset.savedFlex = editorPane.style.flex || '0 0 65%';
        editorPane.style.flex = '1 1 100%';
        editorPane.style.height = '100%';
    }
    if (toggleBtn) {
        toggleBtn.classList.remove('active');
        toggleBtn.title = 'Show Console Output Log';
    }
    setTimeout(() => {
        if (monacoEditor) monacoEditor.layout();
    }, 40);
}

function showConsolePane() {
    const outputPane = document.getElementById('output-pane');
    const resizer = document.getElementById('workspace-resizer');
    const editorPane = document.getElementById('editor-pane');
    const toggleBtn = document.getElementById('btn-toggle-console');

    if (!outputPane) return;
    if (outputPane.style.display === 'flex' || (!outputPane.style.display && window.getComputedStyle(outputPane).display === 'flex')) {
        return; // already visible
    }

    outputPane.style.display = 'flex';
    if (resizer) resizer.style.display = 'block';
    if (editorPane) {
        const savedFlex = editorPane.dataset.savedFlex || '0 0 65%';
        editorPane.style.flex = savedFlex;
        editorPane.style.height = '';
    }
    if (toggleBtn) {
        toggleBtn.classList.add('active');
        toggleBtn.title = 'Hide Console Output Log';
    }
    setTimeout(() => {
        if (monacoEditor) monacoEditor.layout();
    }, 40);
}

function toggleConsolePane() {
    const outputPane = document.getElementById('output-pane');
    if (!outputPane) return;
    const isHidden = outputPane.style.display === 'none';
    if (isHidden) {
        showConsolePane();
    } else {
        hideConsolePane();
    }
}

function clearConsoleOutput() {
    const container = document.getElementById('output-console');
    if (container) {
        container.innerHTML = '<span style="color:var(--text-muted);">Console cleared. Ready.</span>';
    }
    const timerBadge = document.getElementById('output-duration-badge');
    if (timerBadge) timerBadge.textContent = '';
    const sysContainer = document.getElementById('system-design-preview-container');
    if (sysContainer) {
        sysContainer.innerHTML = '<div style="color:var(--text-muted); padding:1rem;">Architecture diagrams and notes will render live here.</div>';
    }
    showToast('Console output cleared', 'info', 1200);
}

// Copy Console Content to Clipboard (Structured, Text, or Design Preview)
async function copyConsoleOutput() {
    const sysDesign = document.getElementById('system-design-preview-container');
    const consoleEl = document.getElementById('output-console');
    const targetNode = (sysDesign && sysDesign.style.display !== 'none') ? sysDesign : consoleEl;
    if (!targetNode) return;

    const textToCopy = targetNode.innerText || targetNode.textContent || '';
    if (!textToCopy.trim() || textToCopy.trim() === 'Ready. Click Run to execute code.') {
        showToast('Console has no output to copy', 'info', 1500);
        return;
    }

    try {
        await navigator.clipboard.writeText(textToCopy);
        showToast('Console output copied to clipboard! 📋', 'success', 1800);
    } catch (e) {
        if (window.selectElementContents) {
            window.selectElementContents(targetNode);
        }
        document.execCommand('copy');
        showToast('Console output copied to clipboard! 📋', 'success', 1800);
    }
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

    document.getElementById('btn-run')?.addEventListener('click', () => runCurrentCode(false));
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
            maxBtn.title = 'Restore standard layout (Esc)';
            showToast('Maximized: 70% Coding Screen | 30% Output Console (Press Esc to restore)', 'info', 2200);
        } else {
            maxBtn.classList.remove('active');
            maxBtn.innerHTML = '<span id="maximize-icon">🗖</span> <span id="maximize-text">Maximize</span>';
            maxBtn.title = 'Maximize Editor & Console (70/30 Split)';
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
