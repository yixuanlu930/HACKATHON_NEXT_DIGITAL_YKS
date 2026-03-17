/* ClimAlert Valencia — Frontend JS */

// Flash auto-dismiss
document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => { el.style.opacity='0'; setTimeout(()=>el.remove(),300); }, 5000);
});

// ── Notification bell ────────────────────────────
let known = new Set();
let first = true;
document.querySelectorAll('[data-id]').forEach(el => known.add(+el.dataset.id));

function toggleNotif() {
    document.getElementById('notifPanel')?.classList.toggle('open');
}
document.addEventListener('click', e => {
    const w = document.getElementById('notifWrap');
    if (w && !w.contains(e.target)) document.getElementById('notifPanel')?.classList.remove('open');
});

async function poll() {
    try {
        const r = await fetch('/api/alertas-poll');
        if (!r.ok) return;
        const alertas = await r.json();
        const list = document.getElementById('notifList');
        const dot = document.getElementById('notifDot');
        const cnt = document.getElementById('notifCount');
        if (cnt) cnt.textContent = alertas.length;

        if (!alertas.length) {
            if (list) list.innerHTML = '<div class="notif-empty">Sin alertas</div>';
            dot?.classList.add('hidden');
            document.title = 'ClimAlert Valencia';
        } else {
            dot?.classList.remove('hidden');
            document.title = '(' + alertas.length + ') ClimAlert Valencia';
            if (list) list.innerHTML = alertas.map(a => {
                const ico = a.nivel==='rojo'?'🔴':a.nivel==='amarillo'?'🟡':'🟢';
                return '<div class="notif-item"><b>'+ico+' '+esc(a.titulo)+'</b><p class="ts tm">'+esc(a.mensaje)+'</p><small class="ts tm">'+esc(a.provincia||'Todas')+'</small></div>';
            }).join('');
        }
        if (!first) alertas.forEach(a => { if (!known.has(a.id)) toast(a); });
        known = new Set(alertas.map(a => a.id));
        first = false;
    } catch(e) {}
}

function toast(a) {
    const c = document.getElementById('toastContainer'); if (!c) return;
    const d = document.createElement('div');
    const ico = a.nivel==='rojo'?'🔴':a.nivel==='amarillo'?'🟡':'🟢';
    d.className = 'toast toast-'+a.nivel;
    d.innerHTML = '<b>'+ico+' '+esc(a.titulo)+'</b><p class="ts">'+esc(a.provincia||'Todas')+'</p>';
    d.onclick = () => d.remove();
    c.appendChild(d);
    try { const ctx=new(window.AudioContext||window.webkitAudioContext)();const o=ctx.createOscillator();const g=ctx.createGain();o.connect(g);g.connect(ctx.destination);o.frequency.value=a.nivel==='rojo'?880:660;g.gain.value=0.08;o.start();o.stop(ctx.currentTime+0.2); } catch(e){}
    setTimeout(() => { d.style.opacity='0'; setTimeout(()=>d.remove(),300); }, 8000);
}

function esc(s) { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }

// ── Tabs ─────────────────────────────────────────
function switchTab(name) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('on'));
    document.querySelectorAll('.tab-c').forEach(t => t.classList.remove('on'));
    event.currentTarget.classList.add('on');
    document.getElementById('tab-'+name)?.classList.add('on');
}

// Start polling
// ━━━ WEBSOCKET: ALERTAS EN TIEMPO REAL ━━━
let socket = null;
let wsConnected = false;

function initWebSocket() {
    try {
        socket = io({ transports: ['websocket', 'polling'] });

        socket.on('connect', () => {
            console.log('[WS] Conectado — alertas en tiempo real');
            wsConnected = true;
        });

        socket.on('disconnect', () => {
            console.log('[WS] Desconectado — volviendo a polling');
            wsConnected = false;
        });

        // ── Nueva alerta en tiempo real ──
        socket.on('nueva_alerta', (alerta) => {
            console.log('[WS] Nueva alerta recibida:', alerta);

            // Toast inmediato
            toast(alerta);

            // Añadir banner al DOM
            const banners = document.getElementById('alertBanners');
            if (banners) {
                const ico = alerta.nivel === 'rojo' ? '🔴' : alerta.nivel === 'amarillo' ? '🟡' : '🟢';
                const div = document.createElement('div');
                div.className = 'alert-ban ban-' + alerta.nivel;
                div.dataset.id = alerta.id;
                div.innerHTML = '<span>' + ico + '</span><div><h3>' + esc(alerta.titulo) + '</h3><p>' + esc(alerta.mensaje) + '</p><small>' + esc(alerta.provincia || 'Toda la comunidad') + '</small></div>';
                banners.prepend(div);
            }

            // Actualizar campana
            known.add(alerta.id);
            poll(); // refrescar lista de notificaciones
        });

        // ── Alerta desactivada en tiempo real ──
        socket.on('alerta_desactivada', (data) => {
            console.log('[WS] Alerta desactivada:', data.id);

            // Quitar banner del DOM
            const banner = document.querySelector('[data-id="' + data.id + '"]');
            if (banner) {
                banner.style.opacity = '0';
                setTimeout(() => banner.remove(), 300);
            }

            known.delete(data.id);
            poll(); // refrescar campana
        });

    } catch (e) {
        console.log('[WS] Error al conectar:', e);
    }
}

// Start: WebSocket + polling como fallback
if (document.getElementById('notifWrap')) {
    poll();
    initWebSocket();
    // Polling más lento como fallback (cada 30s en vez de 15s)
    setInterval(poll, wsConnected ? 60000 : 15000);
}

// ── Password visibility toggle ───────────────────
function showPw(id) { document.getElementById(id).type = 'text'; }
function hidePw(id) { document.getElementById(id).type = 'password'; }
