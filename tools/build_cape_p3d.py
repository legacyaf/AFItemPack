"""Build the AF Cape: textures (PNG) and the worn and ground P3D models.

Run headless (needs the Arma 3 Object Builder add-on enabled in Blender):

    blender -b --python tools/build_cape_p3d.py -- <repo root>

Everything is generated from the numbers below; there is no source model. Writes
Cape_m.p3d, Cape_f.p3d and Cape_g.p3d into AFItemPack/Cape, the three texture PNGs into
AFItemPack/Cape/data (tools/build.ps1 converts them to PAA), and saves the scenes in
tools/blend/.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3d_common as p3d  # noqa: E402

# ---- fit settings (metres; Z up, the character faces -Y, +X is the character's left) ----
# Measured in game on a standing male in a T-shirt (testmission AFCape, [AFMeasure] lines):
# the back is 0.11 behind the spine line at 1.50, 0.15-0.19 at the shoulder blades (1.25-1.45),
# 0.12 at the waist (1.10), 0.14 at the seat (0.90); the shoulder ridge is 1.49-1.50 high
# 0.12 from the centre. A first cape with BLADE_Y 0.17 had its upper half inside the body.
# The cloth's own shape lives in p3d_common.CAPE, where the vest pack build reads it too.
# With NECK_Y 0.17 / BLADE_Y 0.225 / HEM_Y 0.235 the cape fitted a bare back but left no room
# for the vest pack's back panel under it; it now stands 2-2.5 cm further off.
COLLAR = p3d.CAPE["COLLAR"]
TOP_Z = p3d.CAPE["TOP_Z"]
TOP_DROP = p3d.CAPE["TOP_DROP"]
HEM_Z = p3d.CAPE["HEM_Z"]
HALF_WIDTH_TOP = p3d.CAPE["HALF_WIDTH_TOP"]   # wider and the corners meet the shoulder joints, which move
HALF_WIDTH_HEM = p3d.CAPE["HALF_WIDTH_HEM"]
NECK_Y = p3d.CAPE["NECK_Y"]   # 0.135 let the shoulder blades show through
BLADE_Z = p3d.CAPE["BLADE_Z"]
BLADE_Y = p3d.CAPE["BLADE_Y"]
HEM_Y = p3d.CAPE["HEM_Y"]
WRAP = p3d.CAPE["WRAP"]
FOLDS = 5              # vertical folds across the cloth
FOLD_DEPTH_TOP = p3d.CAPE["FOLD_DEPTH_TOP"]
FOLD_DEPTH_HEM = p3d.CAPE["FOLD_DEPTH_HEM"]
HEM_RAGGED = 0.012     # the hem is uneven by up to this much
THICKNESS = p3d.CAPE["THICKNESS"]
# Bone weights: fully the upper back above BLEND_Z[1], fully the hips below BLEND_Z[0], a straight-line mix between. In the idle stance the chest is turned and leaned against the hips, so a short or eased blend shows as a kink where it ends; mixing evenly over the whole length gives one gentle curve.
UPPER_BONE, LOWER_BONE = "Spine3", "Pelvis"
BLEND_Z = p3d.CAPE["BLEND_Z"]
# Shoulder cords: centre line of the character's left cord from the cloth, over the shoulder,
# to the clasp on the chest. The right one is its mirror image.
CORD_PATH = ((0.110, 0.175, 1.505), (0.094, 0.070, 1.537), (0.090, 0.000, 1.540), (0.085, -0.060, 1.487),
             (0.055, -0.105, 1.440), (0.0, -0.125, 1.395))
# The cords run close to the neck (9 cm from the centre) and are 3 cm wide so they pass inside
# the vest pack's shoulder straps, which start 12 cm from the centre; at 10-14 cm they crossed them.
CORD_HALF_WIDTH = 0.015
CLASP_RADIUS = 0.027
GROUND_MASS_KG = 0.6

# Visual LODs: (resolution, columns across, rows down, cord segments).
# Visual LODs: (resolution, columns across, rows down, cord segments). The far LODs (5-7) have
# no folds, cords or clasp (two-segment cords cut through the vest pack's shoulder straps): at that distance the cape is a flat green shape.
LODS = ((1, 32, 40, 20), (2, 20, 24, 10), (3, 12, 14, 5), (4, 8, 8, 5), (5, 4, 5, 0), (6, 2, 3, 0), (7, 1, 2, 0))
FOLDS_MIN_COLUMNS = 8   # fewer columns than this cannot show the folds, only alias them

TEXTURE = r"AFItemPack\Cape\data\cape_co.paa"
RVMAT = r"AFItemPack\Cape\data\cape.rvmat"
# Texture layout (UV space): cloth in the lower part, leather cord and brass clasp on top.
UV_CLOTH = (0.02, 0.02, 0.98, 0.80)
UV_CORD = (0.02, 0.85, 0.60, 0.97)
UV_CLASP = (0.66, 0.84, 0.80, 0.98)
TEXTURE_SIZE = 1024

LOD_VISUAL, LOD_VIEW_PILOT, LOD_GEOMETRY, LOD_VIEW_GEOMETRY, LOD_FIRE_GEOMETRY = "0", "2", "6", "14", "15"

repo = sys.argv[sys.argv.index("--") + 1]
out_dir = os.path.join(repo, "AFItemPack", "Cape")
data_dir = os.path.join(out_dir, "data")
blend_dir = os.path.join(repo, "tools", "blend")
os.makedirs(blend_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

if not hasattr(bpy.ops.a3ob, "export_p3d"):
    raise SystemExit("Arma 3 Object Builder add-on is not enabled in Blender")


def smooth(lo, hi, v):
    t = min(1.0, max(0.0, (v - lo) / (hi - lo)))
    return t * t * (3 - 2 * t)


# ---- textures ------------------------------------------------------------------------
def save_png(name, rgb):
    """rgb: float array (rows, cols, 3), row 0 at the bottom, values 0-1 as stored in the file."""
    size = rgb.shape[0]
    image = bpy.data.images.new(name, size, size, alpha=False)
    rgba = np.ones((size, size, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(rgb, 0, 1)
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = os.path.join(data_dir, name + ".png")
    image.file_format = 'PNG'
    image.save()
    print("TEXTURE", image.filepath_raw)


def region_mask(size, box):
    v, u = np.mgrid[0:size, 0:size] / float(size)
    return (u >= box[0] - 0.015) & (u <= box[2] + 0.015) & (v >= box[1] - 0.015) & (v <= box[3] + 0.015)


def make_textures():
    n = TEXTURE_SIZE
    rng = np.random.default_rng(7)
    v, u = np.mgrid[0:n, 0:n] / float(n)

    def blur_noise(cells):
        """Smooth noise: random values on a coarse grid, interpolated up to the image size."""
        coarse = rng.random((cells + 1, cells + 1))
        gy, gx = v * cells, u * cells
        y0, x0 = np.floor(gy).astype(int), np.floor(gx).astype(int)
        fy, fx = gy - y0, gx - x0
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        return ((coarse[y0, x0] * (1 - fx) + coarse[y0, x0 + 1] * fx) * (1 - fy)
                + (coarse[y0 + 1, x0] * (1 - fx) + coarse[y0 + 1, x0 + 1] * fx) * fy)

    # Woven wool: crossing threads, fine grain, and large uneven fading.
    weave = 0.5 + 0.25 * np.sin(u * n * math.pi / 2) * np.sin(v * n * math.pi / 2) \
        + 0.25 * np.sin((u + v) * n * math.pi / 4)
    grain = rng.random((n, n))
    fade = 0.6 * blur_noise(6) + 0.4 * blur_noise(24)
    height = 0.6 * weave + 0.4 * grain

    cloth = np.array([0.270, 0.310, 0.190])            # dark field green
    shade = 0.86 + 0.05 * weave + 0.12 * (grain - 0.5) + 0.40 * (fade - 0.5)
    co = cloth[None, None, :] * shade[:, :, None]
    # Dirt and wear toward the hem (bottom of the cloth region) and a stitched hem line.
    cloth_v = (v - UV_CLOTH[1]) / (UV_CLOTH[3] - UV_CLOTH[1])
    dirt = np.clip(1 - cloth_v / 0.30, 0, 1) ** 1.5 * (0.5 + 0.8 * blur_noise(12))
    mud = np.array([0.27, 0.22, 0.14])
    co = co * (1 - 0.6 * dirt[:, :, None]) + mud[None, None, :] * 0.6 * dirt[:, :, None]
    stitch = (np.abs(cloth_v - 0.035) < 0.004) & (np.sin(u * n * 0.35) > -0.3)
    co[stitch] *= 1.5
    spec = np.full((n, n), 0.10)
    gloss = np.full((n, n), 0.14)

    cord = region_mask(n, UV_CORD)
    leather = np.array([0.32, 0.19, 0.10])
    co[cord] = (leather[None, :] * (0.75 + 0.5 * blur_noise(40)[cord] + 0.2 * (grain[cord] - 0.5))[:, None])
    spec[cord], gloss[cord] = 0.22, 0.35
    height[cord] = 0.5 + 0.3 * (grain[cord] - 0.5)

    clasp = region_mask(n, UV_CLASP)
    cu = (u - (UV_CLASP[0] + UV_CLASP[2]) / 2) / ((UV_CLASP[2] - UV_CLASP[0]) / 2)
    cv = (v - (UV_CLASP[1] + UV_CLASP[3]) / 2) / ((UV_CLASP[3] - UV_CLASP[1]) / 2)
    radius = np.sqrt(cu * cu + cv * cv)
    brass = np.array([0.62, 0.47, 0.18])
    ring = 0.75 + 0.35 * np.cos(radius * 9) * (radius < 1.0) + 0.15 * (blur_noise(30) - 0.5)
    co[clasp] = brass[None, :] * ring[clasp][:, None]
    spec[clasp], gloss[clasp] = 0.75, 0.65
    height[clasp] = 0.5 + 0.5 * np.cos(radius[clasp] * 9) * (radius[clasp] < 1.0)

    save_png("cape_co", co)
    # Normal map from the height field.
    strength = 0.9
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * strength
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * strength
    length = np.sqrt(dx * dx + dy * dy + 1)
    save_png("cape_nohq", np.stack((0.5 - 0.5 * dx / length, 0.5 - 0.5 * dy / length, 0.5 + 0.5 / length), axis=2))
    # SMDI: red unused (1), green specular strength, blue gloss.
    save_png("cape_smdi", np.stack((np.ones((n, n)), spec, gloss), axis=2))


# ---- geometry ------------------------------------------------------------------------
class Builder:
    def __init__(self):
        self.verts, self.faces, self.uvs, self.weights = [], [], [], []

    def vert(self, co, upper):
        self.verts.append(tuple(co))
        self.weights.append(upper)
        return len(self.verts) - 1

    def face(self, indices, uvs, both_sides=False):
        self.faces.append(tuple(indices))
        self.uvs.append(tuple(uvs))
        if both_sides:
            self.faces.append(tuple(reversed(indices)))
            self.uvs.append(tuple(reversed(uvs)))


def uv_in(box, s, t):
    return (box[0] + (box[2] - box[0]) * s, box[1] + (box[3] - box[1]) * t)


def cloth_point(u, t, folds=True):
    """u: -1 (character's right edge) .. 1 (left edge); t: 0 (top) .. 1 (hem)."""
    top = TOP_Z - TOP_DROP * u * u
    z = top + (HEM_Z - top) * t
    half = HALF_WIDTH_TOP + (HALF_WIDTH_HEM - HALF_WIDTH_TOP) * t ** 0.6   # flares quickly below the shoulders
    blade_t = (TOP_Z - BLADE_Z) / (TOP_Z - HEM_Z)
    if t < blade_t:
        y = NECK_Y + (BLADE_Y - NECK_Y) * smooth(0, 1, t / blade_t)
    else:
        y = BLADE_Y + (HEM_Y - BLADE_Y) * (t - blade_t) / (1 - blade_t)
    y -= WRAP * u * u * t   # none at the top, where the corners must stay clear of the shoulders
    depth = FOLD_DEPTH_TOP + (FOLD_DEPTH_HEM - FOLD_DEPTH_TOP) * t
    if folds:
        y += depth * math.cos(FOLDS * math.pi * u)
    # Folds gather the cloth, so the hem is a little narrower where they are deep.
    x = u * half * (1 - 0.06 * t)
    z += HEM_RAGGED * t * t * math.sin(u * 23.0) * math.cos(u * 7.0)
    return Vector((x, y, z))


def add_cloth(b, cols, rows):
    def upper_weight(z):
        return min(1.0, max(0.0, (z - BLEND_Z[0]) / (BLEND_Z[1] - BLEND_Z[0])))

    # Rows down the cloth. With few rows, one is always put at the shoulder blades, where the
    # cloth stands furthest off the back: evenly spaced, a 2- or 3-row LOD cut straight from the
    # neck to the waist, 4 cm inside the real cloth and through the vest pack under it.
    if rows >= 12:
        ts = [j / rows for j in range(rows + 1)]
    else:
        blade_t = (TOP_Z - BLADE_Z) / (TOP_Z - HEM_Z)
        ts = [0.0] + [blade_t + (1 - blade_t) * j / (rows - 1) for j in range(rows)]
    for side, shift in ((1, 0.0), (-1, -THICKNESS)):   # outer face, then the lining
        grid = []
        for forward, up in reversed(COLLAR):   # rolled collar above the top edge
            row = []
            for i in range(cols + 1):
                p = cloth_point(-1 + 2 * i / cols, 0, cols >= FOLDS_MIN_COLUMNS)
                p.y += shift - forward
                p.z += up
                row.append(b.vert(p, 1.0))
            grid.append(row)
        for j in range(rows + 1):
            row = []
            for i in range(cols + 1):
                p = cloth_point(-1 + 2 * i / cols, ts[j], cols >= FOLDS_MIN_COLUMNS)
                p.y += shift
                row.append(b.vert(p, upper_weight(p.z)))
            grid.append(row)
        total = rows + len(COLLAR)
        for j in range(total):
            for i in range(cols):
                quad = (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
                uvs = (uv_in(UV_CLOTH, i / cols, 1 - j / total), uv_in(UV_CLOTH, (i + 1) / cols, 1 - j / total),
                       uv_in(UV_CLOTH, (i + 1) / cols, 1 - (j + 1) / total), uv_in(UV_CLOTH, i / cols, 1 - (j + 1) / total))
                if side < 0:
                    quad, uvs = tuple(reversed(quad)), tuple(reversed(uvs))
                b.face(quad, uvs)


def cord_points(segments):
    """Catmull-Rom curve through CORD_PATH."""
    pts = [Vector(p) for p in CORD_PATH]
    pts = [pts[0]] + pts + [pts[-1]]
    spans = len(pts) - 3
    out = []
    for k in range(segments + 1):
        f = k / segments * spans
        i = min(int(f), spans - 1)
        t = f - i
        p0, p1, p2, p3 = pts[i:i + 4]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    return out


def add_cords(b, segments):
    centre = Vector((0.0, -0.01, 1.38))   # the cord lies flat against the body around this point
    for mirror in (1, -1):
        pts = cord_points(segments)
        edge = []
        for k, p in enumerate(pts):
            tangent = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]).normalized()
            across = tangent.cross((p - centre).normalized()).normalized() * CORD_HALF_WIDTH
            pair = []
            for sign in (1, -1):
                q = p + across * sign
                pair.append(b.vert((q.x * mirror, q.y, q.z), 1.0))
            edge.append(pair)
        for k in range(segments):
            quad = (edge[k][0], edge[k][1], edge[k + 1][1], edge[k + 1][0])
            uvs = (uv_in(UV_CORD, k / segments, 1), uv_in(UV_CORD, k / segments, 0),
                   uv_in(UV_CORD, (k + 1) / segments, 0), uv_in(UV_CORD, (k + 1) / segments, 1))
            b.face(quad, uvs, both_sides=True)


