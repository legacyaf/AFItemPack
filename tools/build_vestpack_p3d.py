"""Build the AF Vest Pack: textures (PNG) and the worn and ground P3D models, from the
Meshy low-poly GLB in models/vest_pack.

    blender -b --python tools/build_vestpack_p3d.py -- <repo root>

Writes VestPack_m.p3d, _f.p3d and _g.p3d into AFItemPack/VestPack, three texture PNGs into
AFItemPack/VestPack/data (tools/build.ps1 converts them to PAA), and saves the scenes in
tools/blend/.
"""
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3d_common as p3d  # noqa: E402

# ---- fit settings (metres; Z up, the character faces -Y, +X is the character's left) ----
# The GLB is about 0.78 wide, 0.73 deep and 0.95 tall, front toward -Y. Measured inside it
# (GLB units): the back panel's inner face is at y = +0.12, the side panels at x = +-0.24, the
# front panels about y = -0.22, the underside of the shoulder straps about z = +0.45.
# The body (measured in game, T-shirt): back 0.15-0.19 behind the spine line at the shoulder
# blades, chest 0.09 in front, sides about 0.15-0.17 from the centre, shoulders 1.47-1.50 high.
SCALE = (0.78, 0.96, 0.75)      # deepened relative to its height: at 0.88 deep the chest showed through the front panels
# Hip pouches: below HIP_Z[0] (and in front of the pack) the mesh is narrowed to this share of its
# width, fading out up to HIP_Z[1], so the pouches sit in front of the hanging arms, not in them.
HIP_NARROW = 0.86
HIP_Z = (0.985, 1.04)
SRC_INNER_BACK_Y = 0.12
INNER_BACK_Y = 0.18             # where that inner back face goes: just behind the shoulder blades
SRC_STRAP_UNDERSIDE_Z = 0.45
STRAP_UNDERSIDE_Z = 1.495       # where the underside of the shoulder straps goes
# The pack must sit entirely under the Field Cape, never through it (the owner's requirement).
# The room between the back and the cape's lining is about 3 cm, so:
# - the bedroll is removed (GLB box below; nothing 15 cm thick fits under a cape);
# - everything behind SRC_PACK_MIN_Y (the pack body) is squeezed flat against the back panel,
#   to within CAPE_CLEARANCE of the lining (p3d.cape_inner_y), height by height;
# - any vertex still behind that limit is moved onto it.
SRC_BEDROLL_MAX_Z = -0.255
SRC_BEDROLL_MIN_Y = 0.14
SRC_PACK_MIN_Y = 0.135
CAPE_CLEARANCE = 0.006
GROUND_PACK_SQUEEZE = 0.15      # the same flattening for the ground model, as a share of the depth
# Bone weights: in front, the upper back above BLEND_Z[1], the hips below BLEND_Z[0], a
# straight-line mix between. On the back (behind WEIGHT_Y[1]) the mix is the cape's own, so
# pack and cape move together and stay apart in every pose; between the two Y values it fades.
UPPER_BONE, LOWER_BONE = "Spine3", "Pelvis"
BLEND_Z = (0.90, 1.32)
WEIGHT_Y = (0.05, 0.15)
PACK_MIN_Y = 0.19               # behind this is the back: not narrowed with the hip pouches
GROUND_MASS_KG = 2.2
# LODs 6-8 are for far distances: a few hundred triangles down to a few dozen.
LOD_RATIOS = ((2, 0.50, "collapse"), (3, 0.25, "collapse"), (4, 0.10, "cluster"), (5, 0.04, "cluster"),
              (6, 0.02, "cluster"), (7, 0.008, "cluster"), (8, 0.003, "cluster"))

TEXTURE = r"AFItemPack\VestPack\data\vest_pack_co.paa"
RVMAT = r"AFItemPack\VestPack\data\vest_pack.rvmat"

repo = sys.argv[sys.argv.index("--") + 1]
glb = os.path.join(repo, "models", "vest_pack", "lowpoly", "vest_pack_12k.glb")
out_dir = os.path.join(repo, "AFItemPack", "VestPack")
data_dir = os.path.join(out_dir, "data")
blend_dir = os.path.join(repo, "tools", "blend")
os.makedirs(blend_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)
p3d.require_addon()


