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
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';

  const scenes = [
    { dur: 20, title: 'The Shift' },
    { dur: 24, title: 'Layers 1 & 2 — Then Failure' },
    { dur: 22, title: 'Layer 3 — The Execution Boundary' },
    { dur: 24, title: 'Wave Classification' },
    { dur: 22, title: 'Ripple Workflows' },
    { dur: 22, title: 'Agent Intelligence' },
    { dur: 22, title: 'Cross-System Threat Detection' },
    { dur: 20, title: 'Governance Evidence' },
    { dur: 24, title: 'Category Definition' },
  ];

  const totalSeconds = scenes.reduce((a, s) => a + s.dur, 0);
  const cumulative = [];
  scenes.reduce((acc, s) => { cumulative.push(acc); return acc + s.dur; }, 0);

  const C = {
    bgA: '#071227', bgB: '#081831',
    grid: 'rgba(62,97,140,0.18)',
    panel: '#0f2543', panelBorder: '#2d5a86',
    text: '#cfe4f8', muted: '#8cb0d1',
    blue: '#27c2ff', orange: '#ff7c2c',
    green: '#39d48f', red: '#ff6e6e',
    purple: '#a78bfa', yellow: '#eab308',
    w1: '#22c55e', w2: '#38bdf8', w3: '#eab308', w4: '#f97316', w5: '#ef4444',
    surfitGlow: 'rgba(38,194,255,0.06)',
  };

  let running = true;
  let startMs = performance.now();
  let pauseMs = 0;
  let pausedAt = 0;
  let rafId = null;

  // ── Drawing Primitives ──

  function drawBg(t) {
    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, C.bgA);
    grad.addColorStop(1, C.bgB);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);
    const step = 48;
    const drift = (t * 12) % step;
    ctx.strokeStyle = C.grid;
    ctx.lineWidth = 0.5;
    for (let x = -step + drift; x < W + step; x += step) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y < H; y += step) {
      ctx.beginPath(); ctx.moveTo(0, y + drift * 0.15); ctx.lineTo(W, y + drift * 0.15); ctx.stroke();
    }
  }

  function roundedRect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function drawNode(x, y, label, borderColor, w, h) {
    w = w || 180; h = h || 50;
    const nx = x - w / 2, ny = y - h / 2;
    roundedRect(nx, ny, w, h, 8);
    ctx.fillStyle = C.panel;
    ctx.fill();
    ctx.strokeStyle = borderColor || C.panelBorder;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = C.text;
    ctx.font = '600 15px "DM Sans", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, x, y);
  }

  function drawSurfitNode(x, y, w, h, t, showCredentials) {
    w = w || 280; h = h || 200;
    const nx = x - w / 2, ny = y - h / 2;
    // Glow
    const glow = ctx.createRadialGradient(x, y, 0, x, y, w * 0.8);
    glow.addColorStop(0, 'rgba(38,194,255,0.08)');
    glow.addColorStop(1, 'rgba(38,194,255,0)');
    ctx.fillStyle = glow;
    ctx.fillRect(nx - 60, ny - 60, w + 120, h + 120);
    // Border
    roundedRect(nx, ny, w, h, 12);
    ctx.fillStyle = 'rgba(10,30,55,0.95)';
    ctx.fill();
    ctx.strokeStyle = C.blue;
    ctx.lineWidth = 2;
    ctx.stroke();
    // Title
    ctx.font = '700 22px "Righteous", cursive';
    ctx.textAlign = 'center';
    ctx.fillStyle = C.blue;
    ctx.fillText('SURFIT', x - 12, ny + 32);
    ctx.fillStyle = C.orange;
    ctx.fillText('.AI', x + 52, ny + 32);
    // Wave lines inside
    ctx.strokeStyle = 'rgba(38,194,255,0.15)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 4; i++) {
      const wy = ny + 50 + i * 22;
      ctx.beginPath();
      for (let px = nx + 20; px < nx + w - 20; px += 2) {
        const wave = Math.sin((px + t * 60 + i * 40) * 0.03) * 6;
        if (px === nx + 20) ctx.moveTo(px, wy + wave);
        else ctx.lineTo(px, wy + wave);
      }
      ctx.stroke();
    }
    // Credential lock icon
    if (showCredentials) {
      ctx.font = '500 11px "DM Sans", sans-serif';
      ctx.fillStyle = C.green;
      ctx.textAlign = 'center';
      ctx.fillText('🔑 Holds all credentials', x, ny + h - 18);
    }
  }

  function drawPill(x, y, text, color, size) {
    size = size || 'normal';
    ctx.font = size === 'small' ? '600 10px "DM Sans", sans-serif' : '600 12px "DM Sans", sans-serif';
    const tw = ctx.measureText(text).width;
    const pw = tw + 16, ph = size === 'small' ? 20 : 24;
    roundedRect(x - pw / 2, y - ph / 2, pw, ph, ph / 2);
    ctx.fillStyle = color + '25';
    ctx.fill();
    ctx.strokeStyle = color + '80';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, x, y);
  }

  function drawArrow(x1, y1, x2, y2, color, pulse, dashed) {
    ctx.strokeStyle = color || C.blue;
    ctx.lineWidth = 2;
    if (dashed) ctx.setLineDash([6, 4]);
    else ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    // Bezier curve for smooth lines
    const mx = (x1 + x2) / 2;
    ctx.bezierCurveTo(mx, y1, mx, y2, x2, y2);
    ctx.stroke();
    ctx.setLineDash([]);
    // Pulse dot
    if (pulse !== undefined) {
      const t = pulse % 1;
      const px = x1 + (x2 - x1) * t;
      const py = y1 + (y2 - y1) * t;
      // Better bezier interpolation
      const bx = (1-t)*(1-t)*(1-t)*x1 + 3*(1-t)*(1-t)*t*mx + 3*(1-t)*t*t*mx + t*t*t*x2;
      const by = (1-t)*(1-t)*(1-t)*y1 + 3*(1-t)*(1-t)*t*y1 + 3*(1-t)*t*t*y2 + t*t*t*y2;
      ctx.beginPath();
      ctx.arc(bx, by, 4, 0, Math.PI * 2);
      ctx.fillStyle = color || C.blue;
      ctx.fill();
    }
  }

  function drawStraightArrow(x1, y1, x2, y2, color, pulse) {
    ctx.strokeStyle = color || C.blue;
    ctx.lineWidth = 2;
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    if (pulse !== undefined) {
      const t = pulse % 1;
      const px = x1 + (x2 - x1) * t;
      const py = y1 + (y2 - y1) * t;
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fillStyle = color || C.blue;
      ctx.fill();
    }
  }

  function drawStopX(x, y) {
    ctx.beginPath();
    ctx.arc(x, y, 10, 0, Math.PI * 2);
    ctx.fillStyle = C.red + '30';
    ctx.fill();
    ctx.strokeStyle = C.red;
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x - 5, y - 5); ctx.lineTo(x + 5, y + 5);
    ctx.moveTo(x + 5, y - 5); ctx.lineTo(x - 5, y + 5);
    ctx.stroke();
  }

  function drawText(x, y, text, size, color, align, font) {
    ctx.font = (font || '500') + ' ' + (size || 14) + 'px "DM Sans", sans-serif';
    ctx.fillStyle = color || C.text;
    ctx.textAlign = align || 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, x, y);
  }

  function drawHeading(x, y, text, subtitle) {
    roundedRect(x, y, 520, subtitle ? 58 : 42, 8);
    ctx.fillStyle = 'rgba(15,37,67,0.92)';
    ctx.fill();
    ctx.strokeStyle = C.panelBorder;
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.font = '700 18px "DM Sans", sans-serif';
    ctx.fillStyle = C.text;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(text, x + 16, y + 10);
    if (subtitle) {
      ctx.font = '400 13px "DM Sans", sans-serif';
      ctx.fillStyle = C.muted;
      ctx.fillText(subtitle, x + 16, y + 34);
    }
  }

  function drawInfoBox(x, y, w, h, lines, borderColor) {
    roundedRect(x, y, w, h, 8);
    ctx.fillStyle = 'rgba(15,37,67,0.9)';
    ctx.fill();
    ctx.strokeStyle = borderColor || C.panelBorder;
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.font = '400 12px "DM Sans", sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    lines.forEach((line, i) => {
      ctx.fillStyle = line.color || C.muted;
      ctx.font = (line.bold ? '600' : '400') + ' ' + (line.size || 12) + 'px "DM Sans", sans-serif';
      ctx.fillText(line.text, x + 14, y + 12 + i * 18);
    });
  }

  function fadeIn(p, start, dur) {
    if (p < start) return 0;
    if (p > start + dur) return 1;
    return (p - start) / dur;
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

  // ── Agent & System positions ──
  const agents = [
    { name: 'OpenClaw', y: 200 },
    { name: 'LangGraph', y: 360 },
    { name: 'Internal Agent', y: 520 },
  ];
  const agentX = 150;

  const systems = [
    { name: 'GitHub', y: 170 },
    { name: 'AWS', y: 300 },
    { name: 'Slack', y: 430 },
    { name: 'Gmail', y: 560 },
  ];
  const sysX = 1130;
  const surfitX = 640, surfitY = 360;

  // ── SCENE RENDERERS ──

  function drawScene0(t, p, pulse) {
    // The Shift — agents directly hitting systems, no governance
    drawHeading(40, 30, 'The Shift', 'Agents are acting directly on production systems.');

    agents.forEach(a => drawNode(agentX, a.y, a.name, C.blue));
    systems.forEach(s => drawNode(sysX, s.y, s.name, C.panelBorder));

    // Direct connections — no governance
    drawArrow(agentX + 90, agents[0].y, sysX - 90, systems[0].y, C.blue, (pulse + 0.1) % 1);
    drawArrow(agentX + 90, agents[1].y, sysX - 90, systems[1].y, C.blue, (pulse + 0.3) % 1);
    drawArrow(agentX + 90, agents[1].y + 10, sysX - 90, systems[2].y, C.blue, (pulse + 0.5) % 1);
    drawArrow(agentX + 90, agents[2].y, sysX - 90, systems[3].y, C.blue, (pulse + 0.7) % 1);

    // Action labels
    drawPill(400, 175, 'merge_pr', C.blue, 'small');
    drawPill(420, 310, 'modify_iam', C.blue, 'small');
    drawPill(440, 450, 'post_message', C.blue, 'small');
    drawPill(400, 540, 'send_email', C.blue, 'small');

    // Problem badges appear over time
    if (p > 0.4) {
      drawPill(sysX + 10, systems[0].y - 40, 'unreviewed merge', C.red, 'small');
    }
    if (p > 0.6) {
      drawPill(sysX + 10, systems[1].y - 40, 'unauthorized IAM change', C.red, 'small');
    }
    if (p > 0.8) {
      drawPill(sysX + 10, systems[3].y - 40, 'external email — wrong attachment', C.red, 'small');
    }

    // Bottom text
    if (p > 0.5) {
      drawText(640, 670, 'No governance layer. Every agent holds credentials and executes directly.', 14, C.red, 'center');
    }
  }

  function drawScene1(t, p, pulse) {
    // Layer 1 + 2 combined, then failure
    drawHeading(40, 30, 'Layers 1 & 2 — Then Failure', 'Every check passes. The agent still executes on its own.');

    // Agent
    drawNode(130, 360, 'AI Agent', C.blue);
    drawPill(130, 310, '🔑 holds credentials', C.orange, 'small');

    // Layer 1 box
    const l1x = 340, l1y = 200;
    roundedRect(l1x - 80, l1y - 60, 160, 120, 10);
    ctx.fillStyle = 'rgba(34,197,94,0.08)';
    ctx.fill();
    ctx.strokeStyle = C.green + '60';
    ctx.lineWidth = 1;
    ctx.stroke();
    drawText(l1x, l1y - 40, 'LAYER 1', 10, C.green, 'center', '700');
    drawText(l1x, l1y - 18, 'Guardrails AI', 11, C.text, 'center', '500');
    drawText(l1x, l1y, 'NeMo Guardrails', 11, C.text, 'center', '500');
    drawText(l1x, l1y + 18, 'CTGT / Mentat', 11, C.text, 'center', '500');
    if (p > 0.15) drawPill(l1x, l1y + 48, '✓ output safe', C.green, 'small');

    // Layer 2 box
    const l2x = 560, l2y = 200;
    roundedRect(l2x - 90, l2y - 60, 180, 120, 10);
    ctx.fillStyle = 'rgba(167,139,250,0.08)';
    ctx.fill();
    ctx.strokeStyle = C.purple + '60';
    ctx.lineWidth = 1;
    ctx.stroke();
    drawText(l2x, l2y - 40, 'LAYER 2', 10, C.purple, 'center', '700');
    drawText(l2x, l2y - 18, 'IronCurtain', 11, C.text, 'center', '500');
    drawText(l2x, l2y, 'NemoClaw / OpenShell', 11, C.text, 'center', '500');
    drawText(l2x, l2y + 18, 'Cisco DefenseClaw', 11, C.text, 'center', '500');
    if (p > 0.3) drawPill(l2x, l2y + 48, '✓ access permitted', C.purple, 'small');

    // Empty Layer 3
    const l3x = 790, l3y = 200;
    roundedRect(l3x - 70, l3y - 40, 140, 80, 10);
    ctx.fillStyle = 'rgba(255,255,255,0.02)';
    ctx.fill();
    ctx.strokeStyle = C.red + '40';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
    drawText(l3x, l3y - 14, 'LAYER 3', 10, C.red, 'center', '700');
    drawText(l3x, l3y + 6, 'NO LAYER HERE', 12, C.red, 'center', '600');

    // System
    drawNode(1050, 360, 'Production', C.panelBorder);

    // Flow arrows
    drawStraightArrow(220, 360, 260, 280, C.blue, p > 0.1 ? (pulse + 0.2) % 1 : undefined);
    if (p > 0.2) drawStraightArrow(420, 260, 470, 260, C.blue, (pulse + 0.3) % 1);
    if (p > 0.4) drawStraightArrow(650, 260, 720, 260, C.blue, (pulse + 0.4) % 1);
    if (p > 0.5) drawStraightArrow(860, 260, 960, 360, C.blue, (pulse + 0.5) % 1);

    // Catastrophe
    if (p > 0.6) {
      roundedRect(780, 420, 360, 120, 10);
      ctx.fillStyle = 'rgba(239,68,68,0.1)';
      ctx.fill();
      ctx.strokeStyle = C.red + '60';
      ctx.lineWidth = 1;
      ctx.stroke();
      drawText(800, 445, 'CATASTROPHE', 14, C.red, 'left', '700');
      drawText(800, 468, 'Agent merges untested code to production.', 12, C.text, 'left');
      drawText(800, 488, 'Payments break. 14,000 transactions fail.', 12, C.text, 'left');
      drawText(800, 508, 'Every layer said yes. Nobody checked business context.', 11, C.muted, 'left');
    }

    // Bottom repeating line
    if (p > 0.7) {
      drawText(640, 660, 'The agent still executes on its own.', 16, C.red, 'center', '600');
    }
  }

  function drawScene2(t, p, pulse) {
    // Layer 3 — Surfit appears
    drawHeading(40, 30, 'Layer 3 — The Execution Boundary', 'The agent proposes. Surfit decides. Surfit executes.');

    // Agent side
    drawNode(130, 300, 'AI Agent', C.blue);
    drawPill(130, 255, 'No credentials', C.orange, 'small');
    drawText(130, 345, 'Proposes action', 11, C.muted, 'center');

    // Surfit
    drawSurfitNode(520, 360, 340, 280, t, true);

    // Inside Surfit labels
    const sx = 520, sy = 360;
    if (p > 0.2) drawText(sx, sy - 55, 'EVALUATE', 14, C.blue, 'center', '700');
    if (p > 0.3) drawText(sx, sy - 32, 'Business context • Risk • Destination', 12, C.muted, 'center');
    if (p > 0.4) drawText(sx, sy + 0, 'CLASSIFY', 14, C.orange, 'center', '700');
    if (p > 0.45) drawText(sx, sy + 22, 'Wave 1-5 deterministic scoring', 12, C.muted, 'center');
    if (p > 0.55) drawText(sx, sy + 52, 'ENFORCE', 14, C.green, 'center', '700');
    if (p > 0.6) drawText(sx, sy + 74, 'Execute or hold for approval', 12, C.muted, 'center');

    // Systems
    drawNode(1020, 190, 'Slack', C.panelBorder, 150, 44);
    drawNode(1020, 280, 'GitHub', C.panelBorder, 150, 44);
    drawNode(1020, 370, 'AWS', C.panelBorder, 150, 44);
    drawNode(1020, 460, 'Gmail', C.panelBorder, 150, 44);

    // Arrows
    drawArrow(220, 300, 350, 340, C.blue, (pulse + 0.1) % 1);
    if (p > 0.5) {
      drawArrow(690, 270, 945, 190, C.green, (pulse + 0.2) % 1);
      drawPill(870, 170, 'Wave 1 ✓', C.w1, 'small');
      drawArrow(690, 310, 945, 280, C.green, (pulse + 0.35) % 1);
      drawPill(870, 258, 'Wave 2 ✓', C.w2, 'small');
    }
    if (p > 0.65) {
      drawArrow(690, 380, 945, 370, C.orange, (pulse + 0.5) % 1);
      drawPill(870, 348, 'Wave 4 ⏸', C.w4, 'small');
      drawStopX(830, 390);
    }
    if (p > 0.75) {
      drawArrow(690, 430, 945, 460, C.green, (pulse + 0.65) % 1);
      drawPill(870, 484, 'Wave 2 ✓', C.w2, 'small');
    }

    // Bottom text
    drawText(640, 635, 'The agent cannot reach any system without going through Surfit.', 16, C.blue, 'center', '600');
    drawText(640, 662, 'Architectural enforcement — not policy.', 14, C.muted, 'center');
  }

  function drawScene3(t, p, pulse) {
    // Wave Classification
    drawHeading(40, 30, 'Wave Classification', 'Deterministic. Explainable. Sub-100ms. No LLM.');

    // Default waves example — X post
    if (p < 0.5) {
      drawNode(200, 250, 'X Agent', C.blue, 160, 44);
      drawSurfitNode(580, 320, 260, 180, t, false);
      drawNode(1000, 250, 'X (Twitter)', C.panelBorder, 160, 44);

      drawArrow(280, 250, 450, 290, C.blue, (pulse + 0.1) % 1);
      drawPill(360, 230, 'post_tweet', C.blue, 'small');

      // Inside Surfit — wave calculation
      drawText(580, 260, 'System: X → base 2', 14, C.text, 'center');
      drawText(580, 285, 'Action: post_tweet → +0', 14, C.text, 'center');
      drawText(580, 310, 'Content: neutral → +0', 14, C.text, 'center');
      drawText(580, 345, 'Final: Wave 2', 18, C.w2, 'center', '700');
      drawText(580, 372, 'Auto-execute ✓', 14, C.green, 'center', '600');

      if (p > 0.3) {
        drawArrow(710, 280, 920, 250, C.green, (pulse + 0.3) % 1);
        drawPill(830, 240, 'Wave 2 — Automatic', C.w2, 'small');
      }

      // Wave scale at bottom
      const waveY = 500;
      const waveColors = [C.w1, C.w2, C.w3, C.w4, C.w5];
      const waveLabels = ['Auto', 'Auto', 'Auto', 'Approval', 'Approval'];
      for (let i = 0; i < 5; i++) {
        const wx = 280 + i * 150;
        ctx.beginPath();
        ctx.arc(wx, waveY, 22, 0, Math.PI * 2);
        ctx.fillStyle = waveColors[i] + '25';
        ctx.fill();
        ctx.strokeStyle = waveColors[i];
        ctx.lineWidth = 2;
        ctx.stroke();
        drawText(wx, waveY, String(i + 1), 16, waveColors[i], 'center', '700');
        drawText(wx, waveY + 34, waveLabels[i], 11, C.muted, 'center');
      }
      drawText(640, 560, '80%+ of actions auto-execute at Wave 1-3. Zero human involvement.', 12, C.muted, 'center');

    } else { // Custom policy section - more time
      // Custom policy example via NL parser
      drawText(640, 150, 'Custom Policy via Natural Language Parser', 16, C.blue, 'center', '600');

      // NL input box
      roundedRect(140, 190, 540, 60, 8);
      ctx.fillStyle = 'rgba(15,37,67,0.9)';
      ctx.fill();
      ctx.strokeStyle = C.blue + '40';
      ctx.lineWidth = 1;
      ctx.stroke();
      drawText(160, 210, '"External emails with attachments should require', 12, C.text, 'left');
      drawText(160, 228, '  approval unless the recipient is at @acme.com"', 12, C.text, 'left');

      // Arrow to parsed result
      drawStraightArrow(640, 250, 640, 290, C.blue, (pulse + 0.2) % 1);
      drawPill(740, 270, 'Parse Policy', C.blue, 'small');

      // Parsed rules
      drawInfoBox(140, 300, 500, 100, [
        { text: 'PARSED RESULT', size: 10, color: C.green, bold: true },
        { text: 'Gmail / send_email → Wave 4 (Approval)', color: C.text },
        { text: 'Destination: NOT @acme.com', color: C.muted },
        { text: 'Context: has_attachment = true', color: C.muted },
      ], C.green);

      drawInfoBox(140, 420, 500, 80, [
        { text: 'EXCEPTION RULE', size: 10, color: C.w2, bold: true },
        { text: 'Gmail / send_email → Wave 2 (Auto)', color: C.text },
        { text: 'Destination: @acme.com — trusted partner domain', color: C.muted },
      ], C.w2);

      // Visual representation
      drawNode(920, 470, 'Gmail', C.panelBorder, 150, 48);
      drawArrow(640, 460, 830, 450, C.w4, (pulse + 0.3) % 1);
      drawPill(750, 430, 'Wave 4 ⏸', C.w4, 'small');
      drawArrow(640, 540, 830, 490, C.green, (pulse + 0.5) % 1);
      drawPill(750, 520, 'Wave 2 ✓ @acme.com', C.w2, 'small');

      drawText(640, 560, 'Business rules in plain english → deterministic enforcement.', 13, C.muted, 'center');
      drawText(640, 585, 'LLM parses the rule. No LLM in the scoring path.', 12, C.blue, 'center');
    }
  }

  function drawScene4(t, p, pulse) {
    // Ripple Workflows
    drawHeading(40, 30, 'Ripple Workflows', 'Cross-system action chains. Every step governed independently.');

    // Chain: GitHub PR merge → Slack notification → AWS deploy
    const nodes = [
      { x: 180, y: 300, label: 'GitHub', action: 'PR Merge' },
      { x: 500, y: 300, label: 'Slack', action: 'Notify #eng' },
      { x: 820, y: 300, label: 'AWS', action: 'Deploy Lambda' },
    ];

    // Surfit evaluation boxes between each
    const surfitEvals = [
      { x: 340, y: 300, wave: 3, result: 'Auto ✓' },
      { x: 660, y: 300, wave: 1, result: 'Auto ✓' },
      { x: 980, y: 300, wave: 4, result: 'Held ⏸' },
    ];

    // Draw chain with progressive reveal
    nodes.forEach((n, i) => {
      if (p > i * 0.25) {
        drawNode(n.x, n.y, n.label, C.panelBorder, 140, 44);
        drawText(n.x, n.y + 36, n.action, 11, C.muted, 'center');
      }
    });

    // Arrows and Surfit eval boxes
    if (p > 0.15) {
      drawStraightArrow(250, 300, 300, 300, C.blue, (pulse + 0.1) % 1);
      // Surfit eval mini-box
      roundedRect(300, 278, 80, 44, 6);
      ctx.fillStyle = 'rgba(10,30,55,0.95)';
      ctx.fill();
      ctx.strokeStyle = C.blue + '60';
      ctx.lineWidth = 1;
      ctx.stroke();
      drawText(340, 292, 'Wave 3', 11, C.w3, 'center', '700');
      drawText(340, 308, 'Auto ✓', 10, C.green, 'center');
      drawStraightArrow(380, 300, 430, 300, C.green, (pulse + 0.2) % 1);
    }

    if (p > 0.4) {
      drawStraightArrow(570, 300, 620, 300, C.blue, (pulse + 0.3) % 1);
      roundedRect(620, 278, 80, 44, 6);
      ctx.fillStyle = 'rgba(10,30,55,0.95)';
      ctx.fill();
      ctx.strokeStyle = C.blue + '60';
      ctx.lineWidth = 1;
      ctx.stroke();
      drawText(660, 292, 'Wave 1', 11, C.w1, 'center', '700');
      drawText(660, 308, 'Auto ✓', 10, C.green, 'center');
      drawStraightArrow(700, 300, 750, 300, C.green, (pulse + 0.4) % 1);
    }

    if (p > 0.6) {
      drawStraightArrow(890, 300, 940, 300, C.blue, (pulse + 0.5) % 1);
      roundedRect(940, 278, 80, 44, 6);
      ctx.fillStyle = 'rgba(10,30,55,0.95)';
      ctx.fill();
      ctx.strokeStyle = C.w4 + '60';
      ctx.lineWidth = 1.5;
      ctx.stroke();
      drawText(980, 292, 'Wave 4', 11, C.w4, 'center', '700');
      drawText(980, 308, 'Held ⏸', 10, C.orange, 'center');
      drawStopX(1040, 300);
    }

    // Visual flow label
    if (p > 0.3) {
      drawText(340, 400, '→ PR merges (Wave 3, auto)', 12, C.green, 'center');
    }
    if (p > 0.5) {
      drawText(660, 400, '→ Slack notifies (Wave 1, auto)', 12, C.green, 'center');
    }
    if (p > 0.7) {
      drawText(980, 400, '→ AWS deploy held (Wave 4)', 12, C.orange, 'center');
    }

    // Ripple visualization — connecting wave lines
    if (p > 0.3) {
      ctx.strokeStyle = C.blue + '20';
      ctx.lineWidth = 1;
      for (let i = 0; i < 3; i++) {
        const wy = 470 + i * 20;
        ctx.beginPath();
        for (let px = 100; px < 1180; px += 2) {
          const wave = Math.sin((px + t * 40 + i * 30) * 0.015) * 8;
          if (px === 100) ctx.moveTo(px, wy + wave);
          else ctx.lineTo(px, wy + wave);
        }
        ctx.stroke();
      }
    }

    drawText(640, 560, 'One trigger. Multiple systems. Each step scored independently.', 13, C.blue, 'center');
    drawText(640, 585, 'Different risk at every step. Same governance chain.', 12, C.muted, 'center');
  }

  function drawScene5(t, p, pulse) {
    // Agent Intelligence
    drawHeading(40, 30, 'Agent Intelligence', 'Trust scores, budget gates, anomaly detection.');

    // Agent cards
    const agentData = [
      { name: 'x-agent', trust: 72, actions: 156, status: 'Building', color: C.blue },
      { name: 'deploy-bot', trust: 91, actions: 420, status: 'Established', color: C.green },
      { name: 'email-agent', trust: 34, actions: 18, status: 'New', color: C.yellow },
    ];

    agentData.forEach((a, i) => {
      const ax = 200 + i * 320, ay = 200;
      roundedRect(ax - 130, ay - 50, 260, 200, 10);
      ctx.fillStyle = C.panel;
      ctx.fill();
      ctx.strokeStyle = a.color + '40';
      ctx.lineWidth = 1;
      ctx.stroke();

      drawText(ax, ay - 30, a.name, 14, C.text, 'center', '600');
      drawText(ax, ay - 8, a.status, 11, a.color, 'center', '600');

      // Trust bar
      const barW = 200, barH = 8, barX = ax - barW / 2, barY = ay + 16;
      roundedRect(barX, barY, barW, barH, 4);
      ctx.fillStyle = 'rgba(255,255,255,0.06)';
      ctx.fill();
      const fillW = Math.min(barW * (a.trust / 100) * fadeIn(p, i * 0.15, 0.3), barW);
      if (fillW > 0) {
        roundedRect(barX, barY, fillW, barH, 4);
        ctx.fillStyle = a.color;
        ctx.fill();
      }
      drawText(ax + barW / 2 + 10, barY + 4, String(a.trust), 12, a.color, 'left', '700');

      drawText(ax - 80, ay + 50, a.actions + ' actions', 12, C.muted, 'left');
      // Individual stats
      if (p > 0.3) {
        const stats = [
          ['Approved: 142 | Rejected: 14', 'Approved: 408 | Rejected: 12', 'Approved: 10 | Rejected: 8'],
          ['Systems: X, Slack', 'Systems: GitHub, AWS, Slack', 'Systems: Gmail, Outlook'],
          ['Budget: 200/day', 'Budget: 500/day', 'Budget: 50/day'],
        ];
        stats.forEach((row, si) => {
          drawText(ax - 80, ay + 68 + si * 14, row[i], 10, C.muted, 'left');
        });
      }
    });

    // Key insight box
    if (p > 0.4) {
      roundedRect(140, 400, 500, 70, 8);
      ctx.fillStyle = 'rgba(255,115,30,0.08)';
      ctx.fill();
      ctx.strokeStyle = C.orange + '40';
      ctx.lineWidth = 1;
      ctx.stroke();
      drawText(160, 420, 'CRITICAL: Trust scores DO NOT lower Wave classification.', 12, C.orange, 'left', '600');
      drawText(160, 440, 'A trusted agent (score 91) still gets Wave 5 on modify_iam.', 12, C.text, 'left');
      drawText(160, 458, 'Trust affects budget gates and session limits — never risk scoring.', 11, C.muted, 'left');
    }

    // Anomaly detection
    if (p > 0.6) {
      roundedRect(700, 400, 440, 70, 8);
      ctx.fillStyle = 'rgba(239,68,68,0.08)';
      ctx.fill();
      ctx.strokeStyle = C.red + '40';
      ctx.lineWidth = 1;
      ctx.stroke();
      drawText(720, 420, 'ANOMALY DETECTED', 11, C.red, 'left', '700');
      drawText(720, 440, 'email-agent: 200 actions in 10 minutes (baseline: 5/hour)', 12, C.text, 'left');
      drawText(720, 458, 'Burst activity flagged → escalated to operator', 11, C.muted, 'left');
    }

    drawText(640, 560, 'Behavioral monitoring without compromising deterministic scoring.', 13, C.blue, 'center');
  }

  function drawScene6(t, p, pulse) {
    // Cross-System Threat Detection
    drawHeading(40, 30, 'Cross-System Threat Detection', 'Individual actions look safe. The pattern reveals intent.');

    // Show 3 individual actions
    const actions = [
      { sys: 'GitHub', action: 'merge_pr', wave: 3, x: 280, y: 200 },
      { sys: 'AWS', action: 'modify_iam', wave: 3, x: 640, y: 200 },
      { sys: 'Gmail', action: 'send_email (ext)', wave: 3, x: 1000, y: 200 },
    ];

    actions.forEach((a, i) => {
      if (p > i * 0.12) {
        drawNode(a.x, a.y, a.sys, C.panelBorder, 180, 50);
        drawPill(a.x, a.y + 42, a.action, C.w3);
        drawPill(a.x, a.y + 68, 'Wave ' + a.wave + ' — looks safe', C.w3);
      }
    });

    // Timeline connection
    if (p > 0.35) {
      ctx.strokeStyle = C.red + '30';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(380, 200); ctx.lineTo(900, 200);
      ctx.stroke();
      ctx.setLineDash([]);
      drawText(640, 180, '< 30 minutes apart >', 11, C.red, 'center');
    }

    // Correlation engine fires
    if (p > 0.5) {
      roundedRect(180, 340, 920, 130, 10);
      ctx.fillStyle = 'rgba(239,68,68,0.1)';
      ctx.fill();
      ctx.strokeStyle = C.red + '60';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      drawText(220, 368, 'CORRELATION ENGINE — SUSPICIOUS PATTERN DETECTED', 14, C.red, 'left', '700');
      drawText(220, 395, 'Rule: "Code change + IAM modification + external email within 30 min"', 14, C.text, 'left');
      drawText(220, 418, 'Agent may be compromised. Pattern matches known exfiltration sequence.', 13, C.muted, 'left');
      drawText(220, 441, 'Individual scores overridden. All actions escalated.', 13, C.muted, 'left');

      drawPill(940, 370, 'ESCALATE → Wave 5', C.w5, 'normal');
    }

    // Result
    if (p > 0.7) {
      drawText(640, 520, 'All 3 actions held for operator review.', 16, C.red, 'center', '600');
      drawText(640, 548, 'Each action was Wave 3 individually. The cross-system pattern triggered Wave 5.', 13, C.muted, 'center');
      drawText(640, 572, 'Possible compromised agent — rogue or prompt-injected.', 13, C.orange, 'center');
    }

    drawText(640, 620, 'Per-system monitoring misses this. Surfit sees across all systems.', 13, C.blue, 'center');
  }

  function drawScene7(t, p, pulse) {
    // Governance Evidence
    drawHeading(40, 30, 'Governance Evidence', 'Not logging — proof.');

    // Receipt chain
    const receipts = [
      { id: '0x3a8f...', sys: 'Slack', action: 'post_message', wave: 1, decision: 'Auto' },
      { id: '0x7c2d...', sys: 'GitHub', action: 'merge_pr', wave: 4, decision: 'Approved' },
      { id: '0xb1e4...', sys: 'AWS', action: 'deploy_lambda', wave: 3, decision: 'Auto' },
      { id: '0xf5a9...', sys: 'Gmail', action: 'send_email', wave: 2, decision: 'Auto' },
    ];

    const chainX = 180;
    receipts.forEach((r, i) => {
      const ry = 160 + i * 90;
      if (p > i * 0.15) {
        roundedRect(chainX, ry, 480, 68, 8);
        ctx.fillStyle = C.panel;
        ctx.fill();
        ctx.strokeStyle = C.panelBorder;
        ctx.lineWidth = 1;
        ctx.stroke();

        drawText(chainX + 14, ry + 18, r.sys + ' / ' + r.action, 13, C.text, 'left', '600');
        drawText(chainX + 14, ry + 38, 'Hash: ' + r.id, 11, C.blue, 'left');
        drawText(chainX + 14, ry + 54, r.decision + ' by ' + (r.wave >= 4 ? 'operator' : 'engine'), 10, C.muted, 'left');

        const wc = [C.w1, C.w2, C.w3, C.w4, C.w5][r.wave - 1];
        drawPill(chainX + 420, ry + 20, 'Wave ' + r.wave, wc, 'small');
        drawPill(chainX + 420, ry + 48, '✓ Verified', C.green, 'small');

        // Chain link
        if (i > 0) {
          drawStraightArrow(chainX + 240, ry - 22, chainX + 240, ry, C.blue + '40');
          drawText(chainX + 260, ry - 11, 'prev_hash links', 9, C.blue + '60', 'left');
        }
      }
    });

    // Right side — compliance report
    if (p > 0.5) {
      roundedRect(720, 160, 380, 220, 10);
      ctx.fillStyle = 'rgba(34,197,94,0.06)';
      ctx.fill();
      ctx.strokeStyle = C.green + '40';
      ctx.lineWidth = 1;
      ctx.stroke();

      drawText(740, 185, 'COMPLIANCE REPORT', 11, C.green, 'left', '700');
      drawText(740, 210, 'Date range: March 1 - April 6, 2026', 11, C.text, 'left');
      drawText(740, 235, 'Total governed actions: 847', 11, C.text, 'left');
      drawText(740, 255, 'Auto-executed: 712 (84%)', 11, C.green, 'left');
      drawText(740, 275, 'Held for approval: 135 (16%)', 11, C.orange, 'left');
      drawText(740, 295, 'Credential access events: 55', 11, C.text, 'left');
      drawText(740, 320, 'Hash chain: ✓ Integrity verified', 11, C.green, 'left');
      drawText(740, 345, 'Exportable • Auditable • Tamper-evident', 10, C.muted, 'left');
    }

    drawText(640, 560, 'Every action receipted. Every receipt hash-chained.', 13, C.blue, 'center');
    drawText(640, 585, 'If any receipt is modified, the chain breaks. Cryptographically detectable.', 12, C.muted, 'center');
  }

  function drawScene8(t, p, pulse) {
    // Category Definition
    drawHeading(40, 30, 'Category Definition', 'Everyone builds smart and safe. Surfit is correct.');

    // Full stack visual
    const layers = [
      { label: 'LAYER 1 — MODEL', desc: '"Is the output safe?"', tools: 'Guardrails AI • CTGT • NeMo Guardrails', color: C.green, tag: 'Smart' },
      { label: 'LAYER 2 — RUNTIME', desc: '"Is this allowed?"', tools: 'IronCurtain • NemoClaw • Cisco • Microsoft • CrowdStrike', color: C.purple, tag: 'Safe' },
      { label: 'LAYER 3 — DECISION', desc: '"Should this happen right now?"', tools: 'Surfit', color: C.blue, tag: 'Correct' },
    ];

    layers.forEach((l, i) => {
      const ly = 130 + i * 130;
      const lw = i === 2 ? 700 : 600;
      const lx = i === 2 ? 290 : 340;

      if (p > i * 0.15) {
        roundedRect(lx, ly, lw, 100, 10);
        ctx.fillStyle = i === 2 ? 'rgba(38,194,255,0.08)' : 'rgba(255,255,255,0.02)';
        ctx.fill();
        ctx.strokeStyle = l.color + (i === 2 ? '80' : '30');
        ctx.lineWidth = i === 2 ? 2 : 1;
        ctx.stroke();

        drawText(lx + 16, ly + 20, l.label, 12, l.color, 'left', '700');
        drawText(lx + 16, ly + 42, l.desc, 14, C.text, 'left', '500');
        drawText(lx + 16, ly + 64, l.tools, 11, C.muted, 'left');

        // Tag on right
        drawPill(lx + lw - 50, ly + 20, l.tag, l.color, 'small');

        // "Agent still executes" for layers 1 & 2
        if (i < 2 && p > 0.4) {
          drawText(lx + lw - 20, ly + 70, 'The agent still executes on its own →', 10, C.red, 'right');
        }
      }
    });

    // Arrow from L1/L2 showing gap, L3 catching it
    if (p > 0.5) {
      drawText(640, 520, 'Every tool above says "allowed."', 16, C.text, 'center', '600');
    }
    if (p > 0.6) {
      drawText(640, 548, 'Only Surfit asks "correct for your business right now?"', 16, C.blue, 'center', '600');
    }
    if (p > 0.75) {
      roundedRect(240, 580, 800, 60, 8);
      ctx.fillStyle = 'rgba(38,194,255,0.06)';
      ctx.fill();
      ctx.strokeStyle = C.blue + '40';
      ctx.lineWidth = 1;
      ctx.stroke();
      drawText(280, 602, 'The agent cannot bypass Surfit because it does not hold the credentials.', 13, C.text, 'left');
      drawText(280, 622, 'This is architectural enforcement, not policy. The execution boundary.', 12, C.blue, 'left');
    }

    if (p > 0.9) {
      ctx.font = '700 32px "Righteous", cursive';
      ctx.textAlign = 'center';
      ctx.fillStyle = C.blue;
      const sw = ctx.measureText('SURFIT').width;
      ctx.fillText('SURFIT', 620, 680);
      ctx.fillStyle = C.muted;
      ctx.font = '700 22px "Righteous", cursive';
      ctx.fillText('.', 620 + sw / 2 + 4, 680);
      ctx.fillStyle = C.orange;
      ctx.font = '700 32px "Righteous", cursive';
      ctx.fillText('AI', 620 + sw / 2 + 16, 680);
    }
  }

  // ── Main Render Loop ──

  function render(now) {
    const elapsed = now - startMs - pauseMs;
    let t = elapsed / 1000;
    if (t >= totalSeconds) {
      t = 0;
      startMs = now;
      pauseMs = 0;
    }

    const meta = sceneAt(t);
    sceneLabel.textContent = `Segment ${meta.i + 1}/${scenes.length} • ${meta.scene.title}`;
    progressFill.style.width = `${(t / totalSeconds) * 100}%`;

    drawBg(t);
    const pulse = (t * 0.65) % 1;

    switch (meta.i) {
      case 0: drawScene0(t, meta.p, pulse); break;
      case 1: drawScene1(t, meta.p, pulse); break;
      case 2: drawScene2(t, meta.p, pulse); break;
      case 3: drawScene3(t, meta.p, pulse); break;
      case 4: drawScene4(t, meta.p, pulse); break;
      case 5: drawScene5(t, meta.p, pulse); break;
      case 6: drawScene6(t, meta.p, pulse); break;
      case 7: drawScene7(t, meta.p, pulse); break;
      case 8: drawScene8(t, meta.p, pulse); break;
    }

    rafId = requestAnimationFrame(render);
  }

  // ── Controls ──

  function pause() {
    if (!running) return;
    running = false;
    pausedAt = performance.now();
    cancelAnimationFrame(rafId);
    playPauseBtn.textContent = 'Play';
  }

  function play() {
    if (running) return;
    running = true;
    pauseMs += performance.now() - pausedAt;
    playPauseBtn.textContent = 'Pause';
    rafId = requestAnimationFrame(render);
  }

  function restart() {
    startMs = performance.now();
    pauseMs = 0;
    if (!running) {
      running = true;
      playPauseBtn.textContent = 'Pause';
      rafId = requestAnimationFrame(render);
    }
  }

  playPauseBtn.addEventListener('click', () => running ? pause() : play());
  restartBtn.addEventListener('click', restart);

  // Export WebM
  exportBtn.addEventListener('click', async () => {
    exportBtn.disabled = true;
    exportBtn.textContent = 'Recording...';
    const stream = canvas.captureStream(30);
    const recorder = new MediaRecorder(stream, { mimeType: 'video/webm; codecs=vp9' });
    const chunks = [];
    recorder.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: 'video/webm' });
      const url = URL.createObjectURL(blob);
      exportPreview.src = url;
      exportPreview.style.display = 'block';
      const a = document.createElement('a');
      a.href = url;
      a.download = 'surfit-visualization.webm';
      a.click();
      exportBtn.disabled = false;
      exportBtn.textContent = 'Export WebM';
      exportPathHint.textContent = 'Export complete. Video downloaded.';
    };
    // Restart and record
    restart();
    recorder.start();
    setTimeout(() => {
      recorder.stop();
    }, totalSeconds * 1000 + 500);
  });

  // Start
  rafId = requestAnimationFrame(render);
})();
