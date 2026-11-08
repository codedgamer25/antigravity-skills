---
name: blender
description: Best practices for Blender — 3D modeling, materials, and headless rendering via the Python (bpy) API
metadata:
  tags: blender, bpy, 3d, rendering, python, headless, gltf, cycles, eevee
---

## When to use

Use this skill whenever the task involves Blender: creating or editing 3D scenes, modeling, materials, lighting, cameras, animation, importing/exporting 3D assets (glTF/FBX/OBJ), or rendering images and video. Blender is GUI software, but everything below is driven through its **Python API (`bpy`)** run **headless from the command line**, which is how an agent should automate it — deterministic, scriptable, no GUI needed.

Always confirm the Blender version first (`blender --version`). The `bpy` API has breaking changes between major versions; this skill targets **Blender 4.x**.

## Running Blender headless (the core workflow)

Write a `.py` script, then run Blender in background mode. Do **not** try to "open" Blender interactively.

```bash
# Run a script against an empty scene (deterministic — ignores user prefs/startup file)
blender --background --factory-startup --python script.py

# Open an existing .blend, then run a script on it
blender --background --factory-startup my_scene.blend --python script.py

# Pass arguments to your script: everything after `--` lands in sys.argv
blender -b --factory-startup --python script.py -- --out /abs/path/out.png --frames 0 120
```

- `--background` / `-b` = no GUI. `--factory-startup` = reproducible (no add-on/pref interference).
- Parse your own args after `--`: `argv = sys.argv[sys.argv.index("--") + 1:]`.
- Blender exits non-zero on a Python exception — check the exit code and stderr.
- Prefer **absolute paths** for all inputs/outputs; the CWD in background mode is not guaranteed.

## bpy fundamentals: prefer the data API over operators

`bpy.ops.*` operators depend on the current UI **context** (active object, selection, area, mode) and frequently fail or behave unexpectedly in headless mode. Prefer the **data API** (`bpy.data`) which is context-independent and reliable.

```python
import bpy

# Start from a truly empty scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Create a mesh object via the DATA API (reliable headless)
mesh = bpy.data.meshes.new("CubeMesh")
obj = bpy.data.objects.new("Cube", mesh)
bpy.context.collection.objects.link(obj)

# Build geometry with bmesh (procedural, no operators)
import bmesh
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=2.0)
bm.to_mesh(mesh)
bm.free()

# Transform via object properties, not operators
obj.location = (0, 0, 1)
obj.rotation_euler = (0, 0, 0.785)
obj.scale = (1, 1, 1)
```

If you must use an operator that needs context (e.g. some modeling tools), set the active/selected object explicitly and, when needed, use a context override:

```python
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
with bpy.context.temp_override(active_object=obj, selected_objects=[obj]):
    bpy.ops.object.shade_smooth()
```

Quick primitive shortcuts (operators, fine for one-offs): `bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,0))`, `primitive_uv_sphere_add`, `primitive_plane_add`.

## Materials (always use nodes + Principled BSDF)

```python
mat = bpy.data.materials.new("RedMetal")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.8, 0.1, 0.1, 1.0)   # RGBA, linear
bsdf.inputs["Metallic"].default_value = 0.9
bsdf.inputs["Roughness"].default_value = 0.25
# Emission (input names changed in 4.x): use "Emission Color" + "Emission Strength"
bsdf.inputs["Emission Color"].default_value = (1, 0, 0.4, 1)
bsdf.inputs["Emission Strength"].default_value = 5.0
obj.data.materials.append(mat)
```

Note: some Principled BSDF socket names differ across 4.x. If a key raises `KeyError`, print available sockets: `print([s.name for s in bsdf.inputs])`.

## Camera and lighting

```python
# Camera
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (7, -7, 5)
cam.rotation_euler = (1.1, 0, 0.785)
bpy.context.scene.camera = cam          # REQUIRED before rendering

# Area light
light_data = bpy.data.lights.new("Key", type='AREA')   # POINT | SUN | SPOT | AREA
light_data.energy = 1000                                # watts
light = bpy.data.objects.new("Key", light_data)
bpy.context.collection.objects.link(light)
light.location = (4, -4, 6)
```

To aim a camera/light at a target without computing Euler angles, add a `TRACK_TO` constraint pointing at an empty.

## Rendering stills and animation