def add_clasp(b, sides):
    centre = Vector(CORD_PATH[-1]) + Vector((0, -0.006, 0))
    hub = b.vert(centre + Vector((0, -0.004, 0)), 1.0)
    ring = []
    for k in range(sides):
        a = 2 * math.pi * k / sides
        ring.append(b.vert(centre + Vector((math.cos(a), 0, math.sin(a))) * CLASP_RADIUS, 1.0))
    for k in range(sides):
        a0, a1 = 2 * math.pi * k / sides, 2 * math.pi * (k + 1) / sides
        uvs = (uv_in(UV_CLASP, 0.5, 0.5), uv_in(UV_CLASP, 0.5 + 0.5 * math.cos(a0), 0.5 + 0.5 * math.sin(a0)),
               uv_in(UV_CLASP, 0.5 + 0.5 * math.cos(a1), 0.5 + 0.5 * math.sin(a1)))
        b.face((hub, ring[k], ring[(k + 1) % sides]), uvs, both_sides=True)


def material():
    mat = bpy.data.materials.get("cape") or bpy.data.materials.new("cape")
    mat.a3ob_properties_material.texture_path = TEXTURE
    mat.a3ob_properties_material.material_path = RVMAT
    return mat


def to_object(b, name):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(b.verts, [], b.faces)
    layer = mesh.uv_layers.new(name="UVMap")
    k = 0
    for uvs in b.uvs:
        for uv in uvs:
            layer.data[k].uv = uv
            k += 1
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    mesh.materials.append(material())
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def mark_lod(obj, lod, resolution=1, properties=()):
    props = obj.a3ob_properties_object
    props.is_a3_lod = True
    props.lod = lod
    props.resolution = resolution
    for name, value in properties:
        item = props.properties.add()
        item.name, item.value = name, value


