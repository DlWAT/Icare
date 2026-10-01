/* ============================================================================
 * Icare Web — frontend logic
 *
 * The script is dispatched from a single ``DOMContentLoaded`` listener that
 * inspects ``document.body.dataset.page`` (one of "home", "direct",
 * "sequence", "live"). Each page module lives in its own ``bind*`` function
 * below so they don't collide.
 * ============================================================================ */
'use strict';

/* ---------- Tiny HTTP helpers ---------- */

async function postJSON(url, data = {}) {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return await res.json();
  } catch (err) {
    console.error('POST', url, err);
    return { ok: false, error: String(err) };
  }
}

async function getJSON(url) {
  try {
    const res = await fetch(url);
    return await res.json();
  } catch (err) {
    console.error('GET', url, err);
    return { ok: false, error: String(err) };
  }
}

/* ---------- Color helpers ---------- */

function hexToRgb(hex) {
  const m = hex.replace('#', '');
  return {
    r: parseInt(m.slice(0, 2), 16),
    g: parseInt(m.slice(2, 4), 16),
    b: parseInt(m.slice(4, 6), 16),
  };
}

function rgbToHex(r, g, b) {
  const h = (n) => Number(n).toString(16).padStart(2, '0');
  return `#${h(r)}${h(g)}${h(b)}`;
}

/* ---------- Toast notifications ---------- */

function toast(message, kind = 'info', durationMs = 2500) {
  const stack = document.getElementById('toast-stack');
  if (!stack) return;
  const el = document.createElement('div');
  el.className = `toast ${kind}`;
  el.textContent = message;
  stack.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateY(8px)'; }, durationMs - 250);
  setTimeout(() => el.remove(), durationMs);
}

/* ---------- Theme toggle ---------- */

function bindTheme() {
  const btn = document.getElementById('btn-theme-toggle');
  const icon = document.getElementById('theme-icon');
  if (!btn) return;

  const apply = (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    if (icon) icon.textContent = theme === 'dark' ? '🌙' : '☀️';
  };

  btn.addEventListener('click', async () => {
    const cur = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = cur === 'dark' ? 'light' : 'dark';
    apply(next);
    await postJSON('/api/settings', { theme: next });
  });
}

/* ---------- Health pill ---------- */

function bindHealthPolling() {
  const pill = document.getElementById('dmx-status');
  if (!pill) return;
  const label = pill.querySelector('.status-label');

  async function tick() {
    const r = await getJSON('/api/health');
    if (!r.ok) {
      pill.classList.remove('ok'); pill.classList.add('error');
      if (label) label.textContent = 'DMX HS';
    } else if (r.dmx?.connected) {
      pill.classList.add('ok'); pill.classList.remove('error', 'idle');
      if (label) label.textContent = 'DMX OK';
      pill.title = 'DMX connecté';
    } else {
      pill.classList.remove('ok', 'error'); pill.classList.add('idle');
      if (label) label.textContent = 'DMX OFF';
      pill.title = r.dmx?.lastError ? `Erreur: ${r.dmx.lastError}` : 'DMX non connecté';
    }
    setTimeout(tick, 3000);
  }
  tick();
}

/* ============================================================================
 * Direct page (Experiment)
 * ============================================================================ */

function $val(id) { return Number(document.getElementById(id)?.value || 0); }

function updatePreview() {
  const r = $val('range-r'), g = $val('range-g'), b = $val('range-b');
  const hex = rgbToHex(r, g, b);
  const prev = document.getElementById('color-preview');
  if (prev) prev.style.background = hex;
  ['r', 'g', 'b', 'amp', 'pan', 'tilt'].forEach((k) => {
    const span = document.getElementById('val-' + k);
    if (span) span.textContent = $val('range-' + k);
  });
}

async function sendValues() {
  const r = $val('range-r'), g = $val('range-g'), b = $val('range-b');
  const amp = $val('range-amp'), pan = $val('range-pan'), tilt = $val('range-tilt');
  await postJSON('/api/experiment/set-values', { r, g, b, amp, pan, tilt });
}

function bindExperiment() {
  // Slider bindings
  const sliderIds = ['range-r', 'range-g', 'range-b', 'range-amp', 'range-pan', 'range-tilt'];
  for (const id of sliderIds) {
    const el = document.getElementById(id);
    if (!el) continue;
    el.addEventListener('input', () => { updatePreview(); sendValues(); updateDirect3DFromControls(); });
  }
  const colorPicker = document.getElementById('color-picker');
  if (colorPicker) {
    colorPicker.addEventListener('input', () => {
      const { r, g, b } = hexToRgb(colorPicker.value);
      document.getElementById('range-r').value = r;
      document.getElementById('range-g').value = g;
      document.getElementById('range-b').value = b;
      updatePreview(); sendValues(); updateDirect3DFromControls();
    });
  }

  // Connection
  document.getElementById('btn-connect')?.addEventListener('click', async () => {
    const baseChannel = $val('input-conn-channel') || 9;
    const port = document.getElementById('input-conn-port')?.value.trim() || null;
    const r = await postJSON('/api/experiment/connect', { baseChannel, port });
    if (r.ok && r.connected) toast('DMX connecté', 'success');
    else toast(`Connexion échouée: ${r.error || '?'}`, 'error', 4000);
  });
  document.getElementById('btn-update-base')?.addEventListener('click', async () => {
    const baseChannel = $val('input-conn-channel') || 9;
    const r = await postJSON('/api/experiment/base-channel', { baseChannel });
    if (r.ok) toast(`Canal de base: ${r.baseChannel}`, 'success');
    else toast(r.error || 'Erreur', 'error');
  });

  // Transport
  document.getElementById('btn-blackout')?.addEventListener('click', () => postJSON('/api/experiment/blackout'));
  document.getElementById('btn-stop')?.addEventListener('click', () => postJSON('/api/experiment/stop'));

  // Random
  const randFreq = document.getElementById('input-rand-freq');
  const randSmooth = document.getElementById('input-rand-smooth');
  const randBright = document.getElementById('input-rand-bright');
  function sendRandomConfig() {
    if (!randFreq || !randSmooth || !randBright) return;
    postJSON('/api/experiment/mode/random-config', {
      freqHz: Number(randFreq.value || 1),
      smooth: Number(randSmooth.value || 0) / 100,
      brightness: Number(randBright.value || 128),
    });
  }
  randFreq?.addEventListener('input', sendRandomConfig);
  randSmooth?.addEventListener('input', sendRandomConfig);
  randBright?.addEventListener('input', sendRandomConfig);
  document.getElementById('btn-rand-start')?.addEventListener('click', () => {
    sendRandomConfig();
    postJSON('/api/experiment/random-start');
  });
  document.getElementById('btn-rand-stop')?.addEventListener('click', () => postJSON('/api/experiment/random-stop'));

  // Strobe overlay
  document.getElementById('btn-strobe-overlay')?.addEventListener('click', () => {
    postJSON('/api/experiment/mode/strobe-overlay', {
      freqHz: $val('input-ov-freq') || 10,
      duty: ($val('input-ov-duty') || 50) / 100,
      durationSec: $val('input-ov-duration') || 5,
      channel: $val('input-ov-channel') || 0,
    });
  });

  // Effects library
  document.querySelectorAll('.btn-effect').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const name = btn.dataset.effect;
      const r = await postJSON('/api/experiment/effect/start', {
        name,
        speed: Number(document.getElementById('input-fx-speed')?.value || 1),
        brightness: Number(document.getElementById('input-fx-bright')?.value || 200),
      });
      if (r.ok) {
        document.querySelectorAll('.btn-effect').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
      }
    });
  });
  document.getElementById('btn-fx-stop')?.addEventListener('click', async () => {
    await postJSON('/api/experiment/effect/stop');
    document.querySelectorAll('.btn-effect').forEach((b) => b.classList.remove('active'));
  });

  // Favourites
  bindFavourites();

  // Audio-reactive
  bindAudioReactive();

  // 3D + 3D-tied controls
  ['direct-angle', 'direct-x', 'direct-z', 'direct-y'].forEach((id) => {
    document.getElementById(id)?.addEventListener('input', updateDirect3DFromControls);
  });
  setupDirect3D();
  updateDirect3DFromControls();
  updatePreview();

  // Status polling — keep server-side state mirrored on the UI
  pollExperimentStatus();
}

