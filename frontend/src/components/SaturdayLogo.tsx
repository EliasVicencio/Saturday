import { useEffect, useRef } from "react";

interface SaturdayLogoProps {
  audioLevel?: number;
  size?: number;
}

interface Particle {
  theta: number;
  phi: number;
  r: number;
  baseSize: number;
  twinkle: number;
  twinkleSpeed: number;
  brightness: number;
}

const GOLD_R = 214;
const GOLD_G = 178;
const GOLD_B = 94;
const BRIGHT_R = 240;
const BRIGHT_G = 211;
const BRIGHT_B = 145;

function createParticles(count: number): Particle[] {
  const particles: Particle[] = [];
  for (let i = 0; i < count; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const rJitter = 0.88 + Math.random() * 0.24;
    particles.push({
      theta,
      phi,
      r: rJitter,
      baseSize: 0.6 + Math.random() * 2.0,
      twinkle: Math.random() * Math.PI * 2,
      twinkleSpeed: 0.008 + Math.random() * 0.02,
      brightness: 0.3 + Math.random() * 0.7,
    });
  }
  return particles;
}

export default function SaturdayLogo({ audioLevel = 0, size = 460 }: SaturdayLogoProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const dustRef = useRef<Particle[]>([]);
  const rotationRef = useRef(0);
  const rafRef = useRef<number | null>(null);
  const audioRef = useRef(0);
  const smoothAudioRef = useRef(0);

  useEffect(() => {
    audioRef.current = audioLevel;
  }, [audioLevel]);

  useEffect(() => {
    particlesRef.current = createParticles(220);
    const dust: Particle[] = [];
    for (let i = 0; i < 350; i++) {
      dust.push({
        theta: Math.random() * Math.PI * 2,
        phi: Math.acos(2 * Math.random() - 1),
        r: 0.7 + Math.random() * 0.5,
        baseSize: 0.2 + Math.random() * 0.8,
        twinkle: Math.random() * Math.PI * 2,
        twinkleSpeed: 0.005 + Math.random() * 0.012,
        brightness: 0.15 + Math.random() * 0.4,
      });
    }
    dustRef.current = dust;
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
    const baseRadius = size * 0.38;

    const project = (x: number, y: number, z: number, rot: number) => {
      const cosR = Math.cos(rot);
      const sinR = Math.sin(rot);
      const xr = x * cosR - z * sinR;
      const zr = x * sinR + z * cosR;
      const scale = 1 / (1.7 - zr);
      return { x2: cx + xr * baseRadius * scale, y2: cy + y * baseRadius * scale, z: zr, scale };
    };

    const render = () => {
      ctx.clearRect(0, 0, size, size);

      const rawAudio = audioRef.current;
      smoothAudioRef.current += (rawAudio - smoothAudioRef.current) * 0.15;
      const level = smoothAudioRef.current;

      rotationRef.current += 0.002 + level * 0.015;
      const rot = rotationRef.current;

      const breathScale = 1 + level * 0.12;

      // --- dust (background particles) ---
      const dustPts: { x: number; y: number; z: number; alpha: number; rad: number }[] = [];
      for (const d of dustRef.current) {
        d.twinkle += d.twinkleSpeed;
        const x3 = Math.sin(d.phi) * Math.cos(d.theta) * d.r * breathScale;
        const y3 = Math.cos(d.phi) * d.r * breathScale;
        const z3 = Math.sin(d.phi) * Math.sin(d.theta) * d.r * breathScale;
        const { x2, y2, z, scale } = project(x3, y3, z3, rot * 0.35);
        const twinkleAlpha = 0.3 + 0.7 * (0.5 + 0.5 * Math.sin(d.twinkle));
        const alpha = d.brightness * twinkleAlpha * (0.15 + scale * 0.35) * (1 + level * 0.4);
        dustPts.push({ x: x2, y: y2, z, alpha, rad: Math.max(0.2, d.baseSize * scale) });
      }
      dustPts.sort((a, b) => a.z - b.z);
      for (const p of dustPts) {
        if (p.alpha < 0.02) continue;
        ctx.beginPath();
        ctx.fillStyle = `rgba(${GOLD_R}, ${GOLD_G}, ${GOLD_B}, ${Math.min(1, p.alpha)})`;
        ctx.arc(p.x, p.y, p.rad, 0, Math.PI * 2);
        ctx.fill();
      }

      // --- main sphere particles ---
      const mainPts: {
        x: number; y: number; z: number;
        alpha: number; rad: number;
        glow: boolean;
      }[] = [];
      for (const p of particlesRef.current) {
        p.twinkle += p.twinkleSpeed;
        const x3 = Math.sin(p.phi) * Math.cos(p.theta) * p.r * breathScale;
        const y3 = Math.cos(p.phi) * p.r * breathScale;
        const z3 = Math.sin(p.phi) * Math.sin(p.theta) * p.r * breathScale;
        const proj = project(x3, y3, z3, rot);
        const twinkleA = 0.6 + 0.4 * Math.sin(p.twinkle);
        const depthAlpha = 0.25 + proj.scale * 0.75;
        const alpha = p.brightness * twinkleA * depthAlpha * (1 + level * 0.5);
        const rad = Math.max(0.8, p.baseSize * proj.scale * (1 + level * 0.5));
        mainPts.push({
          x: proj.x2, y: proj.y2, z: proj.z,
          alpha, rad,
          glow: p.brightness > 0.7,
        });
      }
      mainPts.sort((a, b) => a.z - b.z);

      for (const p of mainPts) {
        if (p.alpha < 0.02) continue;
        const brightMix = p.alpha > 0.6 ? 1 : p.alpha / 0.6;
        const r = Math.round(GOLD_R + (BRIGHT_R - GOLD_R) * brightMix);
        const g = Math.round(GOLD_G + (BRIGHT_G - GOLD_G) * brightMix);
        const b = Math.round(GOLD_B + (BRIGHT_B - GOLD_B) * brightMix);

        ctx.beginPath();
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${Math.min(1, p.alpha)})`;
        if (p.glow || level > 0.2) {
          ctx.shadowColor = `rgba(${BRIGHT_R}, ${BRIGHT_G}, ${BRIGHT_B}, ${Math.min(1, p.alpha * 0.8 + level * 0.3)})`;
          ctx.shadowBlur = (p.glow ? 6 : 3) + level * 14;
        }
        ctx.arc(p.x, p.y, p.rad, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      // --- central glow ---
      const glowR = baseRadius * (0.85 + level * 0.25);
      const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, glowR);
      glow.addColorStop(0, `rgba(${GOLD_R}, ${GOLD_G}, ${GOLD_B}, ${0.06 + level * 0.12})`);
      glow.addColorStop(0.5, `rgba(${GOLD_R}, ${GOLD_G}, ${GOLD_B}, ${0.02 + level * 0.04})`);
      glow.addColorStop(1, `rgba(${GOLD_R}, ${GOLD_G}, ${GOLD_B}, 0)`);
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(cx, cy, glowR, 0, Math.PI * 2);
      ctx.fill();

      rafRef.current = requestAnimationFrame(render);
    };

    rafRef.current = requestAnimationFrame(render);
    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [size]);

  return (
    <div className="saturday-logo-wrap">
      <canvas ref={canvasRef} className="saturday-logo-canvas" />
    </div>
  );
}
