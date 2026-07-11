/* ============================================================
   HouseBot AI — app.js
   Frontend Logic: Predict, EMI, Area Finder, Chat, Dark Mode
   ============================================================ */

// ============================================================
//  UTILITY FUNCTIONS
// ============================================================

/** Format number as Indian currency (₹ XX,XX,XXX) */
function formatINR(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(amount);
}

/** Show/hide the loading overlay */
function showLoading(text = 'IBM Granite AI is thinking...') {
  document.getElementById('loadingText').textContent = text;
  document.getElementById('loadingOverlay').classList.remove('d-none');
}
function hideLoading() {
  document.getElementById('loadingOverlay').classList.add('d-none');
}

/** Display a result container */
function showResult(containerId, bodyId, html) {
  const container = document.getElementById(containerId);
  const body = document.getElementById(bodyId);
  body.innerHTML = html;
  container.classList.remove('d-none');
  container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/** Convert plain text with markdown-style formatting to HTML */
function renderMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^#{1,3}\s(.+)$/gm, '<h4 style="margin:1rem 0 0.4rem;font-weight:700;color:var(--accent-blue)">$1</h4>')
    .replace(/^[-•]\s(.+)$/gm, '<div style="display:flex;gap:6px;margin:3px 0"><span style="color:var(--accent-blue)">•</span><span>$1</span></div>')
    .replace(/^\d+\.\s(.+)$/gm, '<div style="display:flex;gap:6px;margin:3px 0"><span style="color:var(--accent-purple);font-weight:700">›</span><span>$1</span></div>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');
}

/** POST JSON to a Flask endpoint */
async function postAPI(endpoint, data) {
  const resp = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const json = await resp.json();
  if (!resp.ok || json.error) throw new Error(json.error || 'API request failed');
  return json;
}

/** Get selected amenity chips */
function getSelectedAmenities() {
  return Array.from(document.querySelectorAll('.chip.active'))
    .map(c => c.dataset.val)
    .join(', ') || 'Basic';
}