async function pollExperimentStatus() {
  const r = await getJSON('/api/experiment/status');
  if (r.ok) {
    const s = r.state;
    window.__overlay = s.overlay || null;
    // Sync RGB sliders if changed server-side (random / effect / audio modes)
    [['range-r', s.r], ['range-g', s.g], ['range-b', s.b], ['range-amp', s.amp]].forEach(([id, v]) => {
      const el = document.getElementById(id);
      if (el && Number(el.value) !== v) el.value = v;
    });
    // Random config reflection
    if (s.random) {
      const f = document.getElementById('input-rand-freq');
      const sm = document.getElementById('input-rand-smooth');
      const br = document.getElementById('input-rand-bright');
      if (f && document.activeElement !== f) f.value = String(s.random.freq_hz ?? 1);
      if (sm && document.activeElement !== sm) sm.value = String(Math.round(100 * (s.random.smooth ?? 0)));
      if (br && document.activeElement !== br) br.value = String(s.random.brightness ?? 128);
    }
    updatePreview();
    updateDirect3DFromControls();
  }
  setTimeout(pollExperimentStatus, 200);
}

/* ---------- Favourite colours ---------- */

async function bindFavourites() {
  const box = document.getElementById('favorite-colors');
  if (!box) return;

  async function refresh() {
    const r = await getJSON('/api/palettes/favorites');
    box.innerHTML = '';
    (r.colors || []).forEach((color) => {
      const sw = document.createElement('div');
      sw.className = 'swatch';
      sw.style.background = color;
      sw.title = color;
      sw.addEventListener('click', () => {
        const { r: cr, g: cg, b: cb } = hexToRgb(color);
        document.getElementById('range-r').value = cr;
        document.getElementById('range-g').value = cg;
        document.getElementById('range-b').value = cb;
        document.getElementById('color-picker').value = color;
        updatePreview(); sendValues(); updateDirect3DFromControls();
      });
      const x = document.createElement('div');
      x.className = 'swatch-x'; x.textContent = '×';
      x.addEventListener('click', async (e) => {
        e.stopPropagation();
        await postJSON('/api/palettes/favorites/remove', { color });
        refresh();
      });
      sw.appendChild(x);
      box.appendChild(sw);
    });
  }

  document.getElementById('btn-fav-add')?.addEventListener('click', async () => {
    const color = document.getElementById('color-picker')?.value || rgbToHex($val('range-r'), $val('range-g'), $val('range-b'));
    const r = await postJSON('/api/palettes/favorites/add', { color });
    if (r.ok) { toast(`Couleur ajoutée: ${color}`, 'success', 1200); refresh(); }
  });

  refresh();
}

/* ---------- Audio-reactive (Web Audio API) ---------- */

function bindAudioReactive() {
  const startBtn = document.getElementById('btn-audio-start');
  const stopBtn = document.getElementById('btn-audio-stop');
  const meter = document.getElementById('audio-level-bar');
  const gainEl = document.getElementById('input-audio-gain');
  const colorEl = document.getElementById('audio-color');
  if (!startBtn) return;

  let audioCtx = null;
  let mediaStream = null;
  let analyser = null;
  let rafId = null;
  let running = false;
  let lastSent = 0;

  async function start() {
    if (running) return;
    if (!navigator.mediaDevices?.getUserMedia) {
      toast('API micro non disponible', 'error');
      return;
    }
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false } });
    } catch (err) {
      toast('Accès micro refusé', 'error');
      return;
    }
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(mediaStream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 1024;
    analyser.smoothingTimeConstant = 0.4;
    source.connect(analyser);
    await postJSON('/api/experiment/audio/start');
    running = true;
    loop();
    toast('Audio-réactif activé', 'success');
  }

  function loop() {
    if (!running) return;
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteTimeDomainData(data);
    // RMS
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      const v = (data[i] - 128) / 128;
      sum += v * v;
    }
    const rms = Math.sqrt(sum / data.length);
    const gain = Number(gainEl?.value || 2);
    const level = Math.max(0, Math.min(1, rms * gain));
    if (meter) meter.style.width = `${(level * 100).toFixed(1)}%`;

    // Throttle to ~30 Hz
    const now = performance.now();
    if (now - lastSent > 33) {
      lastSent = now;
      postJSON('/api/experiment/audio/push', { level, color: colorEl?.value });
    }
    rafId = requestAnimationFrame(loop);
  }

  async function stop() {
    running = false;
    if (rafId) cancelAnimationFrame(rafId);
    if (mediaStream) mediaStream.getTracks().forEach((t) => t.stop());
    if (audioCtx) try { await audioCtx.close(); } catch {}
    audioCtx = null; mediaStream = null; analyser = null;
    if (meter) meter.style.width = '0%';
    await postJSON('/api/experiment/audio/stop');
  }

  startBtn.addEventListener('click', start);
  stopBtn?.addEventListener('click', stop);
}

/* ============================================================================
 * Direct page — Three.js scene
 * ============================================================================ */

