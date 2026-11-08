#!/usr/bin/env python3
"""
Optimize a model for the web: merge by distance, decimate, triangulate,
downscale textures, and export a Draco-compressed .glb. Validated on Blender 5.1.2.

Usage:
    blender --background --factory-startup <input.blend> \
        --python optimize_model.py -- <output.glb> [decimate_ratio] [tex_max]

    decimate_ratio: 0..1 fraction of polys to KEEP (default 0.3)
    tex_max:        max texture dimension in px (default 1024)
"""
import bpy
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
out_path = argv[0] if argv else "/tmp/optimized.glb"
ratio = float(argv[1]) if len(argv) > 1 else 0.3
tex_max = int(argv[2]) if len(argv) > 2 else 1024


def clean_and_decimate(obj, target_ratio):
    if obj.type != "MESH":
        return
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Merge by distance + triangulate (edit mode)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.merge(type="DISTANCE")
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode="OBJECT")

    # Decimate
    dec = obj.modifiers.new(name="Decimate", type="DECIMATE")
    dec.ratio = target_ratio
    dec.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier="Decimate")
    print(f"  {obj.name}: {len(obj.data.polygons)} tris after optimize")


# Operate on all mesh objects
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print(f"Optimizing {len(meshes)} mesh object(s) (keep ratio={ratio})")
for obj in meshes:
    clean_and_decimate(obj, ratio)

# Downscale oversized textures
for img in bpy.data.images:
    if img.size[0] > tex_max or img.size[1] > tex_max:
        img.scale(min(img.size[0], tex_max), min(img.size[1], tex_max))
        print(f"  downscaled {img.name} -> {img.size[0]}x{img.size[1]}")

# Export
bpy.ops.export_scene.gltf(
    filepath=out_path,
    export_format="GLB",
    export_apply=True,
    export_draco_mesh_compression_enable=True,
    export_draco_mesh_compression_level=8,
    export_draco_position_quantization=12,
    export_draco_normal_quantization=8,
    export_draco_texcoord_quantization=10,
)
import os
print(f"Exported -> {out_path} ({os.path.getsize(out_path)/1024:.0f} KB)")
