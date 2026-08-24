const state = {
    sessionId: null,
    provider: null,
    model: null,
    providers: [],
    isStreaming: false,
    toolCount: 0,
};

const $ = (sel) => document.querySelector(sel);

// --- Init ---
document.addEventListener('DOMContentLoaded', init);

async function init() {
    setupMobileNav();
    await loadProviders();
    await loadConfig();
    setupEventListeners();
    loadFiles();
    checkHealth();
}

function setupMobileNav() {
    $('#menu-button').addEventListener('click', () => {
        document.body.classList.toggle('sidebar-open');
    });
    document.addEventListener('click', (event) => {
        const sidebar = $('#sidebar');
        if (
            document.body.classList.contains('sidebar-open') &&
            !sidebar.contains(event.target) &&
            !event.target.closest('#menu-button')
        ) {
            document.body.classList.remove('sidebar-open');
        }
    });
}

async function loadProviders() {
    try {
        const res = await fetch('/api/providers');
        const data = await res.json();
        state.providers = data.providers;
        renderProviders();
    } catch (e) {
        console.error('Failed to load providers:', e);
    }
}

function renderProviders() {
    const providerSelect = $('#provider-select');
    const modelSelect = $('#model-select');
    providerSelect.innerHTML = '';

    state.providers.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = `${p.name}${p.configured ? '' : ' ⚠'}`;
        providerSelect.appendChild(opt);
    });

    if (state.providers.length > 0) {
        updateModels();
    }
}

function updateModels() {
    const providerId = $('#provider-select').value;
    const modelSelect = $('#model-select');
    const provider = state.providers.find(p => p.id === providerId);
    if (!provider) return;

    state.allModels = provider.models;
    renderModelOptions(provider.models);

    $('#model-count').textContent = `${provider.models.length} free`;
    $('#model-search').value = '';

    modelSelect.innerHTML = '';
    state.provider = providerId;
}

function renderModelOptions(models) {
    const modelSelect = $('#model-select');
    modelSelect.innerHTML = '';
    models.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = m.name;
        modelSelect.appendChild(opt);
    });
    if (models.length > 0) {
        state.model = models[0].id;
    }
}

function setupEventListeners() {
    $('#provider-select').addEventListener('change', updateModels);
    $('#model-select').addEventListener('change', () => {
        state.provider = $('#provider-select').value;
        state.model = $('#model-select').value;
    });
    $('#model-search').addEventListener('input', filterModels);

    $('#new-session').addEventListener('click', newSession);
    $('#refresh-files').addEventListener('click', loadFiles);
    $('#clear-activity').addEventListener('click', clearActivity);
    $('#send-btn').addEventListener('click', sendMessage);

    setupSettings();

    const input = $('#message-input');
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    input.addEventListener('input', autoResize);
}

function setupSettings() {
    ['open-settings', 'header-settings', 'welcome-settings', 'banner-settings'].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('click', openSettings);
    });
    document.querySelectorAll('[data-close]').forEach((el) => {
        el.addEventListener('click', closeSettings);
    });
    document.getElementById('settings-save').addEventListener('click', saveSettings);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeSettings();
    });
}

function filterModels() {
    const query = $('#model-search').value.toLowerCase();
    if (!state.allModels) return;
    const filtered = state.allModels.filter(m =>
        m.name.toLowerCase().includes(query) || m.id.toLowerCase().includes(query)
    );
    renderModelOptions(filtered);
    $('#model-count').textContent = `${filtered.length} shown`;
}

function autoResize() {
    const input = $('#message-input');
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
}

function sendQuick(text) {
    $('#message-input').value = text;
    sendMessage();
}

async function checkHealth() {
    try {
        const res = await fetch('/health');
        const data = await res.json();
        $('#status-text').textContent = `${data.app} v${data.version}`;
        $('#status-dot').classList.remove('offline');
    } catch {
        $('#status-dot').classList.add('offline');
        $('#status-text').textContent = 'Offline';
    }
}