function setupDirect3D() {
  const container = document.getElementById('direct3d');
  if (!container) return;
  if (typeof THREE === 'undefined') {
    container.innerHTML = '<div style="color:#bbb;padding:12px;">Three.js non disponible.</div>';
    return;
  }

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0d0f12);
  const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.set(7, 6, 10);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  container.innerHTML = '';
  container.appendChild(renderer.domElement);

  const stage = new THREE.Mesh(
    new THREE.PlaneGeometry(14, 7),
    new THREE.MeshStandardMaterial({ color: 0x22252a, side: THREE.DoubleSide, roughness: 1 }),
  );
  stage.rotation.x = -Math.PI / 2;
  scene.add(stage);

  scene.add(new THREE.AmbientLight(0x202020, 0.8));
  scene.add(new THREE.HemisphereLight(0x222222, 0x111111, 0.6));

  const spot = new THREE.SpotLight(0xffffff, 1.5);
  spot.position.set(0, 4, 0);
  spot.angle = THREE.MathUtils.degToRad(45);
  spot.penumbra = 0.3; spot.decay = 2; spot.distance = 25;
  scene.add(spot);

  const targetObj = new THREE.Object3D();
  scene.add(targetObj);
  spot.target = targetObj;

  const height = 4.0;
  const radius = Math.tan(THREE.MathUtils.degToRad(22.5)) * height;
  const beam = new THREE.Mesh(
    new THREE.ConeGeometry(radius, height, 64, 1, true),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.12, depthWrite: false, blending: THREE.AdditiveBlending }),
  );
  beam.position.copy(spot.position);
  scene.add(beam);

  const fixture = new THREE.Mesh(
    new THREE.BoxGeometry(0.5, 0.35, 0.5),
    new THREE.MeshStandardMaterial({ color: 0x2b2f37, roughness: 0.8, metalness: 0.2 }),
  );
  fixture.position.copy(spot.position);
  scene.add(fixture);

  function onResize() {
    const w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', onResize);

  const defaultOpacity = 0.12;
  function animate() {
    requestAnimationFrame(animate);
    const ov = window.__overlay;
    if (ov?.active && typeof ov.freq_hz === 'number') {
      const t = performance.now() / 1000;
      const phase = (t * Math.max(0.1, ov.freq_hz)) % 1.0;
      const on = phase < Math.max(0.0, Math.min(1.0, ov.duty || 0.5));
      beam.material.opacity = on ? defaultOpacity : defaultOpacity * 0.08;
    } else {
      beam.material.opacity = defaultOpacity;
    }
    renderer.render(scene, camera);
  }
  animate();

  window.__direct3d = { scene, camera, renderer, stage, spot, beam, fixture, targetObj };
}

function updateDirect3DFromControls() {
  const ctx = window.__direct3d;
  if (!ctx || typeof THREE === 'undefined') return;
  const r = $val('range-r'), g = $val('range-g'), b = $val('range-b');
  const amp = $val('range-amp'), pan = $val('range-pan'), tilt = $val('range-tilt');
  const deg = Number(document.getElementById('direct-angle')?.value || 45);
  const lx = Number(document.getElementById('direct-x')?.value || 0);
  const lz = Number(document.getElementById('direct-z')?.value || 0);
  const ly = Number(document.getElementById('direct-y')?.value || 4);

  const color = new THREE.Color(r / 255, g / 255, b / 255);
  ctx.spot.color = color;
  ctx.beam.material.color = color;
  ctx.beam.material.needsUpdate = true;
  ctx.spot.intensity = 0.5 + (amp / 255) * 2.0;

  ctx.spot.position.set(lx, ly, lz);

  const angleRad = THREE.MathUtils.degToRad(deg);
  ctx.spot.angle = angleRad;
  const radius = Math.tan(angleRad / 2) * ly;
  ctx.beam.geometry.dispose();
  ctx.beam.geometry = new THREE.ConeGeometry(radius, ly, 64, 1, true);
  ctx.beam.position.set(lx, ly / 2, lz);
  ctx.beam.rotation.x = Math.PI;

  const yaw = THREE.MathUtils.degToRad((pan / 255) * 180 - 90);
  const pitch = THREE.MathUtils.degToRad((tilt / 255) * 90);
  const tpos = new THREE.Vector3(
    lx + Math.sin(yaw) * Math.cos(pitch) * 5,
    Math.max(0, ly - Math.sin(pitch) * 5),
    lz + Math.cos(yaw) * Math.cos(pitch) * 5,
  );
  ctx.targetObj.position.copy(tpos);
  ctx.spot.target = ctx.targetObj;
  ctx.beam.lookAt(tpos);
  ctx.fixture.position.set(lx, ly, lz);
  ctx.fixture.lookAt(tpos);
}

/* ============================================================================
 * Sequence page
 * ============================================================================ */

