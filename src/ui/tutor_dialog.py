"""
Copyright (C) 2024 Michael Piazza

This file is part of Smart Notes.

Smart Notes is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Smart Notes is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Smart Notes.  If not, see <https://www.gnu.org/licenses/>.
"""

import json

from aqt import QDialog, QVBoxLayout
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

from ..config import config
from ..constants import get_server_url


class TutorDialog(QDialog):
    """Prototype AI Tutor dialog. Single webview with a streaming chat UI."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Smart Notes — AI Tutor (alpha)")
        self.resize(720, 720)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._web = QWebEngineView(self)
        layout.addWidget(self._web)

        server_url = get_server_url()
        jwt = config.auth_token or ""
        html = build_tutor_html(server_url=server_url, jwt=jwt)
        # baseUrl sets the page origin so fetch() requests are same-origin to
        # the API server and skip CORS preflight.
        self._web.setHtml(html, QUrl(server_url + "/"))


def build_tutor_html(server_url: str, jwt: str) -> str:
    config_blob = json.dumps({"serverUrl": server_url, "jwt": jwt})
    # Single self-contained page — no external assets, no template engine.
    return TUTOR_HTML.replace("__CONFIG__", config_blob)


TUTOR_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>AI Tutor</title>
<style>
  :root {
    --bg: #0f1115;
    --panel: #161a22;
    --border: #232936;
    --text: #e7ecf3;
    --muted: #8b94a7;
    --accent: #7c8cff;
    --user: #2a3650;
    --assistant: #1b212c;
  }
  @media (prefers-color-scheme: light) {
    :root {
      --bg: #f7f8fb;
      --panel: #ffffff;
      --border: #e3e6ec;
      --text: #1a1d23;
      --muted: #6b7280;
      --accent: #4956d6;
      --user: #e8edff;
      --assistant: #f1f3f7;
    }
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    display: flex;
    flex-direction: column;
  }
  header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--panel);
  }
  header .title { font-weight: 600; }
  header .badge {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 2px 6px;
    border-radius: 999px;
    background: var(--accent);
    color: white;
  }
  #log {
    flex: 1 1 auto;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .row { display: flex; }
  .row.user { justify-content: flex-end; }
  .bubble {
    max-width: 78%;
    padding: 10px 14px;
    border-radius: 14px;
    border: 1px solid var(--border);
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  .row.user .bubble {
    background: var(--user);
    border-top-right-radius: 4px;
  }
  .row.assistant .bubble {
    background: var(--assistant);
    border-top-left-radius: 4px;
  }
  .bubble.streaming::after {
    content: "▍";
    color: var(--accent);
    margin-left: 2px;
    animation: blink 1s steps(2, start) infinite;
  }
  @keyframes blink { to { visibility: hidden; } }
  .meta {
    font-size: 11px;
    color: var(--muted);
    margin: 0 6px;
    align-self: flex-end;
  }
  footer {
    border-top: 1px solid var(--border);
    background: var(--panel);
    padding: 10px;
    display: flex;
    gap: 8px;
    align-items: flex-end;
  }
  textarea {
    flex: 1;
    resize: none;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--bg);
    color: var(--text);
    padding: 10px 12px;
    font: inherit;
    min-height: 38px;
    max-height: 160px;
    outline: none;
  }
  textarea:focus { border-color: var(--accent); }
  button {
    background: var(--accent);
    color: white;
    border: 0;
    border-radius: 10px;
    padding: 10px 16px;
    font: inherit;
    font-weight: 600;
    cursor: pointer;
    height: 38px;
  }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .hint {
    font-size: 11px;
    color: var(--muted);
    padding: 0 16px 8px;
    background: var(--panel);
  }
  .error {
    color: #ff8585;
    font-style: italic;
  }
</style>
</head>
<body>
  <header>
    <span class="title">AI Tutor</span>
    <span class="badge">alpha</span>
  </header>
  <div id="log" aria-live="polite"></div>
  <footer>
    <textarea id="input" rows="1" placeholder="Ask anything…"></textarea>
    <button id="send">Send</button>
  </footer>
  <div class="hint">Enter to send · Shift+Enter for newline</div>

<script>
(() => {
  const CFG = __CONFIG__;
  const history = [];
  const log = document.getElementById('log');
  const input = document.getElementById('input');
  const send = document.getElementById('send');

  const autosize = () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 160) + 'px';
  };
  input.addEventListener('input', autosize);

  const scrollToBottom = () => {
    log.scrollTop = log.scrollHeight;
  };

  const appendBubble = (role, text) => {
    const row = document.createElement('div');
    row.className = 'row ' + role;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    row.appendChild(bubble);
    log.appendChild(row);
    scrollToBottom();
    return bubble;
  };

  const setBusy = (busy) => {
    input.disabled = busy;
    send.disabled = busy;
    if (!busy) input.focus();
  };

  // Parse one SSE event block into {event, data}
  const parseEvent = (block) => {
    let ev = 'message';
    const data = [];
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) ev = line.slice(6).trim();
      else if (line.startsWith('data:')) {
        const v = line.slice(5);
        data.push(v.startsWith(' ') ? v.slice(1) : v);
      }
    }
    return { event: ev, data: data.join('\n') };
  };

  const sendMessage = async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    autosize();
    setBusy(true);

    history.push({ role: 'user', content: text });
    appendBubble('user', text);

    const bubble = appendBubble('assistant', '');
    bubble.classList.add('streaming');

    let assistantText = '';
    try {
      const res = await fetch(CFG.serverUrl + '/api/tutor', {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer ' + CFG.jwt,
          'Content-Type': 'application/json',
          'x-sn-source': 'anki-plugin',
        },
        body: JSON.stringify({ messages: history }),
      });

      if (!res.ok || !res.body) {
        const errText = await res.text().catch(() => '');
        bubble.classList.remove('streaming');
        bubble.classList.add('error');
        bubble.textContent = `Request failed (${res.status}). ${errText}`;
        history.pop();
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buf.indexOf('\n\n')) >= 0) {
          const block = buf.slice(0, idx);
          buf = buf.slice(idx + 2);
          if (!block.trim()) continue;
          const { event, data } = parseEvent(block);
          if (event === 'delta') {
            assistantText += data;
            bubble.textContent = assistantText;
            scrollToBottom();
          } else if (event === 'error') {
            bubble.classList.add('error');
            bubble.textContent += `\n[error] ${data}`;
          }
        }
      }

      if (assistantText) {
        history.push({ role: 'assistant', content: assistantText });
      } else {
        bubble.textContent = '(no response)';
      }
    } catch (e) {
      bubble.classList.add('error');
      bubble.textContent = `Network error: ${e && e.message || e}`;
      history.pop();
    } finally {
      bubble.classList.remove('streaming');
      setBusy(false);
    }
  };

  send.addEventListener('click', sendMessage);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  input.focus();
})();
</script>
</body>
</html>
"""
