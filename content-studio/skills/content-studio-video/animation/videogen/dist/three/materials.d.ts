export type StandardMat = {
    color: string;
    roughness: number;
    metalness: number;
    emissive?: string;
    emissiveIntensity?: number;
    transparent?: boolean;
    opacity?: number;
    toneMapped?: boolean;
};
export declare const PALETTE: {
    readonly bg: "#05070a";
    readonly bgDeep: '#02040a';
    readonly text: "#f4f8fd";
    readonly muted: "#9aa7b8";
    readonly plasticLight: '#e6ebf2';
    readonly plasticMid: '#ccd5e0';
    readonly plasticShade: '#aab6c4';
    readonly glassCore: '#d9f3ff';
    readonly glassCoreHi: '#eefaff';
    readonly glassClad: '#a9cdf0';
    readonly glassCladDeep: '#7fb0dd';
    readonly metalLight: '#cfd8e3';
    readonly metalDark: '#8f9aa8';
    readonly copper: '#b87333';
    readonly wood: '#c9a26b';
    readonly rubber: '#b5764e';
    readonly rubberDark: '#7a4c33';
    readonly coreWhite: '#eef3f7';
    readonly seaDeep: '#040910';
    readonly seabed: '#2b3646';
    readonly rock: '#8b97a6';
    readonly seaLight: '#a9d4ff';
    readonly accentLight: '#fff3b0';
    readonly accentLightHot: '#fffbe6';
    readonly accentData: '#00e0ff';
    readonly accentEnergy: '#b15cff';
    readonly accentSignal: '#ffd400';
    readonly accentDetect: '#2bff88';
    readonly accentWarn: '#ff8a1f';
    readonly accentPop: '#ff2e93';
};
export declare const MAT: {
    /** Light neutral matte plastic — the default for primary objects. */
    readonly plastic: StandardMat;
    /** Slightly darker satin plastic for secondary shells / jackets. */
    readonly satin: StandardMat;
    /** Light satin metal (not mirrored). */
    readonly metal: StandardMat;
    /** Muted copper. */
    readonly copper: StandardMat;
    /** Natural light wood. */
    readonly wood: StandardMat;
    /** Colored satin/rubber cable jacket. */
    readonly rubber: (color?: string) => StandardMat;
    /** Pale teaching glass core: translucent but clearly visible. */
    readonly core: (color?: string, opacity?: number) => StandardMat;
    /** Translucent light glass/fiber. */
    readonly glass: (tint?: string, opacity?: number) => StandardMat;
    /** Emissive semantic accent — reserved for light, data, energy, signals. */
    readonly accent: (color: string, intensity?: number) => StandardMat;
};
export declare const LIGHT: {
    readonly ambient: {
        readonly color: '#cfe0f2';
        readonly intensity: 0.5;
    };
    readonly key: {
        readonly color: '#ffffff';
        readonly intensity: 1.15;
    };
    readonly rim: {
        readonly color: '#bcd8ff';
        readonly intensity: 0.9;
    };
    readonly fill: {
        readonly color: '#ffe8c0';
        readonly intensity: 0.35;
    };
};