function seqRenderTable(header, rows) {
  const tbl = document.getElementById('seq-table');
  if (!tbl) return;
  tbl.innerHTML = '';
  const thead = document.createElement('thead');
  const trh = document.createElement('tr');
  header.forEach((h) => {
    const th = document.createElement('th');
    th.textContent = h;
    trh.appendChild(th);
  });
  thead.appendChild(trh);
  tbl.appendChild(thead);
  const tbody = document.createElement('tbody');
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    header.forEach((_, colIdx) => {
      const td = document.createElement('td');
      td.contentEditable = colIdx >= 2;
      td.textContent = row[colIdx] ?? '';
      td.addEventListener('input', () => { row[colIdx] = td.textContent; });
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
}

async function bindSequence() {
  const moduleSelect = document.getElementById('seq-module-select');
  let currentHeader = ['Line', 'Structure', 'ParLED1', 'ParLED2', 'ParLED3', 'ParLED4', 'ParLED5', 'ParLED6', 'ParLED7', 'ParLED8', 'ParLED9', 'Strobe1', 'Strobe2'];
  let currentRows = [
    ['1', 'Intro_x4', '', '', '', '', '', '', '', '', '', '', ''],
    ['2', 'Intro_x4', '', '', '', '', '', '', '', '', '', '', ''],
  ];

  function refreshModuleSelect(modules) {
    moduleSelect.innerHTML = '';
    modules.forEach((m) => {
      const opt = document.createElement('option');
      opt.value = m; opt.textContent = m;
      moduleSelect.appendChild(opt);
    });
  }

  seqRenderTable(currentHeader, currentRows);
  refreshModuleSelect(currentHeader.slice(2));

  // Files list
  async function refreshFiles() {
    const r = await getJSON('/api/sequence/list');
    const ul = document.getElementById('seq-file-list');
    ul.innerHTML = '';
    (r.files || []).forEach((name) => {
      const li = document.createElement('li');
      const span = document.createElement('span');
      span.textContent = name;
      li.appendChild(span);
      const loadBtn = document.createElement('button');
      loadBtn.textContent = 'Charger'; loadBtn.className = 'btn-small';
      loadBtn.addEventListener('click', async () => {
        const res = await getJSON(`/api/sequence/load?name=${encodeURIComponent(name)}`);
        if (!res.ok) { toast(res.error || 'Erreur de chargement', 'error'); return; }
        currentHeader = ['Line', 'Structure', ...res.data.Header.Modules];
        currentRows = Object.keys(res.data.data)
          .sort((a, b) => Number(a) - Number(b))
          .map((k) => [k, res.data.data[k].section, ...res.data.data[k].function]);
        seqRenderTable(currentHeader, currentRows);
        refreshModuleSelect(res.data.Header.Modules);
        document.getElementById('seq-save-name').value = name.replace(/\.json$/i, '');
        toast(`${name} chargé`, 'success');
      });
      const delBtn = document.createElement('button');
      delBtn.textContent = '×'; delBtn.className = 'btn-small btn-danger';
      delBtn.addEventListener('click', async () => {
        if (!confirm(`Supprimer ${name} ?`)) return;
        const r = await postJSON('/api/sequence/delete', { name });
        if (r.ok) { toast('Supprimé', 'success'); refreshFiles(); }
        else toast(r.error || 'Erreur', 'error');
      });
      li.appendChild(loadBtn); li.appendChild(delBtn);
      ul.appendChild(li);
    });
  }
  refreshFiles();

  // Effect insertion helpers
  function insertAt(rowIdx, col, tokens) {
    for (let i = 0; i < tokens.length; i++) {
      if (!currentRows[rowIdx + i]) {
        currentRows[rowIdx + i] = [String(rowIdx + i + 1), '', ...new Array(currentHeader.length - 2).fill('')];
      }
      currentRows[rowIdx + i][col] = tokens[i];
    }
    seqRenderTable(currentHeader, currentRows);
  }

  document.getElementById('btn-seq-add-row').addEventListener('click', () => {
    const lastNum = currentRows.length ? Number(currentRows[currentRows.length - 1][0]) : 0;
    currentRows.push([String(lastNum + 1), 'New', ...new Array(currentHeader.length - 2).fill('')]);
    seqRenderTable(currentHeader, currentRows);
  });

  document.getElementById('btn-seq-uni').addEventListener('click', () => {
    const col = currentHeader.indexOf(moduleSelect.value);
    if (col < 0) return;
    const row = ($val('seq-line') || 1) - 1;
    const n = $val('seq-tps') || 1;
    const { r, g, b } = hexToRgb(document.getElementById('seq-color-1').value);
    const tokens = Array.from({ length: n }, (_, i) => i === 0 ? `uni_${n}_${r}_${g}_${b}` : '|');
    insertAt(row, col, tokens);
  });

  document.getElementById('btn-seq-fondu').addEventListener('click', () => {
    const col = currentHeader.indexOf(moduleSelect.value);
    if (col < 0) return;
    const row = ($val('seq-line') || 1) - 1;
    const n = $val('seq-tps') || 1;
    const a = hexToRgb(document.getElementById('seq-color-1').value);
    const b = hexToRgb(document.getElementById('seq-color-2').value);
    const tokens = Array.from({ length: n }, (_, i) =>
      i === 0 ? `fond_${n}_${a.r}_${a.g}_${a.b}_${b.r}_${b.g}_${b.b}` : '|',
    );
    insertAt(row, col, tokens);
  });

  document.getElementById('btn-seq-strobe').addEventListener('click', () => {
    const col = currentHeader.indexOf(moduleSelect.value);
    if (col < 0) return;
    const row = ($val('seq-line') || 1) - 1;
    const n = $val('seq-tps') || 1;
    const freq = $val('seq-freq') || 60;
    const { r, g, b } = hexToRgb(document.getElementById('seq-color-1').value);
    const tokens = Array.from({ length: n }, (_, i) => i === 0 ? `str_${n}_${r}_${g}_${b}_${freq}` : '|');
    insertAt(row, col, tokens);
  });

  document.getElementById('btn-seq-clear-cell').addEventListener('click', () => {
    const col = currentHeader.indexOf(moduleSelect.value);
    if (col < 0) return;
    const row = ($val('seq-line') || 1) - 1;
    const n = $val('seq-tps') || 1;
    insertAt(row, col, new Array(n).fill(''));
  });

  document.getElementById('btn-seq-save').addEventListener('click', async () => {
    const name = document.getElementById('seq-save-name').value.trim();
    if (!name) { toast('Nom de fichier requis', 'error'); return; }
    const header = {
      Structure: currentRows.map((r) => r[1]),
      Tempo: '60',
      Modules: currentHeader.slice(2),
      Line: currentRows.map((r) => r[0]),
    };
    const data = {};
    currentRows.forEach((r) => { data[r[0]] = { section: r[1], function: r.slice(2) }; });
    const res = await postJSON('/api/sequence/save', { name, data: { Header: header, data } });
    if (res.ok) { toast(`Sauvegardé: ${res.saved}`, 'success'); refreshFiles(); }
    else toast(res.error || 'Erreur de sauvegarde', 'error');
  });
}

/* ============================================================================
 * Live page
 * ============================================================================ */

async function bindLive() {
  // Files
  async function refreshFiles() {
    const r = await getJSON('/api/live/list');
    const ul = document.getElementById('live-file-list');
    ul.innerHTML = '';
    (r.files || []).forEach((name) => {
      const li = document.createElement('li');
      const span = document.createElement('span');
      span.textContent = name;
      li.appendChild(span);
      const btn = document.createElement('button');
      btn.textContent = 'Charger'; btn.className = 'btn-small';
      btn.addEventListener('click', async () => {
        const res = await postJSON('/api/live/load', { name });
        if (!res.ok) { toast(res.error || 'Erreur', 'error'); return; }
        document.querySelectorAll('#live-file-list li').forEach((x) => x.classList.remove('active'));
        li.classList.add('active');
        const mods = res.data.Header.Modules || [];
        const list = document.getElementById('live-modules');
        list.innerHTML = '';
        mods.forEach((m) => {
          const li2 = document.createElement('li');
          const cb = document.createElement('input');
          cb.type = 'checkbox';
          cb.id = `mod-${m}`;
          cb.addEventListener('change', () => postJSON('/api/live/toggle-module', { name: m }));
          const lab = document.createElement('label');
          lab.htmlFor = cb.id;
          lab.style.flexDirection = 'row';
          lab.style.alignItems = 'center';
          lab.style.gap = '8px';
          lab.appendChild(cb);
          const sp = document.createElement('span');
          sp.textContent = m;
          lab.appendChild(sp);
          li2.appendChild(lab);
          list.appendChild(li2);
        });
        toast(`${name} chargé (${mods.length} modules)`, 'success');
      });
      li.appendChild(btn);
      ul.appendChild(li);
    });
  }
  refreshFiles();

  // Module selection
  document.getElementById('btn-live-select-all').addEventListener('click', async () => {
    await postJSON('/api/live/select-all');
    document.querySelectorAll('#live-modules input[type="checkbox"]').forEach((cb) => { cb.checked = true; });
  });
  document.getElementById('btn-live-unselect-all').addEventListener('click', async () => {
    await postJSON('/api/live/unselect-all');
    document.querySelectorAll('#live-modules input[type="checkbox"]').forEach((cb) => { cb.checked = false; });
  });

  // Transport
  document.getElementById('btn-live-play').addEventListener('click', () => {
    const bpm = $val('live-bpm') || 60;
    postJSON('/api/live/play', { bpm });
  });
  document.getElementById('btn-live-pause').addEventListener('click', () => postJSON('/api/live/pause'));
  document.getElementById('btn-live-stop').addEventListener('click', () => postJSON('/api/live/stop'));
  document.getElementById('btn-live-prev').addEventListener('click', () => postJSON('/api/live/prev'));
  document.getElementById('btn-live-next').addEventListener('click', () => postJSON('/api/live/next'));

  // BPM input
  document.getElementById('live-bpm').addEventListener('change', (e) => {
    postJSON('/api/live/bpm', { bpm: Number(e.target.value) });
  });

  // Tap-tempo
  const tapBtn = document.getElementById('btn-tap');
  tapBtn?.addEventListener('click', async () => {
    tapBtn.classList.add('flash');
    setTimeout(() => tapBtn.classList.remove('flash'), 80);
    const r = await postJSON('/api/live/tap');
    if (r.ok && r.bpm) {
      const inp = document.getElementById('live-bpm');
      if (inp) inp.value = r.bpm;
      const v = document.getElementById('val-bpm');
      if (v) v.textContent = r.bpm;
    }
  });
  document.getElementById('btn-tap-reset')?.addEventListener('click', () => postJSON('/api/live/tap-reset'));

  // Status polling
  pollLiveStatus();

  // 3D
  setupLive3D();
}

async function pollLiveStatus() {
  const r = await getJSON('/api/live/status');
  if (r.ok) {
    const s = r.status;
    document.getElementById('live-progress-bar').style.width = `${s.progress}%`;
    document.getElementById('live-section').textContent = `Section: ${s.section ?? '-'}`;
    const counter = document.getElementById('live-counter');
    if (counter) counter.textContent = `${s.index} / ${s.total}`;
    const valBpm = document.getElementById('val-bpm');
    if (valBpm) valBpm.textContent = s.bpm;
    const inpBpm = document.getElementById('live-bpm');
    if (inpBpm && document.activeElement !== inpBpm) inpBpm.value = s.bpm;
    if (window.__live3d && s.rgb) {
      const c = new THREE.Color(s.rgb.r / 255, s.rgb.g / 255, s.rgb.b / 255);
      window.__live3d.spot.color = c;
      window.__live3d.beam.material.color = c;
      window.__live3d.beam.material.needsUpdate = true;
    }
  }
  setTimeout(pollLiveStatus, 250);
}

function setupLive3D() {
  const container = document.getElementById('live3d');
  if (!container || typeof THREE === 'undefined') return;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0d0f12);
  const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 100);
  camera.position.set(6, 5, 8);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  container.innerHTML = '';
  container.appendChild(renderer.domElement);

  const stage = new THREE.Mesh(
    new THREE.PlaneGeometry(12, 6),
    new THREE.MeshStandardMaterial({ color: 0x22252a, side: THREE.DoubleSide, roughness: 1 }),
  );
  stage.rotation.x = -Math.PI / 2;
  scene.add(stage);

  scene.add(new THREE.AmbientLight(0x202020, 0.8));
  scene.add(new THREE.HemisphereLight(0x222222, 0x111111, 0.6));

  const spot = new THREE.SpotLight(0xffffff, 1.5);
  spot.position.set(0, 4, 0);
  spot.angle = THREE.MathUtils.degToRad(45);
  spot.penumbra = 0.3; spot.decay = 2; spot.distance = 20;
  scene.add(spot);

  const targetObj = new THREE.Object3D();
  scene.add(targetObj);
  spot.target = targetObj;

  const height = 4.0;
  const radius = Math.tan(THREE.MathUtils.degToRad(22.5)) * height;
  const beam = new THREE.Mesh(
    new THREE.ConeGeometry(radius, height, 64, 1, true),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.12, depthWrite: false, blending: THREE.AdditiveBlending }),
  );
  beam.position.copy(spot.position);
  beam.rotation.x = Math.PI;
  beam.position.y -= height / 2;
  scene.add(beam);

  const fixture = new THREE.Mesh(
    new THREE.BoxGeometry(0.45, 0.30, 0.45),
    new THREE.MeshStandardMaterial({ color: 0x2b2f37, roughness: 0.8, metalness: 0.2 }),
  );
  fixture.position.copy(spot.position);
  fixture.position.y += 0.05;
  scene.add(fixture);

  function onResize() {
    const w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', onResize);

  function animate() {
    requestAnimationFrame(animate);
    if (window.__live3d?.fixture && window.__live3d?.targetObj) {
      window.__live3d.fixture.lookAt(window.__live3d.targetObj.position);
    }
    renderer.render(scene, camera);
  }
  animate();

  window.__live3d = { scene, camera, renderer, stage, spot, beam, fixture, targetObj };
}