def export(path):
    # The exporter switches to object mode first, which needs an active object.
    bpy.context.view_layer.objects.active = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    bpy.ops.a3ob.export_p3d(filepath=path, relative_paths=True, apply_transforms=True,
                            apply_modifiers=True, lod_collisions='FAIL')
    print("EXPORTED", path, os.path.getsize(path))


# ---- textures ------------------------------------------------------------------------
bpy.ops.wm.read_homefile(use_empty=True)  # keeps the user's enabled add-ons
make_textures()

# ---- worn model (male; the female file is the same mesh) -------------------------------
bpy.ops.wm.read_homefile(use_empty=True)
for resolution, cols, rows, segments in LODS:
    b = Builder()
    add_cloth(b, cols, rows)
    if segments:
        add_cords(b, segments)
        add_clasp(b, 12 if resolution < 3 else 6)
    obj = to_object(b, "cape_worn_lod%d" % resolution)
    mark_lod(obj, LOD_VISUAL, resolution)
    upper = obj.vertex_groups.new(name=UPPER_BONE)
    lower = obj.vertex_groups.new(name=LOWER_BONE)
    for index, weight in enumerate(b.weights):
        if weight > 0:
            upper.add([index], weight, 'REPLACE')
        if weight < 1:
            lower.add([index], 1 - weight, 'REPLACE')
    if resolution == 1:
        first_person = obj.a3ob_properties_object.copies.add()
        first_person.lod = LOD_VIEW_PILOT
        first_person.resolution = 1
    print("LOD", obj.name, "triangles", sum(len(p.vertices) - 2 for p in obj.data.polygons))