async function loadConfig() {
    try {
        const res = await fetch('/api/config');
        const data = await res.json();
        state.config = data;
        renderProviderStatus(data);
        showKeyBannerIfNeeded(data);
        document.getElementById('cfg-openrouter').value = data.keys.OPENROUTER_API_KEY || '';
        document.getElementById('cfg-nvidia').value = data.keys.NVIDIA_API_KEY || '';
        document.getElementById('cfg-opencode').value = data.keys.OPENCODE_ZEN_API_KEY || '';
        document.getElementById('cfg-opencode-url').value = data.keys.OPENCODE_ZEN_BASE_URL || '';
        document.getElementById('cfg-provider').value = data.defaults.provider || 'openrouter';
        document.getElementById('cfg-model').value = data.defaults.model || '';
        document.getElementById('cfg-shell').value = data.defaults.shell_enabled ? 'true' : 'false';
        document.getElementById('cfg-timeout').value = data.defaults.command_timeout || 180;
    } catch (e) {
        console.error('Failed to load config', e);
    }
}

function renderProviderStatus(data) {
    const names = { openrouter: 'OpenRouter', nvidia: 'NVIDIA', opencode_zen: 'OpenCode Zen' };
    const el = document.getElementById('provider-status');
    if (!el) return;
    el.innerHTML = Object.entries(data.providers)
        .map(([id, p]) => `<div class="ps"><span class="dot ${p.configured ? 'ok' : ''}"></span>${names[id] || id} ${p.configured ? 'connected' : 'no key'}</div>`)
        .join('');
}

function showKeyBannerIfNeeded(data) {
    const any = Object.values(data.providers).some((p) => p.configured);
    const banner = document.getElementById('key-banner');
    if (any) {
        banner.classList.add('hidden');
        document.body.classList.remove('has-banner');
    } else {
        banner.classList.remove('hidden');
        document.body.classList.add('has-banner');
    }
}

function openSettings() {
    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettings() {
    document.getElementById('settings-modal').classList.add('hidden');
}

async function saveSettings() {
    const payload = {
        OPENROUTER_API_KEY: document.getElementById('cfg-openrouter').value.trim(),
        NVIDIA_API_KEY: document.getElementById('cfg-nvidia').value.trim(),
        OPENCODE_ZEN_API_KEY: document.getElementById('cfg-opencode').value.trim(),
        OPENCODE_ZEN_BASE_URL: document.getElementById('cfg-opencode-url').value.trim(),
        DEFAULT_PROVIDER: document.getElementById('cfg-provider').value,
        DEFAULT_MODEL: document.getElementById('cfg-model').value.trim(),
        SHELL_ENABLED: document.getElementById('cfg-shell').value,
        COMMAND_TIMEOUT: Number(document.getElementById('cfg-timeout').value || 180),
    };
    const status = document.getElementById('settings-status');
    status.className = 'settings-status';
    status.textContent = 'Saving...';
    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error('save failed');
        status.className = 'settings-status ok';
        status.textContent = 'Saved. Reloading providers...';
        await loadProviders();
        await loadConfig();
        setTimeout(closeSettings, 800);
    } catch (e) {
        status.className = 'settings-status err';
        status.textContent = 'Could not save settings.';
    }
}

function newSession() {
    state.sessionId = null;
    state.toolCount = 0;
    clearActivity();
    $('#chat-title').textContent = 'New Conversation';
    $('#active-tools-badge').classList.add('hidden');
    resetChatMessages();
}

