"""Original tile-readable strategy settlement with two resource dispatches."""

from pathlib import Path

import bpy

from common import area_light, camera, cube, cylinder, material, reset_scene, sphere


def key(obj, path, samples):
    for frame, value in samples:
        setattr(obj, path, value)
        obj.keyframe_insert(data_path=path, frame=frame)


def cone(name, location, radius, depth, mat, vertices=6):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
                                    radius2=0, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def worker(name, x, y, mat):
    # Shared colored base and helmet make each unit readable at the overview scale.
    bpy.ops.object.empty_add(location=(x, y, 0))
    rig = bpy.context.object
    rig.name = name
    for part in (
        cylinder(name + " base", (x, y, 0.20), 0.32, 0.11, mat, vertices=16),
        cylinder(name + " body", (x, y, 0.48), 0.18, 0.43, mat, vertices=10),
        sphere(name + " head", (x, y, 0.78), 0.19, mat, segments=12, rings=8),
    ):
        bpy.context.view_layer.update()
        world = part.matrix_world.copy()
        part.parent = rig
        part.matrix_world = world
    return rig


def make_scene(spec, spec_dir=Path(".")):
    variant = spec.get("variant", 2)
    if variant not in (1, 2):
        raise ValueError("Unknown strategy settlement candidate")
    scene = reset_scene(spec, background=(0.065, 0.09, 0.12))
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.58
    ground = material("Strategy deep slate", (0.075, 0.10, 0.13), roughness=0.92)
    grass = material("Strategy olive tile", (0.22, 0.36, 0.25), roughness=0.92)
    path = material("Strategy sandstone path", (0.42, 0.37, 0.28), roughness=0.92)
    border = material("Strategy grid edge", (0.14, 0.20, 0.24), roughness=0.8)
    timber = material("Strategy hall timber", (0.38, 0.22, 0.12), roughness=0.86)
    roof = material("Strategy hall copper roof", (0.20, 0.48, 0.47), roughness=0.78)
    crop = material("Strategy golden crop", (0.72, 0.61, 0.18), roughness=0.78)
    ore = material("Strategy ore cyan", (0.10, 0.68, 0.80),
                   emission=(0.06, 0.55, 0.71), emission_strength=0.75)
    miner_mat = material("Strategy miner blue", (0.14, 0.48, 0.91), roughness=0.64)
    farmer_mat = material("Strategy farmer amber", (0.95, 0.43, 0.08), roughness=0.64)
    cube("Strategy map plinth", (0, 0, -0.30), (8.0, 6.4, 0.34), ground, edge=0.10)
    # Separate tiles preserve ownership and path clarity from the fixed strategy camera.
    for row in range(3):
        for col in range(4):
            x = -2.64 + col * 1.76
            y = -1.76 + row * 1.76
            tile_mat = path if (row == 1 or col == 1) else grass
            cube(f"SM_Strategy_Tile_{col}_{row}", (x, y, 0),
                 (1.68, 1.68, 0.20), tile_mat, edge=0.035)
            for edge_y in (-0.82, 0.82):
                cube(f"Strategy edge {col} {row} {edge_y}",
                     (x, y + edge_y, 0.11), (1.61, 0.035, 0.03), border)
    hall_x, hall_y = -0.88, 0
    cube("SM_Strategy_Command_Hall", (hall_x, hall_y, 0.59),
         (1.05, 0.97, 0.98), timber, edge=0.035)
    cube("Strategy command roof", (hall_x, hall_y, 1.16),
         (1.26, 1.20, 0.18), roof, edge=0.035)
    cylinder("Strategy command banner pole", (hall_x, hall_y, 1.49),
             0.035, 0.54, timber, vertices=10)
    cube("Strategy command banner", (hall_x + 0.22, hall_y, 1.62),
         (0.41, 0.04, 0.23), ore)
    farm_x, farm_y = -2.64, 1.76
    cube("SM_Strategy_Farm", (farm_x, farm_y, 0.18),
         (1.37, 1.31, 0.17), timber)
    for row in range(3):
        for col in range(4):
            cone(f"Strategy crop {row} {col}",
                 (farm_x - 0.48 + col * 0.32, farm_y - 0.42 + row * 0.39, 0.39),
                 0.105, 0.41, crop, vertices=5)
    mine_x, mine_y = 2.64, 0
    cube("SM_Strategy_Mine", (mine_x, mine_y, 0.38),
         (1.24, 1.33, 0.55), ground, edge=0.04)
    for i, offset in enumerate((-0.38, 0.02, 0.40)):
        cone(f"Strategy ore seam {i}", (mine_x + offset, mine_y, 0.92),
             0.18, 0.68 + i * 0.10, ore, vertices=6)
    tower_x, tower_y = 0.88, -1.76
    tower = cube("SM_Strategy_Watch_Tower", (tower_x, tower_y, 0.65),
                 (0.61, 0.61, 1.09), timber, edge=0.025)
    crown = cube("Strategy watch platform", (tower_x, tower_y, 1.27),
                 (1.00, 1.00, 0.16), roof)
    if variant == 2:
        # The tower visibly builds after dispatch, without claiming actual simulation rules.
        key(tower, "scale", ((1, (1, 1, 0.18)), (39, (1, 1, 0.18)),
                              (62, (1, 1, 1)), (72, (1, 1, 1))))
        key(crown, "location", ((1, (tower_x, tower_y, 0.43)),
                                (39, (tower_x, tower_y, 0.43)),
                                (62, (tower_x, tower_y, 1.27)),
                                (72, (tower_x, tower_y, 1.27))))
    miner = worker("SM_Strategy_Miner_Rig", -1.49, -0.57, miner_mat)
    farmer = worker("SM_Strategy_Farmer_Rig", -2.62, -0.42, farmer_mat)
    if variant == 2:
        key(miner, "location", ((1, (-1.49, -0.57, 0)),
                                 (18, (-1.49, -0.57, 0)),
                                 (55, (2.05, -0.57, 0)),
                                 (72, (2.05, -0.57, 0))))
        key(farmer, "location", ((1, (-2.62, -0.42, 0)),
                                  (23, (-2.62, -0.42, 0)),
                                  (58, (-2.48, 1.20, 0)),
                                  (72, (-2.48, 1.20, 0))))
    else:
        key(miner, "location", ((1, (-1.49, -0.57, 0)),
                                 (72, (-1.38, -0.57, 0))))
    area_light("Strategy warm settlement key", (-3, -4, 8), 1300, 6,
               color=(1.0, 0.79, 0.57), target=(0, 0, 0.3))
    area_light("Strategy blue fill", (5, 3, 6), 780, 5,
               color=(0.44, 0.76, 1.0), target=(0, 0, 0.3))
    cam = camera("Strategy settlement overview camera", (7.8, -10.2, 10.8),
                 (0, 0, 0.45), ortho=11.4)
    if variant == 2:
        key(cam, "location", ((1, (7.8, -10.2, 10.8)),
                              (72, (7.15, -9.45, 10.0))))
    scene["strategy_recipe"] = "readable tiles, iconic hall and resource buildings, color-coded units, growing watch tower"
    scene["strategy_variant"] = variant
    return scene
