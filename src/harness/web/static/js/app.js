// ─── Harness Web UI — App Logic ───

let messageCount = 0;

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
function newConversation() {
  document.getElementById('messageContainer').innerHTML = `
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
  messageCount = 0;
}

// ─── Send Message ───
async function sendMessage() {
  const input = document.getElementById('chatInput');
  let text = input.value.trim();

  // Append uploaded file references to the message
  if (uploadedFiles.length > 0) {
    const fileRefs = uploadedFiles.map(f => `[附件: ${f.filename}]`).join(' ');
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
  input.value = '';
  input.style.height = 'auto';
  messageCount++;

  // Typing indicator
  const typingId = 'typing-' + messageCount;
  const typing = document.createElement('div');
  typing.className = 'typing-indicator';
  typing.id = typingId;
  typing.innerHTML = `
    <div class="msg-avatar" style="background:var(--accent);color:white;">H</div>
    <div class="typing-dots"><span></span><span></span><span></span></div>`;
  container.appendChild(typing);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    document.getElementById(typingId)?.remove();

    const data = await res.json();
    const reply = data.reply || '(无回复)';
    addMessage(container, 'assistant', 'H', formatReply(reply), time);
    updateStatusBar(data);
  } catch (err) {
    document.getElementById(typingId)?.remove();
    addMessage(container, 'assistant', 'H', '❌ 网络错误: ' + err.message, time);
  }

  container.scrollTop = container.scrollHeight;
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
    document.getElementById('curWorkdir').textContent = wd.workdir || '—';
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

async function setWorkdir() {
  const path = document.getElementById('workdirInput').value.trim();
  if (!path) return alert('请输入目录路径');
  try {
    const res = await fetch('/api/config/workdir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      document.getElementById('curWorkdir').textContent = data.workdir;
      document.getElementById('workdirInput').value = '';
    } else {
      alert(data.message || '切换失败');
    }
  } catch (e) {
    alert('网络错误');
  }
}

function updateStatusBar(data) {
  if (data.timestamp) {
    document.getElementById('statusLatency').textContent = '活跃';
  }
}

// ─── Init ───
refreshDashboard();
setInterval(refreshDashboard, 30000); // refresh every 30s