function resetChatMessages() {
    $('#chat-messages').innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">⚡</div>
            <h2>Nexus AI Agent</h2>
            <p>I can search the web, create files, run commands, and build anything you need.</p>
            <div class="quick-actions">
                <button onclick="sendQuick('Search the web for the latest AI news and summarize')">🔍 Search &amp; Summarize</button>
                <button onclick="sendQuick('Create a Python web scraper that extracts product prices from an e-commerce site')">📝 Create a Script</button>
                <button onclick="sendQuick('Build a simple REST API with FastAPI and test it')">🚀 Build an API</button>
                <button onclick="sendQuick('List all files in the workspace and describe what you find')">📁 Explore Workspace</button>
            </div>
        </div>`;
}

async function sendMessage() {
    const input = $('#message-input');
    const message = input.value.trim();
    if (!message || state.isStreaming) return;

    input.value = '';
    autoResize();
    removeWelcome();

    addMessage('user', message);
    setStreaming(true);

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                message,
                provider: state.provider,
                model: state.model,
            }),
        });

        state.sessionId = res.headers.get('X-Session-Id') || state.sessionId;
        $('#chat-title').textContent = message.substring(0, 40) + (message.length > 40 ? '...' : '');

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let finalContent = '';

        let assistantEl = null;

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const event = JSON.parse(line);
                    handleAgentEvent(event);
                    if (event.type === 'final') finalContent = event.content;
                } catch {}
            }
        }

        if (finalContent) {
            addMessage('assistant', finalContent);
        }
    } catch (e) {
        console.error('Chat error:', e);
        addMessage('assistant', `⚠ Error: ${e.message}`);
    } finally {
        setStreaming(false);
        hideToolBadge();
    }
}

function handleAgentEvent(event) {
    if (event.type === 'tool_calls') {
        showToolBadge(event.tools.length);
        event.tools.forEach(t => addActivity('tool-call', t.name, JSON.stringify(t.args).substring(0, 100)));
    }
    if (event.type === 'tool_result') {
        addActivity('tool-result', event.tool, typeof event.result === 'string' ? event.result.substring(0, 150) : '');
    }
}

function removeWelcome() {
    const welcome = $('.welcome-message');
    if (welcome) welcome.remove();
}

function addMessage(role, content) {
    const container = $('#chat-messages');
    const el = document.createElement('div');
    el.className = `message ${role}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = formatMessage(content);
    el.appendChild(bubble);
    container.appendChild(el);
    container.scrollTop = container.scrollHeight;
}

function formatMessage(text) {
    // Basic code block formatting
    text = text.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
        return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
    });
    text = text.replace(/`([^`\n]+)`/g, '<code>$1</code>');
    return escapeHtml(text).replace(/&lt;pre&gt;/g, '<pre>').replace(/&lt;\/pre&gt;/g, '</pre>')
        .replace(/&lt;code&gt;/g, '<code>').replace(/&lt;\/code&gt;/g, '</code>');
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function showToolBadge(count) {
    $('#active-tools-badge').classList.remove('hidden');
    $('#tool-count').textContent = count;
}

function hideToolBadge() {
    $('#active-tools-badge').classList.add('hidden');
}

function addActivity(type, name, detail) {
    const log = $('#activity-log');
    const item = document.createElement('div');
    item.className = `activity-item ${type}`;
    item.innerHTML = `
        <span class="tool-name">${type === 'tool-call' ? '⚡' : '✓'} ${name}</span>
        ${detail ? `<div class="result-preview">${escapeHtml(detail)}</div>` : ''}
    `;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
}

function clearActivity() {
    $('#activity-log').innerHTML = '';
}

async function loadFiles() {
    try {
        const res = await fetch('/api/files?path=.');
        const data = await res.json();
        const tree = $('#file-tree');
        tree.innerHTML = '';

        if (data.entries) {
            data.entries.forEach(entry => {
                const div = document.createElement('div');
                div.className = entry.type === 'dir' ? 'dir' : 'file';
                div.textContent = `${entry.type === 'dir' ? '📁' : '📄'} ${entry.name}`;
                if (entry.type === 'file') {
                    div.title = `${entry.size || 0} bytes`;
                }
                tree.appendChild(div);
            });
        }
    } catch (e) {
        console.error('Failed to load files:', e);
    }
}

function setStreaming(active) {
    state.isStreaming = active;
    $('#send-btn').disabled = active;
    if (active) {
        const container = $('#chat-messages');
        const typing = document.createElement('div');
        typing.className = 'message assistant typing';
        typing.innerHTML = '<div class="bubble"><div class="typing-dots"><span></span><span></span><span></span></div></div>';
        container.appendChild(typing);
        container.scrollTop = container.scrollHeight;
    } else {
        $('.typing')?.remove();
    }
}
