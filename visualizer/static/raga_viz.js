/**
 * raga_viz.js — Swara Circle Canvas Animation
 *
 * Draws a circle of 7 swara nodes on a <canvas> element.
 * Each node represents one degree of the active Melakarta raga's scale.
 * Nodes light up (glow gold) when their lane is activated during hashing.
 *
 * Usage:
 *   const viz = new SwaraCircle(canvasElement);
 *   viz.activateLane(3, 329.63);  // light up lane 3 (typically Ma)
 *   viz.reset();                  // reset all nodes to dim
 */

class SwaraCircle {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx    = canvas.getContext("2d");
    this.w      = canvas.width;
    this.h      = canvas.height;
    this.cx     = this.w / 2;
    this.cy     = this.h / 2;
    this.radius = Math.min(this.w, this.h) * 0.36;

    // 7 swara positions — evenly spaced around the circle
    this.lanes = Array.from({ length: 7 }, (_, i) => ({
      label:    ["Sa", "Ri", "Ga", "Ma", "Pa", "Dha", "Ni"][i],
      angle:    (i / 7) * 2 * Math.PI - Math.PI / 2,
      glow:     0.0,   // 0 = dark, 1 = full glow
      pulseDir: 0,     // +1 rising, -1 fading
      freq:     0,
    }));

    // Active connection lines (Amsa ↔ Nyasa analogue — lanes 0 & 4 = Sa & Pa)
    this.connections = [[0, 4]];  // Sa – Pa (perfect fifth, the invariant axis)

    this._animFrame = null;
    this._draw();
  }

  activateLane(laneIdx, freq) {
    const lane = this.lanes[laneIdx];
    if (!lane) return;
    lane.glow     = 1.0;
    lane.pulseDir = -1;   // start fading
    lane.freq     = freq;
    this._ensureAnimating();
  }

  reset() {
    this.lanes.forEach(l => { l.glow = 0; l.pulseDir = 0; l.freq = 0; });
    this._draw();
  }

  _ensureAnimating() {
    if (this._animFrame) return;
    const loop = () => {
      this._tick();
      this._draw();
      const anyActive = this.lanes.some(l => l.glow > 0.01);
      if (anyActive) {
        this._animFrame = requestAnimationFrame(loop);
      } else {
        this._animFrame = null;
      }
    };
    this._animFrame = requestAnimationFrame(loop);
  }

  _tick() {
    this.lanes.forEach(l => {
      if (l.pulseDir === -1) {
        l.glow -= 0.025;
        if (l.glow <= 0) { l.glow = 0; l.pulseDir = 0; }
      }
    });
  }

  _draw() {
    const { ctx, cx, cy, w, h } = this;

    // Background
    ctx.clearRect(0, 0, w, h);
    const bg = ctx.createRadialGradient(cx, cy, 10, cx, cy, this.radius * 1.4);
    bg.addColorStop(0,   "#2a0808");
    bg.addColorStop(1,   "#0f0404");
    ctx.fillStyle = bg;
    ctx.beginPath();
    ctx.arc(cx, cy, this.radius * 1.55, 0, 2 * Math.PI);
    ctx.fill();

    // Outer ring
    ctx.strokeStyle = "#5a2020";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, this.radius * 1.4, 0, 2 * Math.PI);
    ctx.stroke();

    // Connection lines (Sa–Pa axis)
    this._drawConnections();

    // Spokes from centre
    this.lanes.forEach((lane, i) => {
      const x = cx + this.radius * Math.cos(lane.angle);
      const y = cy + this.radius * Math.sin(lane.angle);
      ctx.strokeStyle = `rgba(90, 32, 32, ${0.3 + lane.glow * 0.5})`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(x, y);
      ctx.stroke();
    });

    // Centre dot
    const centerGlow = Math.max(...this.lanes.map(l => l.glow));
    ctx.fillStyle = `rgba(212, 175, 55, ${0.2 + centerGlow * 0.6})`;
    ctx.beginPath();
    ctx.arc(cx, cy, 8 + centerGlow * 4, 0, 2 * Math.PI);
    ctx.fill();

    // Swara nodes
    this.lanes.forEach(lane => {
      const x = cx + this.radius * Math.cos(lane.angle);
      const y = cy + this.radius * Math.sin(lane.angle);
      this._drawNode(x, y, lane);
    });
  }

  _drawConnections() {
    const { ctx, cx, cy } = this;
    this.connections.forEach(([a, b]) => {
      const la = this.lanes[a], lb = this.lanes[b];
      const ax = cx + this.radius * Math.cos(la.angle);
      const ay = cy + this.radius * Math.sin(la.angle);
      const bx = cx + this.radius * Math.cos(lb.angle);
      const by = cy + this.radius * Math.sin(lb.angle);
      const glow = Math.max(la.glow, lb.glow);
      ctx.strokeStyle = `rgba(212, 175, 55, ${0.08 + glow * 0.4})`;
      ctx.lineWidth = 1.5 + glow * 2;
      ctx.beginPath();
      ctx.moveTo(ax, ay);
      ctx.lineTo(bx, by);
      ctx.stroke();
    });
  }

  _drawNode(x, y, lane) {
    const { ctx } = this;
    const r = 22;
    const g = lane.glow;

    // Glow halo
    if (g > 0.02) {
      const halo = ctx.createRadialGradient(x, y, r * 0.5, x, y, r * 2.2);
      halo.addColorStop(0,   `rgba(212, 175, 55, ${g * 0.6})`);
      halo.addColorStop(1,   "rgba(212, 175, 55, 0)");
      ctx.fillStyle = halo;
      ctx.beginPath();
      ctx.arc(x, y, r * 2.5, 0, 2 * Math.PI);
      ctx.fill();
    }

    // Node circle
    const nodeGrad = ctx.createRadialGradient(x - r * 0.3, y - r * 0.3, 2, x, y, r);
    if (g > 0.05) {
      nodeGrad.addColorStop(0, `rgba(255, 240, 120, ${0.6 + g * 0.4})`);
      nodeGrad.addColorStop(1, `rgba(180, 100, 10,  ${0.3 + g * 0.5})`);
    } else {
      nodeGrad.addColorStop(0, "#3a1818");
      nodeGrad.addColorStop(1, "#1a0808");
    }
    ctx.fillStyle = nodeGrad;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.fill();

    // Node border
    ctx.strokeStyle = g > 0.05 ? `rgba(212, 175, 55, ${0.4 + g * 0.6})` : "#5a2020";
    ctx.lineWidth = 1.5 + g * 1.5;
    ctx.stroke();

    // Swara label
    ctx.fillStyle = g > 0.05
      ? `rgba(255, 245, 180, ${0.7 + g * 0.3})`
      : "rgba(192, 160, 100, 0.6)";
    ctx.font = `bold ${12 + g * 2}px sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(lane.label, x, y);

    // Frequency label below node (only when active)
    if (g > 0.15 && lane.freq > 0) {
      ctx.fillStyle = `rgba(180, 140, 60, ${g * 0.85})`;
      ctx.font = "9px monospace";
      ctx.fillText(`${lane.freq.toFixed(0)}Hz`, x, y + r + 10);
    }
  }
}
