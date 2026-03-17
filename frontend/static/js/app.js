/**
 * ClimAlert Valencia — Frontend JS
 * Notificaciones en tiempo real, toasts, campana, renderizado LLM
 */

// ═══════════════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss flash messages
    document.querySelectorAll('.fl-msg').forEach(el => {
        setTimeout(() => {
            el.style.transition = 'opacity .3s, transform .3s';
            el.style.opacity = '0';
            el.style.transform = 'translateY(-6px)';
            setTimeout(() => el.remove(), 300);
        }, 5000);
    });

    // Start notification polling if logged in
    if (document.getElementById('notifWrap')) {
        initNotifications();
    }
});

// ═══════════════════════════════════════════════════════════════════════
// 🔔 NOTIFICATION SYSTEM
// ═══════════════════════════════════════════════════════════════════════

let knownIds = new Set();
let isFirstPoll = true;

function initNotifications() {
    // Seed known IDs from existing banners on page
    document.querySelectorAll('[data-id]').forEach(el => {
        knownIds.add(parseInt(el.dataset.id));
    });

    // First poll (no toasts)
    pollAlertas();

    // Poll every 15 seconds
    setInterval(pollAlertas, 15000);
}

async function pollAlertas() {
    try {
        const r = await fetch('/api/alertas');
        if (!r.ok) return;
        const alertas = await r.json();

        // Update notification panel
        renderNotifPanel(alertas);

        // Update tab title
        const base = 'ClimAlert Valencia';
        document.title = alertas.length > 0
            ? `(${alertas.length}) ${base}` : base;

        // Show toasts for NEW alerts (skip first poll)
        if (!isFirstPoll) {
            for (const a of alertas) {
                if (!knownIds.has(a.id)) {
                    showToast(a);
                    addBannerLive(a);
                    playAlertSound(a.nivel);
                }
            }
        }

        // Update known IDs
        knownIds = new Set(alertas.map(a => a.id));
        isFirstPoll = false;
    } catch (e) {
        // Silent fail — network might be down
    }
}

// ── Notification Panel (bell dropdown) ───────────────────────────────

function toggleNotif() {
    const panel = document.getElementById('notifPanel');
    const btn = document.querySelector('.notif-bell');
    if (!panel) return;
    const open = panel.classList.toggle('open');
    btn?.setAttribute('aria-expanded', open);
}

// Close on outside click
document.addEventListener('click', (e) => {
    const wrap = document.getElementById('notifWrap');
    const panel = document.getElementById('notifPanel');
    if (wrap && panel && !wrap.contains(e.target)) {
        panel.classList.remove('open');
        document.querySelector('.notif-bell')?.setAttribute('aria-expanded', 'false');
    }
});

function renderNotifPanel(alertas) {
    const list = document.getElementById('notifList');
    const headCount = document.getElementById('notifHeadCount');
    const dot = document.getElementById('notifDot');
    const badge = document.getElementById('notifBadge');
    if (!list) return;

    headCount.textContent = `${alertas.length} activa${alertas.length !== 1 ? 's' : ''}`;

    if (alertas.length === 0) {
        list.innerHTML = '<div class="notif-empty">Sin alertas activas</div>';
        dot?.classList.add('hidden');
        badge?.classList.add('hidden');
        return;
    }

    // Show dot and badge
    dot?.classList.remove('hidden');
    if (badge) {
        badge.classList.remove('hidden');
        badge.textContent = alertas.length;
    }

    list.innerHTML = alertas.map(a => {
        const d = new Date(a.created_at);
        const t = d.toLocaleString('es-ES', {
            day: '2-digit', month: '2-digit',
            hour: '2-digit', minute: '2-digit'
        });
        return `
            <div class="notif-item" role="listitem">
                <div class="notif-item-head">
                    <span class="notif-level-dot nd-${a.nivel}"></span>
                    <span class="notif-item-title">${esc(a.titulo)}</span>
                </div>
                <div class="notif-item-desc">${esc(a.descripcion)}</div>
                <div class="notif-item-meta">${esc(a.zona)} · ${t}</div>
            </div>`;
    }).join('');
}

// ── Toast Notifications ──────────────────────────────────────────────

