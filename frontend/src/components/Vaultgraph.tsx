import { useEffect, useRef, useState } from "react";
import { getVaultGraph, type VaultGraphNode, type VaultGraphEdge } from "../services/api";

interface VaultGraphProps {
  active?: boolean;
  size?: number;
  /** cada cuántos ms vuelve a pedir el grafo al backend */
  refreshMs?: number;
}

interface LayoutNode extends VaultGraphNode {
  // posición en espacio 3D normalizado (-1..1), fija tras el layout inicial
  x: number;
  y: number;
  z: number;
  degree: number;
  twinkle: number;
  twinkleSpeed: number;
}

interface DustParticle {
  theta: number;
  phi: number;
  r: number;
  twinkle: number;
  twinkleSpeed: number;
}

/** Layout de fuerzas simple (repulsión + resortes) sobre una esfera, corrido pocas veces al cargar los datos. */
function computeForceLayout(nodes: VaultGraphNode[], edges: VaultGraphEdge[]): LayoutNode[] {
  const degree: Record<string, number> = {};
  edges.forEach((e) => {
    degree[e.source] = (degree[e.source] ?? 0) + 1;
    degree[e.target] = (degree[e.target] ?? 0) + 1;
  });

  const positioned: LayoutNode[] = nodes.map((n) => {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    return {
      ...n,
      x: Math.sin(phi) * Math.cos(theta),
      y: Math.cos(phi),
      z: Math.sin(phi) * Math.sin(theta),
      degree: degree[n.id] ?? 0,
      twinkle: Math.random() * Math.PI * 2,
      twinkleSpeed: 0.01 + Math.random() * 0.02,
    };
  });

  const byId: Record<string, LayoutNode> = {};
  positioned.forEach((n) => (byId[n.id] = n));

  const ITER = 120;
  const REPEL = 0.0025;
  const SPRING = 0.02;
  const REST_LEN = 0.55;

  for (let iter = 0; iter < ITER; iter++) {
    // repulsión entre todos los pares (ok para grafos chicos/medianos de notas)
    for (let i = 0; i < positioned.length; i++) {
      for (let j = i + 1; j < positioned.length; j++) {
        const a = positioned[i];
        const b = positioned[j];
        let dx = a.x - b.x;
        let dy = a.y - b.y;
        let dz = a.z - b.z;
        let distSq = dx * dx + dy * dy + dz * dz || 0.0001;
        const force = REPEL / distSq;
        const dist = Math.sqrt(distSq);
        dx = (dx / dist) * force;
        dy = (dy / dist) * force;
        dz = (dz / dist) * force;
        a.x += dx; a.y += dy; a.z += dz;
        b.x -= dx; b.y -= dy; b.z -= dz;
      }
    }
    // atracción por resorte a lo largo de las aristas
    edges.forEach((e) => {
      const a = byId[e.source];
      const b = byId[e.target];
      if (!a || !b) return;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dz = b.z - a.z;
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 0.0001;
      const force = (dist - REST_LEN) * SPRING;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      const fz = (dz / dist) * force;
      a.x += fx; a.y += fy; a.z += fz;
      b.x -= fx; b.y -= fy; b.z -= fz;
    });
    // recentrar y normalizar a la superficie de una esfera unitaria
    positioned.forEach((n) => {
      const len = Math.sqrt(n.x * n.x + n.y * n.y + n.z * n.z) || 0.0001;
      n.x /= len; n.y /= len; n.z /= len;
    });
  }

  return positioned;
}

