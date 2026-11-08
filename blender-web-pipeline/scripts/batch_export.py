#!/usr/bin/env python3
"""
Batch export every .blend in a directory to web-optimized glTF (.glb).
Validated on Blender 5.1.2.

Usage:
    blender --background --factory-startup --python batch_export.py -- <input_dir> [output_dir]

If output_dir is omitted, "<input_dir>_gltf" is used. Each .blend is opened in
isolation and exported with Draco geometry compression.
"""
import bpy
import os
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []

input_dir = argv[0] if argv else os.getcwd()
output_dir = argv[1] if len(argv) > 1 else input_dir.rstrip("/\\") + "_gltf"
os.makedirs(output_dir, exist_ok=True)

blend_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".blend")]
print(f"Found {len(blend_files)} .blend file(s) in {input_dir}")

ok, fail = 0, 0
for blend_file in blend_files:
    in_path = os.path.join(input_dir, blend_file)
    out_path = os.path.join(output_dir, blend_file[:-6] + ".glb")
    print(f"Processing: {blend_file}")
    try:
        bpy.ops.wm.open_mainfile(filepath=in_path)
        bpy.ops.export_scene.gltf(
            filepath=out_path,
            export_format="GLB",
            export_apply=True,
            export_draco_mesh_compression_enable=True,
            export_draco_mesh_compression_level=6,
        )
        size = os.path.getsize(out_path) / 1024.0
        print(f"  OK -> {os.path.basename(out_path)} ({size:.0f} KB)")
        ok += 1
    except Exception as e:  # noqa: BLE001
        print(f"  FAILED {blend_file}: {e!r}")
        fail += 1

print(f"Batch export complete: {ok} ok, {fail} failed -> {output_dir}")
