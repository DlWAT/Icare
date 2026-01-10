async function postJSON(url, data = {}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

function hexToRgb(hex) {
  const m = hex.replace('#', '');
  const r = parseInt(m.slice(0, 2), 16);
  const g = parseInt(m.slice(2, 4), 16);
  const b = parseInt(m.slice(4, 6), 16);
  return { r, g, b };
}

function updatePreview() {
  const r = document.getElementById('range-r').value;
  const g = document.getElementById('range-g').value;
  const b = document.getElementById('range-b').value;
  const hex = `#${Number(r).toString(16).padStart(2,'0')}${Number(g).toString(16).padStart(2,'0')}${Number(b).toString(16).padStart(2,'0')}`;
  document.getElementById('color-preview').style.background = hex;
}

async function sendValues() {
  const r = Number(document.getElementById('range-r').value);
  const g = Number(document.getElementById('range-g').value);
  const b = Number(document.getElementById('range-b').value);
  const amp = Number(document.getElementById('range-amp').value);
  const pan = Number(document.getElementById('range-pan').value);
  const tilt = Number(document.getElementById('range-tilt').value);
  await postJSON('/api/experiment/set-values', { r, g, b, amp, pan, tilt });
}

function bindExperiment() {
  const inputs = ['range-r','range-g','range-b','range-amp','range-pan','range-tilt'];
  for (const id of inputs) {
    const el = document.getElementById(id);
    if (!el) continue;
    el.addEventListener('input', () => { updatePreview(); sendValues(); updateDirect3DFromControls(); });
  }

  const color = document.getElementById('color-picker');
  if (color) {
    color.addEventListener('input', () => {
      const { r, g, b } = hexToRgb(color.value);
      document.getElementById('range-r').value = r;
      document.getElementById('range-g').value = g;
      document.getElementById('range-b').value = b;
      updatePreview();
      sendValues();
      updateDirect3DFromControls();
    });
  }

  document.getElementById('btn-connect')?.addEventListener('click', () => {
    const baseChannel = Number(document.getElementById('input-conn-channel').value || 9);
    postJSON('/api/experiment/connect', { baseChannel });
  });
  document.getElementById('btn-update-base')?.addEventListener('click', () => {
    const baseChannel = Number(document.getElementById('input-conn-channel').value || 9);
    postJSON('/api/experiment/base-channel', { baseChannel });
  });
  document.getElementById('btn-blackout')?.addEventListener('click', () => postJSON('/api/experiment/blackout'));
  // Random color mode config + start/stop
  const randFreq = document.getElementById('input-rand-freq');
  const randSmooth = document.getElementById('input-rand-smooth');
  const randBright = document.getElementById('input-rand-bright');
  function sendRandomConfig() {
    if (!randFreq || !randSmooth || !randBright) return;
    const freqHz = Number(randFreq.value || 1);
    const smoothPct = Number(randSmooth.value || 0);
    const brightness = Number(randBright.value || 128);
    postJSON('/api/experiment/mode/random-config', { freqHz, smooth: smoothPct/100, brightness });
  }
  randFreq?.addEventListener('input', sendRandomConfig);
  randSmooth?.addEventListener('input', sendRandomConfig);
  randBright?.addEventListener('input', sendRandomConfig);
  document.getElementById('btn-rand-start')?.addEventListener('click', () => {
    sendRandomConfig();
    postJSON('/api/experiment/random-start');
  });
  document.getElementById('btn-rand-stop')?.addEventListener('click', () => postJSON('/api/experiment/random-stop'));
  document.getElementById('btn-strobe-overlay')?.addEventListener('click', () => {
    const freqHz = Number(document.getElementById('input-ov-freq').value || 10);
    const duty = Number(document.getElementById('input-ov-duty').value || 50) / 100;
    const durationSec = Number(document.getElementById('input-ov-duration').value || 5);
    const channel = Number(document.getElementById('input-ov-channel').value || 0);
    postJSON('/api/experiment/mode/strobe-overlay', { freqHz, duty, durationSec, channel });
  });

  updatePreview();
  // Additional controls for 3D
  ['direct-angle','direct-x','direct-z','direct-y'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateDirect3DFromControls);
  });

  // Setup 3D
  setupDirect3D();
  updateDirect3DFromControls();

  // Poll experiment status to reflect server-side modes (random/strobe-random)
  async function pollExperiment() {
    try {
      const res = await (await fetch('/api/experiment/status')).json();
      if (res.ok) {
        const s = res.state;
        // Cache overlay params for client-side visualization
        window.__overlay = s.overlay || null;
        // Update only RGB to reflect changes
        ['range-r','range-g','range-b'].forEach((id, idx) => {
          const val = [s.r, s.g, s.b][idx];
          const el = document.getElementById(id);
          if (el && Number(el.value) !== val) el.value = val;
        });
        // Reflect random config
        if (s.random) {
          if (randFreq) randFreq.value = String(s.random.freq_hz ?? 1);
          if (randSmooth) randSmooth.value = String(Math.round(100 * (s.random.smooth ?? 0)));
          if (randBright) randBright.value = String(s.random.brightness ?? 128);
        }
        updatePreview();
        updateDirect3DFromControls();
      }
    } catch {}
    setTimeout(pollExperiment, 100);
  }
  pollExperiment();
}

