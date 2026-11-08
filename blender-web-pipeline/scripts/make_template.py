#!/usr/bin/env python3
"""
Generate assets/export_template.blend — a clean, pre-configured scene for glTF
export testing: a single mesh with a Principled BSDF (PBR) material, transforms
applied, origin at geometry center. Validated on Blender 5.1.2.

Usage:
    blender --background --factory-startup --python make_template.py -- <output.blend>
"""
import bpy
import bmesh
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
out = argv[0] if argv else "export_template.blend"

bpy.ops.wm.read_factory_settings(use_empty=True)

# Subdivided rounded cube as a representative export subject
mesh = bpy.data.meshes.new("TemplateMesh")
obj = bpy.data.objects.new("ExportSubject", mesh)
bpy.context.collection.objects.link(obj)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=2.0)
bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=2, use_grid_fill=True)
for v in bm.verts:  # spherify a touch
    v.co = v.co.normalized() * 1.1 + v.co * 0.2
bm.to_mesh(mesh)
bm.free()

# PBR material (the only material type glTF exports cleanly)
mat = bpy.data.materials.new("PBR_Template")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.6, 0.6, 0.65, 1.0)
b.inputs["Metallic"].default_value = 0.0
b.inputs["Roughness"].default_value = 0.5
obj.data.materials.append(mat)

# Clean transforms / origin
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

bpy.ops.wm.save_as_mainfile(filepath=out)
print(f"Template saved -> {out}")