export default function VaultGraph({ active = true, size = 460, refreshMs = 30000 }: VaultGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<LayoutNode[]>([]);
  const edgesRef = useRef<VaultGraphEdge[]>([]);
  const dustRef = useRef<DustParticle[]>([]);
  const rotationRef = useRef(0);
  const rafRef = useRef<ReturnType<typeof requestAnimationFrame> | null>(null);
  const [nodeCount, setNodeCount] = useState(0);

  // partículas de fondo (polvo decorativo, siempre presentes)
  useEffect(() => {
    const dust: DustParticle[] = [];
    for (let i = 0; i < 500; i++) {
      dust.push({
        theta: Math.random() * Math.PI * 2,
        phi: Math.acos(2 * Math.random() - 1),
        r: 0.85 + Math.random() * 0.3,
        twinkle: Math.random() * Math.PI * 2,
        twinkleSpeed: 0.008 + Math.random() * 0.015,
      });
    }
    dustRef.current = dust;
  }, []);

  // cargar el grafo real desde el backend
  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await getVaultGraph();
        if (cancelled) return;
        if (data.nodes.length > 0) {
          nodesRef.current = computeForceLayout(data.nodes, data.edges);
          edgesRef.current = data.edges;
          setNodeCount(data.nodes.length);
        } else {
          nodesRef.current = [];
          edgesRef.current = [];
          setNodeCount(0);
        }
      } catch {
        // backend no disponible: se queda con el modo decorativo (solo polvo)
        nodesRef.current = [];
        edgesRef.current = [];
        setNodeCount(0);
      }
    };

    load();
    const interval = setInterval(load, refreshMs);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [refreshMs]);

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

    const cx = size / 2;
    const cy = size / 2;
    const radius = size * 0.4;

    const project = (x: number, y: number, z: number, rot: number) => {
      // rotación sobre el eje Y
      const cosR = Math.cos(rot);
      const sinR = Math.sin(rot);
      const xr = x * cosR - z * sinR;
      const zr = x * sinR + z * cosR;
      const scale = 1 / (1.8 - zr);
      return {
        x2: cx + xr * radius * scale,
        y2: cy + y * radius * scale,
        z: zr,
        scale,
      };
    };

    const render = () => {
      ctx.clearRect(0, 0, size, size);
      rotationRef.current += active ? 0.0018 : 0.0005;
      const rot = rotationRef.current;

      // ----- polvo de fondo -----
      const dustPts = dustRef.current.map((d) => {
        d.twinkle += d.twinkleSpeed;
        const x3 = Math.sin(d.phi) * Math.cos(d.theta) * d.r;
        const y3 = Math.cos(d.phi) * d.r;
        const z3 = Math.sin(d.phi) * Math.sin(d.theta) * d.r;
        const { x2, y2, z, scale } = project(x3, y3, z3, rot * 0.4);
        const alpha = (0.12 + scale * 0.25) * (0.5 + 0.5 * Math.sin(d.twinkle));
        return { x: x2, y: y2, z, alpha, rad: Math.max(0.3, 1 * scale) };
      });
      dustPts.sort((a, b) => a.z - b.z);
      for (const p of dustPts) {
        ctx.beginPath();
        ctx.fillStyle = `rgba(214, 178, 94, ${Math.max(0, Math.min(1, p.alpha))})`;
        ctx.arc(p.x, p.y, p.rad, 0, Math.PI * 2);
        ctx.fill();
      }

      // ----- grafo real de la bóveda -----
      const nodes = nodesRef.current;
      if (nodes.length > 0) {
        const projected: Record<string, { x2: number; y2: number; z: number; scale: number }> = {};
        nodes.forEach((n) => {
          projected[n.id] = project(n.x, n.y, n.z, rot);
        });

        // aristas primero (detrás de los nodos)
        ctx.lineWidth = 0.6;
        edgesRef.current.forEach((e) => {
          const a = projected[e.source];
          const b = projected[e.target];
          if (!a || !b) return;
          const avgZ = (a.z + b.z) / 2;
          const alpha = 0.08 + Math.max(0, avgZ) * 0.25;
          ctx.strokeStyle = `rgba(214, 178, 94, ${alpha})`;
          ctx.beginPath();
          ctx.moveTo(a.x2, a.y2);
          ctx.lineTo(b.x2, b.y2);
          ctx.stroke();
        });

        // nodos, ordenados por profundidad
        const nodePts = nodes.map((n) => {
          n.twinkle += n.twinkleSpeed;
          const p = projected[n.id];
          const sizeBoost = 1 + Math.min(n.degree, 6) * 0.18;
          const alpha = (0.35 + p.scale * 0.65) * (0.7 + 0.3 * Math.sin(n.twinkle));
          return {
            ...p,
            title: n.title,
            rad: Math.max(1.4, 2.4 * p.scale * sizeBoost),
            alpha,
          };
        });
        nodePts.sort((a, b) => a.z - b.z);

        for (const p of nodePts) {
          ctx.beginPath();
          ctx.fillStyle = `rgba(240, 211, 145, ${Math.max(0, Math.min(1, p.alpha))})`;
          ctx.shadowColor = "rgba(240, 211, 145, 0.95)";
          ctx.shadowBlur = active ? 8 : 4;
          ctx.arc(p.x2, p.y2, p.rad, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // halo central
      const glow = ctx.createRadialGradient(cx, cy, radius * 0.05, cx, cy, radius * 1.05);
      glow.addColorStop(0, "rgba(214, 178, 94, 0.10)");
      glow.addColorStop(1, "rgba(214, 178, 94, 0)");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(cx, cy, radius * 1.05, 0, Math.PI * 2);
      ctx.fill();

      rafRef.current = requestAnimationFrame(render);
    };

    rafRef.current = requestAnimationFrame(render);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [active, size]);

  return (
    <div className="vault-graph-wrap">
      <canvas ref={canvasRef} className="vault-sphere-canvas" />
      {nodeCount === 0 && (
        <div className="vault-graph-empty-hint">bóveda vacía — sin notas enlazadas todavía</div>
      )}
    </div>
  );
}