(() => {
  const canvas = document.getElementById('explainerCanvas');
  const ctx = canvas.getContext('2d');
  const playPauseBtn = document.getElementById('playPauseBtn');
  const restartBtn = document.getElementById('restartBtn');
  const exportBtn = document.getElementById('exportBtn');
  const sceneLabel = document.getElementById('sceneLabel');
  const progressFill = document.getElementById('progressFill');
  const exportPreview = document.getElementById('exportPreview');
  const exportPathHint = document.getElementById('exportPathHint');

  const W = canvas.width;
  const H = canvas.height;

  const scenes = [
    { dur: 6, title: 'Scene 1 — The New Reality', text: 'AI agents can now modify critical systems.' },
    { dur: 7, title: 'Scene 2 — The Problem', text: 'Orchestrators route tasks, but they do not enforce execution boundaries.' },
    { dur: 7, title: 'Scene 3 — Surfit Boundary', text: 'Surfit is a neutral execution boundary.' },
    { dur: 10, title: 'Scene 4 — Policy Evaluation', text: 'Every action is evaluated against policy before execution.' },
    { dur: 10, title: 'Scene 5 — Approval Governance', text: 'Sensitive actions require explicit approval.' },
    { dur: 8, title: 'Scene 6 — Cross-Agent Governance', text: 'Different agents. Same governance boundary.' },
    { dur: 6, title: 'Scene 7 — Closing Frame', text: 'Surfit governs execution — not prompts.' },
  ];

  const totalSeconds = scenes.reduce((a, s) => a + s.dur, 0);
  const cumulative = [];
  scenes.reduce((acc, s) => {
    cumulative.push(acc);
    return acc + s.dur;
  }, 0);

  const agents = [
    { name: 'OpenClaw', x: 165, y: 180, c: '#27c2ff' },
    { name: 'LangGraph', x: 165, y: 360, c: '#27c2ff' },
    { name: 'Internal Automation', x: 165, y: 540, c: '#ff7c2c' },
  ];

  const systems = [
    { name: 'GitHub', x: 1120, y: 150 },
    { name: 'AWS', x: 1120, y: 290 },
    { name: 'Databases', x: 1120, y: 430 },
    { name: 'Internal APIs', x: 1120, y: 570 },
  ];

  const surfit = { x: 640, y: 360, w: 340, h: 250 };

  const colors = {
    bgA: '#071227',
    bgB: '#081831',
    grid: 'rgba(62,97,140,0.26)',
    line: '#2a6da5',
    lineHot: '#27c2ff',
    lineDeny: '#ff6e6e',
    panel: '#0f2543',
    panelBorder: '#2d5a86',
    text: '#cfe4f8',
    muted: '#8cb0d1',
    orange: '#ff7c2c',
    green: '#39d48f',
  };

  let running = true;
  let loop = true;
  let startMs = performance.now();
  let pauseMs = 0;
  let pausedAt = 0;
  let rafId = null;

  function roundedRect(x, y, w, h, r = 10) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function drawBg(t) {
    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, colors.bgA);
    grad.addColorStop(1, colors.bgB);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    const step = 42;
    const drift = (t * 18) % step;
    ctx.strokeStyle = colors.grid;
    ctx.lineWidth = 1;
    for (let x = -step + drift; x < W + step; x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, H);
      ctx.stroke();
    }
    for (let y = 0; y < H; y += step) {
      ctx.beginPath();
      ctx.moveTo(0, y + drift * 0.2);
      ctx.lineTo(W, y + drift * 0.2);
      ctx.stroke();
    }
  }

  function drawNode(x, y, label, color = colors.panelBorder, fill = colors.panel) {
    const w = 210;
    const h = 72;
    roundedRect(x - w / 2, y - h / 2, w, h, 11);
    ctx.fillStyle = fill;
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.2;
    ctx.stroke();

    ctx.fillStyle = colors.text;
    ctx.font = '600 18px DM Sans, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(label, x, y + 6);
  }

  function drawSmallPill(x, y, txt, tone) {
    ctx.font = '600 13px DM Sans, sans-serif';
    const padX = 12;
    const w = ctx.measureText(txt).width + padX * 2;
    const h = 30;
    roundedRect(x - w / 2, y - h / 2, w, h, 15);
    ctx.fillStyle = tone === 'allow' ? 'rgba(57,212,143,0.14)' : 'rgba(255,110,110,0.14)';
    ctx.fill();
    ctx.strokeStyle = tone === 'allow' ? '#39d48f' : '#ff6e6e';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = tone === 'allow' ? '#39d48f' : '#ff6e6e';
    ctx.textAlign = 'center';
    ctx.fillText(txt, x, y + 5);
  }

  function drawLink(x1, y1, x2, y2, mode = 'normal', pulse = 0) {
    const cp = (x2 - x1) * 0.45;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.bezierCurveTo(x1 + cp, y1, x2 - cp, y2, x2, y2);
    ctx.lineWidth = mode === 'active' ? 2.4 : 1.4;
    ctx.strokeStyle = mode === 'deny' ? colors.lineDeny : mode === 'active' ? colors.lineHot : colors.line;
    ctx.globalAlpha = mode === 'active' ? 0.95 : 0.72;
    ctx.stroke();
    ctx.globalAlpha = 1;

    if (mode === 'active' || mode === 'deny') {
      const tx = x1 + (x2 - x1) * pulse;
      const ty = y1 + (y2 - y1) * pulse;
      ctx.beginPath();
      ctx.arc(tx, ty, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = mode === 'deny' ? '#ff6e6e' : '#27c2ff';
      ctx.shadowColor = ctx.fillStyle;
      ctx.shadowBlur = 12;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  function drawSurfitBoundary(t, alpha = 1, showLayers = false) {
    const x = surfit.x - surfit.w / 2;
    const y = surfit.y - surfit.h / 2;

    ctx.save();
    ctx.globalAlpha = alpha;

    roundedRect(x, y, surfit.w, surfit.h, 16);
    ctx.fillStyle = 'rgba(10,33,58,0.95)';
    ctx.fill();
    ctx.strokeStyle = '#2a7cbd';
    ctx.lineWidth = 1.8;
    ctx.stroke();

    // Ocean/wave pulse rings
    const pulse = ((t * 0.8) % 1);
    for (let i = 0; i < 3; i++) {
      const p = (pulse + i * 0.28) % 1;
      ctx.beginPath();
      ctx.ellipse(surfit.x, surfit.y, 140 + p * 110, 85 + p * 56, 0, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(39,194,255,${0.22 * (1 - p)})`;
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    ctx.fillStyle = colors.text;
    ctx.textAlign = 'center';
    ctx.font = '700 24px DM Sans, sans-serif';
    ctx.fillText('SURFIT', surfit.x, y + 44);
    ctx.font = '600 12px DM Sans, sans-serif';
    ctx.fillStyle = '#95c8eb';
    ctx.fillText('Execution Governance Boundary', surfit.x, y + 65);

    if (showLayers) {
      const layers = [
        { label: 'token_scope', y: y + 104 },
        { label: 'policy_manifest', y: y + 146 },
        { label: 'runtime_rules', y: y + 188 },
      ];
      layers.forEach((layer, idx) => {
        const pulseGate = ((t * 1.2) - idx * 0.18) % 1;
        roundedRect(x + 34, layer.y - 16, surfit.w - 68, 30, 8);
        ctx.fillStyle = `rgba(39,194,255,${0.08 + 0.10 * Math.max(0, pulseGate)})`;
        ctx.fill();
        ctx.strokeStyle = 'rgba(74,166,226,0.8)';
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.fillStyle = '#bde2ff';
        ctx.font = '600 13px DM Sans, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(layer.label, x + 50, layer.y + 4);
      });
    }

    ctx.restore();
  }

  function sceneAt(seconds) {
    for (let i = 0; i < scenes.length; i++) {
      const start = cumulative[i];
      const end = start + scenes[i].dur;
      if (seconds >= start && seconds < end) {
        return { i, start, end, p: (seconds - start) / scenes[i].dur, scene: scenes[i] };
      }
    }
    return { i: scenes.length - 1, start: cumulative[scenes.length - 1], end: totalSeconds, p: 1, scene: scenes[scenes.length - 1] };
  }

  function drawOverlay(title, subtitle) {
    roundedRect(36, 28, 690, 96, 10);
    ctx.fillStyle = 'rgba(8,24,45,0.86)';
    ctx.fill();
    ctx.strokeStyle = '#2a5078';
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.fillStyle = '#cde7ff';
    ctx.textAlign = 'left';
    ctx.font = '700 20px DM Sans, sans-serif';
    ctx.fillText(title, 58, 66);
    ctx.fillStyle = '#9ec3e2';
    ctx.font = '500 16px DM Sans, sans-serif';
    ctx.fillText(subtitle, 58, 98);
  }

  function drawActionTag(x, y, label, color) {
    ctx.font = '600 13px DM Sans, sans-serif';
    const w = ctx.measureText(label).width + 18;
    roundedRect(x - w / 2, y - 14, w, 28, 14);
    ctx.fillStyle = color === 'deny' ? 'rgba(255,110,110,0.15)' : 'rgba(39,194,255,0.15)';
    ctx.fill();
    ctx.strokeStyle = color === 'deny' ? '#ff6e6e' : '#27c2ff';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = color === 'deny' ? '#ff9f9f' : '#bce8ff';
    ctx.textAlign = 'center';
    ctx.fillText(label, x, y + 5);
  }

  function drawStopMarker(x, y) {
    ctx.beginPath();
    ctx.arc(x, y, 9, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,110,110,0.2)';
    ctx.fill();
    ctx.strokeStyle = '#ff6e6e';
    ctx.lineWidth = 1.3;
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(x - 4, y - 4);
    ctx.lineTo(x + 4, y + 4);
    ctx.moveTo(x + 4, y - 4);
    ctx.lineTo(x - 4, y + 4);
    ctx.strokeStyle = '#ff8e8e';
    ctx.lineWidth = 1.4;
    ctx.stroke();
  }

  function drawApprovalFlow(progress) {
    const y = 640;
    const nodes = [
      'propose_change',
      'pull_request_created',
      'approval_artifact_required',
      'approval_granted',
      'merge_allowed',
    ];
    const startX = 160;
    const gap = 235;

    for (let i = 0; i < nodes.length; i++) {
      const x = startX + i * gap;
      const active = progress > i / nodes.length;
      const isBlocked = i === 2 && progress < 0.62;
      drawActionTag(x, y, nodes[i], isBlocked ? 'deny' : (active ? 'allow' : 'idle'));
      if (i < nodes.length - 1) {
        drawLink(x + 72, y, x + gap - 72, y, isBlocked ? 'deny' : (active ? 'active' : 'normal'), (progress * 1.7) % 1);
      }
    }
  }

  function drawDecisionMatrix() {
    const x = 812;
    const y = 500;
    const w = 420;
    const h = 172;
    roundedRect(x, y, w, h, 10);
    ctx.fillStyle = 'rgba(9,30,52,0.9)';
    ctx.fill();
    ctx.strokeStyle = '#2b618f';
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.fillStyle = '#cfe6fb';
    ctx.textAlign = 'left';
    ctx.font = '700 13px DM Sans, sans-serif';
    ctx.fillText('Execution outcomes to GitHub', x + 14, y + 24);

    const rows = [
      { text: 'OpenClaw commit_file -> DENY (PATH_NOT_ALLOWED)', tone: 'deny' },
      { text: 'LangGraph bounded workflow -> ALLOW (to GitHub)', tone: 'allow' },
      { text: 'Internal merge w/o approval -> DENY (APPROVAL_REQUIRED)', tone: 'deny' },
    ];
    rows.forEach((r, idx) => {
      const yy = y + 54 + idx * 36;
      ctx.fillStyle = r.tone === 'allow' ? '#66e7b0' : '#ff9f9f';
      ctx.font = '600 12px DM Sans, sans-serif';
      ctx.fillText(r.text, x + 14, yy);
    });
  }

  function drawCrossAgentSummary() {
    const x = 368;
    const y = 610;
    const w = 544;
    const h = 90;
    roundedRect(x, y, w, h, 12);
    ctx.fillStyle = 'rgba(9,30,52,0.88)';
    ctx.fill();
    ctx.strokeStyle = '#2b618f';
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.fillStyle = '#bfe2ff';
    ctx.textAlign = 'left';
    ctx.font = '700 13px DM Sans, sans-serif';
    ctx.fillText('Single Surfit boundary, same policy semantics across origins', x + 14, y + 22);

    const rows = [
      { left: 'OpenClaw', right: 'DENY  PATH_NOT_ALLOWED', tone: 'deny' },
      { left: 'LangGraph', right: 'ALLOW', tone: 'allow' },
      { left: 'Internal Automation', right: 'DENY  APPROVAL_REQUIRED', tone: 'deny' },
    ];

    rows.forEach((row, idx) => {
      const yy = y + 44 + idx * 15;
      ctx.fillStyle = '#9ec3e2';
      ctx.font = '600 12px DM Sans, sans-serif';
      ctx.fillText(row.left, x + 14, yy);
      ctx.fillStyle = row.tone === 'allow' ? '#66e7b0' : '#ff9f9f';
      ctx.fillText(row.right, x + 210, yy);
    });
  }

  function render(now) {
    const elapsed = running
      ? (now - startMs - pauseMs) / 1000
      : (pausedAt - startMs - pauseMs) / 1000;

    let t = Math.max(0, elapsed);
    if (loop) {
      t = t % totalSeconds;
    } else {
      t = Math.min(t, totalSeconds);
      if (t >= totalSeconds) running = false;
    }

    const meta = sceneAt(t);
    sceneLabel.textContent = `Scene ${meta.i + 1}/${scenes.length} • ${meta.scene.title}`;
    progressFill.style.width = `${(t / totalSeconds) * 100}%`;

    drawBg(t);

    // Static nodes
    agents.forEach(a => drawNode(a.x, a.y, a.name, a.c, 'rgba(12,34,59,0.95)'));
    systems.forEach(s => drawNode(s.x, s.y, s.name, '#3c6e9b', 'rgba(12,34,59,0.95)'));

    const pulse = ((t * 0.85) % 1);

    if (meta.i === 0) {
      // direct but neutral connectivity
      agents.forEach((a, idx) => {
        drawLink(a.x + 105, a.y, systems[idx % systems.length].x - 105, systems[idx % systems.length].y, 'normal', pulse);
      });
    }

    if (meta.i === 1) {
      const acts = ['commit_file', 'merge_pull_request', 'delete_resource', 'deploy_change'];
      agents.forEach((a, idx) => {
        const s = systems[idx];
        drawLink(a.x + 105, a.y, s.x - 105, s.y, idx % 2 === 0 ? 'deny' : 'active', (pulse + idx * 0.17) % 1);
      });
      acts.forEach((act, idx) => drawActionTag(640, 180 + idx * 86, act, idx < 2 ? 'deny' : 'allow'));
    }

    if (meta.i >= 2) {
      const intro = meta.i === 2 ? Math.min(1, meta.p * 1.8) : 1;
      drawSurfitBoundary(t, intro, meta.i >= 3);

      if (meta.i !== 3 && meta.i !== 5) {
        agents.forEach((a, idx) => {
          drawLink(a.x + 105, a.y, surfit.x - surfit.w / 2, 230 + idx * 130, 'active', (pulse + idx * 0.12) % 1);
        });

        systems.forEach((s, idx) => {
          const mode = (meta.i === 4 && idx === 0 && meta.p < 0.58) ? 'deny' : 'active';
          drawLink(surfit.x + surfit.w / 2, 235 + idx * 95, s.x - 105, s.y, mode, (pulse + idx * 0.09) % 1);
        });
      }
    }

    if (meta.i === 3) {
      const flow = (meta.p * 1.3) % 1;
      drawLink(agents[0].x + 105, agents[0].y, surfit.x - surfit.w / 2, 232, 'deny', flow);
      drawLink(agents[1].x + 105, agents[1].y, surfit.x - surfit.w / 2, 360, 'active', (flow + 0.25) % 1);
      drawLink(agents[2].x + 105, agents[2].y, surfit.x - surfit.w / 2, 488, 'deny', (flow + 0.5) % 1);

      drawStopMarker(surfit.x - surfit.w / 2 + 4, 232);
      drawStopMarker(surfit.x - surfit.w / 2 + 4, 488);
      drawLink(surfit.x + surfit.w / 2, 360, systems[0].x - 105, systems[0].y, 'active', (flow + 0.25) % 1);

      drawActionTag(316, agents[0].y - 34, 'commit_file', 'deny');
      drawActionTag(386, agents[1].y - 34, 'create_branch -> commit -> pr', 'allow');
      drawActionTag(350, agents[2].y - 34, 'merge_pull_request', 'deny');
      drawDecisionMatrix();
    }

    if (meta.i === 4) {
      drawApprovalFlow(meta.p);
    }

    if (meta.i === 5) {
      const flow = (meta.p * 1.15) % 1;
      drawLink(agents[0].x + 105, agents[0].y, surfit.x - surfit.w / 2, 232, 'deny', flow);
      drawLink(agents[1].x + 105, agents[1].y, surfit.x - surfit.w / 2, 360, 'active', (flow + 0.2) % 1);
      drawLink(agents[2].x + 105, agents[2].y, surfit.x - surfit.w / 2, 488, 'deny', (flow + 0.4) % 1);
      drawStopMarker(surfit.x - surfit.w / 2 + 4, 232);
      drawStopMarker(surfit.x - surfit.w / 2 + 4, 488);

      drawLink(surfit.x + surfit.w / 2, 360, systems[0].x - 105, systems[0].y, 'active', (flow + 0.2) % 1);
      drawLink(surfit.x + surfit.w / 2, 232, surfit.x + surfit.w / 2 + 72, 232, 'deny', flow);
      drawLink(surfit.x + surfit.w / 2, 488, surfit.x + surfit.w / 2 + 72, 488, 'deny', (flow + 0.4) % 1);
      drawStopMarker(surfit.x + surfit.w / 2 + 72, 232);
      drawStopMarker(surfit.x + surfit.w / 2 + 72, 488);

      drawCrossAgentSummary();
    }

    if (meta.i === 6) {
      drawSmallPill(640, 610, 'Surfit governs execution — not prompts.', 'allow');
      drawActionTag(640, 648, 'The execution boundary for AI agents', 'allow');
    }

    drawOverlay(meta.scene.title, meta.scene.text);

    rafId = requestAnimationFrame(render);
  }

  function pause() {
    if (!running) return;
    running = false;
    pausedAt = performance.now();
    playPauseBtn.textContent = 'Play';
  }

  function play() {
    if (running) return;
    running = true;
    pauseMs += performance.now() - pausedAt;
    playPauseBtn.textContent = 'Pause';
  }

  function restart(keepLoop = true) {
    startMs = performance.now();
    pauseMs = 0;
    pausedAt = 0;
    running = true;
    loop = keepLoop;
    playPauseBtn.textContent = 'Pause';
  }

  async function renderWebMBlob() {
    const mimeCandidates = [
      'video/webm;codecs=vp9',
      'video/webm;codecs=vp8',
      'video/webm',
    ];
    const mimeType = mimeCandidates.find(m => MediaRecorder.isTypeSupported(m)) || 'video/webm';

    const stream = canvas.captureStream(30);
    const recorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 8_500_000 });
    const chunks = [];

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunks.push(e.data);
    };

    const done = new Promise((resolve) => {
      recorder.onstop = () => resolve(new Blob(chunks, { type: mimeType }));
    });

    restart(false);
    recorder.start(250);

    await new Promise(r => setTimeout(r, (totalSeconds + 0.8) * 1000));
    recorder.stop();

    const blob = await done;
    stream.getTracks().forEach(t => t.stop());
    loop = true;
    restart(true);
    return blob;
  }

  async function blobToDataURL(blob) {
    return new Promise((resolve, reject) => {
      const fr = new FileReader();
      fr.onload = () => resolve(fr.result);
      fr.onerror = reject;
      fr.readAsDataURL(blob);
    });
  }

  async function exportWebM() {
    exportBtn.disabled = true;
    exportBtn.textContent = 'Rendering...';
    exportPathHint.textContent = 'Rendering 54s WebM locally...';
    try {
      const blob = await renderWebMBlob();
      const url = URL.createObjectURL(blob);
      exportPreview.src = url;
      const a = document.createElement('a');
      a.href = url;
      a.download = 'surfit-explainer-54s.webm';
      a.click();
      exportPathHint.textContent = `Generated ${Math.round(blob.size / (1024 * 1024) * 10) / 10} MB WebM.`;
      return blob;
    } finally {
      exportBtn.disabled = false;
      exportBtn.textContent = 'Export WebM';
    }
  }

  // Exposed for headless local export script.
  window.renderWebMDataURL = async () => {
    const blob = await renderWebMBlob();
    return blobToDataURL(blob);
  };

  playPauseBtn.addEventListener('click', () => (running ? pause() : play()));
  restartBtn.addEventListener('click', () => restart(true));
  exportBtn.addEventListener('click', exportWebM);

  restart(true);
  rafId = requestAnimationFrame(render);
})();
