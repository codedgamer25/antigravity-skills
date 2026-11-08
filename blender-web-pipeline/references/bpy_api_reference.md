# bpy Quick Reference (Blender 5.x, headless)

## Launch

```bash
blender --background --factory-startup --python script.py -- arg1 arg2
blender --background --factory-startup file.blend --python script.py
```

- `--factory-startup` = deterministic (ignores user prefs/add-ons).
- Args after `--`: `argv = sys.argv[sys.argv.index('--')+1:]`.
- Blender exits `0` even on a Python traceback — check stderr, or use `--python-exit-code 1`.

## Data API vs operators

Prefer `bpy.data.*` (context-independent) over `bpy.ops.*` (depends on selection/active/area) in headless scripts.

```python
mesh = bpy.data.meshes.new("M")
obj = bpy.data.objects.new("Obj", mesh)
bpy.context.collection.objects.link(obj)
```

When an operator is required, set context first:
```python
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
```

## Scene / objects

```python
scene = bpy.context.scene
obj.location = (0, 0, 1); obj.rotation_euler = (0, 0, 0); obj.scale = (1, 1, 1)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
bpy.ops.wm.read_factory_settings(use_empty=True)   # blank scene
bpy.ops.wm.save_as_mainfile(filepath='out.blend')
```

## Mesh cleanup

```python
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.merge(type='DISTANCE')          # remove_doubles still aliases this in 5.1
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')
```

## Modifiers

```python
m = obj.modifiers.new(name='Decimate', type='DECIMATE'); m.ratio = 0.3
bpy.context.view_layer.objects.active = obj
bpy.ops.object.modifier_apply(modifier='Decimate')
```

## Materials (PBR / Principled BSDF — the glTF-friendly path)

```python
mat = bpy.data.materials.new('M'); mat.use_nodes = True
b = mat.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.8, 0.1, 0.1, 1)
b.inputs['Metallic'].default_value = 0.0
b.inputs['Roughness'].default_value = 0.5
# Emission split in 4.x+: 'Emission Color' + 'Emission Strength'
obj.data.materials.append(mat)
```

## Images / textures

```python
for img in bpy.data.images:
    if max(img.size) > 1024:
        img.scale(1024, 1024)
```

## Introspect anything

```python
print(bpy.app.version)                                   # (5, 1, 2)
print(sorted(bpy.ops.export_scene.gltf.get_rna_type().properties.keys()))
print([s.name for s in mat.node_tree.nodes['Principled BSDF'].inputs])
```