// ============================================================
//  DARK MODE
// ============================================================
(function initTheme() {
  const saved = localStorage.getItem('housebot-theme') || 'light';
  applyTheme(saved);
})();

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const icon = document.getElementById('themeIcon');
  if (icon) {
    icon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
  }
  localStorage.setItem('housebot-theme', theme);
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('themeToggle').addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });

  // ============================================================
  //  AMENITY CHIP TOGGLE
  // ============================================================
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => chip.classList.toggle('active'));
  });

  // ============================================================
  //  EMI SLIDERS ↔ INPUTS SYNC
  // ============================================================
  const rateInput = document.getElementById('emiRate');
  const rateSlider = document.getElementById('emiRateSlider');
  const tenureInput = document.getElementById('emiTenure');
  const tenureSlider = document.getElementById('emiTenureSlider');

  rateSlider.addEventListener('input', () => { rateInput.value = rateSlider.value; });
  rateInput.addEventListener('input', () => { rateSlider.value = rateInput.value; });
  tenureSlider.addEventListener('input', () => { tenureInput.value = tenureSlider.value; });
  tenureInput.addEventListener('input', () => { tenureSlider.value = tenureInput.value; });

  // ============================================================
  //  PRICE PREDICTION FORM
  // ============================================================
  document.getElementById('predictForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('predictBtn');
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Predicting...';
    showLoading('Analyzing property data with IBM Granite AI...');

    try {
      const data = {
        city: document.getElementById('city').value.trim(),
        locality: document.getElementById('locality').value.trim(),
        property_type: document.getElementById('property_type').value,
        bhk: document.getElementById('bhk').value,
        size: document.getElementById('size').value,
        floor: document.getElementById('floor').value,
        age: document.getElementById('age').value,
        budget: document.getElementById('budget').value,
        amenities: getSelectedAmenities()
      };

      const result = await postAPI('/api/predict', data);
      showResult('predictResult', 'predictResultBody', renderMarkdown(result.response));
    } catch (err) {
      showResult('predictResult', 'predictResultBody',
        `<div style="color:var(--accent-red)"><strong>⚠️ Error:</strong> ${err.message}</div>`);
    } finally {
      hideLoading();
      btn.disabled = false;
      btn.innerHTML = originalHTML;
    }
  });

  // ============================================================
  //  EMI CALCULATOR
  // ============================================================
  document.getElementById('emiForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const principal = parseFloat(document.getElementById('emiPrincipal').value);
    const rate = parseFloat(document.getElementById('emiRate').value);
    const tenure = parseInt(document.getElementById('emiTenure').value);

    if (!principal || principal <= 0) {
      alert('Please enter a valid loan amount');
      return;
    }

    showLoading('Calculating EMI and generating AI loan advice...');

    try {
      const result = await postAPI('/api/emi', { principal, rate, tenure });

      // Update stat boxes
      document.getElementById('emiMonthly').textContent = formatINR(result.emi);
      document.getElementById('emiInterest').textContent = formatINR(result.total_interest);
      document.getElementById('emiTotal').textContent = formatINR(result.total_amount);
      document.getElementById('emiSummary').classList.remove('d-none');

      // Draw pie chart
      drawEMIPieChart(principal, result.total_interest);

      // AI response
      if (result.ai_response) {
        showResult('emiAiResult', 'emiAiBody', renderMarkdown(result.ai_response));
      }

      document.getElementById('emiSummary').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      alert('EMI calculation error: ' + err.message);
    } finally {
      hideLoading();
    }
  });

  // ============================================================
  //  AREA FINDER
  // ============================================================
  document.getElementById('areasForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    showLoading('Finding best areas within your budget...');

    try {
      const data = {
        city: document.getElementById('areaCity').value.trim(),
        budget: document.getElementById('areaBudget').value,
        bhk: document.getElementById('areaBhk').value
      };
      const result = await postAPI('/api/suggest-areas', data);
      showResult('areasResult', 'areasResultBody', renderMarkdown(result.response));
    } catch (err) {
      showResult('areasResult', 'areasResultBody',
        `<div style="color:var(--accent-red)"><strong>⚠️ Error:</strong> ${err.message}</div>`);
    } finally {
      hideLoading();
    }
  });

  // ============================================================
  //  CHAT INTERFACE
  // ============================================================
  const chatMessages = document.getElementById('chatMessages');
  const chatInput = document.getElementById('chatInput');
  const chatSendBtn = document.getElementById('chatSendBtn');

  function scrollChat() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendBubble(role, content, isTyping = false) {
    const div = document.createElement('div');
    div.className = `chat-bubble ${role === 'user' ? 'user-bubble' : 'bot-bubble'}${isTyping ? ' typing-bubble' : ''}`;
    const icon = role === 'user' ? 'fa-user' : 'fa-robot';
    const bubbleContent = isTyping
      ? `<div class="typing-dots"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`
      : (role === 'user' ? escapeHtml(content) : renderMarkdown(content));

    div.innerHTML = `
      <div class="bubble-avatar"><i class="fa-solid ${icon}"></i></div>
      <div class="bubble-content">${bubbleContent}</div>
    `;
    chatMessages.appendChild(div);
    scrollChat();
    return div;
  }

  function escapeHtml(text) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(text));
    return d.innerHTML;
  }

  async function sendChatMessage(message) {
    if (!message.trim()) return;
    chatInput.value = '';
    chatSendBtn.disabled = true;

    appendBubble('user', message);
    const typingEl = appendBubble('bot', '', true);

    try {
      const result = await postAPI('/api/chat', { message });
      chatMessages.removeChild(typingEl);
      appendBubble('bot', result.response);
    } catch (err) {
      chatMessages.removeChild(typingEl);
      appendBubble('bot', `⚠️ Error: ${err.message}`);
    } finally {
      chatSendBtn.disabled = false;
      chatInput.focus();
    }
  }

  chatSendBtn.addEventListener('click', () => sendChatMessage(chatInput.value));
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage(chatInput.value);
    }
  });

  // Quick prompts
  document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      sendChatMessage(btn.dataset.msg);
      document.getElementById('quickPrompts').style.display = 'none';
    });
  });

  // Clear chat
  document.getElementById('clearChatBtn').addEventListener('click', async () => {
    await fetch('/api/clear-chat', { method: 'POST' });
    chatMessages.innerHTML = '';
    document.getElementById('quickPrompts').style.display = 'flex';
    appendBubble('bot', '✅ Chat cleared. How can I help you with real estate today?');
  });

  // ============================================================
  //  NAVBAR ACTIVE STATE ON SCROLL
  // ============================================================
  const sections = ['predict-section', 'emi-section', 'areas-section', 'chat-section'];
  const navLinks = document.querySelectorAll('.nav-link');

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link => link.classList.remove('active'));
        const target = document.querySelector(`.nav-link[href="#${entry.target.id}"]`);
        if (target) target.classList.add('active');
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el);
  });

  // ============================================================
  //  SCROLL REVEAL ANIMATION
  // ============================================================
  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animation = 'slideInUp 0.5s ease forwards';
        entry.target.style.opacity = '1';
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.feature-card, .glass-card, .section-header').forEach(el => {
    el.style.opacity = '0';
    revealObserver.observe(el);
  });
});

// ============================================================
//  EMI PIE CHART (Pure Canvas — No external lib)
// ============================================================
function drawEMIPieChart(principal, interest) {
  const canvas = document.getElementById('emiPieChart');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const total = principal + interest;
  const pRatio = principal / total;
  const iRatio = interest / total;

  const cx = W / 2, cy = H / 2, r = Math.min(W, H) / 2 - 12;
  const pColor = '#2563eb';
  const iColor = '#dc2626';

  // Principal slice
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + pRatio * Math.PI * 2);
  ctx.closePath();
  ctx.fillStyle = pColor;
  ctx.fill();

  // Interest slice
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, r, -Math.PI / 2 + pRatio * Math.PI * 2, -Math.PI / 2 + Math.PI * 2);
  ctx.closePath();
  ctx.fillStyle = iColor;
  ctx.fill();

  // Center hole (donut)
  ctx.beginPath();
  ctx.arc(cx, cy, r * 0.52, 0, Math.PI * 2);
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--surface').trim() || '#fff';
  ctx.fill();

  // Center text
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text').trim() || '#222';
  ctx.font = `bold 11px Segoe UI`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('Breakup', cx, cy - 7);
  ctx.font = `10px Segoe UI`;
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#888';
  ctx.fillText(`${(iRatio * 100).toFixed(0)}% interest`, cx, cy + 9);

  // Legend
  const legendEl = document.getElementById('emiChartLegend');
  legendEl.innerHTML = `
    <div class="legend-item"><div class="legend-dot" style="background:${pColor}"></div>Principal (${(pRatio * 100).toFixed(1)}%)</div>
    <div class="legend-item"><div class="legend-dot" style="background:${iColor}"></div>Interest (${(iRatio * 100).toFixed(1)}%)</div>
  `;
}
