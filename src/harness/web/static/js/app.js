// ─── Harness Web UI — App Logic ───

let messageCount = 0;
let currentConvId = null;

// ─── Tab Switching ───
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'dashboard') refreshDashboard();
  });
});

// ─── Textarea ───
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

document.getElementById('chatInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// ─── Suggestions ───
let pendingSuggest = '';
let uploadedFiles = [];  // track uploaded files for the next message
function suggest(text) {
  document.getElementById('chatInput').value = text;
  autoResize(document.getElementById('chatInput'));
  sendMessage();
}

// ─── New Conversation ───
async function newConversation() {
  try {
    const res = await fetch('/api/conversations', { method: 'POST' });
    const conv = await res.json();
    currentConvId = conv.id;
    switchConversation(conv.id);
  } catch (e) {}
}

async function switchConversation(convId) {
  currentConvId = convId;
  const container = document.getElementById('messageContainer');
  container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted)">加载中…</div>';
  try {
    const res = await fetch('/api/conversations/' + convId);
    const conv = await res.json();
    container.innerHTML = '';
    if (conv.messages.length === 0) {
      container.innerHTML = `
        <div class="empty-state" id="emptyState">
          <div class="empty-state-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
          </div>
          <h3>Harness Agent 已就绪</h3>
          <p>输入你的需求，Agent 会使用工具来帮助你</p>
          <div class="suggestions">
            <span class="suggestion-chip" onclick="suggest('读取当前目录的文件')">读取当前目录的文件</span>
            <span class="suggestion-chip" onclick="suggest('运行测试')">运行测试</span>
            <span class="suggestion-chip" onclick="suggest('帮我看看这张图')">帮我看看这张图</span>
          </div>
        </div>`;
    } else {
      for (const msg of conv.messages) {
        const role = msg.role === 'user' ? 'user' : 'assistant';
        const avatar = role === 'user' ? 'U' : 'H';
        const time = (msg.timestamp || '').slice(11, 16);
        addMessage(container, role, avatar, escapeHtml(msg.content), time);
      }
    }
    messageCount = conv.messages.length;
    // Update sidebar
    refreshSidebar(convId);
  } catch (e) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--status-error)">加载失败</div>';
  }
}

async function saveMessage(role, content) {
  if (!currentConvId) return;
  try {
    await fetch('/api/conversations/' + currentConvId + '/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role, content }),
    });
    refreshSidebar(currentConvId);
  } catch (e) {}
}

async function refreshSidebar(activeId) {
  try {
    const res = await fetch('/api/conversations');
    const convs = await res.json();
    const list = document.getElementById('conversationList');
    list.innerHTML = convs.map(c => `
      <div class="conversation-item ${c.id === activeId ? 'active' : ''}" onclick="switchConversation('${c.id}')">
        <span class="conv-icon"></span>
        <div class="conv-info">
          <div class="conv-title">${escapeHtml(c.title)}</div>
          <div class="conv-meta">${c.message_count} 条消息</div>
        </div>
      </div>
    `).join('');
  } catch (e) {}
}

// ─── Send Message ───
async function sendMessage() {
  const input = document.getElementById('chatInput');
  let text = input.value.trim();

  // Append uploaded file references to the message
  if (uploadedFiles.length > 0) {
    const fileRefs = uploadedFiles.map(f => `[附件: ${f.path}]`).join(' ');
    text = text ? `${text} ${fileRefs}` : `请查看这些附件: ${fileRefs}`;
    uploadedFiles = [];
    document.getElementById('fileStatus')?.remove();
  }
  if (!text) return;

  const container = document.getElementById('messageContainer');
  const emptyState = document.getElementById('emptyState');
  if (emptyState) emptyState.remove();

  const now = new Date();
  const time = pad(now.getHours()) + ':' + pad(now.getMinutes());

  // User message
  addMessage(container, 'user', 'U', text, time);
  saveMessage('user', text);
  input.value = '';
  input.style.height = 'auto';
  messageCount++;

  // Progress area — shows live agent activity
  const progressDiv = document.createElement('div');
  progressDiv.id = 'progressArea';
  progressDiv.style.cssText = 'padding:4px 24px 0;font-size:13px;color:var(--text-muted);font-family:var(--font-mono)';
  container.appendChild(progressDiv);

  // SSE connection via fetch (EventSource only supports GET)
  const replyText = await new Promise((resolve) => {
    let result = '';
    fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    }).then(async (res) => {
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'thinking' || data.type === 'tool') {
                progressDiv.textContent = data.data;
              } else if (data.type === 'tool_result' || data.type === 'info') {
                progressDiv.textContent = data.data;
              } else if (data.type === 'result') {
                result = data.data;
                progressDiv.remove();
                addMessage(container, 'assistant', 'H', formatReply(data.data), time);
                saveMessage('assistant', data.data);
              } else if (data.type === 'error') {
                progressDiv.textContent = '❌ ' + data.data;
              }
              container.scrollTop = container.scrollHeight;
            } catch (e) {}
          }
        }
      }
      resolve(result);
    }).catch(() => {
      if (!result) progressDiv.textContent = '❌ 连接断开';
      resolve(result);
    });
  });
}

