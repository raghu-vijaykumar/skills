"""Original analog-horror security tape of an empty corporate training room."""

from pathlib import Path
import math

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def animate(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def words(name, body, location, size, mat, parent=None):
    """Keep tape UI and screen copy editable as Blender text objects."""
    curve = bpy.data.curves.new(name, "FONT")
    curve.body = body
    curve.size = size
    curve.extrude = 0
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.data.materials.append(mat)
    if parent is not None:
        obj.parent = parent
    return obj


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2, 3):
        raise ValueError("Unknown authored analog tape candidate")
    scene = reset_scene(spec, background=(0.006, 0.008, 0.007))
    scene.view_settings.view_transform = "Standard"
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.20
    floor = material("Tape institutional linoleum", (0.20, 0.24, 0.20), roughness=0.88)
    wall = material("Tape stale mint plaster", (0.25, 0.32, 0.26), roughness=0.94)
    dark = material("Tape unlit doorway", (0.011, 0.018, 0.016), roughness=1)
    plastic = material("Tape brown plastic chair", (0.16, 0.11, 0.08), roughness=0.74)
    steel = material("Tape desk steel", (0.21, 0.23, 0.21), metallic=0.65,
                     roughness=0.66)
    screen = material("Tape dead green phosphor", (0.12, 0.25, 0.16),
                      emission=(0.22, 0.47, 0.25), emission_strength=1.6)
    ui = material("Tape pale tracking UI", (0.58, 0.73, 0.58),
                  emission=(0.66, 0.85, 0.68), emission_strength=1.2)
    mute = material("Tape rolling charcoal", (0.035, 0.056, 0.050), roughness=1)
    red = material("Tape chroma bleed red", (0.61, 0.09, 0.07),
                   emission=(0.66, 0.13, 0.09), emission_strength=0.7)
    blue = material("Tape chroma bleed blue", (0.05, 0.20, 0.35),
                    emission=(0.08, 0.25, 0.42), emission_strength=0.7)

    # A mundane, slightly asymmetrical training room reads as recorded evidence.
    cube("SM_Tape_Room_Floor", (0, 0, -0.16), (9, 9, 0.3), floor)
    cube("Tape back wall", (0, 3.15, 2.4), (9, 0.18, 4.9), wall)
    cube("Tape left wall", (-4.45, 0, 2.4), (0.18, 6.6, 4.9), wall)
    cube("Tape ceiling strip", (0, 0, 4.77), (9, 7, 0.16), wall)
    for i in range(7):
        cube(f"Tape floor seam {i}", (-3.9 + i * 1.25, 0, 0.006),
             (0.015, 8.3, 0.008), steel)
    for i in range(5):
        cube(f"Tape cross seam {i}", (0, -3.5 + i * 1.5, 0.008),
             (8.4, 0.015, 0.008), steel)
    # The training monitor sits too far from its single empty chair.
    cube("Tape desk top", (-1.90, 2.18, 1.25), (2.1, 0.72, 0.12), steel,
         edge=0.035)
    for x in (-2.75, -1.08):
        cube(f"Tape desk leg {x}", (x, 2.20, 0.62),
             (0.08, 0.07, 1.18), steel)
    cube("Tape monitor shell", (-1.90, 2.02, 1.98),
         (1.37, 0.25, 1.05), plastic, edge=0.045)
    cube("SM_Tape_Monitor_Screen", (-1.90, 1.86, 2.02),
         (1.13, 0.035, 0.76), screen, edge=0.02)
    training = words("Tape monitor orientation", "SAFETY\nORIENTATION",
                     (-2.34, 1.825, 2.20), 0.16, mute)
    training.rotation_euler.x = math.pi / 2
    if variant == 3:
        signal = words("Tape monitor dead channel", "NO SIGNAL",
                       (-2.33, 1.81, 2.05), 0.17, ui)
        signal.rotation_euler.x = math.pi / 2
        for obj, visible_first in ((training, True), (signal, False)):
            obj.hide_render = not visible_first
            obj.keyframe_insert(data_path="hide_render", frame=1)
            obj.keyframe_insert(data_path="hide_render", frame=47)
            obj.hide_render = visible_first
            obj.keyframe_insert(data_path="hide_render", frame=48)
        phosphor = screen.node_tree.nodes.get("Principled BSDF")
        glow = phosphor.inputs["Emission Strength"]
        for frame, strength in ((1, 1.6), (36, 1.4), (47, 1.6),
                                (48, 0.10), (72, 0.06)):
            glow.default_value = strength
            glow.keyframe_insert(data_path="default_value", frame=frame)
    cube("Tape chair seat", (-0.15, -0.38, 0.68),
         (0.73, 0.68, 0.09), plastic, edge=0.025)
    cube("SM_Tape_Empty_Chair", (-0.15, -0.02, 1.12),
         (0.73, 0.09, 0.90), plastic, edge=0.04)
    for x in (-0.47, 0.17):
        for y in (-0.65, -0.08):
            cylinder(f"Tape chair leg {x} {y}", (x, y, 0.33),
                     0.025, 0.65, steel, vertices=12)

    cube("Tape doorway black", (2.05, 3.01, 1.36),
         (1.25, 0.07, 2.68), dark)
    cube("Tape doorway left trim", (1.36, 2.89, 1.36),
         (0.13, 0.19, 2.85), steel)
    cube("Tape doorway right trim", (2.74, 2.89, 1.36),
         (0.13, 0.19, 2.85), steel)
    cube("Tape doorway lintel", (2.05, 2.89, 2.78),
         (1.5, 0.19, 0.13), steel)
    figure = bpy.data.objects.new("Tape implied figure control", None)
    scene.collection.objects.link(figure)
    figure.location = (2.12, 2.92, 0)
    torso = sphere("SM_Tape_Implied_Figure", (0, -0.11, 1.06),
                   1, dark, segments=24, rings=12,
                   scale=(0.31, 0.12, 0.88))
    head = sphere("Tape implied figure head", (0, -0.11, 2.03),
                  0.25, dark, segments=20, rings=10,
                  scale=(0.90, 0.60, 1.0))
    for obj in (torso, head):
        obj.parent = figure
        # The doorway must be empty in the opening frame, then reveal only a silhouette.
        obj.hide_render = True
        if variant >= 2:
            obj.keyframe_insert(data_path="hide_render", frame=1)
            obj.keyframe_insert(data_path="hide_render", frame=41)
            obj.hide_render = False
            obj.keyframe_insert(data_path="hide_render", frame=42)
    figure["implied_only"] = True
    if variant >= 2:
        animate(figure, "location", ((1, (2.60, 2.92, 0)),
                                     (37, (2.60, 2.92, 0)),
                                     (54, (2.13, 2.92, 0)),
                                     (72, (2.13, 2.92, 0))))

    light = area_light("Tape unreliable fluorescent", (0.0, -0.4, 4.5),
                       690, 3.2, color=(0.68, 0.86, 0.69),
                       target=(0, 0, 1.4))
    animate(light.data, "energy", ((1, 690), (28, 675), (36, 210),
                                    (39, 720), (54, 480 if variant == 2 else 690),
                                    (72, 640)))
    area_light("Tape monitor bounce", (-1.9, 0.8, 2.35), 90, 1.4,
               color=(0.18, 0.75, 0.36), target=(-1.7, 0.2, 1.2))
    cam = camera("Tape locked security camera", (3.5, -5.1, 3.25),
                 (0, 0.5, 1.65), ortho=9.0)
    if variant >= 2:
        animate(cam, "location", ((1, (3.5, -5.1, 3.25)),
                                  (22, (3.48, -5.09, 3.27)),
                                  (37, (3.55, -5.13, 3.20)),
                                  (54, (3.47, -5.07, 3.28)),
                                  (72, (3.5, -5.1, 3.25))))
    # Flat UI in camera space makes the tape effect survive a full headless render.
    words("SM_Tape_Camera_Label", "CAM 03   TRAINING  /  1997",
          (-4.15, 2.18, -1.8), 0.23, ui, cam)
    words("Tape REC indicator", "REC  ●", (3.00, 2.18, -1.8), 0.22, red, cam)
    words("Tape timestamp", "10:24:17  SP", (-4.15, -2.40, -1.8), 0.20, ui, cam)
    words("Tape corporate warning", "PROPERTY OF FACILITIES DIVISION",
          (-1.95, -2.42, -1.8), 0.16, ui, cam)
    # Chroma-offset duplicate UI and dense dark scanlines suggest tape recording,
    # while one traveling pale line visibly damages the exact output frames.
    if variant >= 2:
        words("Tape red bleed", "CAM 03", (-4.12, 2.18, -1.82), 0.23, red, cam)
        words("Tape blue bleed", "CAM 03", (-4.18, 2.18, -1.84), 0.23, blue, cam)
    for i in range(18 if variant == 1 else 31):
        y = -2.45 + i * (4.90 / (17 if variant == 1 else 30))
        line = cube(f"Tape fixed scanline {i}", (0, y, -1.7),
                    (8.5, 0.010 if variant == 1 else 0.015, 0.003), mute)
        line.parent = cam
    bar = cube("SM_Tape_Rolling_Tracking_Bar", (0, 2.4, -1.65),
               (8.5, 0.065 if variant >= 2 else 0.025, 0.005), ui)
    bar.parent = cam
    tracking_samples = [(1, (0, 2.4, -1.65)), (36, (0, -0.2, -1.65))]
    if variant == 3:
        tracking_samples.extend(((46, (0, -1.4, -1.65)),
                                 (47, (0, 2.1, -1.65))))
    tracking_samples.append((72, (0, -2.35, -1.65)))
    animate(bar, "location", tracking_samples)
    scene["analog_recipe"] = "mundane training room, implied doorway, locked tape UI, scanlines, tracking"
    scene["analog_variant"] = variant
    return scene
