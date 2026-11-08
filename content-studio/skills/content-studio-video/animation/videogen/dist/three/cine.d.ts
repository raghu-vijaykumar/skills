import React from 'react';
export declare function CineLights({ variant }: {
    variant?: 'studio' | 'subsea';
}): React.JSX.Element;
/**
 * Installs a tiny dark-studio equirect environment so PBR clearcoat/metal have
 * something truthful (but dim) to reflect. Per-material envMapIntensity stays
 * low by convention; nothing becomes glossy. Safe no-op if WebGL/PMREM fails.
 */
export declare function CineEnvironment({ intensity }: {
    intensity?: number;
}): null;
/** Linear scene fog for depth falloff (DOF cue: distant layers go soft/dark). */
export declare function CineFog({ color, near, far }: {
    color?: string;
    near?: number;
    far?: number;
}): React.JSX.Element;
/** Cheap deterministic contact shadow: radial dark blob under an object. */
export declare function ContactShadow({ position, scale, opacity, }: {
    position: [number, number, number];
    scale?: number;
    opacity?: number;
}): React.JSX.Element | null;
/** Shared additive glow sprite (restrained bloom substitute). */
export declare function GlowSprite({ color, position, size, opacity, }: {
    color: string;
    position: [number, number, number];
    size: number;
    opacity?: number;
}): React.JSX.Element | null;
/** A few soft volumetric-feeling light shafts (deterministic sway). */
export declare function GodRays({ now, opacity }: {
    now: number;
    opacity?: number;
}): React.JSX.Element | null;
/** Seabed with sand albedo + slow caustic shimmer (frame-driven, deterministic). */
export declare function CausticBed({ now, y, z }: {
    now: number;
    y: number;
    z?: number;
}): React.JSX.Element;
/** Dark water-column gradient backdrop for depth. */
export declare function WaterColumn(): React.JSX.Element;
/** Restrained 9:16 vignette overlay (DOM; no text, no font metrics). */
export declare function CineVignette(): React.JSX.Element;