function showToast(alerta) {
    const c = document.getElementById('toastContainer');
    if (!c) return;

    const icons = { roja: '🔴', naranja: '🟠', amarilla: '🟡' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${alerta.nivel}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <button class="toast-x" onclick="this.parentElement.remove()" aria-label="Cerrar">&times;</button>
        <div class="toast-body">
            <span class="toast-ico">${icons[alerta.nivel] || '⚠'}</span>
            <div>
                <strong>${esc(alerta.titulo)}</strong>
                <p>${esc(alerta.zona || 'Valencia')}</p>
            </div>
        </div>
    `;
    c.appendChild(toast);

    // Auto-remove after 10s
    setTimeout(() => {
        toast.style.transition = 'opacity .3s, transform .3s';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(30px)';
        setTimeout(() => toast.remove(), 300);
    }, 10000);
}

// ── Live Banner Injection ────────────────────────────────────────────

function addBannerLive(a) {
    const container = document.getElementById('alertBanners');
    if (!container) return;

    const icons = { roja: '🔴', naranja: '🟠', amarilla: '🟡' };
    const div = document.createElement('div');
    div.className = `alert-banner ab-${a.nivel}`;
    div.setAttribute('role', 'alert');
    div.dataset.id = a.id;
    div.innerHTML = `
        <span class="ab-icon">${icons[a.nivel] || '⚠'}</span>
        <div>
            <h3>${esc(a.titulo)}</h3>
            <p>${esc(a.descripcion)}</p>
            <span class="ab-meta">${esc(a.zona)} · Ahora</span>
        </div>`;
    container.prepend(div);
}

// ── Alert Sound ──────────────────────────────────────────────────────

function playAlertSound(nivel) {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const freqs = { roja: [880, 660], naranja: [660, 520], amarilla: [440] };
        const tones = freqs[nivel] || [440];
        tones.forEach((freq, i) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.08, ctx.currentTime + i * 0.15);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.15 + 0.25);
            osc.start(ctx.currentTime + i * 0.15);
            osc.stop(ctx.currentTime + i * 0.15 + 0.25);
        });
    } catch (e) { /* no audio support */ }
}

// ═══════════════════════════════════════════════════════════════════════
// TABS
// ═══════════════════════════════════════════════════════════════════════

function switchTab(name) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('on'));
    document.querySelectorAll('.tab-c').forEach(t => t.classList.remove('on'));
    event.currentTarget.classList.add('on');
    const el = document.getElementById('tab-' + name);
    if (el) el.classList.add('on');
}

// ═══════════════════════════════════════════════════════════════════════
// WEATHER GRID RENDERER
// ═══════════════════════════════════════════════════════════════════════

function renderWeather(data, gridId) {
    const grid = document.getElementById(gridId);
    if (!grid || !data || data.error) return;

    const items = [];
    function flatten(obj, prefix) {
        for (const [k, v] of Object.entries(obj)) {
            const label = prefix ? `${prefix} › ${k}` : k;
            if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
                flatten(v, label);
            } else {
                items.push({ label: label.replace(/_/g, ' '), value: v });
            }
        }
    }
    flatten(data, '');
    grid.innerHTML = items.map(i => `
        <div class="wi">
            <div class="wi-l">${esc(String(i.label))}</div>
            <div class="wi-v">${esc(String(i.value))}</div>
        </div>
    `).join('');
}

// ═══════════════════════════════════════════════════════════════════════
// LLM RESPONSE RENDERER (basic markdown → HTML)
// ═══════════════════════════════════════════════════════════════════════

function renderLLM(text) {
    if (!text) return '<span class="tm">Sin respuesta.</span>';
    let html = esc(text);
    // Bold: **text** or __text__
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
    // Numbered lists
    html = html.replace(/^(\d+)\.\s+(.+)$/gm, '<div class="llm-step"><span class="llm-num">$1.</span> $2</div>');
    // Bullet points
    html = html.replace(/^[-•]\s+(.+)$/gm, '<div class="llm-bullet">• $1</div>');
    // Level badges
    html = html.replace(/\b(MUY ALTO|ALTO|MODERADO|BAJO)\b/g, (m) => {
        const cls = { 'MUY ALTO': 'nv-r', 'ALTO': 'nv-o', 'MODERADO': 'nv-y', 'BAJO': 'nv-g' }[m] || '';
        return `<span class="nv ${cls}">${m}</span>`;
    });
    // Phone numbers
    html = html.replace(/\b(112|085)\b/g, '<a href="tel:$1" class="llm-phone">$1</a>');
    // Paragraphs (double newlines)
    html = html.replace(/\n\n/g, '</p><p>');
    // Single newlines
    html = html.replace(/\n/g, '<br>');
    return `<p>${html}</p>`;
}

// ═══════════════════════════════════════════════════════════════════════
// UTILITIES
// ═══════════════════════════════════════════════════════════════════════

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}