// ─── File Upload ───
async function uploadFile(input) {
  const files = input.files;
  if (!files.length) return;

  const statusEl = document.createElement('div');
  statusEl.id = 'fileStatus';
  statusEl.style.cssText = 'padding:4px 24px;font-size:12px;color:var(--text-muted);';

  for (const file of files) {
    statusEl.textContent = `📤 上传中: ${file.name}...`;
    document.querySelector('.chat-input-area').insertBefore(statusEl, document.querySelector('.input-wrapper'));

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', { method: 'POST', body: formData });
      const data = await res.json();
      if (data.status === 'ok') {
        uploadedFiles.push({ filename: data.filename, path: data.path });
        statusEl.textContent = `📎 ${data.filename} (${(data.size/1024).toFixed(1)}KB) 已添加`;
        statusEl.style.color = 'var(--status-online)';
      } else {
        statusEl.textContent = `❌ ${file.name} 上传失败`;
        statusEl.style.color = 'var(--status-error)';
      }
    } catch (e) {
      statusEl.textContent = `❌ 上传错误: ${e.message}`;
      statusEl.style.color = 'var(--status-error)';
    }
  }

  input.value = '';
  setTimeout(() => statusEl.remove(), 3000);
}

// ─── Dashboard ───

function addMessage(container, role, avatar, content, time) {
  const msg = document.createElement('div');
  msg.className = 'message ' + role;
  msg.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div>
      <div class="msg-bubble">${content}</div>
      <div class="msg-time">${time}</div>
    </div>`;
  container.appendChild(msg);
}

function formatReply(text) {
  // Simple markdown-like formatting for code blocks
  return text
    .split('\n').map(line => {
      if (line.startsWith('```')) return '<pre><code>' + escapeHtml(line.slice(3)) + '</code></pre>';
      return '<p>' + escapeHtml(line) + '</p>';
    }).join('');
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function pad(n) { return n.toString().padStart(2, '0'); }

// ─── Dashboard ───
async function refreshDashboard() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    document.getElementById('statusModel').textContent = data.model || '—';
    document.getElementById('statusProvider').textContent = data.connected ? '已连接' : '未连接';
    document.getElementById('statRules').textContent = data.guardrail_rules ?? '—';
    document.getElementById('statTools').textContent = (data.tools_available || []).length + ' 个';
    document.getElementById('statKey').textContent = data.connected ? '已配置' : '未配置';
    document.getElementById('statusDot').className = 'status-dot ' + (data.connected ? 'online' : 'offline');
    document.getElementById('statusModelName').textContent = data.model || '—';

    document.getElementById('statusConnection').textContent = data.connected ? '● 已连接' : '○ 未连接';
  } catch (e) {
    document.getElementById('statusConnection').textContent = '○ 离线';
  }

  // Guardrail log
  try {
    const r2 = await fetch('/api/guardrail-log');
    const log = await r2.json();
    const logEl = document.getElementById('guardrailLog');
    if (log.length === 0) {
      logEl.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:8px 0">暂无拦截记录</div>';
    } else {
      logEl.innerHTML = log.reverse().map(e => `
        <div class="guardrail-entry">
          <span class="guardrail-time">${(e.timestamp || '').slice(11,19)}</span>
          <span class="guardrail-action">${escapeHtml(e.action_name || '?')}</span>
          <span class="guardrail-verdict ${(e.verdict || 'allow').toLowerCase()}">${escapeHtml(e.verdict || '?')}</span>
          <span style="font-size:11px;color:var(--text-muted)">${escapeHtml(e.user_decision || '')}</span>
        </div>
      `).join('');
    }
  } catch (e) {
    document.getElementById('guardrailLog').innerHTML = '<div style="color:var(--status-error);font-size:13px">加载失败</div>';
  }

  // Key status
  try {
    const r3 = await fetch('/api/key/status');
    const ks = await r3.json();
    document.getElementById('keyStatus').textContent = ks.configured ? '✅ API Key 已配置' : '❌ 未配置 API Key';
  } catch (e) {}

  // Workdir
  try {
    const r4 = await fetch('/api/config/workdir');
    const wd = await r4.json();
    document.getElementById('workdirDisplay').textContent = wd.workdir || '—';
  } catch (e) {}
}

