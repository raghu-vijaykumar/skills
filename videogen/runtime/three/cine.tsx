// Reusable cinematic R3F building blocks for Revise Labs 3D videos.
//
// Restrained by design: fake (deterministic, cheap) contact shadows instead of
// shadow maps, additive glow sprites instead of a bloom pass, fog + parallax
// instead of optical DOF. No new render pipeline; plain three.js + R3F.

import React, {useMemo} from 'react';
import {useThree} from '@react-three/fiber';
import * as THREE from 'three';
import {LIGHT, PALETTE} from './materials.ts';
import {causticMap, radialMap, sandMaps, waterGradientMap} from './realism.ts';

// ---------------------------------------------------------------------------
// Lighting rigs (punctual lights only; separation comes from rim + fill)
// ---------------------------------------------------------------------------

export function CineLights({variant = 'studio'}: {variant?: 'studio' | 'subsea'}) {
  if (variant === 'subsea') {
    return (
      <group>
        <hemisphereLight args={[PALETTE.seaLight, PALETTE.seaDeep, 0.55]} />
        <directionalLight position={[3, 8, 4]} color="#cfe6ff" intensity={1.15} />
        <directionalLight position={[-5, 2, -5]} color={LIGHT.rim.color} intensity={0.5} />
        <pointLight position={[0, 7, -3]} color={PALETTE.seaLight} intensity={1.0} distance={42} />
        <pointLight position={[-6, -1, 4]} color={LIGHT.fill.color} intensity={0.3} distance={20} />
        <ambientLight color={LIGHT.ambient.color} intensity={0.35} />
      </group>
    );
  }
  return (
    <group>
      <hemisphereLight args={['#cfe0f2', '#1a2230', 0.5]} />
      <ambientLight color={LIGHT.ambient.color} intensity={LIGHT.ambient.intensity} />
      <directionalLight position={[4, 6, 8]} color={LIGHT.key.color} intensity={LIGHT.key.intensity} />
      <pointLight position={[-6, 3, -6]} color={LIGHT.rim.color} intensity={LIGHT.rim.intensity} distance={22} />
      <pointLight position={[6, -3, 5]} color={LIGHT.fill.color} intensity={LIGHT.fill.intensity} distance={22} />
    </group>
  );
}

// ---------------------------------------------------------------------------
// Procedural studio environment (restrained IBL for physical materials)
// ---------------------------------------------------------------------------

/**
 * Installs a tiny dark-studio equirect environment so PBR clearcoat/metal have
 * something truthful (but dim) to reflect. Per-material envMapIntensity stays
 * low by convention; nothing becomes glossy. Safe no-op if WebGL/PMREM fails.
 */
export function CineEnvironment({intensity = 0.5}: {intensity?: number}) {
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);
  React.useLayoutEffect(() => {
    let env: THREE.Texture | null = null;
    try {
      const cv = document.createElement('canvas');
      cv.width = 64;
      cv.height = 32;
      const g = cv.getContext('2d') as CanvasRenderingContext2D;
      const grd = g.createLinearGradient(0, 0, 0, 32);
      grd.addColorStop(0, '#3d4f6b');
      grd.addColorStop(0.45, '#0b111c');
      grd.addColorStop(1, '#010205');
      g.fillStyle = grd;
      g.fillRect(0, 0, 64, 32);
      g.fillStyle = 'rgba(255,222,170,0.28)';
      g.fillRect(45, 9, 5, 12);
      g.fillStyle = 'rgba(150,200,255,0.35)';
      g.fillRect(10, 4, 22, 5);
      const tex = new THREE.CanvasTexture(cv);
      tex.mapping = THREE.EquirectangularReflectionMapping;
      tex.colorSpace = THREE.SRGBColorSpace;
      const pmrem = new THREE.PMREMGenerator(gl);
      env = pmrem.fromEquirectangular(tex).texture;
      scene.environment = env;
      (scene as unknown as {environmentIntensity?: number}).environmentIntensity = intensity;
      tex.dispose();
      pmrem.dispose();
    } catch {
      env = null;
    }
    return () => {
      try {
        scene.environment = null;
        env?.dispose();
      } catch {
        /* noop */
      }
    };
  }, [gl, scene, intensity]);
  return null;
}

// ---------------------------------------------------------------------------
// Depth, shadow, atmosphere
// ---------------------------------------------------------------------------

/** Linear scene fog for depth falloff (DOF cue: distant layers go soft/dark). */
export function CineFog({color = PALETTE.seaDeep, near = 14, far = 48}: {color?: string; near?: number; far?: number}) {
  return <fog attach="fog" args={[color, near, far]} />;
}

/** Cheap deterministic contact shadow: radial dark blob under an object. */
export function ContactShadow({
  position,
  scale = 2,
  opacity = 0.55,
}: {
  position: [number, number, number];
  scale?: number;
  opacity?: number;
}) {
  const tex = useMemo(() => radialMap('rgba(0,0,0,0.6)', 'rgba(0,0,0,0)'), []);
  if (!tex) return null;
  return (
    <mesh position={position} rotation={[-Math.PI / 2, 0, 0]} renderOrder={-5}>
      <planeGeometry args={[scale, scale]} />
      <meshBasicMaterial map={tex} transparent opacity={opacity} depthWrite={false} />
    </mesh>
  );
}

