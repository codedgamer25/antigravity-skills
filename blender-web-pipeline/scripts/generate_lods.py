#!/usr/bin/env python3
"""
Generate LOD (Level of Detail) copies of every mesh with decreasing polycount,
and optionally export each LOD as its own .glb. Validated on Blender 5.1.2.

Usage:
    blender --background --factory-startup <input.blend> \
        --python generate_lods.py -- [out_dir]

Produces, per source mesh: <name>_LOD0 (75%), _LOD1 (50%), _LOD2 (25%).
If out_dir is given, each LOD level is exported as <name>_LOD<i>.glb.
"""
import bpy
import os
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
out_dir = argv[0] if argv else None
if out_dir:
    os.makedirs(out_dir, exist_ok=True)

LOD_LEVELS = [0.75, 0.5, 0.25]


def make_lods(obj):
    created = []
    for i, ratio in enumerate(LOD_LEVELS):
        lod = obj.copy()
        lod.data = obj.data.copy()
        lod.name = f"{obj.name}_LOD{i}"
        bpy.context.collection.objects.link(lod)

        dec = lod.modifiers.new(name="Decimate", type="DECIMATE")
        dec.ratio = ratio
        bpy.context.view_layer.objects.active = lod
        bpy.ops.object.modifier_apply(modifier="Decimate")

        created.append(lod)
        print(f"  {lod.name}: {len(lod.data.polygons)} tris")
    return created


source_meshes = [o for o in list(bpy.data.objects) if o.type == "MESH"]
for src in source_meshes:
    print(f"LODs for {src.name}:")
    lods = make_lods(src)

    if out_dir:
        for i, lod in enumerate(lods):
            bpy.ops.object.select_all(action="DESELECT")
            lod.select_set(True)
            bpy.context.view_layer.objects.active = lod
            path = os.path.join(out_dir, f"{lod.name}.glb")
            bpy.ops.export_scene.gltf(
                filepath=path,
                export_format="GLB",
                use_selection=True,
                export_apply=True,
                export_draco_mesh_compression_enable=True,
                export_draco_mesh_compression_level=6,
            )
            print(f"    exported {os.path.basename(path)}")

print("LOD generation complete.")
