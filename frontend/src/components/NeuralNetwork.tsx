import { useEffect, useRef } from "react";

interface NeuralNode {
  x: number;
  y: number;
  radius: number;
  layer: number;
  angle: number;
  pulse: number;
  pulseSpeed: number;
  brightness: number;
  connections: number[];
}

interface NeuralNetworkProps {
  active?: boolean;
  size?: number;
}

const LAYERS = 4;
const NODES_PER_LAYER = [1, 6, 12, 20];
const GOLD = [214, 178, 94];
const GOLD_LIGHT = [240, 211, 145];
const GOLD_BRIGHT = [255, 220, 130];

function createNetwork(w: number, h: number): NeuralNode[] {
  const nodes: NeuralNode[] = [];
  const layerRadii = [0, w * 0.12, w * 0.25, w * 0.4];

  for (let l = 0; l < LAYERS; l++) {
    const count = NODES_PER_LAYER[l];
    const r = layerRadii[l];
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2 + l * 0.3;
      const jitter = l === 0 ? 0 : (Math.random() - 0.5) * 20;
      nodes.push({
        x: w / 2 + Math.cos(angle) * r + jitter,
        y: h / 2 + Math.sin(angle) * r + jitter,
        radius: l === 0 ? 6 : 3 - l * 0.4,
        layer: l,
        angle,
        pulse: Math.random() * Math.PI * 2,
        pulseSpeed: 0.02 + Math.random() * 0.03,
        brightness: 0.5 + Math.random() * 0.5,
        connections: [],
      });
    }
  }

  for (let i = 0; i < nodes.length; i++) {
    const a = nodes[i];
    if (a.layer > 0) {
      const ls = NODES_PER_LAYER.slice(0, a.layer).reduce((s, n) => s + n, 0);
      const idx = i - ls;
      const next = ls + ((idx + 1) % NODES_PER_LAYER[a.layer]);
      if (next !== i) a.connections.push(next);
    }
    if (a.layer > 0) {
      const is_ = NODES_PER_LAYER.slice(0, a.layer - 1).reduce((s, n) => s + n, 0);
      const ic = NODES_PER_LAYER[a.layer - 1];
      let closest = is_;
      let minD = Infinity;
      for (let j = 0; j < ic; j++) {
        const b = nodes[is_ + j];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < minD) { minD = d; closest = is_ + j; }
      }
      if (!a.connections.includes(closest)) a.connections.push(closest);
    }
    if (a.layer >= 2) {
      const ps = NODES_PER_LAYER.slice(0, a.layer - 1).reduce((s, n) => s + n, 0);
      const pc = NODES_PER_LAYER[a.layer - 1];
      for (let j = 0; j < pc; j++) {
        const b = nodes[ps + j];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 100 && !a.connections.includes(ps + j)) {
          a.connections.push(ps + j);
        }
      }
    }
  }
  return nodes;
}