/* ============================================================================
 * Show page (Ableton link, looks, patch)
 * ============================================================================ */

function bindShow() {
  const state = { look: { name: '', targets: {}, fog: {} }, looks: [], patch: [], groups: [], fixtures: [] };

  function targetOptions() {
    const sel = document.getElementById('look-target');
    if (!sel) return;
    sel.innerHTML = '';
    ['*', ...state.groups, ...state.fixtures].forEach((o) => {
      const opt = document.createElement('option');
      opt.value = o;
      opt.textContent = o === '*' ? 'Tous les projecteurs' : o;
      sel.appendChild(opt);
    });
  }

  function renderTargets() {
    const box = document.getElementById('look-targets');
    if (!box) return;
    box.innerHTML = '';
    Object.entries(state.look.targets).forEach(([target, st]) => {
      const chip = document.createElement('span');
      chip.className = 'chip';
      const color = rgbToHex(st.r || 0, st.g || 0, st.b || 0);
      const sw = document.createElement('i');
      sw.style.background = color;
      chip.appendChild(sw);
      chip.appendChild(document.createTextNode(`${target} · ${st.dimmer ?? 255}`));
      const x = document.createElement('button');
      x.className = 'chip-x';
      x.textContent = '×';
      x.addEventListener('click', () => { delete state.look.targets[target]; renderTargets(); });
      chip.appendChild(x);
      box.appendChild(chip);
    });
  }

  function renderPatch() {
    const tbl = document.getElementById('patch-table');
    if (!tbl) return;
    const thead = '<thead><tr><th>Nom</th><th>Profil</th><th>Groupe</th><th>Canal</th><th>Canaux</th></tr></thead>';
    const rows = state.patch.map((f) =>
      `<tr><td>${f.name}</td><td>${f.profileLabel}</td><td>${f.group || ''}</td><td>${f.address + 1}</td><td>${f.channels}</td></tr>`).join('');
    tbl.innerHTML = thead + `<tbody>${rows}</tbody>`;
  }

  function renderScenes(ableton, scenes) {
    const tbl = document.getElementById('scene-table');
    if (!tbl) return;
    const names = (ableton.sceneNames || []).map((n, i) => [i + 1, n]).filter(([, n]) => n);
    const head = '<thead><tr><th>#</th><th>Scène</th><th>Look</th></tr></thead>';
    const rows = names.map(([idx, name]) => {
      const current = scenes.mapping?.[name] || '';
      const opts = ['<option value="">—</option>']
        .concat(state.looks.map((l) => `<option value="${l}"${l === current ? ' selected' : ''}>${l}</option>`))
        .join('');
      const active = scenes.activeScene === name ? ' style="color:var(--accent)"' : '';
      return `<tr><td>${idx}</td><td${active}>${name}</td><td><select data-scene="${name}">${opts}</select></td></tr>`;
    }).join('');
    tbl.innerHTML = head + `<tbody>${rows}</tbody>`;
    tbl.querySelectorAll('select[data-scene]').forEach((sel) => {
      sel.addEventListener('change', async () => {
        const r = await postJSON('/api/scenes/mapping', { scene: sel.dataset.scene, look: sel.value });
        if (r.ok) toast('Mapping enregistré', 'success', 1200);
      });
    });
  }

  function renderLooks() {
    const ul = document.getElementById('looks-list');
    if (!ul) return;
    ul.innerHTML = '';
    state.looks.forEach((name) => {
      const li = document.createElement('li');
      const span = document.createElement('span');
      span.textContent = name;
      li.appendChild(span);
      const load = document.createElement('button');
      load.textContent = 'Charger'; load.className = 'btn-small';
      load.addEventListener('click', () => loadLook(name));
      const apply = document.createElement('button');
      apply.textContent = 'Appliquer'; apply.className = 'btn-small';
      apply.addEventListener('click', async () => {
        const r = await postJSON('/api/looks/apply', { name });
        if (r.ok) toast(`Look « ${name} » appliqué`, 'success', 1200);
      });
      const del = document.createElement('button');
      del.textContent = '×'; del.className = 'btn-small btn-danger';
      del.addEventListener('click', async () => {
        if (!confirm(`Supprimer le look ${name} ?`)) return;
        await postJSON('/api/looks/delete', { name });
        refresh();
      });
      li.appendChild(load); li.appendChild(apply); li.appendChild(del);
      ul.appendChild(li);
    });
  }

  async function loadLook(name) {
    const r = await getJSON(`/api/looks/load?name=${encodeURIComponent(name)}`);
    if (!r.ok) { toast(r.error || 'Erreur', 'error'); return; }
    state.look = { name: r.look.name, targets: r.look.targets || {}, fog: r.look.fog || {} };
    document.getElementById('look-name').value = state.look.name;
    renderTargets();
  }

  function updateStats(a) {
    document.getElementById('abl-tempo').textContent = a.tempo ?? '–';
    document.getElementById('abl-scene').textContent = a.selectedSceneName || (a.selectedScene >= 0 ? `#${a.selectedScene + 1}` : '–');
    document.getElementById('abl-beat').textContent = a.beat;
    document.getElementById('abl-playing').textContent = a.isPlaying ? '▶' : '⏹';
    const pill = document.getElementById('abl-status');
    if (pill) {
      pill.classList.toggle('ok', !!a.connected);
      pill.classList.toggle('idle', !a.connected);
      const label = pill.querySelector('.status-label');
      if (label) label.textContent = a.connected ? 'Ableton OK' : 'Ableton OFF';
    }
  }

  async function refresh() {
    const r = await getJSON('/api/scenes');
    if (!r.ok) return;
    state.looks = r.looks || [];
    updateStats(r.ableton || {});
    renderLooks();
    renderScenes(r.ableton || {}, r.scenes || {});
    const enabled = document.getElementById('scenes-enabled');
    if (enabled) enabled.checked = !!r.scenes?.enabled;
  }

  async function refreshPatch() {
    const r = await getJSON('/api/patch');
    if (!r.ok) return;
    state.patch = r.patch || [];
    state.fixtures = state.patch.map((f) => f.name);
    state.groups = [...new Set(state.patch.map((f) => f.group).filter(Boolean))];
    targetOptions();
    renderPatch();
    buildStageFixtures(state.patch);
  }

  document.getElementById('btn-abl-connect')?.addEventListener('click', async () => {
    const r = await postJSON('/api/ableton/connect');
    if (r.ok) { toast('Liaison Ableton active — lance Ableton avec le script AbletonOSC', 'success', 3500); refresh(); }
    else toast(r.error || 'Erreur', 'error', 4000);
  });
  document.getElementById('btn-abl-disconnect')?.addEventListener('click', async () => {
    await postJSON('/api/ableton/disconnect');
    refresh();
  });

  document.getElementById('btn-look-new')?.addEventListener('click', () => {
    state.look = { name: '', targets: {}, fog: {} };
    document.getElementById('look-name').value = '';
    renderTargets();
  });
  document.getElementById('btn-look-addtarget')?.addEventListener('click', () => {
    const target = document.getElementById('look-target').value;
    const { r, g, b } = hexToRgb(document.getElementById('look-color').value);
    state.look.targets[target] = {
      r, g, b,
      dimmer: Number($val('look-dimmer')),
      strobe: Number($val('look-strobe')),
    };
    renderTargets();
  });
  document.getElementById('btn-look-save')?.addEventListener('click', async () => {
    state.look.name = document.getElementById('look-name').value.trim();
    if (!state.look.name) { toast('Nom de look requis', 'error'); return; }
    const r = await postJSON('/api/looks/save', state.look);
    if (r.ok) { toast(`Look « ${state.look.name} » sauvegardé`, 'success'); refresh(); }
    else toast(r.error || 'Erreur', 'error');
  });
  document.getElementById('btn-look-apply')?.addEventListener('click', async () => {
    const r = await postJSON('/api/looks/apply', { look: state.look });
    if (r.ok) toast('Look appliqué', 'success', 1200);
  });
  document.getElementById('scenes-enabled')?.addEventListener('change', (e) => {
    postJSON('/api/scenes/enabled', { enabled: e.target.checked });
  });

  refreshPatch();
  refresh();
  setInterval(refresh, 1000);

  // ---- 3D simulation ----
  setupStage3D();
  setInterval(pollSim, 120);

  const fogSlider = document.getElementById('fog-level');
  const fogValue = document.getElementById('fog-value');
  function sendFog() {
    if (fogSlider) postJSON('/api/fog', { level: Number(fogSlider.value) });
  }
  fogSlider?.addEventListener('input', () => {
    if (fogValue) fogValue.textContent = fogSlider.value;
  });
  fogSlider?.addEventListener('change', sendFog);
  document.getElementById('btn-fog-apply')?.addEventListener('click', sendFog);
  document.getElementById('btn-fog-cut')?.addEventListener('click', () => {
    if (fogSlider) fogSlider.value = '0';
    if (fogValue) fogValue.textContent = '0';
    postJSON('/api/fog', { level: 0 });
  });
  document.getElementById('smoke-visible')?.addEventListener('change', (e) => {
    if (window.__stage) window.__stage.smokeOn = e.target.checked;
  });
  document.getElementById('stage-exposure')?.addEventListener('input', (e) => {
    if (window.__stage) window.__stage.renderer.toneMappingExposure = Number(e.target.value);
  });
}