// ─── API Key ───
async function setApiKey() {
  const key = document.getElementById('keyInput').value.trim();
  if (!key) return alert('请输入 API Key');
  try {
    const res = await fetch('/api/key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key }),
    });
    if (res.ok) {
      document.getElementById('keyStatus').textContent = '✅ API Key 已保存';
      document.getElementById('keyInput').value = '';
      refreshDashboard();
    } else {
      alert('保存失败');
    }
  } catch (e) {
    alert('网络错误');
  }
}

async function clearApiKey() {
  if (!confirm('确定清除 API Key 吗？')) return;
  try {
    await fetch('/api/key/clear', { method: 'POST' });
    document.getElementById('keyStatus').textContent = '❌ API Key 已清除';
    refreshDashboard();
  } catch (e) {}
}

function editWorkdir() {
  const display = document.getElementById('workdirDisplay');
  const input = document.getElementById('workdirInput');
  input.value = display.textContent;
  document.getElementById('workdirDisplay').style.display = 'none';
  document.getElementById('workdirEdit').style.display = 'block';
  input.focus();
  input.select();
}

function cancelWorkdirEdit() {
  document.getElementById('workdirDisplay').style.display = 'block';
  document.getElementById('workdirEdit').style.display = 'none';
}

async function saveWorkdir() {
  const path = document.getElementById('workdirInput').value.trim();
  if (!path) { cancelWorkdirEdit(); return; }
  try {
    const res = await fetch('/api/config/workdir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      document.getElementById('workdirDisplay').textContent = data.workdir;
    } else {
      alert(data.message || '切换失败');
    }
  } catch (e) {
    alert('网络错误');
  }
  cancelWorkdirEdit();
}

async function quickWorkdir(path) {
  try {
    const res = await fetch('/api/config/workdir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      document.getElementById('workdirDisplay').textContent = data.workdir;
      document.getElementById('dirBrowser').style.display = 'none';
    }
  } catch (e) {}
}

async function browseDir(path) {
  const browser = document.getElementById('dirBrowser');
  const current = path || document.getElementById('workdirDisplay').textContent;
  browser.style.display = 'block';
  browser.innerHTML = '<div style="padding:8px;color:var(--text-muted);font-size:12px">加载中…</div>';

  try {
    const res = await fetch('/api/config/workdir/list?path=' + encodeURIComponent(current));
    const data = await res.json();
    let html = '<div style="padding:4px 6px;font-size:11px;color:var(--text-muted);border-bottom:1px solid var(--border-light)">' + data.path + '</div>';

    if (data.parent) {
      const parentPath = data.parent.replace(/\\\\/g, '/');
      html += '<div style="padding:4px 6px;cursor:pointer;font-size:13px;color:var(--accent)" onclick="browseDir(\'' + parentPath + '\')">📂 ..</div>';
    }
    for (const d of data.dirs) {
      const full = data.path.replace(/\\/g, '/') + '/' + d;
      html += '<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 6px;border-bottom:1px solid var(--border-light)">' +
        '<span style="cursor:pointer;font-size:13px" onclick="browseDir(\'' + full + '\')">📁 ' + d + '</span>' +
        '<button class="btn btn-ghost" style="font-size:11px;padding:2px 8px" onclick="quickWorkdir(\'' + full + '\')">选择</button>' +
        '</div>';
    }
    if (data.dirs.length === 0) {
      html += '<div style="padding:8px 6px;font-size:12px;color:var(--text-muted)">(空目录)</div>';
    }
    browser.innerHTML = html;
  } catch (e) {
    browser.innerHTML = '<div style="padding:8px;color:var(--status-error);font-size:12px">加载失败</div>';
  }
}

function pickFolder(input) {
  const files = input.files;
  if (!files.length) return;
  const formData = new FormData();
  formData.append('file', files[0]);
  fetch('/api/upload', { method: 'POST', body: formData }).then(r => r.json()).then(data => {
    if (data.status === 'ok') {
      const dir = data.original_dir;
      if (dir) {
        quickWorkdir(dir.replace(/\\\\/g, '/'));
      } else {
        // Fallback: use upload dir, then open tree browser
        const uploadDir = data.path.replace(/\\\\/g, '/').replace(/\/[^/]+$/, '');
        quickWorkdir(uploadDir);
        browseDir('C:/Users');
      }
    }
  });
  input.value = '';
}

// ─── Status Bar Update ───

function updateStatusBar(data) {
  if (data.timestamp) {
    document.getElementById('statusLatency').textContent = '活跃';
  }
}

// ─── Init ───
async function initApp() {
  try {
    const res = await fetch('/api/conversations');
    const convs = await res.json();
    if (convs.length > 0) {
      await switchConversation(convs[0].id);
    } else {
      await newConversation();
    }
  } catch (e) {
    newConversation();
  }
  refreshDashboard();
}
initApp();
setInterval(refreshDashboard, 30000);