export default function NeuralNetwork({ active = false, size = 460 }: NeuralNetworkProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<NeuralNode[]>([]);
  const frameRef = useRef(0);
  const energyRef = useRef(0);
  const waveRef = useRef<{ r: number; life: number }[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.scale(dpr, dpr);

    nodesRef.current = createNetwork(size, size);

    let raf: number;
    const cx = size / 2;
    const cy = size / 2;
    const layerRadii = [0, size * 0.12, size * 0.25, size * 0.4];

    const animate = () => {
      frameRef.current++;
      const t = frameRef.current;
      const nodes = nodesRef.current;

      if (active) {
        energyRef.current = Math.min(1, energyRef.current + 0.02);
      } else {
        energyRef.current = Math.max(0, energyRef.current - 0.008);
      }
      const energy = energyRef.current;

      if (active && t % 20 === 0) {
        waveRef.current.push({ r: 0, life: 1 });
      }

      ctx.fillStyle = "rgba(8, 8, 12, 0.15)";
      ctx.fillRect(0, 0, size, size);

      const glowR = 140 + energy * 60;
      const grd = ctx.createRadialGradient(cx, cy, 0, cx, cy, glowR);
      grd.addColorStop(0, `rgba(${GOLD[0]}, ${GOLD[1]}, ${GOLD[2]}, ${0.06 + energy * 0.08})`);
      grd.addColorStop(0.5, `rgba(${GOLD[0]}, ${GOLD[1]}, ${GOLD[2]}, ${0.02 + energy * 0.03})`);
      grd.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = grd;
      ctx.fillRect(0, 0, size, size);

      for (let i = waveRef.current.length - 1; i >= 0; i--) {
        const w = waveRef.current[i];
        w.r += 3;
        w.life -= 0.015;
        if (w.life <= 0) { waveRef.current.splice(i, 1); continue; }
        ctx.beginPath();
        ctx.arc(cx, cy, w.r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${GOLD_LIGHT[0]}, ${GOLD_LIGHT[1]}, ${GOLD_LIGHT[2]}, ${w.life * 0.3 * (0.5 + energy * 0.5)})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      for (const node of nodes) {
        node.pulse += node.pulseSpeed * (1 + energy * 2);
        const drift = active ? 0.8 : 0.15;
        node.x += Math.cos(node.angle + t * 0.001) * drift * 0.1;
        node.y += Math.sin(node.angle + t * 0.001) * drift * 0.1;
        const ox = cx + Math.cos(node.angle) * layerRadii[node.layer];
        const oy = cy + Math.sin(node.angle) * layerRadii[node.layer];
        node.x += (ox - node.x) * 0.005;
        node.y += (oy - node.y) * 0.005;
        node.brightness = 0.4 + Math.sin(node.pulse) * 0.3 + energy * 0.3;
      }

      ctx.lineCap = "round";
      for (const node of nodes) {
        for (const ci of node.connections) {
          const other = nodes[ci];
          if (!other) continue;
          const dx = other.x - node.x;
          const dy = other.y - node.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const maxDist = node.layer === 0 || other.layer === 0 ? 200 : 150;
          if (dist > maxDist) continue;
          const alpha = (1 - dist / maxDist) * 0.25 * (0.4 + energy * 0.6);
          const pulsePhase = Math.sin(node.pulse + dist * 0.02) * 0.5 + 0.5;
          ctx.beginPath();
          ctx.moveTo(node.x, node.y);
          ctx.lineTo(other.x, other.y);
          ctx.strokeStyle = `rgba(${GOLD_BRIGHT[0]}, ${GOLD_BRIGHT[1]}, ${GOLD_BRIGHT[2]}, ${alpha * (0.5 + pulsePhase * 0.5)})`;
          ctx.lineWidth = 0.8 + energy * 0.8;
          ctx.stroke();
          if (energy > 0.3 && pulsePhase > 0.7) {
            const frac = (t * 0.01 + node.pulse) % 1;
            const px = node.x + dx * frac;
            const py = node.y + dy * frac;
            ctx.beginPath();
            ctx.arc(px, py, 1.5, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${GOLD_BRIGHT[0]}, ${GOLD_BRIGHT[1]}, ${GOLD_BRIGHT[2]}, ${energy * 0.6})`;
            ctx.fill();
          }
        }
      }

      for (const node of nodes) {
        const pulseVal = Math.sin(node.pulse);
        const r = node.radius + pulseVal * 1.2 * (0.3 + energy * 0.7);
        const bright = node.brightness;
        const glowSize = r * (2.5 + energy * 2);
        const ng = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, glowSize);
        ng.addColorStop(0, `rgba(${GOLD_LIGHT[0]}, ${GOLD_LIGHT[1]}, ${GOLD_LIGHT[2]}, ${bright * 0.4})`);
        ng.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = ng;
        ctx.beginPath();
        ctx.arc(node.x, node.y, glowSize, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
        const c = node.layer === 0 ? GOLD_BRIGHT : node.layer === 1 ? GOLD_LIGHT : GOLD;
        ctx.fillStyle = `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${0.7 + bright * 0.3})`;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(node.x, node.y, r * 0.4, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 245, 200, ${0.5 + bright * 0.5})`;
        ctx.fill();
      }

      const coreR = 10 + energy * 15 + Math.sin(t * 0.05) * 3;
      const cg = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 3);
      cg.addColorStop(0, `rgba(${GOLD_BRIGHT[0]}, ${GOLD_BRIGHT[1]}, ${GOLD_BRIGHT[2]}, ${0.3 + energy * 0.4})`);
      cg.addColorStop(0.4, `rgba(${GOLD[0]}, ${GOLD[1]}, ${GOLD[2]}, ${0.1 + energy * 0.15})`);
      cg.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = cg;
      ctx.beginPath();
      ctx.arc(cx, cy, coreR * 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx, cy, 4 + energy * 4, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 245, 220, ${0.8 + energy * 0.2})`;
      ctx.fill();

      raf = requestAnimationFrame(animate);
    };

    animate();
    return () => cancelAnimationFrame(raf);
  }, [size, active]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        display: "block",
        borderRadius: "50%",
      }}
    />
  );
}