/* ============================================================================
 * Show page — 3D stage simulation (all fixtures + fluid smoke)
 * ============================================================================ */

function makeSmokeTexture() {
  const size = 128;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const g = canvas.getContext('2d');
  for (let i = 0; i < 8; i++) {
    const x = size / 2 + (Math.random() - 0.5) * size * 0.42;
    const y = size / 2 + (Math.random() - 0.5) * size * 0.42;
    const r = size * (0.16 + Math.random() * 0.22);
    const grad = g.createRadialGradient(x, y, 0, x, y, r);
    grad.addColorStop(0, 'rgba(255,255,255,0.55)');
    grad.addColorStop(1, 'rgba(255,255,255,0)');
    g.fillStyle = grad;
    g.beginPath();
    g.arc(x, y, r, 0, Math.PI * 2);
    g.fill();
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}

function makePoolTexture() {
  const size = 128;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const g = canvas.getContext('2d');
  const grad = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grad.addColorStop(0, 'rgba(255,255,255,0.85)');
  grad.addColorStop(0.55, 'rgba(255,255,255,0.30)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, size, size);
  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  return tex;
}

// Volumetric beam: soft radial falloff, distance falloff, brightest near the
// source. No hard cone edges, no flat fill.
const BEAM_VERTEX = `
varying float vNR;
varying float vD;
uniform float uLength;
uniform float uRadius;
void main() {
  float h = uLength;
  float d = (h * 0.5) - position.y;                 // 0 at apex, h at base
  float localR = max(0.0001, uRadius * d / h);
  vNR = clamp(length(position.xz) / localR, 0.0, 1.0);
  vD = d;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;

const BEAM_FRAGMENT = `
varying float vNR;
varying float vD;
uniform vec3 uColor;
uniform float uIntensity;
uniform float uLength;
uniform float uPower;
void main() {
  float core = pow(max(0.0, 1.0 - vNR), uPower);
  float axial = (1.0 - smoothstep(0.72, 1.0, vD / uLength)) * (0.35 + 0.65 * (1.0 - vD / uLength));
  float a = uIntensity * core * axial;
  gl_FragColor = vec4(uColor * a, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

// Relative brightness and core tightness per fixture family.
const BEAM_GAIN = { pars: 0.16, wash: 0.075, spots: 0.26, fx: 0.0 };
const BEAM_POWER = { pars: 1.9, wash: 1.15, spots: 2.8, fx: 2.0 };

function setupStage3D() {
  const container = document.getElementById('stage3d');
  if (!container || typeof THREE === 'undefined') return;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x07080b);
  scene.fog = new THREE.FogExp2(0x07080b, 0.03);

  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / Math.max(1, container.clientHeight), 0.1, 300);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setSize(container.clientWidth, container.clientHeight);
  // Physical-ish response: highlights roll off instead of clipping to white.
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.innerHTML = '';
  container.appendChild(renderer.domElement);

  // A dark room: only the beams, their floor pools and the lit smoke glow.
  scene.add(new THREE.AmbientLight(0x2a2f38, 0.25));
  scene.add(new THREE.HemisphereLight(0x1b2026, 0x05070a, 0.15));

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(50, 40),
    new THREE.MeshStandardMaterial({ color: 0x0d0f14, roughness: 1 }),
  );
  floor.rotation.x = -Math.PI / 2;
  scene.add(floor);

  const grid = new THREE.GridHelper(44, 22, 0x1b2130, 0x121722);
  grid.position.y = 0.01;
  scene.add(grid);

  const wall = new THREE.Mesh(
    new THREE.PlaneGeometry(30, 12),
    new THREE.MeshStandardMaterial({ color: 0x0b0d12, roughness: 1 }),
  );
  wall.position.set(0, 6, -6);
  scene.add(wall);

  const tex = makeSmokeTexture();
  const poolTex = makePoolTexture();
  const smoke = [];
  for (let i = 0; i < 110; i++) {
    const mat = new THREE.SpriteMaterial({
      map: tex, color: 0x000000, transparent: true, opacity: 0,
      depthWrite: false, blending: THREE.AdditiveBlending,
    });
    const sp = new THREE.Sprite(mat);
    sp.visible = false;
    scene.add(sp);
    smoke.push({ sprite: sp, life: 0, max: 1, vy: 0, drift: 0, seed: 0, spin: 0, size: 1 });
  }

  const cam = { theta: 0, phi: 1.15, radius: 15 };
  function updateCam() {
    camera.position.set(
      Math.sin(cam.phi) * Math.sin(cam.theta) * cam.radius,
      1.4 + Math.cos(cam.phi) * cam.radius,
      Math.sin(cam.phi) * Math.cos(cam.theta) * cam.radius,
    );
    camera.lookAt(0, 1.4, 0);
  }
  updateCam();

  let drag = false;
  let px = 0;
  let py = 0;
  renderer.domElement.addEventListener('pointerdown', (e) => { drag = true; px = e.clientX; py = e.clientY; });
  window.addEventListener('pointerup', () => { drag = false; });
  window.addEventListener('pointermove', (e) => {
    if (!drag) return;
    cam.theta -= (e.clientX - px) * 0.006;
    cam.phi = Math.max(0.25, Math.min(1.35, cam.phi - (e.clientY - py) * 0.005));
    px = e.clientX; py = e.clientY;
    updateCam();
  });
  window.addEventListener('resize', () => {
    const w = container.clientWidth;
    const h = Math.max(1, container.clientHeight);
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  });

  window.__stage = {
    scene, camera, renderer, smoke, poolTex,
    fixtures: {},
    fogPos: new THREE.Vector3(0, 0.35, 1.5),
    level: 0,
    smokeOn: true,
    last: 0,
    emitAcc: 0,
  };

  stageAnimate();
}

function buildStageFixtures(patch) {
  const st = window.__stage;
  if (!st) return;
  Object.values(st.fixtures).forEach((f) => {
    st.scene.remove(f.beam);
    st.scene.remove(f.body);
    if (f.pool) st.scene.remove(f.pool);
  });
  st.fixtures = {};

  const Y = 2.2;    // fixtures on stands
  const REACH = 10; // maximum beam reach (metres)

  patch.forEach((f) => {
    const isFog = f.group === 'fx';
    const y = isFog ? 0.35 : Y;

    const body = new THREE.Mesh(
      new THREE.BoxGeometry(0.42, 0.3, 0.42),
      new THREE.MeshStandardMaterial({ color: 0x22252b, roughness: 0.85, metalness: 0.15 }),
    );
    body.position.set(f.x, y, f.z);
    st.scene.add(body);

    const a = THREE.MathUtils.degToRad(f.angle || 0);
    const dir = new THREE.Vector3(Math.sin(a), -0.32, Math.cos(a)).normalize();

    const beamDeg = f.beamAngle || 25;
    const tanHalf = Math.tan(THREE.MathUtils.degToRad(beamDeg) / 2);

    // The beam stops where it meets the floor.
    const tFloor = dir.y < -0.001 ? y / (-dir.y) : Infinity;
    const length = Math.max(1.0, Math.min(REACH, tFloor));
    const radius = Math.max(0.08, length * tanHalf);

    const uniforms = {
      uColor: { value: new THREE.Color(0xffffff) },
      uIntensity: { value: 0 },
      uLength: { value: length },
      uRadius: { value: radius },
      uPower: { value: BEAM_POWER[f.group] || 1.9 },
    };
    const beam = new THREE.Mesh(
      new THREE.ConeGeometry(radius, length, 32, 1, true),
      new THREE.ShaderMaterial({
        uniforms, vertexShader: BEAM_VERTEX, fragmentShader: BEAM_FRAGMENT,
        transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
      }),
    );
    beam.visible = false;
    beam.quaternion.copy(
      new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().negate()),
    );
    const pos = new THREE.Vector3(f.x, y, f.z);
    beam.position.copy(pos).addScaledVector(dir, length / 2);
    st.scene.add(beam);

    // Light pool on the floor where the beam lands.
    let pool = null;
    if (f.group !== 'fx' && isFinite(tFloor) && tFloor > 0.1) {
      const end = Math.min(tFloor, length);
      pool = new THREE.Mesh(
        new THREE.CircleGeometry(1, 40),
        new THREE.MeshBasicMaterial({
          map: st.poolTex, color: 0xffffff, transparent: true, opacity: 0,
          depthWrite: false, blending: THREE.AdditiveBlending,
        }),
      );
      pool.rotation.x = -Math.PI / 2;
      const fp = pos.clone().addScaledVector(dir, end);
      pool.position.set(fp.x, 0.02, fp.z);
      const pr = Math.max(0.3, end * tanHalf * 1.15);
      pool.scale.set(pr, pr, 1);
      pool.visible = false;
      st.scene.add(pool);
    }

    st.fixtures[f.name] = {
      body, beam, pool, color: new THREE.Color(0x000000), intensity: 0,
      pos, dir, tanHalf, length, isFog,
    };
  });
}

