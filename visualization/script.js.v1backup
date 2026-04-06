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
    { dur: 22, title: 'Segment 1 — The Shift' },
    { dur: 22, title: 'Segment 2 — The Missing Layer' },
    { dur: 26, title: 'Segment 3 — Runtime Action Evaluation' },
    { dur: 24, title: 'Segment 4 — Governance Evidence' },
    { dur: 24, title: 'Segment 5 — Multi-Stage Governance' },
    { dur: 24, title: 'Segment 6 — Cross-Agent Governance' },
    { dur: 20, title: 'Segment 7 — Category Definition' },
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
    { name: 'Internal Automation', x: 165, y: 540, c: '#27c2ff' },
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
    drawSurfitWaveFlow(t, x, y);

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

      });
    }

    ctx.restore();
  }

  function drawSurfitWaveFlow(t, x, y) {
    const left = x + 24;
    const right = x + surfit.w - 24;
    const width = right - left;
    const baseYs = [y + 96, y + 124, y + 152, y + 180, y + 208];
    baseYs.forEach((baseY, idx) => {
      ctx.beginPath();
      for (let i = 0; i <= 72; i++) {
        const px = left + (i / 72) * width;
        const phase = ((t * 1.8) + idx * 0.55 + i * 0.08);
        const py = baseY + Math.sin(phase) * (3 + idx * 0.3);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.strokeStyle = `rgba(39,194,255,${0.2 + idx * 0.06})`;
      ctx.lineWidth = 1.1;
      ctx.stroke();
    });
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
    const y = 642;
    const nodes = [
      'propose_change',
      'pull_request_created',
      'approval_artifact_required',
      'approval_granted',
      'merge_allowed',
    ];
    const startX = 160;
    const gap = 235;

    const positions = [];
    for (let i = 0; i < nodes.length; i++) {
      const x = startX + i * gap;
      positions.push(x);
      const active = progress > i / nodes.length;
      const isBlocked = i === 2 && progress < 0.62;
      drawActionTag(x, y, nodes[i], isBlocked ? 'deny' : (active ? 'allow' : 'idle'));
      if (i < nodes.length - 1) {
        drawLink(x + 72, y, x + gap - 72, y, isBlocked ? 'deny' : (active ? 'normal' : 'normal'), 0);
      }
    }

    // Single progression dot across the chain.
    const segments = nodes.length - 1;
    const phase = Math.min(0.999, progress) * segments;
    const segIdx = Math.floor(phase);
    const segP = phase - segIdx;
    const from = positions[segIdx] + 72;
    const to = positions[Math.min(segIdx + 1, segments)] - 72;
    const dotX = from + (to - from) * segP;
    ctx.beginPath();
    ctx.arc(dotX, y, 5, 0, Math.PI * 2);
    ctx.fillStyle = progress < 0.62 && segIdx >= 2 ? '#ff6e6e' : '#27c2ff';
    ctx.shadowColor = ctx.fillStyle;
    ctx.shadowBlur = 10;
    ctx.fill();
    ctx.shadowBlur = 0;
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

  function drawDecisionReasonsBottom() {
    const x = 280;
    const y = 594;
    const w = 760;
    const h = 96;
    roundedRect(x, y, w, h, 10);
    ctx.fillStyle = 'rgba(9,30,52,0.86)';
    ctx.fill();
    ctx.strokeStyle = '#2b618f';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.textAlign = 'left';
    ctx.font = '700 12px DM Sans, sans-serif';
    ctx.fillStyle = '#cfe6fb';
    ctx.fillText('Decision reasons', x + 14, y + 20);
    ctx.font = '600 12px DM Sans, sans-serif';
    ctx.fillStyle = '#ff9f9f';
    ctx.fillText('OpenClaw DENY: token_scope violation', x + 14, y + 44);
    ctx.fillText('Internal Automation DENY: runtime_rules + approval requirement', x + 14, y + 66);
    ctx.fillStyle = '#66e7b0';
    ctx.fillText('LangGraph ALLOW: policy_manifest + token_scope satisfied', x + 14, y + 86);
  }

  function drawClosingRecapPanel() {
    const x = 250;
    const y = 602;
    const w = 780;
    const h = 98;
    roundedRect(x, y, w, h, 10);
    ctx.fillStyle = 'rgba(9,30,52,0.86)';
    ctx.fill();
    ctx.strokeStyle = '#2b618f';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.textAlign = 'left';
    ctx.fillStyle = '#cfe6fb';
    ctx.font = '700 13px DM Sans, sans-serif';
    ctx.fillText('Surfit: execution governance for enterprise AI', x + 14, y + 24);
    ctx.font = '600 13px DM Sans, sans-serif';
    ctx.fillStyle = '#9ec3e2';
    ctx.fillText('Govern every agent action at runtime across repositories, infrastructure, and internal APIs.', x + 14, y + 50);
    ctx.fillText('Deterministic ALLOW/DENY + verifiable governance evidence before system mutation.', x + 14, y + 74);
  }

  function overlayLineForScene(sceneIndex, p) {
    const lines = [
      [
        'AI agents are beginning to interact directly with real systems.',
        'Repositories • Infrastructure • Internal APIs',
        'What governs what these agents are allowed to execute?',
      ],
      [
        'Surfit is an execution governance layer.',
        'The missing layer between agent intent and system mutation.',
        'Surfit governs execution, not prompts.',
      ],
      [
        'Every attempted action is evaluated at runtime.',
        'ALLOW or DENY.',
      ],
      [
        'Execution produces governance evidence.',
        'Export • Verify • Audit',
      ],
      [
        'Sensitive actions require approval.',
        'Proposal -> Approval -> Execution',
      ],
      [
        'Surfit governs execution across agent frameworks.',
        'Agent-neutral governance.',
      ],
      [
        'Orchestrators coordinate agents.',
        'Surfit governs execution.',
        'The execution governance layer for AI agents.',
      ],
    ];
    const sceneLines = lines[sceneIndex] || [''];
    const idx = Math.min(sceneLines.length - 1, Math.floor(p * sceneLines.length));
    return sceneLines[idx];
  }

  function drawVerticalArchitectureStack() {
    drawNode(640, 170, 'Agents / Orchestrators', '#2b7fbc', 'rgba(12,34,59,0.95)');
    drawSurfitBoundary(0.2, 1, false);
    drawNode(640, 560, 'Enterprise Systems', '#2b7fbc', 'rgba(12,34,59,0.95)');
    drawLink(640, 208, 640, 230, 'active', 0.5);
    drawLink(640, 486, 640, 522, 'active', 0.2);
  }

  function drawHorizontalMissingLayer(pulse) {
    drawNode(170, 250, 'Agents', '#2b7fbc', 'rgba(12,34,59,0.95)');
    drawNode(170, 470, 'Orchestrators', '#2b7fbc', 'rgba(12,34,59,0.95)');
    systems.forEach(s => drawNode(s.x, s.y, s.name, '#3c6e9b', 'rgba(12,34,59,0.95)'));
    drawSurfitBoundary(pulse, 1, false);
    drawLink(275, 250, surfit.x - surfit.w / 2, 300, 'active', (pulse * 0.8) % 1);
    drawLink(275, 470, surfit.x - surfit.w / 2, 430, 'active', (pulse * 0.9 + 0.3) % 1);
    drawLink(surfit.x + surfit.w / 2, 300, 1015, systems[0].y, 'active', (pulse + 0.1) % 1);
    drawLink(surfit.x + surfit.w / 2, 430, 1015, systems[2].y, 'active', (pulse + 0.45) % 1);
    drawActionTag(640, 620, 'Missing governance layer resolved', 'allow');
  }


  function drawBoundaryLaneHints() {
    drawActionTag(536, 214, 'token_scope check', 'info');
    drawActionTag(548, 360, 'policy_manifest check', 'allow');
    drawActionTag(548, 506, 'runtime_rules check', 'info');
  }

  function drawSegment2Narrative() {
    const x = 330;
    const y = 566;
    const w = 620;
    const h = 90;
    roundedRect(x, y, w, h, 10);
    ctx.fillStyle = 'rgba(9,30,52,0.88)';
    ctx.fill();
    ctx.strokeStyle = '#2b618f';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.textAlign = 'left';
    ctx.fillStyle = '#cfe6fb';
    ctx.font = '700 12px DM Sans, sans-serif';
    ctx.fillText('Missing Governance Layer Resolved', x + 14, y + 22);
    ctx.fillStyle = '#9ec3e2';
    ctx.font = '600 12px DM Sans, sans-serif';
    ctx.fillText('Orchestrators coordinate agents; Surfit governs execution to enterprise systems.', x + 14, y + 46);
    ctx.fillText('Actions cross the Surfit boundary only after runtime policy evaluation.', x + 14, y + 66);
  }

  function drawSystemProblemBadges(p) {
    const alerts = [
      { x: 1060, y: 112, text: 'unreviewed commit' },
      { x: 1060, y: 252, text: 'unsafe deploy risk' },
      { x: 1060, y: 392, text: 'schema mutation risk' },
      { x: 1060, y: 532, text: 'unauthorized API change' },
    ];
    alerts.forEach((a, idx) => {
      if (p > idx * 0.2) drawActionTag(a.x, a.y, a.text, 'deny');
    });
  }

  function drawLayerTapLabels() {
    drawActionTag(745, 525, 'OpenClaw blocked at token_scope', 'deny');
    drawActionTag(770, 560, 'Internal blocked by runtime_rules', 'deny');
    drawActionTag(825, 595, 'LangGraph allowed via policy_manifest + scope', 'allow');
  }

  function drawEvidenceBoard(p) {
    const x = 820;
    const y = 292;
    const w = 390;
    const h = 190;
    roundedRect(x, y, w, h, 10);
    ctx.fillStyle = 'rgba(9,30,52,0.9)';
    ctx.fill();
    ctx.strokeStyle = '#2b618f';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = '#cfe6fb';
    ctx.font = '700 13px DM Sans, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Governance Evidence', x + 14, y + 22);

    const rows = [
      { text: 'bundle_export: wave_bundle_*.json', tone: 'allow', gate: 0.15 },
      { text: 'offline_verify: PASS', tone: 'allow', gate: 0.45 },
      { text: 'server_audit: VALID', tone: 'allow', gate: 0.75 },
    ];
    rows.forEach((r, idx) => {
      if (p < r.gate) return;
      const yy = y + 52 + idx * 42;
      drawActionTag(x + 170, yy, r.text, r.tone);
    });
  }

  function drawEvidencePipeline(p) {
    const nodes = ['Execution Event', 'Export Bundle', 'Offline Verify', 'Server Audit'];
    const y = 652;
    const startX = 200;
    const gap = 285;
    for (let i = 0; i < nodes.length; i++) {
      const x = startX + i * gap;
      const active = p > (i / nodes.length);
      drawActionTag(x, y, nodes[i], active ? 'allow' : 'idle');
      if (i < nodes.length - 1) {
        drawLink(x + 82, y, x + gap - 82, y, active ? 'active' : 'normal', (p * 1.4) % 1);
      }
    }
    if (p > 0.7) drawSmallPill(1025, 688, 'audit_verify = VALID', 'allow');
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
    sceneLabel.textContent = `Segment ${meta.i + 1}/${scenes.length} • ${meta.scene.title}`;
    progressFill.style.width = `${(t / totalSeconds) * 100}%`;

    drawBg(t);
    const pulse = ((t * 0.65) % 1);

    if (meta.i === 0) {
      agents.forEach(a => drawNode(a.x, a.y, a.name, a.c, 'rgba(12,34,59,0.95)'));
      systems.forEach(s => drawNode(s.x, s.y, s.name, '#3c6e9b', 'rgba(12,34,59,0.95)'));
      drawLink(agents[0].x + 105, agents[0].y, systems[0].x - 105, systems[0].y, 'active', (pulse + 0.1) % 1);
      drawLink(agents[1].x + 105, agents[1].y, systems[1].x - 105, systems[1].y, 'active', (pulse + 0.3) % 1);
      drawLink(agents[1].x + 105, agents[1].y + 8, systems[2].x - 105, systems[2].y - 8, 'active', (pulse + 0.42) % 1);
      drawLink(agents[2].x + 105, agents[2].y, systems[3].x - 105, systems[3].y, 'active', (pulse + 0.55) % 1);
      drawActionTag(305, 148, 'commit_file', 'allow');
      drawActionTag(328, 284, 'merge_pull_request', 'allow');
      drawActionTag(350, 462, 'infrastructure_change', 'allow');
      drawSystemProblemBadges(meta.p);
    }

    if (meta.i === 1) {
      drawNode(86, 270, 'Agent 1', '#2b7fbc', 'rgba(12,34,59,0.95)');
      drawNode(86, 360, 'Agent 2', '#2b7fbc', 'rgba(12,34,59,0.95)');
      drawNode(86, 450, 'Agent 3', '#2b7fbc', 'rgba(12,34,59,0.95)');
      drawNode(300, 360, 'Orchestrator', '#2b7fbc', 'rgba(12,34,59,0.95)');
      systems.forEach(s => drawNode(s.x, s.y, s.name, '#3c6e9b', 'rgba(12,34,59,0.95)'));
      drawSurfitBoundary(t, 1, false);

      drawLink(191, 270, 196, 332, 'active', (pulse + 0.1) % 1);
      drawLink(191, 360, 196, 360, 'active', (pulse + 0.3) % 1);
      drawLink(191, 450, 196, 388, 'active', (pulse + 0.55) % 1);
      drawLink(405, 360, surfit.x - surfit.w / 2, 360, 'active', (pulse + 0.2) % 1);

      drawLink(surfit.x + surfit.w / 2, 250, systems[0].x - 105, systems[0].y, 'active', (pulse + 0.05) % 1);
      drawLink(surfit.x + surfit.w / 2, 328, systems[1].x - 105, systems[1].y, 'active', (pulse + 0.2) % 1);
      drawLink(surfit.x + surfit.w / 2, 406, systems[2].x - 105, systems[2].y, 'active', (pulse + 0.35) % 1);
      drawLink(surfit.x + surfit.w / 2, 486, systems[3].x - 105, systems[3].y, 'active', (pulse + 0.55) % 1);

      drawActionTag(640, 524, 'Agents / Orchestrators', 'allow');
      drawSegment2Narrative();
    }

    if (meta.i === 2) {
      agents.forEach(a => drawNode(a.x, a.y, a.name, a.c, 'rgba(12,34,59,0.95)'));
      systems.forEach(s => drawNode(s.x, s.y, s.name, '#3c6e9b', 'rgba(12,34,59,0.95)'));
      drawSurfitBoundary(t, 1, false);

      drawLink(agents[0].x + 105, agents[0].y, surfit.x - surfit.w / 2, 232, 'deny', pulse);
      drawLink(agents[1].x + 105, agents[1].y, surfit.x - surfit.w / 2, 360, 'active', (pulse + 0.2) % 1);
      drawLink(agents[2].x + 105, agents[2].y, surfit.x - surfit.w / 2, 488, 'deny', (pulse + 0.4) % 1);

      drawStopMarker(surfit.x - surfit.w / 2 + 2, 232);
      drawStopMarker(surfit.x - surfit.w / 2 + 2, 488);
      drawLink(surfit.x + surfit.w / 2, 360, systems[0].x - 105, systems[0].y, 'active', (pulse + 0.2) % 1);
      drawActionTag(312, 144, 'commit', 'deny');
      drawActionTag(334, 322, 'merge', 'allow');
      drawActionTag(350, 502, 'infra_change', 'deny');
      drawSmallPill(534, 214, 'DENY', 'deny');
      drawSmallPill(534, 506, 'DENY', 'deny');
      drawSmallPill(1020, 212, 'ALLOW -> GitHub', 'allow');
      drawDecisionReasonsBottom();
    }

    if (meta.i === 3) {
      drawNode(agents[1].x, agents[1].y, agents[1].name, agents[1].c, 'rgba(12,34,59,0.95)');
      drawNode(systems[0].x, systems[0].y, systems[0].name, '#3c6e9b', 'rgba(12,34,59,0.95)');
      drawSurfitBoundary(t, 1, false);
      drawLink(agents[1].x + 105, agents[1].y, surfit.x - surfit.w / 2, 360, 'active', pulse);
      drawLink(surfit.x + surfit.w / 2, 360, systems[0].x - 105, systems[0].y, 'active', pulse);
      drawEvidencePipeline(meta.p);
      drawEvidenceBoard(meta.p);
    }

    if (meta.i === 4) {
      agents.forEach(a => drawNode(a.x, a.y, a.name, a.c, 'rgba(12,34,59,0.95)'));
      systems.forEach(s => drawNode(s.x, s.y, s.name, '#3c6e9b', 'rgba(12,34,59,0.95)'));
      drawSurfitBoundary(t, 1, false);
      drawApprovalFlow(meta.p);
      drawLink(agents[1].x + 105, agents[1].y, surfit.x - surfit.w / 2, 360, 'active', pulse);
      if (meta.p > 0.62) {
        drawLink(surfit.x + surfit.w / 2, 360, systems[0].x - 105, systems[0].y, 'active', pulse);
        drawActionTag(980, 240, 'human approval artifact attached', 'allow');
      } else {
        drawLink(surfit.x + surfit.w / 2, 360, surfit.x + surfit.w / 2 + 44, 360, 'deny', pulse);
        drawStopMarker(surfit.x + surfit.w / 2 + 44, 360);
        drawActionTag(980, 240, 'awaiting human approval artifact', 'deny');
      }
    }

    if (meta.i === 5) {
      agents.forEach(a => drawNode(a.x, a.y, a.name, a.c, 'rgba(12,34,59,0.95)'));
      drawNode(systems[0].x, systems[0].y, systems[0].name, '#3c6e9b', 'rgba(12,34,59,0.95)');
      drawSurfitBoundary(t, 1, false);

      drawLink(agents[0].x + 105, agents[0].y, surfit.x - surfit.w / 2, 232, 'deny', pulse);
      drawLink(agents[1].x + 105, agents[1].y, surfit.x - surfit.w / 2, 360, 'active', (pulse + 0.25) % 1);
      drawLink(agents[2].x + 105, agents[2].y, surfit.x - surfit.w / 2, 488, 'deny', (pulse + 0.45) % 1);
      drawStopMarker(surfit.x - surfit.w / 2 + 2, 232);
      drawStopMarker(surfit.x - surfit.w / 2 + 2, 488);
      drawLink(surfit.x + surfit.w / 2, 360, systems[0].x - 105, systems[0].y, 'active', (pulse + 0.25) % 1);
      drawBoundaryLaneHints();
      drawCrossAgentSummary();
    }

    if (meta.i === 6) {
      agents.forEach(a => drawNode(a.x, a.y, a.name, a.c, 'rgba(12,34,59,0.95)'));
      systems.forEach(s => drawNode(s.x, s.y, s.name, '#3c6e9b', 'rgba(12,34,59,0.95)'));
      drawSurfitBoundary(t, 1, false);
      const cyc = meta.p;
      const burst = Math.floor(meta.p * 10) % 10;

      const topMode = burst % 2 ? 'active' : 'deny';
      const midMode = 'active';
      const lowMode = burst % 3 ? 'deny' : 'active';

      drawLink(agents[0].x + 105, agents[0].y, surfit.x - surfit.w / 2, 232, topMode, (pulse + cyc) % 1);
      drawLink(agents[1].x + 105, agents[1].y, surfit.x - surfit.w / 2, 360, midMode, (pulse + 0.27 + cyc) % 1);
      drawLink(agents[2].x + 105, agents[2].y, surfit.x - surfit.w / 2, 488, lowMode, (pulse + 0.61 + cyc) % 1);
      if (topMode === 'deny') drawStopMarker(surfit.x - surfit.w / 2 + 2, 232);
      if (lowMode === 'deny') drawStopMarker(surfit.x - surfit.w / 2 + 2, 488);

      const topAllowed = topMode === 'active';
      const midAllowed = true;
      const lowAllowed = lowMode === 'active';

      const topOutY = 300; // OpenClaw lane -> GitHub
      const midOutY = burst % 2 ? 360 : 420; // LangGraph alternates AWS/Databases
      const lowOutY = 430; // Internal lane -> Internal APIs

      if (topAllowed) {
        drawLink(surfit.x + surfit.w / 2, topOutY, systems[0].x - 105, systems[0].y, 'active', (pulse + cyc + 0.08) % 1);
      } else {
        drawLink(surfit.x + surfit.w / 2, topOutY, surfit.x + surfit.w / 2 + 42, topOutY, 'deny', (pulse + cyc + 0.08) % 1);
        drawStopMarker(surfit.x + surfit.w / 2 + 42, topOutY);
      }

      drawLink(surfit.x + surfit.w / 2, midOutY, (burst % 2 ? systems[1] : systems[2]).x - 105, (burst % 2 ? systems[1] : systems[2]).y, midAllowed ? 'active' : 'deny', (pulse + cyc + 0.24) % 1);

      if (lowAllowed) {
        drawLink(surfit.x + surfit.w / 2, lowOutY, systems[3].x - 105, systems[3].y, 'active', (pulse + cyc + 0.42) % 1);
      } else {
        drawLink(surfit.x + surfit.w / 2, lowOutY, surfit.x + surfit.w / 2 + 42, lowOutY, 'deny', (pulse + cyc + 0.42) % 1);
        drawStopMarker(surfit.x + surfit.w / 2 + 42, lowOutY);
      }

      drawBoundaryLaneHints();
      drawClosingRecapPanel();
    }

    drawOverlay(meta.scene.title, overlayLineForScene(meta.i, meta.p));

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
    exportPathHint.textContent = `Rendering ${Math.round(totalSeconds)}s WebM locally...`;
    try {
      const blob = await renderWebMBlob();
      const url = URL.createObjectURL(blob);
      exportPreview.src = url;
      const a = document.createElement('a');
      a.href = url;
      a.download = `surfit-visualization-${Math.round(totalSeconds)}s.webm`;
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