/** Shared additive glow sprite (restrained bloom substitute). */
export function GlowSprite({
  color,
  position,
  size,
  opacity = 1,
}: {
  color: string;
  position: [number, number, number];
  size: number;
  opacity?: number;
}) {
  const tex = useMemo(() => radialMap(color, 'rgba(0,0,0,0)'), [color]);
  if (!tex) return null;
  return (
    <sprite position={position} scale={[size, size, 1]} renderOrder={18}>
      <spriteMaterial map={tex} transparent opacity={opacity} depthWrite={false} blending={THREE.AdditiveBlending} />
    </sprite>
  );
}

const shaftCache = new Map<string, THREE.CanvasTexture>();
function shaftTexture(): THREE.CanvasTexture | null {
  const hit = shaftCache.get('cine-shaft');
  if (hit) return hit;
  if (typeof document === 'undefined') return null;
  const cv = document.createElement('canvas');
  cv.width = 64;
  cv.height = 256;
  const g = cv.getContext('2d') as CanvasRenderingContext2D;
  const grd = g.createLinearGradient(0, 0, 0, 256);
  grd.addColorStop(0, 'rgba(169,212,255,0.42)');
  grd.addColorStop(1, 'rgba(169,212,255,0)');
  g.fillStyle = grd;
  g.fillRect(0, 0, 64, 256);
  const tex = new THREE.CanvasTexture(cv);
  tex.anisotropy = 4;
  shaftCache.set('cine-shaft', tex);
  return tex;
}

/** A few soft volumetric-feeling light shafts (deterministic sway). */
export function GodRays({now, opacity = 0.16}: {now: number; opacity?: number}) {
  const tex = useMemo(() => shaftTexture(), []);
  if (!tex) return null;
  return (
    <group>
      {[-6, -1.5, 3, 7].map((x, i) => (
        <mesh
          key={i}
          position={[x + Math.sin(now * 0.3 + i * 1.3) * 0.6, 3.5, -4 - (i % 2)]}
          rotation={[0.5, 0.1 * (i - 1.5), Math.sin(now * 0.2 + i) * 0.1]}
          renderOrder={2}
        >
          <planeGeometry args={[1.7, 17]} />
          <meshBasicMaterial map={tex} transparent opacity={opacity} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} />
        </mesh>
      ))}
    </group>
  );
}

/** Seabed with sand albedo + slow caustic shimmer (frame-driven, deterministic). */
export function CausticBed({now, y, z = -2}: {now: number; y: number; z?: number}) {
  const sand = useMemo(() => sandMaps(5), []);
  const caustic = useMemo(() => causticMap(11), []);
  const causticAnim = useMemo(() => {
    if (!caustic) return null;
    caustic.offset.set((now * 0.008) % 1, (now * 0.005) % 1);
    return caustic;
  }, [caustic, now]);
  return (
    <group>
      <mesh position={[0, y, z]} rotation={[-Math.PI / 2, 0, 0]} renderOrder={1}>
        <planeGeometry args={[110, 44]} />
        {sand ? (
          <meshStandardMaterial map={sand.map} bumpMap={sand.bumpMap} bumpScale={0.05} color="#ffffff" roughness={0.96} metalness={0} />
        ) : (
          <meshStandardMaterial color={PALETTE.seabed} roughness={0.96} metalness={0} />
        )}
      </mesh>
      {causticAnim && (
        <mesh position={[0, y + 0.02, z]} rotation={[-Math.PI / 2, 0, 0]} renderOrder={2}>
          <planeGeometry args={[90, 36]} />
          <meshBasicMaterial map={causticAnim} transparent opacity={0.16} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} />
        </mesh>
      )}
    </group>
  );
}

/** Dark water-column gradient backdrop for depth. */
export function WaterColumn() {
  const tex = useMemo(() => waterGradientMap(), []);
  return (
    <mesh position={[0, 0, -14]} renderOrder={0}>
      <planeGeometry args={[120, 90]} />
      {tex ? (
        <meshBasicMaterial map={tex} toneMapped={false} />
      ) : (
        <meshBasicMaterial color={PALETTE.seaDeep} toneMapped={false} />
      )}
    </mesh>
  );
}

/** Restrained 9:16 vignette overlay (DOM; no text, no font metrics). */
export function CineVignette() {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        background:
          'radial-gradient(ellipse 92% 78% at 50% 46%, rgba(0,0,0,0) 58%, rgba(1,3,7,0.42) 100%), linear-gradient(to bottom, rgba(1,3,7,0.18) 0%, rgba(0,0,0,0) 18%, rgba(0,0,0,0) 82%, rgba(1,3,7,0.3) 100%)',
      }}
    />
  );
}