function computeSmokeLight(p, st) {
  let R = 0;
  let G = 0;
  let B = 0;
  let total = 0;
  for (const name in st.fixtures) {
    const fx = st.fixtures[name];
    if (fx.isFog || !fx.beam.visible || fx.intensity <= 0.01) continue;
    const vx = p.x - fx.pos.x;
    const vy = p.y - fx.pos.y;
    const vz = p.z - fx.pos.z;
    const t = vx * fx.dir.x + vy * fx.dir.y + vz * fx.dir.z;
    if (t < 0.2 || t > fx.length) continue;
    const px = vx - t * fx.dir.x;
    const py = vy - t * fx.dir.y;
    const pz = vz - t * fx.dir.z;
    const r = Math.sqrt(px * px + py * py + pz * pz);
    const maxR = t * fx.tanHalf;
    if (r > maxR) continue;
    const radial = 1 - r / Math.max(0.001, maxR);
    const axial = 1 - t / fx.length;
    const contrib = fx.intensity * radial * radial * (0.35 + 0.65 * axial);
    R += fx.color.r * contrib;
    G += fx.color.g * contrib;
    B += fx.color.b * contrib;
    total += contrib;
  }
  return { R, G, B, total };
}

function updateStage(snap) {
  const st = window.__stage;
  if (!st) return;
  st.level = (snap.fog && snap.fog.level) || 0;

  snap.fixtures.forEach((f) => {
    const fx = st.fixtures[f.name];
    if (!fx) return;
    if (fx.isFog) {
      st.fogPos.set(f.x, 0.35, f.z);
      return;
    }
    const v = f.values || {};
    const hasDimmer = 'dimmer' in v;
    const base = hasDimmer ? (v.dimmer || 0) / 255 : 1;
    let R = (v.r || 0) / 255;
    let G = (v.g || 0) / 255;
    let B = (v.b || 0) / 255;
    const w = (v.w || 0) / 255;
    const am = (v.a || 0) / 255;
    R += w; G += w; B += w;
    R += am; G += am * 0.66; B += am * 0.24;
    const amount = Math.min(1, Math.max(R, G, B));
    R = Math.min(1, R); G = Math.min(1, G); B = Math.min(1, B);
    const intensity = base * amount;

    fx.color.setRGB(R, G, B);
    fx.intensity = intensity;
    const gain = BEAM_GAIN[f.group] !== undefined ? BEAM_GAIN[f.group] : 0.16;
    fx.beam.material.uniforms.uColor.value.copy(fx.color);
    fx.beam.material.uniforms.uIntensity.value = intensity * gain;
    fx.beam.visible = intensity > 0.02;
    if (fx.pool) {
      fx.pool.material.color.copy(fx.color);
      fx.pool.material.opacity = Math.min(0.5, intensity * 0.42);
      fx.pool.visible = intensity > 0.02;
    }
    if (fx.body.material.emissive) {
      fx.body.material.emissive.copy(fx.color).multiplyScalar(0.5 * intensity);
    }
  });
}