// ----- Direct 3D -----
function setupDirect3D() {
  const container = document.getElementById('direct3d');
  if (!container) return;
  if (typeof THREE === 'undefined') {
    container.innerHTML = '<div style="color:#bbb;padding:12px;">Three.js non chargé — vérifiez la connexion Internet ou le CDN.</div>';
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

  const stageGeom = new THREE.PlaneGeometry(14, 7);
  const stageMat = new THREE.MeshStandardMaterial({ color: 0x22252a, side: THREE.DoubleSide, roughness: 1, metalness: 0 });
  const stage = new THREE.Mesh(stageGeom, stageMat);
  stage.rotation.x = -Math.PI / 2;
  stage.position.set(0, 0, 0);
  scene.add(stage);

  scene.add(new THREE.AmbientLight(0x202020, 0.8));

  const spot = new THREE.SpotLight(0xffffff, 1.5);
  spot.position.set(0, 4.0, 0);
  spot.angle = THREE.MathUtils.degToRad(45);
  spot.penumbra = 0.3;
  spot.decay = 2;
  spot.distance = 25;
  spot.castShadow = false;
  scene.add(spot);

  const targetObj = new THREE.Object3D();
  targetObj.position.set(0, 0, 0);
  scene.add(targetObj);
  spot.target = targetObj;

  const height = 4.0;
  const half = THREE.MathUtils.degToRad(45 / 2);
  const radius = Math.tan(half) * height;
  const coneGeom = new THREE.ConeGeometry(radius, height, 64, 1, true);
  const defaultOpacity = 0.12;
  const coneMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: defaultOpacity, depthWrite: false, blending: THREE.AdditiveBlending });
  const beam = new THREE.Mesh(coneGeom, coneMat);
  beam.position.copy(spot.position);
  scene.add(beam);

  // Fixture body (parallélépipède rectangle)
  const fixtureGeom = new THREE.BoxGeometry(0.50, 0.35, 0.50);
  const fixtureMat = new THREE.MeshStandardMaterial({ color: 0x2b2f37, roughness: 0.8, metalness: 0.2 });
  const fixture = new THREE.Mesh(fixtureGeom, fixtureMat);
  fixture.position.copy(spot.position);
  fixture.castShadow = false;
  scene.add(fixture);

  const hemi = new THREE.HemisphereLight(0x222222, 0x111111, 0.6);
  scene.add(hemi);

  function onResize() {
    const w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', onResize);

  function animate() {
    requestAnimationFrame(animate);
    // Client-side visualization of overlay strobe (beam gating)
    const ov = window.__overlay;
    if (ov && ov.active && typeof ov.freq_hz === 'number' && typeof ov.duty === 'number') {
      const t = performance.now() / 1000;
      const phase = (t * Math.max(0.1, ov.freq_hz)) % 1.0;
      const on = phase < Math.max(0.0, Math.min(1.0, ov.duty));
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
  const r = Number(document.getElementById('range-r').value || 0);
  const g = Number(document.getElementById('range-g').value || 0);
  const b = Number(document.getElementById('range-b').value || 0);
  const amp = Number(document.getElementById('range-amp').value || 0);
  const pan = Number(document.getElementById('range-pan').value || 0);
  const tilt = Number(document.getElementById('range-tilt').value || 0);
  const deg = Number(document.getElementById('direct-angle').value || 45);
  const lx = Number(document.getElementById('direct-x').value || 0);
  const lz = Number(document.getElementById('direct-z').value || 0);
  const ly = Number(document.getElementById('direct-y').value || 4);

  // Color + intensity
  const color = new THREE.Color(r / 255, g / 255, b / 255);
  ctx.spot.color = color;
  ctx.beam.material.color = color;
  ctx.beam.material.needsUpdate = true;
  ctx.spot.intensity = 0.5 + (amp / 255) * 2.0;

  // Position
  ctx.spot.position.set(lx, ly, lz);
  // Center cone along its height so apex matches spot position (base of ray)
  ctx.beam.position.set(lx, ly - (ly / 2), lz);
  ctx.beam.rotation.x = Math.PI;

  // Beam angle
  const angleRad = THREE.MathUtils.degToRad(deg);
  ctx.spot.angle = angleRad;
  const h = ly; // approximate height to ground
  const half = angleRad / 2;
  const radius = Math.tan(half) * h;
  ctx.beam.geometry.dispose();
  ctx.beam.geometry = new THREE.ConeGeometry(radius, h, 64, 1, true);
  // Keep apex at spot position after geometry change
  ctx.beam.position.set(lx, ly - (h / 2), lz);
  ctx.beam.rotation.x = Math.PI;

  // Direction from pan/tilt
  // Map pan in [-90,90], tilt in [0,90]
  const panDeg = (pan / 255) * 180 - 90;
  const tiltDeg = (tilt / 255) * 90;
  const yaw = THREE.MathUtils.degToRad(panDeg);
  const pitch = THREE.MathUtils.degToRad(tiltDeg);
  // Direction vector
  const dx = Math.sin(yaw) * Math.cos(pitch);
  const dy = -Math.sin(pitch);
  const dz = Math.cos(yaw) * Math.cos(pitch);
  const tpos = new THREE.Vector3(lx + dx * 5, Math.max(0, ly + dy * 5), lz + dz * 5);
  ctx.targetObj.position.copy(tpos);
  ctx.spot.target = ctx.targetObj;
  ctx.beam.lookAt(tpos);
  if (ctx.fixture) {
    // Attach fixture to base of beam and orient toward target
    ctx.fixture.position.set(lx, ly, lz);
    ctx.fixture.lookAt(tpos);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.body.querySelector('h1')?.textContent?.includes('Direct')) {
    bindExperiment();
  }
  if (document.body.querySelector('h1')?.textContent?.includes('Séquence')) {
    bindSequence();
  }
  if (document.body.querySelector('h1')?.textContent?.includes('Live')) {
    bindLive();
  }
});

// ----- Sequence -----
function seqBuildHeader(modules) {
  return ['Line','Structure', ...modules];
}

function seqRenderTable(header, rows) {
  const tbl = document.getElementById('seq-table');
  tbl.innerHTML = '';
  const thead = document.createElement('thead');
  const trh = document.createElement('tr');
  header.forEach(h => {
    const th = document.createElement('th');
    th.textContent = h;
    trh.appendChild(th);
  });
  thead.appendChild(trh);
  tbl.appendChild(thead);
  const tbody = document.createElement('tbody');
  rows.forEach((row, idx) => {
    const tr = document.createElement('tr');
    header.forEach((_, colIdx) => {
      const td = document.createElement('td');
      td.contentEditable = colIdx >= 2; // allow editing function cells
      td.textContent = row[colIdx] ?? '';
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  tbl.appendChild(tbody);
}

async function bindSequence() {
  const moduleSelect = document.getElementById('seq-module-select');
  let currentHeader = ['Line','Structure','ParLED1','ParLED2','ParLED3','ParLED4','ParLED5','ParLED6','ParLED7','ParLED8','ParLED9','Strobe1','Strobe2'];
  let currentRows = [
    ['1','Intro_x4','','','','','','','','','','',''],
    ['2','Intro_x4','','','','','','','','','','',''],
  ];
  seqRenderTable(currentHeader, currentRows);
  moduleSelect.innerHTML = '';
  currentHeader.slice(2).forEach(m => {
    const opt = document.createElement('option');
    opt.value = m; opt.textContent = m; moduleSelect.appendChild(opt);
  });

  // list files
  const listRes = await fetch('/api/sequence/list');
  const listData = await listRes.json();
  const ul = document.getElementById('seq-file-list');
  ul.innerHTML = '';
  (listData.files || []).forEach(name => {
    const li = document.createElement('li');
    li.textContent = name;
    const btn = document.createElement('button');
    btn.textContent = 'Charger';
    btn.addEventListener('click', async () => {
      const res = await fetch(`/api/sequence/load?name=${encodeURIComponent(name)}`);
      const dat = await res.json();
      if (!dat.ok) return;
      const data = dat.data;
      currentHeader = ['Line','Structure', ...data.Header.Modules];
      currentRows = Object.keys(data.data).map(k => [k, data.data[k].section, ...data.data[k].function]);
      seqRenderTable(currentHeader, currentRows);
      moduleSelect.innerHTML = '';
      data.Header.Modules.forEach(m => {
        const opt = document.createElement('option'); opt.value = m; opt.textContent = m; moduleSelect.appendChild(opt);
      });
    });
    li.appendChild(btn);
    ul.appendChild(li);
  });

  // Add row
  document.getElementById('btn-seq-add-row').addEventListener('click', () => {
    const line = String((currentRows.length ? Number(currentRows[currentRows.length-1][0]) : 0) + 1);
    const struct = 'New';
    const funcs = new Array(currentHeader.length - 2).fill('');
    currentRows.push([line, struct, ...funcs]);
    seqRenderTable(currentHeader, currentRows);
  });

  // Uniform
  document.getElementById('btn-seq-uni').addEventListener('click', () => {
    const name = moduleSelect.value;
    const col = currentHeader.indexOf(name);
    const row = Number(document.getElementById('seq-line').value || 1) - 1;
    const nbrtps = Number(document.getElementById('seq-tps').value || 1);
    const c1 = document.getElementById('seq-color-1').value;
    const { r, g, b } = hexToRgb(c1);
    for (let i=0; i<nbrtps; i++) {
      const val = i===0 ? `uni_${nbrtps}_${r}_${g}_${b}` : '|';
      if (!currentRows[row + i]) currentRows[row + i] = [String(row+i+1),'', ...new Array(currentHeader.length-2).fill('')];
      currentRows[row + i][col] = val;
    }
    seqRenderTable(currentHeader, currentRows);
  });

  // Fondu
  document.getElementById('btn-seq-fondu').addEventListener('click', () => {
    const name = moduleSelect.value;
    const col = currentHeader.indexOf(name);
    const row = Number(document.getElementById('seq-line').value || 1) - 1;
    const nbrtps = Number(document.getElementById('seq-tps').value || 1);
    const c1 = document.getElementById('seq-color-1').value;
    const c2 = document.getElementById('seq-color-2').value;
    const a = hexToRgb(c1), b = hexToRgb(c2);
    for (let i=0; i<nbrtps; i++) {
      const val = i===0 ? `fond_${nbrtps}_${a.r}_${a.g}_${a.b}_${b.r}_${b.g}_${b.b}` : '|';
      if (!currentRows[row + i]) currentRows[row + i] = [String(row+i+1),'', ...new Array(currentHeader.length-2).fill('')];
      currentRows[row + i][col] = val;
    }
    seqRenderTable(currentHeader, currentRows);
  });

  // Strobe
  document.getElementById('btn-seq-strobe').addEventListener('click', () => {
    const name = moduleSelect.value;
    const col = currentHeader.indexOf(name);
    const row = Number(document.getElementById('seq-line').value || 1) - 1;
    const nbrtps = Number(document.getElementById('seq-tps').value || 1);
    const c1 = document.getElementById('seq-color-1').value;
    const freq = Number(document.getElementById('seq-freq').value || 60);
    const { r, g, b } = hexToRgb(c1);
    for (let i=0; i<nbrtps; i++) {
      const val = i===0 ? `str_${nbrtps}_${r}_${g}_${b}_${freq}` : '|';
      if (!currentRows[row + i]) currentRows[row + i] = [String(row+i+1),'', ...new Array(currentHeader.length-2).fill('')];
      currentRows[row + i][col] = val;
    }
    seqRenderTable(currentHeader, currentRows);
  });

  // Save sequence
  document.getElementById('btn-seq-save').addEventListener('click', async () => {
    const name = document.getElementById('seq-save-name').value.trim();
    if (!name) return;
    const header = { Structure: currentRows.map(r => r[1]), Tempo: '60', Modules: currentHeader.slice(2), Line: currentRows.map(r => r[0]) };
    const data = {};
    currentRows.forEach(r => { data[r[0]] = { section: r[1], function: r.slice(2) }; });
    const payload = { name, data: { Header: header, data } };
    const res = await postJSON('/api/sequence/save', payload);
    if (res.ok) alert('Séquence sauvegardée: ' + res.saved);
  });
}

// ----- Live -----
async function bindLive() {
  const fileList = await (await fetch('/api/live/list')).json();
  const ul = document.getElementById('live-file-list');
  ul.innerHTML = '';
  (fileList.files || []).forEach(name => {
    const li = document.createElement('li');
    li.textContent = name;
    const btn = document.createElement('button'); btn.textContent = 'Charger';
    btn.addEventListener('click', async () => {
      const res = await postJSON('/api/live/load', { name });
      if (!res.ok) return;
      const mods = res.data.Header.Modules || [];
      const list = document.getElementById('live-modules');
      list.innerHTML = '';
      mods.forEach(m => {
        const li2 = document.createElement('li');
        const cb = document.createElement('input'); cb.type = 'checkbox';
        cb.addEventListener('change', () => postJSON('/api/live/toggle-module', { name: m }));
        li2.appendChild(cb);
        const span = document.createElement('span'); span.textContent = m; li2.appendChild(span);
        list.appendChild(li2);
      });
    });
    li.appendChild(btn);
    ul.appendChild(li);
  });

  document.getElementById('btn-live-select-all').addEventListener('click', () => postJSON('/api/live/select-all'));
  document.getElementById('btn-live-unselect-all').addEventListener('click', () => postJSON('/api/live/unselect-all'));
  document.getElementById('btn-live-play').addEventListener('click', () => {
    const freq = Number(document.getElementById('live-freq').value || 60);
    postJSON('/api/live/play', { freq });
  });
  document.getElementById('btn-live-pause').addEventListener('click', () => postJSON('/api/live/pause'));
  document.getElementById('btn-live-stop').addEventListener('click', () => postJSON('/api/live/stop'));
  document.getElementById('btn-live-prev').addEventListener('click', () => postJSON('/api/live/prev'));
  document.getElementById('btn-live-next').addEventListener('click', () => postJSON('/api/live/next'));

  // Poll status
  async function poll() {
    try {
      const res = await (await fetch('/api/live/status')).json();
      if (res.ok) {
        const s = res.status;
        document.getElementById('live-progress-bar').style.width = `${s.progress}%`;
        document.getElementById('live-section').textContent = 'Section: ' + (s.section ?? '-');
        // Update 3D color
        if (window.__live3d && s.rgb) {
          const c = new THREE.Color(s.rgb.r / 255, s.rgb.g / 255, s.rgb.b / 255);
          window.__live3d.spot.color = c;
          window.__live3d.beam.material.color = c;
          window.__live3d.beam.material.needsUpdate = true;
        }
      }
    } catch {}
    setTimeout(poll, 250);
  }
  poll();

  // Setup 3D
  setupLive3D();
}

function setupLive3D() {
  const container = document.getElementById('live3d');
  if (!container) return;
  if (typeof THREE === 'undefined') {
    container.innerHTML = '<div style="color:#bbb;padding:12px;">Three.js non chargé — vérifiez la connexion Internet ou le CDN.</div>';
    return;
  }

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

  // Stage: rectangle horizontal on ground (x-z plane)
  const stageGeom = new THREE.PlaneGeometry(12, 6);
  const stageMat = new THREE.MeshStandardMaterial({ color: 0x22252a, side: THREE.DoubleSide, roughness: 1, metalness: 0 });
  const stage = new THREE.Mesh(stageGeom, stageMat);
  stage.rotation.x = -Math.PI / 2;
  stage.position.set(0, 0, 0);
  scene.add(stage);

  // Ambient light
  scene.add(new THREE.AmbientLight(0x202020, 0.8));

  // Par LED 90W RGBWU at top of the scene, beam angle ~45°
  const spot = new THREE.SpotLight(0xffffff, 1.5);
  spot.position.set(0, 4.0, 0); // top center
  spot.angle = THREE.MathUtils.degToRad(45);
  spot.penumbra = 0.3;
  spot.decay = 2;
  spot.distance = 20;
  spot.castShadow = false;
  scene.add(spot);

  const targetObj = new THREE.Object3D();
  targetObj.position.set(0, 0, 0);
  scene.add(targetObj);
  spot.target = targetObj;

  // Beam visualization as semi-transparent cone
  const height = 4.0; // distance from light to stage
  const half = THREE.MathUtils.degToRad(45 / 2);
  const radius = Math.tan(half) * height;
  const coneGeom = new THREE.ConeGeometry(radius, height, 64, 1, true);
  const coneMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.12, depthWrite: false, blending: THREE.AdditiveBlending });
  const beam = new THREE.Mesh(coneGeom, coneMat);
  beam.position.copy(spot.position);
  beam.rotation.x = Math.PI; // point downwards
  beam.position.y -= height / 2; // center cone along beam
  scene.add(beam);

  // Fixture body (parallélépipède rectangle)
  const fixtureGeom = new THREE.BoxGeometry(0.45, 0.30, 0.45);
  const fixtureMat = new THREE.MeshStandardMaterial({ color: 0x2b2f37, roughness: 0.8, metalness: 0.2 });
  const fixture = new THREE.Mesh(fixtureGeom, fixtureMat);
  fixture.position.copy(spot.position);
  fixture.position.y += 0.05;
  fixture.castShadow = false;
  scene.add(fixture);

  // Floor reflection hint
  const hemi = new THREE.HemisphereLight(0x222222, 0x111111, 0.6);
  scene.add(hemi);

  // Resize handling
  function onResize() {
    const w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', onResize);

  // Animate
  function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
  }
  animate();

  // Expose for updates
  window.__live3d = { scene, camera, renderer, stage, spot, beam, fixture, targetObj };

  // Animate
  function animate() {
    requestAnimationFrame(animate);
    // Keep fixture oriented toward target (beam direction)
    if (window.__live3d?.fixture && window.__live3d?.targetObj) {
      window.__live3d.fixture.lookAt(window.__live3d.targetObj.position);
    }
    renderer.render(scene, camera);
  }
  animate();
}
