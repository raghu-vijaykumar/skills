import * as THREE from 'three';
/** Deterministic pseudo-random in [0, 1) from an integer + seed. */
export declare function hash01(n: number, seed?: number): number;
/** Deterministic PRNG (mulberry32). Create per call-site with a fixed seed. */
export declare function mulberry32(seed: number): () => number;
/** Smooth 1D value noise in [0, 1]. */
export declare function valueNoise1(x: number, seed?: number): number;
/** Fractal 1D noise in [0, 1]. */
export declare function fbm1(x: number, seed?: number, octaves?: number): number;
export declare const clamp01: (u: number) => number;
export declare const lerp: (a: number, b: number, u: number) => number;
/** Soft radial gradient (glow sprites, contact shadows). */
export declare function radialMap(inner: string, outer: string, size?: number): THREE.CanvasTexture | null;
/** Fine-grain roughness + bump pair for polymers/rubber/satin. */
export declare function grainMaps(seed?: number, size?: number): {
    roughnessMap: THREE.CanvasTexture;
    bumpMap: THREE.CanvasTexture;
} | null;
/** Brushed-metal streaks (roughness variation along one axis). */
export declare function brushedMaps(seed?: number, size?: number): {
    roughnessMap: THREE.CanvasTexture;
    bumpMap: THREE.CanvasTexture;
} | null;
/** Dark seabed albedo + bump (sand speckle over soft blotches). */
export declare function sandMaps(seed?: number, size?: number): {
    map: THREE.CanvasTexture;
    bumpMap: THREE.CanvasTexture;
} | null;
/** Soft underwater caustic web (additive overlay, animated via texture offset). */
export declare function causticMap(seed?: number, size?: number): THREE.CanvasTexture | null;
/** Vertical water-column gradient (dark cinematic). */
export declare function waterGradientMap(): THREE.CanvasTexture | null;
export type PhysicalMat = {
    color: string;
    roughness: number;
    metalness: number;
    clearcoat?: number;
    clearcoatRoughness?: number;
    roughnessMap?: THREE.Texture;
    bumpMap?: THREE.Texture;
    bumpScale?: number;
    transparent?: boolean;
    opacity?: number;
    emissive?: string;
    emissiveIntensity?: number;
    envMapIntensity?: number;
    ior?: number;
    thickness?: number;
    specularIntensity?: number;
    toneMapped?: boolean;
    side?: THREE.Side;
    depthWrite?: boolean;
};
/** Satin polymer shell: soft clearcoat sheen, never mirror. */
export declare function pbrSatin(color: string): PhysicalMat;
/** Matte polymer: flat, light, readable. */
export declare function pbrMatte(color: string): PhysicalMat;
/** Rubber cable jacket: high roughness, micro-bump, faint sheen. */
export declare function pbrRubber(color: string): PhysicalMat;
/** Brushed light metal: restrained anisotropic feel via streak roughness. */
export declare function pbrMetal(color: string): PhysicalMat;
/** Translucent glass/fiber: physical, low roughness, restrained env response. */
export declare function pbrGlass(tint: string, opacity?: number): PhysicalMat;
/** Pale teaching glass core: translucent but unmistakably present. */
export declare function pbrCore(color: string, opacity?: number): PhysicalMat;
export type Vec3 = [number, number, number];
/** Gently perturb path points so cables/strands avoid a CG-perfect line. */
export declare function wobblePoints(points: Vec3[], amp?: number, freq?: number, seed?: number): Vec3[];
/** Build a CatmullRom curve from path points. */
export declare function naturalCurve(points: Vec3[]): THREE.CatmullRomCurve3;
/**
 * Helical armor wrap around a curve (subsea cable steel-wire layer).
 * Returns strand polylines in world space; render as thin tubes.
 */
export declare function helixAroundCurve(curve: THREE.CatmullRomCurve3, radius: number, wires?: number, turns?: number, samples?: number, phase?: number): Vec3[][];
/**
 * Tube with subtly varying radius (avoids CG-perfect cylinders).
 * radiusFn(u) multiplies the base radius; keep variation within ±6%.
 */
export declare function variableTubeGeometry(curve: THREE.CatmullRomCurve3, radiusFn: (u: number) => number, baseRadius: number, tubularSegments?: number, radialSegments?: number): THREE.BufferGeometry;
/** Gently irregular rock (displaced icosahedron, deterministic). */
export declare function rockGeometry(r: number, seed: number, detail?: number): THREE.BufferGeometry;
/** Subtle handheld sway added on top of authored camera anchors. */
export declare function sway3(t: number, amp?: number, seed?: number): Vec3;
export declare function add3(a: Vec3, b: Vec3): Vec3;
/** 9:16-safe vertical framing constants (fractions of frame height). */
export declare const CINE: {
    readonly captionBandY: 0.115;
    readonly subjectBandTop: 0.24;
    readonly subjectBandBottom: 0.92;
    readonly glowRestraint: 0.85;
};