# Character-attached models must not be re-centred by the engine.
geo = bpy.data.objects.new("cape_worn_geometry", bpy.data.meshes.new("cape_worn_geometry"))
bpy.context.scene.collection.objects.link(geo)
mark_lod(geo, LOD_GEOMETRY, 1, properties=(("autocenter", "0"),))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_dir, "cape_worn.blend"))
export(os.path.join(out_dir, "Cape_m.p3d"))
export(os.path.join(out_dir, "Cape_f.p3d"))

# ---- ground model: the cape folded into a bundle, tied with its cord ------------------
bpy.ops.wm.read_homefile(use_empty=True)


def slab(b, half_x, half_y, z0, z1, uv_box, arc=6):
    """A folded layer: flat top and bottom, rounded fold edges along both X ends."""
    radius = (z1 - z0) / 2
    profile = [(-half_x + radius, z0)]
    for k in range(arc + 1):          # +X end, bottom to top
        a = -math.pi / 2 + math.pi * k / arc
        profile.append((half_x - radius + radius * math.cos(a), z0 + radius + radius * math.sin(a)))
    for k in range(arc + 1):          # -X end, top to bottom
        a = math.pi / 2 + math.pi * k / arc
        profile.append((-half_x + radius + radius * math.cos(a), z0 + radius + radius * math.sin(a)))
    count = len(profile)
    rings = [[b.vert((x, y, z), 1.0) for x, z in profile] for y in (-half_y, half_y)]
    for k in range(count):
        n = (k + 1) % count
        s0, s1 = k / count, (k + 1) / count
        b.face((rings[0][k], rings[0][n], rings[1][n], rings[1][k]),
               (uv_in(uv_box, s0, 0.35), uv_in(uv_box, s1, 0.35), uv_in(uv_box, s1, 0.95), uv_in(uv_box, s0, 0.95)))
    for ring, flip in ((rings[0], False), (rings[1], True)):   # open ends: cap them
        cap = list(ring) if flip else list(reversed(ring))
        uvs = [uv_in(uv_box, 0.5 + 0.4 * (b.verts[i][0] / half_x), 0.4 + 0.3 * ((b.verts[i][2] - z0) / (z1 - z0))) for i in cap]
        for k in range(1, len(cap) - 1):   # P3D faces have at most four corners: fan of triangles
            b.face((cap[0], cap[k], cap[k + 1]), (uvs[0], uvs[k], uvs[k + 1]))