def load():
    p3d.new_scene()
    bpy.ops.import_scene.gltf(filepath=glb)
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    for mat in obj.data.materials:
        mat.a3ob_properties_material.texture_path = TEXTURE
        mat.a3ob_properties_material.material_path = RVMAT
    # Remove the bedroll and tag the pack body (GLB coordinates).
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    layer = bm.verts.layers.int.new("pack")   # before collecting: adding a layer invalidates references
    # The bedroll and its straps are separate pieces of the mesh: remove every connected piece
    # whose middle lies in the bedroll's box. (Removing only the faces inside the box left a
    # pale sliver of bedroll along the pack's bottom edge.)
    bedroll, seen = [], set()
    for start in bm.verts:
        if start in seen:
            continue
        piece, stack = [], [start]
        seen.add(start)
        while stack:
            vert = stack.pop()
            piece.append(vert)
            for edge in vert.link_edges:
                other = edge.other_vert(vert)
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        ys, zs = [p.co.y for p in piece], [p.co.z for p in piece]
        if (min(zs) + max(zs)) / 2 < SRC_BEDROLL_MAX_Z and (min(ys) + max(ys)) / 2 > SRC_BEDROLL_MIN_Y:
            bedroll.extend({f for p in piece for f in p.link_faces})
            print("BEDROLL piece", len(piece), "verts, z %.2f..%.2f y %.2f..%.2f" % (min(zs), max(zs), min(ys), max(ys)))
    bedroll = list(set(bedroll))
    bmesh.ops.delete(bm, geom=bedroll, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    for v in bm.verts:
        v[layer] = 1 if v.co.y > SRC_PACK_MIN_Y else 0
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    print("BEDROLL faces removed", len(bedroll))
    return obj


def pack_vertices(obj):
    attr = obj.data.attributes["pack"]
    return [obj.data.vertices[i] for i, d in enumerate(attr.data) if d.value]


# ---- textures ------------------------------------------------------------------------
def image_behind(socket):
    """The image texture feeding a shader input, looking through normal-map and separate nodes."""
    node = socket.links[0].from_node if socket.links else None
    while node and node.type != 'TEX_IMAGE':
        link = next((i.links[0] for i in node.inputs if i.links), None)
        node = link.from_node if link else None
    return node.image if node else None


def pixels(image):
    w, h = image.size
    data = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(data)
    return data.reshape(h, w, 4)


def save_png(name, rgb):
    h, w = rgb.shape[:2]
    image = bpy.data.images.new(name, w, h, alpha=False)
    image.colorspace_settings.name = 'Non-Color'   # write the numbers as they are
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(rgb, 0, 1)
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = os.path.join(data_dir, name + ".png")
    image.file_format = 'PNG'
    image.save()
    print("TEXTURE", image.filepath_raw)


def export_textures(obj):
    bsdf = next(n for n in obj.data.materials[0].node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    colour = image_behind(bsdf.inputs["Base Color"])
    normal = image_behind(bsdf.inputs["Normal"])
    rough = image_behind(bsdf.inputs["Roughness"])
    # Pixels of an 8-bit image come back as stored in the file (sRGB), which is what the game
    # texture wants. Converting them again washed the colours out to pale grey.
    srgb = pixels(colour)[:, :, :3]
    save_png("vest_pack_co", srgb)
    if normal:
        save_png("vest_pack_nohq", pixels(normal)[:, :, :3])
    else:
        save_png("vest_pack_nohq", np.dstack([np.full(srgb.shape[:2], v, dtype=np.float32) for v in (0.5, 0.5, 1.0)]))
    # SMDI: red unused (1), green specular strength, blue gloss. glTF packs roughness in green
    # and metalness in blue. Cloth stays dull; the brass buckles get a highlight.
    if rough:
        orm = pixels(rough)
        roughness, metal = orm[:, :, 1], orm[:, :, 2]
    else:
        roughness, metal = np.full(srgb.shape[:2], 0.9, dtype=np.float32), np.zeros(srgb.shape[:2], dtype=np.float32)
    # With 0.06 + 0.20 * (1 - roughness) the wool panels had a pale sheen in daylight.
    spec = 0.03 + 0.08 * (1 - roughness) + 0.55 * metal
    gloss = 0.08 + 0.25 * (1 - roughness) + 0.40 * metal
    save_png("vest_pack_smdi", np.dstack((np.ones_like(spec), spec, gloss)))


# ---- worn model (male; the female file is the same mesh) -------------------------------
vest = load()
export_textures(vest)
fit = (Matrix.Translation((0, INNER_BACK_Y - SRC_INNER_BACK_Y * SCALE[1], STRAP_UNDERSIDE_Z - SRC_STRAP_UNDERSIDE_Z * SCALE[2]))
       @ Matrix.Diagonal((*SCALE, 1.0)))
vest.data.transform(fit)
for v in vest.data.vertices:
    if v.co.y < PACK_MIN_Y and v.co.z < HIP_Z[1]:
        keep = min(1.0, max(0.0, (v.co.z - HIP_Z[0]) / (HIP_Z[1] - HIP_Z[0])))
        v.co.x *= HIP_NARROW + (1 - HIP_NARROW) * keep
# Squeeze the pack body under the cape, then make sure nothing at all is behind the limit.
pack = pack_vertices(vest)
pack_front = SRC_PACK_MIN_Y * SCALE[1] + fit.translation.y
pack_back = max(v.co.y for v in pack)
for v in pack:
    limit = p3d.cape_inner_y(v.co.x, v.co.z)
    if limit is not None:
        room = max(0.0, limit - CAPE_CLEARANCE - pack_front)
        v.co.y = pack_front + (v.co.y - pack_front) * room / (pack_back - pack_front)
moved = 0
for v in vest.data.vertices:
    limit = p3d.cape_inner_y(v.co.x, v.co.z)
    if limit is not None and v.co.y > limit - CAPE_CLEARANCE:
        v.co.y = limit - CAPE_CLEARANCE
        moved += 1
vest.data.update()
gaps = [p3d.cape_inner_y(v.co.x, v.co.z) - v.co.y for v in vest.data.vertices if p3d.cape_inner_y(v.co.x, v.co.z) is not None]
print("CAPE CLEARANCE smallest gap to the cape's lining %.1f mm over %d vertices; %d moved onto the limit; pack depth was %.0f mm"
      % (min(gaps) * 1000, len(gaps), moved, (pack_back - pack_front) * 1000))
if min(gaps) < CAPE_CLEARANCE - 1e-6:
    raise SystemExit("the vest pack reaches the cape")
vest.name = "vestpack_worn_lod1"
p3d.mark_lod(vest, p3d.LOD_VISUAL, 1)
upper = vest.vertex_groups.new(name=UPPER_BONE)
lower = vest.vertex_groups.new(name=LOWER_BONE)
for v in vest.data.vertices:
    front = min(1.0, max(0.0, (v.co.z - BLEND_Z[0]) / (BLEND_Z[1] - BLEND_Z[0])))
    back = min(1.0, max(0.0, (v.co.y - WEIGHT_Y[0]) / (WEIGHT_Y[1] - WEIGHT_Y[0])))
    w = front + (p3d.cape_blend(v.co.z) - front) * back
    if w > 0:
        upper.add([v.index], w, 'REPLACE')
    if w < 1:
        lower.add([v.index], 1 - w, 'REPLACE')
p3d.add_copy(vest, p3d.LOD_VIEW_PILOT)   # first person uses the full-detail mesh
p3d.add_lower_lods(vest, "vestpack_worn", LOD_RATIOS)
# Reducing a mesh moves its vertices a little; put the lower LODs back inside the limit too.
for lod in (o for o in bpy.context.scene.objects if o.name.startswith("vestpack_worn_lod")):
    for v in lod.data.vertices:
        limit = p3d.cape_inner_y(v.co.x, v.co.z)
        if limit is not None and v.co.y > limit - CAPE_CLEARANCE:
            v.co.y = limit - CAPE_CLEARANCE
    lod.data.update()
p3d.worn_geometry("vestpack_worn_geometry")
print("WORN BOUNDS", [tuple(round(c, 3) for c in b) for b in p3d.bounds(vest)])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_dir, "vestpack_worn.blend"))
p3d.export(os.path.join(out_dir, "VestPack_m.p3d"))
p3d.export(os.path.join(out_dir, "VestPack_f.p3d"))

# ---- ground model: lying on its back -----------------------------------------------
vest = load()
for v in pack_vertices(vest):
    v.co.y = SRC_PACK_MIN_Y + (v.co.y - SRC_PACK_MIN_Y) * GROUND_PACK_SQUEEZE
vest.data.transform(Matrix.Rotation(-1.5707963267948966, 4, 'X') @ Matrix.Diagonal((*SCALE, 1.0)))
mn, mx = p3d.bounds(vest)
vest.data.transform(Matrix.Translation((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z)))
vest.data.update()
vest.name = "vestpack_ground_lod1"
p3d.mark_lod(vest, p3d.LOD_VISUAL, 1)
p3d.add_lower_lods(vest, "vestpack_ground", LOD_RATIOS)
mn, mx = p3d.bounds(vest)
p3d.ground_geometry("vestpack_ground_geometry", mn, mx, GROUND_MASS_KG)
print("GROUND BOUNDS", [tuple(round(c, 3) for c in b) for b in (mn, mx)])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_dir, "vestpack_ground.blend"))
p3d.export(os.path.join(out_dir, "VestPack_g.p3d"))
