# glTF Export Reference (Blender 5.x)

Operator: `bpy.ops.export_scene.gltf(...)` — 108 keyword properties on Blender 5.1.2.
List them live with:

```python
print(sorted(bpy.ops.export_scene.gltf.get_rna_type().properties.keys()))
```

## Most-used parameters

| Parameter | Values | Notes |
|---|---|---|
| `filepath` | str | Output path (absolute recommended). |
| `export_format` | `'GLB'` \| `'GLTF_SEPARATE'` \| `'GLTF_EMBEDDED'` | `GLB` = single binary, best for web. |
| `use_selection` | bool | Export only selected objects. |
| `export_apply` | bool | Apply modifiers (almost always `True`). |
| `export_texcoords` | bool | UVs. |
| `export_normals` | bool | Normals. |
| `export_materials` | `'EXPORT'` \| `'PLACEHOLDER'` \| `'NONE'` | |
| `export_vertex_color` | `'MATERIAL'` \| `'ACTIVE'` \| `'NONE'` | **Renamed from `export_colors`** in modern Blender. |
| `export_animations` | bool | Include actions/animation. |
| `export_cameras` / `export_lights` | bool | Usually `False` for web (recreate in code). |
| `export_image_format` | `'AUTO'` \| `'JPEG'` \| `'WEBP'` \| `'NONE'` | `'WEBP'` = smallest web textures. |
| `export_image_quality` | 0–100 | General image quality (newer). |
| `export_jpeg_quality` | 0–100 | JPEG-specific (still valid). |
| `export_image_add_webp` | bool | Add WebP alongside fallback. |

## Draco geometry compression (verified working)

| Parameter | Range | Recommended |
|---|---|---|
| `export_draco_mesh_compression_enable` | bool | `True` for web |
| `export_draco_mesh_compression_level` | 0–10 | 6 (balance), 8–10 (max) |
| `export_draco_position_quantization` | 8–14 | 12–14 |
| `export_draco_normal_quantization` | 8–10 | 8–10 |
| `export_draco_texcoord_quantization` | 8–12 | 10–12 |
| `export_draco_color_quantization` | 8–12 | 10 |

⚠️ Draco-compressed files need a Draco **decoder** on the web side (e.g. Three.js `DRACOLoader` with `/draco/` decoder path). Without it the model won't load.

## Quick recipes

```python
# Smallest web GLB
bpy.ops.export_scene.gltf(filepath="m.glb", export_format="GLB", export_apply=True,
    export_image_format="WEBP", export_image_quality=85,
    export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=8)

# Selection only, with animation
bpy.ops.export_scene.gltf(filepath="m.glb", export_format="GLB",
    use_selection=True, export_apply=True, export_animations=True)
```

## Verify exports

Drop the `.glb` into a viewer before shipping: https://gltf-viewer.donmccurdy.com/