b = Builder()
slab(b, 0.17, 0.13, 0.0, 0.035, UV_CLOTH)
slab(b, 0.165, 0.125, 0.035, 0.065, UV_CLOTH)
slab(b, 0.155, 0.12, 0.065, 0.09, UV_CLOTH)
slab(b, 0.022, 0.135, -0.002, 0.094, UV_CORD, arc=3)   # the cord tied around the bundle
bundle = to_object(b, "cape_ground_lod1")
mark_lod(bundle, LOD_VISUAL, 1)

mn, mx = (-0.17, -0.135, 0.0), (0.17, 0.135, 0.094)
x0, y0, z0 = mn
x1, y1, z1 = mx
mesh = bpy.data.meshes.new("cape_ground_geometry")
mesh.from_pydata([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                  (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], [],
                 [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
mesh.update()
geo = bpy.data.objects.new("cape_ground_geometry", mesh)
bpy.context.scene.collection.objects.link(geo)
mark_lod(geo, LOD_GEOMETRY, 1, properties=(("autocenter", "0"),))
geo.vertex_groups.new(name="Component01").add(range(8), 1.0, 'REPLACE')
bm = bmesh.new()
bm.from_mesh(geo.data)
layer = bm.verts.layers.float.new("a3ob_mass")
for v in bm.verts:
    v[layer] = GROUND_MASS_KG / 8
bm.to_mesh(geo.data)
bm.free()
for lod in (LOD_VIEW_GEOMETRY, LOD_FIRE_GEOMETRY):
    copy = geo.a3ob_properties_object.copies.add()
    copy.lod = lod
    copy.resolution = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_dir, "cape_ground.blend"))
export(os.path.join(out_dir, "Cape_g.p3d"))