```python
scene = bpy.context.scene

# Engine: 'CYCLES' (path-traced, reliable) or EEVEE.
# EEVEE engine id is version-dependent: 'BLENDER_EEVEE_NEXT' (Blender >= 4.2),
# 'BLENDER_EEVEE' (<= 4.1). Use CYCLES if unsure.
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.film_transparent = True            # transparent background (PNG alpha)

scene.render.image_settings.file_format = 'PNG'  # PNG | JPEG | OPEN_EXR | FFMPEG
scene.render.filepath = '/abs/out/frame.png'
bpy.ops.render.render(write_still=True)          # single still

# Animation: filepath is treated as a prefix; frames append numbers
scene.frame_start, scene.frame_end = 1, 120
scene.render.filepath = '/abs/out/anim_'         # -> anim_0001.png ...
bpy.ops.render.render(animation=True)
```

For a video file directly (Blender **4.x only**): `file_format = 'FFMPEG'`, then `scene.render.ffmpeg.format = 'MPEG4'` and `scene.render.ffmpeg.codec = 'H264'`.

> ⚠️ **Blender 5.x removed FFmpeg/video output from render settings.** The `image_settings.file_format` enum no longer contains `'FFMPEG'` (only image formats: PNG, OPEN_EXR, JPEG, WEBP, etc.). Setting it raises `TypeError: enum "FFMPEG" not found`. On 5.x, **render a PNG sequence and encode externally** with ffmpeg:
> ```bash
> ffmpeg -y -framerate 24 -start_number 1 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 out.mp4
> ```
> `-pix_fmt yuv420p` composites any alpha over black (no `color`/filter needed — works with minimal ffmpeg builds). Rendering PNG-with-alpha + encoding downstream is also the more flexible path on any version (e.g. compositing into a Remotion video).

### Cycles GPU (renders are CPU-only unless you enable a device)

```python
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'   # CUDA | OPTIX | HIP | METAL | ONEAPI
prefs.get_devices()
for d in prefs.devices:
    d.use = (d.type != 'CPU')
scene.cycles.device = 'GPU'
```

Headless machines may have no GPU — wrap this in try/except and fall back to CPU.

## Import / export

```python
# glTF is the best choice for web/3D and for handing assets to other tools
bpy.ops.export_scene.gltf(filepath='/abs/out/model.glb', export_format='GLB')

# Import examples
bpy.ops.import_scene.gltf(filepath='/abs/in/model.glb')
bpy.ops.wm.obj_import(filepath='/abs/in/model.obj')      # 4.x native OBJ
bpy.ops.import_scene.fbx(filepath='/abs/in/model.fbx')

# Save the working .blend
bpy.ops.wm.save_as_mainfile(filepath='/abs/out/scene.blend')
```

## Common gotchas

- **Operators fail silently/with `RuntimeError` in headless** — use the `bpy.data` API; reserve `bpy.ops` for things with no data-level equivalent, and set context first.
- **No `scene.camera` set** → render produces nothing. Always assign it.
- **Units / scale**: Blender's default unit is 1 m. glTF/FBX importers may bring in different scales — check and apply scale (`obj.scale`, then bake if needed).
- **Linear vs sRGB color**: node color inputs are linear; a UI hex color must be converted, not pasted as 0–255.
- **`bpy.context` is read-mostly in scripts**; mutate through `bpy.data` and call `bpy.context.view_layer.update()` after transform changes if a later step reads world matrices.
- **Enable a built-in add-on** if an importer is missing: `bpy.ops.preferences.addon_enable(module='io_scene_gltf2')` (glTF ships enabled in 4.x).
- **Determinism**: always launch with `--factory-startup` so user preferences/add-ons don't change results between machines.
- **Verify before big renders**: render one low-sample frame at `resolution_percentage = 25` to sanity-check framing/lighting before committing to a full animation.

## Minimal end-to-end script

```python
# render_cube.py  ->  blender -b --factory-startup --python render_cube.py
import bpy, bmesh, sys
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[0] if argv else "/tmp/cube.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

mesh = bpy.data.meshes.new("M"); obj = bpy.data.objects.new("Cube", mesh)
scene.collection.objects.link(obj)
bm = bmesh.new(); bmesh.ops.create_cube(bm, size=2.0); bm.to_mesh(mesh); bm.free()

mat = bpy.data.materials.new("Mat"); mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.5, 0.9, 1)
obj.data.materials.append(mat)

cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d)
scene.collection.objects.link(cam); cam.location = (6, -6, 5)
cam.rotation_euler = (1.05, 0, 0.785); scene.camera = cam

l_d = bpy.data.lights.new("L", type='AREA'); l_d.energy = 1500
light = bpy.data.objects.new("L", l_d); scene.collection.objects.link(light)
light.location = (4, -4, 6)

scene.render.engine = 'CYCLES'; scene.cycles.samples = 64
scene.render.resolution_x = 1280; scene.render.resolution_y = 720
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("rendered ->", out)
```