function spawnSmoke() {
  const st = window.__stage;
  if (!st || !st.smokeOn) return;
  const p = st.smoke.find((s) => !s.sprite.visible);
  if (!p) return;
  p.life = 0;
  p.max = 3.2 + Math.random() * 2.8;
  p.vy = 0.4 + Math.random() * 0.5;
  p.drift = (Math.random() - 0.5) * 0.6;
  p.seed = Math.random() * 10;
  p.spin = (Math.random() - 0.5) * 2.2;
  p.size = 0.7 + Math.random() * 0.9;
  const sp = p.sprite;
  sp.visible = true;
  sp.position.set(
    st.fogPos.x + (Math.random() - 0.5) * 0.6,
    st.fogPos.y + Math.random() * 0.4,
    st.fogPos.z + (Math.random() - 0.5) * 0.6,
  );
  sp.scale.set(p.size, p.size, 1);
  sp.material.opacity = 0;
}

function stageAnimate() {
  requestAnimationFrame(stageAnimate);
  const st = window.__stage;
  if (!st) return;
  const now = performance.now() / 1000;
  const dt = Math.min(0.05, st.last ? now - st.last : 0.016);
  st.last = now;

  if (st.smokeOn) {
    st.emitAcc += (st.level / 255) * 20 * dt;
    while (st.emitAcc >= 1) {
      st.emitAcc -= 1;
      spawnSmoke();
    }
  }

  st.smoke.forEach((p) => {
    if (!p.sprite.visible) return;
    p.life += dt;
    const t = p.life / p.max;
    if (t >= 1) {
      p.sprite.visible = false;
      p.sprite.material.opacity = 0;
      return;
    }
    p.sprite.position.y += p.vy * dt;
    p.sprite.position.x += (Math.sin(p.seed + p.life * 0.9) * 0.5 + p.drift) * dt;
    p.sprite.position.z += Math.cos(p.seed * 1.3 + p.life * 0.6) * 0.3 * dt;
    const s = p.size * (1 + t * 2.4);
    p.sprite.scale.set(s, s, 1);
    p.sprite.material.rotation += p.spin * dt * 0.25;

    // Smoke is lit by the beams: colour and opacity come from the light that
    // actually reaches the particle. Only a very faint natural glow remains.
    const lit = computeSmokeLight(p.sprite.position, st);
    if (lit.total > 0.001) {
      p.sprite.material.color.setRGB(lit.R / lit.total, lit.G / lit.total, lit.B / lit.total);
    } else {
      p.sprite.material.color.setRGB(0.55, 0.58, 0.62);
    }
    const litAmount = Math.min(1, lit.total);
    const fadeIn = Math.min(1, t * 7);
    const fadeOut = 1 - Math.max(0, (t - 0.35) / 0.65);
    p.sprite.material.opacity = fadeIn * fadeOut * (0.02 + 0.42 * litAmount);
  });

  st.renderer.render(st.scene, st.camera);
}

async function pollSim() {
  if (!window.__stage) return;
  const r = await getJSON('/api/simulation');
  if (r.ok) updateStage(r);
}

/* ============================================================================
 * Boot
 * ============================================================================ */

document.addEventListener('DOMContentLoaded', () => {
  bindTheme();
  bindHealthPolling();

  const page = document.body.dataset.page;
  if (page === 'direct') bindExperiment();
  else if (page === 'sequence') bindSequence();
  else if (page === 'live') bindLive();
  else if (page === 'show') bindShow();
});
