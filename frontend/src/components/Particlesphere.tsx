import { useEffect, useRef } from "react";

interface ParticleSphereProps {
  active?: boolean;
  size?: number;
}

interface Particle {
  theta: number; // ángulo horizontal base
  phi: number; // ángulo vertical base
  r: number; // radio (con variación para dar volumen a la esfera)
  twinkle: number;
  twinkleSpeed: number;
}

/**
 * Esfera de partículas doradas, tipo "núcleo de inteligencia" (V.A.U.L.T.).
 * Se dibuja en un <canvas> con proyección 3D simple (rotación + perspectiva).
 */
export default function ParticleSphere({ active = true, size = 460 }: ParticleSphereProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const rotationRef = useRef(0);
  const rafRef = useRef<ReturnType<typeof requestAnimationFrame> | null>(null);

  useEffect(() => {
    const COUNT = 900;
    const particles: Particle[] = [];
    for (let i = 0; i < COUNT; i++) {
      particles.push({
        theta: Math.random() * Math.PI * 2,
        phi: Math.acos(2 * Math.random() - 1),
        r: 0.78 + Math.random() * 0.22,
        twinkle: Math.random() * Math.PI * 2,
        twinkleSpeed: 0.01 + Math.random() * 0.02,
      });
    }
    particlesRef.current = particles;
  }, []);

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

    const render = () => {
      ctx.clearRect(0, 0, size, size);

      rotationRef.current += active ? 0.0022 : 0.0006;
      const rot = rotationRef.current;

      const pts = particlesRef.current.map((p) => {
        p.twinkle += p.twinkleSpeed;
        const theta = p.theta + rot;
        const x3 = Math.sin(p.phi) * Math.cos(theta) * p.r;
        const y3 = Math.cos(p.phi) * p.r;
        const z3 = Math.sin(p.phi) * Math.sin(theta) * p.r;

        // perspectiva simple
        const scale = 1 / (1.8 - z3);
        const x2 = cx + x3 * radius * scale;
        const y2 = cy + y3 * radius * scale;
        const alpha = (0.25 + scale * 0.6) * (0.55 + 0.45 * Math.sin(p.twinkle));
        const rad = Math.max(0.4, 1.6 * scale);
        return { x: x2, y: y2, z: z3, alpha, rad };
      });

      pts.sort((a, b) => a.z - b.z);

      for (const p of pts) {
        ctx.beginPath();
        ctx.fillStyle = `rgba(214, 178, 94, ${Math.max(0, Math.min(1, p.alpha))})`;
        ctx.shadowColor = "rgba(230, 196, 110, 0.9)";
        ctx.shadowBlur = active ? 4 : 2;
        ctx.arc(p.x, p.y, p.rad, 0, Math.PI * 2);
        ctx.fill();
      }

      // halo central suave
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

  return <canvas ref={canvasRef} className="vault-sphere-canvas" />;
}