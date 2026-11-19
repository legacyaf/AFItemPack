"""Build the AF Command Post: an enterable desert outpost building with a command room in
front and a large windowless panic room behind a vault door.

    blender -b --python tools/build_commandpost_p3d.py -- <repo root>

Everything is generated from the numbers below; there is no source model. Writes
AF_CommandPost.p3d into AFItemPack/Structures/CommandPost and saves the scene in tools/blend/.

The model carries: visual LODs 1-3, a shadow volume, geometry / view geometry / fire geometry
(one convex box or prism per wall piece), a roadway LOD (the floors and roof you can stand on)
and a memory LOD (door axes). Doors are the named selections doors1 (entrance) and doors2
(vault); model.cfg turns them and config.cpp makes them usable.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3d_common as p3d  # noqa: E402

# ---- layout (metres; Z up; the entrance faces -Y; the origin is the middle of the footprint
# at ground level) ----------------------------------------------------------------------
HALF_W = 4.0            # the building is 8 m wide (X) ...
HALF_L = 7.0            # ... and 14 m long (Y)
FLOOR = 0.12            # floor height above the ground
FOUNDATION = -1.2       # the foundation reaches this far down, so the building can sit on a slope
CEILING = 3.12          # underside of the roof slab
ROOF_TOP = 3.37
ROOF_OVERHANG = 0.15
PARAPET_TOP = 3.72
PARAPET_THICK = 0.30
WALL = 0.35             # command room walls
VAULT_WALL = 0.70       # panic room walls and the dividing wall
DIVIDE_Y = (-1.0, -0.3)  # the dividing wall: command room in front of it, panic room behind
DOOR_X = (-0.1, 1.0)    # entrance opening in the front wall
DOOR_TOP = FLOOR + 2.10
VAULT_X = (-0.65, 0.65)  # vault opening in the dividing wall
VAULT_TOP = FLOOR + 2.05
WINDOW_Z = (FLOOR + 1.50, FLOOR + 2.00)
FRONT_WINDOWS_X = ((-3.0, -2.1), (-1.7, -0.8))
SIDE_WINDOWS_Y = ((-5.6, -4.7), (-3.4, -2.5))
BATTER = (0.25, 1.0)    # sloped wall base: how far out at the ground, how high it reaches

# name: (texture, material, metres per texture repeat)
DATA = r"AFItemPack\Structures\CommandPost\data" + "\\"
MATERIALS = {
    "plaster": (r"dz\structures_takistan\data\plaster\plaster_mil_beige_co.paa", DATA + "af_plaster.rvmat", 3.0),
    "concrete": (r"dz\structures\data\concrete\concretecrude_co.paa", DATA + "af_concrete.rvmat", 3.0),
    "metal": (r"dz\structures\data\metal\metal_seam_rusty_co.paa", DATA + "af_metal.rvmat", 1.5),
    "vault": (r"dz\structures\data\metal\rotfurnace_metal_01_co.paa", DATA + "af_vault.rvmat", 2.0),
    # A flat sand colour: the game's own sandbag texture is a laid-out sheet, and repeated over
    # plain boxes it read as green crates.
    "sandbag": ("#(argb,8,8,3)color(0.60,0.52,0.37,1.0,CO)", DATA + "af_concrete.rvmat", 1.2),
    "paint": ("#(argb,8,8,3)color(0.07,0.07,0.06,1.0,CO)", "", 1.0),
}
# What a bullet meets in the fire geometry, per visual material.
PENETRATION = {"metal": r"dz\data\data\penetration\iron.rvmat", "vault": r"dz\data\data\penetration\armor_3mm_plate.rvmat"}
PENETRATION_DEFAULT = r"dz\data\data\penetration\concrete.rvmat"
ROADWAY_TEXTURE = r"dz\structures\data\concrete\concretecrude_co.paa"

repo = sys.argv[sys.argv.index("--") + 1]
out_dir = os.path.join(repo, "AFItemPack", "Structures", "CommandPost")
blend_dir = os.path.join(repo, "tools", "blend")
os.makedirs(out_dir, exist_ok=True)
os.makedirs(blend_dir, exist_ok=True)
p3d.require_addon()


class Piece:
    """One convex solid: 8 corners (or a prism), a material, and where it is used."""
    def __init__(self, verts, faces, material, detail, collide, selection):
        self.verts, self.faces, self.material = verts, faces, material
        self.detail, self.collide, self.selection = detail, collide, selection


pieces = []
walkable = []   # quads (four corners, counter-clockwise seen from above)


def box(mn, mx, material, detail=3, collide=True, selection=None):
    """detail: the box is drawn in visual LODs 1..detail (3 = always, 1 = close up only)."""
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    pieces.append(Piece(verts, faces, material, detail, collide, selection))


def prism(profile, axis, a0, a1, material, detail=3, collide=True, selection=None):
    """Extrude a convex profile along X or Y. profile: (u, z) points, counter-clockwise when
    looking along the extrusion axis from a0 toward a1 ... either winding is repaired later."""
    def at(u, z, a):
        return (a, u, z) if axis == "X" else (u, a, z)
    n = len(profile)
    verts = [at(u, z, a0) for u, z in profile] + [at(u, z, a1) for u, z in profile]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    pieces.append(Piece(verts, faces, material, detail, collide, selection))


def wall(axis, thick, span, z, material, openings=()):
    """A straight wall with rectangular openings. axis "X": the wall runs along X, thick is its
    (y0, y1); axis "Y": it runs along Y, thick is its (x0, x1). openings: (start, end, bottom, top)."""
    def piece(a0, a1, z0, z1):
        if a1 - a0 < 1e-6 or z1 - z0 < 1e-6:
            return
        if axis == "X":
            box((a0, thick[0], z0), (a1, thick[1], z1), material)
        else:
            box((thick[0], a0, z0), (thick[1], a1, z1), material)
    cursor = span[0]
    for start, end, bottom, top in sorted(openings):
        piece(cursor, start, z[0], z[1])
        piece(start, end, z[0], bottom)   # below the opening
        piece(start, end, top, z[1])      # above it
        cursor = end
    piece(cursor, span[1], z[0], z[1])


# ---- the building ----------------------------------------------------------------------
W, L = HALF_W, HALF_L
win = WINDOW_Z
# Foundation and floor.
box((-W, -L, FOUNDATION), (W, L, FLOOR), "concrete")
walkable.append(((-W, -L, FLOOR), (W, -L, FLOOR), (W, L, FLOOR), (-W, L, FLOOR)))
# Command room: front wall with the entrance and two slit windows, two side walls with two each.
wall("X", (-L, -L + WALL), (-W, W), (FLOOR, CEILING), "plaster",
     [(x0, x1, win[0], win[1]) for x0, x1 in FRONT_WINDOWS_X] + [(DOOR_X[0], DOOR_X[1], FLOOR, DOOR_TOP)])
side_windows = [(y0, y1, win[0], win[1]) for y0, y1 in SIDE_WINDOWS_Y]
wall("Y", (-W, -W + WALL), (-L + WALL, DIVIDE_Y[0]), (FLOOR, CEILING), "plaster", side_windows)
wall("Y", (W - WALL, W), (-L + WALL, DIVIDE_Y[0]), (FLOOR, CEILING), "plaster", side_windows)
# Panic room: thick windowless walls, and the dividing wall with the vault opening.
wall("Y", (-W, -W + VAULT_WALL), (DIVIDE_Y[0], L), (FLOOR, CEILING), "concrete")
wall("Y", (W - VAULT_WALL, W), (DIVIDE_Y[0], L), (FLOOR, CEILING), "concrete")
wall("X", (L - VAULT_WALL, L), (-W + VAULT_WALL, W - VAULT_WALL), (FLOOR, CEILING), "concrete")
wall("X", DIVIDE_Y, (-W + VAULT_WALL, W - VAULT_WALL), (FLOOR, CEILING), "concrete",
     [(VAULT_X[0], VAULT_X[1], FLOOR, VAULT_TOP)])
# Roof slab, parapet, sandbags.
R = ROOF_OVERHANG
box((-W - R, -L - R, CEILING), (W + R, L + R, ROOF_TOP), "concrete")
walkable.append(((-W - R, -L - R, ROOF_TOP), (W + R, -L - R, ROOF_TOP), (W + R, L + R, ROOF_TOP), (-W - R, L + R, ROOF_TOP)))
P = PARAPET_THICK
box((-W - R, -L - R, ROOF_TOP), (W + R, -L - R + P, PARAPET_TOP), "concrete")
box((-W - R, L + R - P, ROOF_TOP), (W + R, L + R, PARAPET_TOP), "concrete")
box((-W - R, -L - R + P, ROOF_TOP), (-W - R + P, L + R - P, PARAPET_TOP), "concrete")
box((W + R - P, -L - R + P, ROOF_TOP), (W + R, L + R - P, PARAPET_TOP), "concrete")


def sandbag_row(start, direction, count, base_z, layers=2):
    """Sandbags laid end to end on the parapet; close up each bag is its own box."""
    length, width, height = 0.62, 0.34, 0.17
    dx, dy = direction
    for layer in range(layers):
        for k in range(count - layer):
            along = (k + 0.5 * layer) * length
            cx, cy = start[0] + dx * along, start[1] + dy * along
            hx, hy = (length * 0.47, width / 2) if dx else (width / 2, length * 0.47)
            z0 = base_z + layer * height
            box((cx, cy, z0), (cx + 2 * hx, cy + 2 * hy, z0 + height), "sandbag", detail=1, collide=False)
    # One plain block stands in for the row further away and for collision.
    ex, ey = (count * length, width) if dx else (width, count * length)
    pieces.append(Piece(*_box_data((start[0], start[1], base_z), (start[0] + ex, start[1] + ey, base_z + layers * height)),
                        "sandbag", -2, True, None))


def _box_data(mn, mx):
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    return ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])


sandbag_row((-W - R, -L - R - 0.02, PARAPET_TOP), (1, 0), 5, PARAPET_TOP)
sandbag_row((W + R - 3.1, -L - R - 0.02, PARAPET_TOP), (1, 0), 5, PARAPET_TOP)
sandbag_row((-W - R - 0.02, -L - R + 0.4, PARAPET_TOP), (0, 1), 4, PARAPET_TOP)
sandbag_row((W + R - 0.32, 1.5, PARAPET_TOP), (0, 1), 6, PARAPET_TOP)
sandbag_row((-W - R, L + R - 0.32, PARAPET_TOP), (1, 0), 6, PARAPET_TOP)

# Sloped wall base, left open at the entrance.
b_out, b_top = BATTER
prism([(-L - b_out, 0.0), (-L, 0.0), (-L, b_top)], "X", -W - b_out, DOOR_X[0] - 0.25, "plaster")
prism([(-L - b_out, 0.0), (-L, 0.0), (-L, b_top)], "X", DOOR_X[1] + 0.25, W + b_out, "plaster")
prism([(L, 0.0), (L + b_out, 0.0), (L, b_top)], "X", -W - b_out, W + b_out, "concrete")
prism([(-W - b_out, 0.0), (-W, 0.0), (-W, b_top)], "Y", -L, DIVIDE_Y[0], "plaster")
prism([(W, 0.0), (W + b_out, 0.0), (W, b_top)], "Y", -L, DIVIDE_Y[0], "plaster")
prism([(-W - b_out, 0.0), (-W, 0.0), (-W, b_top)], "Y", DIVIDE_Y[0], L, "concrete")
prism([(W, 0.0), (W + b_out, 0.0), (W, b_top)], "Y", DIVIDE_Y[0], L, "concrete")
# Entrance step.
box((DOOR_X[0] - 0.25, -L - 0.7, FOUNDATION), (DOOR_X[1] + 0.25, -L, FLOOR), "concrete")
walkable.append(((DOOR_X[0] - 0.25, -L - 0.7, FLOOR), (DOOR_X[1] + 0.25, -L - 0.7, FLOOR), (DOOR_X[1] + 0.25, -L, FLOOR), (DOOR_X[0] - 0.25, -L, FLOOR)))

# Corrugated awning over the entrance.
prism([(-L - 1.0, 2.38), (-L - 1.0, 2.35), (-L, 2.62), (-L, 2.65)], "X", DOOR_X[0] - 0.4, DOOR_X[1] + 0.4, "metal", detail=3, collide=False)
for x in (DOOR_X[0] - 0.35, DOOR_X[1] + 0.31):
    prism([(-L - 0.9, 2.36), (-L, 2.05), (-L, 2.10), (-L - 0.86, 2.40)], "X", x, x + 0.04, "metal", detail=1, collide=False)
# Window shutters, swung open against the wall, and steel frames in the window reveals.
for x0, x1 in FRONT_WINDOWS_X:
    box((x0 - 0.47, -L - 0.03, win[0] - 0.03), (x0 - 0.02, -L, win[1] + 0.03), "metal", detail=2, collide=False)
    box((x1 + 0.02, -L - 0.03, win[0] - 0.03), (x1 + 0.47, -L, win[1] + 0.03), "metal", detail=2, collide=False)
for side in (-1, 1):
    for y0, y1 in SIDE_WINDOWS_Y:
        xa, xb = (-W - 0.03, -W) if side < 0 else (W, W + 0.03)
        box((xa, y0 - 0.47, win[0] - 0.03), (xb, y0 - 0.02, win[1] + 0.03), "metal", detail=2, collide=False)
        box((xa, y1 + 0.02, win[0] - 0.03), (xb, y1 + 0.47, win[1] + 0.03), "metal", detail=2, collide=False)
# Steel plates on the panic room's outside corners and wall middles.
for y in (DIVIDE_Y[0] + 0.1, 3.0, L - 0.7):
    for xa, xb in ((-W - 0.025, -W), (W, W + 0.025)):
        box((xa, y, b_top + 0.05), (xb, y + 0.6, CEILING - 0.05), "metal", detail=2, collide=False)
for x in (-W + 0.1, -0.3, W - 0.7):
    box((x, L, b_top + 0.05), (x + 0.6, L + 0.025, CEILING - 0.05), "metal", detail=2, collide=False)
# Steel lining of the vault opening.
vy0, vy1 = DIVIDE_Y
box((VAULT_X[0] - 0.05, vy0 - 0.02, FLOOR), (VAULT_X[0], vy1 + 0.02, VAULT_TOP + 0.05), "vault", detail=2, collide=False)
box((VAULT_X[1], vy0 - 0.02, FLOOR), (VAULT_X[1] + 0.05, vy1 + 0.02, VAULT_TOP + 0.05), "vault", detail=2, collide=False)
box((VAULT_X[0], vy0 - 0.02, VAULT_TOP), (VAULT_X[1], vy1 + 0.02, VAULT_TOP + 0.05), "vault", detail=2, collide=False)
# Antenna mast and the (for now decorative) ladder up the back wall.
box((-2.6, 4.0, ROOF_TOP), (-2.3, 4.3, ROOF_TOP + 0.25), "concrete", detail=2, collide=False)
box((-2.49, 4.11, ROOF_TOP + 0.25), (-2.41, 4.19, ROOF_TOP + 5.5), "metal", detail=3, collide=False)
for x in (2.30, 2.76):
    box((x, L + b_out, 0.0), (x + 0.04, L + b_out + 0.04, PARAPET_TOP + 0.9), "metal", detail=2, collide=False)
for k in range(13):
    z = 0.3 + k * 0.3
    box((2.34, L + b_out + 0.005, z), (2.76, L + b_out + 0.035, z + 0.03), "metal", detail=1, collide=False)

# "AF" stencilled on the front wall, as thin dark slabs just off the plaster.
ay = (-L - 0.012, -L - 0.002)


def stroke(points):
    """A flat stroke in the wall plane from (x, z) corner points."""
    verts = [(x, ay[0], z) for x, z in points] + [(x, ay[1], z) for x, z in points]
    n = len(points)
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    pieces.append(Piece(verts, faces, "paint", 2, False, None))


az0, az1, t = 1.25, 2.20, 0.16
stroke([(1.55, az0), (1.55 + t, az0), (2.00 + t / 2, az1), (2.00 - t / 2, az1)])          # A, left leg
stroke([(2.45 - t, az0), (2.45, az0), (2.00 + t / 2, az1), (2.00 - t / 2, az1)])          # A, right leg
stroke([(1.78, 1.55), (2.22, 1.55), (2.22, 1.55 + t * 0.8), (1.78, 1.55 + t * 0.8)])      # A, bar
stroke([(2.75, az0), (2.75 + t, az0), (2.75 + t, az1), (2.75, az1)])                      # F, stem
stroke([(2.75 + t, az1 - t), (3.45, az1 - t), (3.45, az1), (2.75 + t, az1)])              # F, top bar
stroke([(2.75 + t, 1.68), (3.25, 1.68), (3.25, 1.68 + t * 0.8), (2.75 + t, 1.68 + t * 0.8)])  # F, middle bar

# Doors. The entrance door hangs in the opening; the vault door is a thick slab that seats
# against the command-room face of the dividing wall, with a spoked wheel.
DOOR1_HINGE = (DOOR_X[0], -L + 0.06)
box((DOOR_X[0], -L + 0.03, FLOOR), (DOOR_X[1], -L + 0.09, DOOR_TOP), "metal", selection="doors1")
box((DOOR_X[1] - 0.16, -L - 0.02, FLOOR + 1.0), (DOOR_X[1] - 0.06, -L + 0.14, FLOOR + 1.06), "vault", detail=2, collide=False, selection="doors1")
VAULT_SLAB_X = (VAULT_X[0] - 0.12, VAULT_X[1] + 0.12)
VAULT_SLAB_Y = (DIVIDE_Y[0] - 0.18, DIVIDE_Y[0])
DOOR2_HINGE = (VAULT_SLAB_X[0], VAULT_SLAB_Y[0] + 0.02)
box((VAULT_SLAB_X[0], VAULT_SLAB_Y[0], FLOOR + 0.02), (VAULT_SLAB_X[1], VAULT_SLAB_Y[1], VAULT_TOP + 0.12), "vault", selection="doors2")
wheel_c = ((VAULT_X[0] + VAULT_X[1]) / 2, FLOOR + 1.15)
wheel = [(wheel_c[0] + 0.30 * math.cos(math.radians(a)), wheel_c[1] + 0.30 * math.sin(math.radians(a))) for a in range(0, 360, 45)]
wy = (VAULT_SLAB_Y[0] - 0.07, VAULT_SLAB_Y[0] - 0.03)
verts = [(x, wy[0], z) for x, z in wheel] + [(x, wy[1], z) for x, z in wheel]
faces = [tuple(range(7, -1, -1)), tuple(range(8, 16))] + [(k, (k + 1) % 8, 8 + (k + 1) % 8, 8 + k) for k in range(8)]
pieces.append(Piece(verts, faces, "metal", 2, False, "doors2"))
box((wheel_c[0] - 0.04, VAULT_SLAB_Y[0] - 0.03, wheel_c[1] - 0.04), (wheel_c[0] + 0.04, VAULT_SLAB_Y[0], wheel_c[1] + 0.04), "metal", detail=2, collide=False, selection="doors2")
for z in (FLOOR + 0.35, FLOOR + 1.85):   # hinge blocks
    box((VAULT_SLAB_X[0] - 0.08, VAULT_SLAB_Y[0], z), (VAULT_SLAB_X[0], VAULT_SLAB_Y[1], z + 0.22), "metal", detail=2, collide=False)


# ---- meshes ------------------------------------------------------------------------------
def outward(piece):
    """Faces of a convex piece with their normals pointing away from its middle."""
    centre = sum((Vector(v) for v in piece.verts), Vector()) / len(piece.verts)
    out = []
    for face in piece.faces:
        pts = [Vector(piece.verts[i]) for i in face]
        normal = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        mid = sum(pts, Vector()) / len(pts)
        out.append(face if normal.dot(mid - centre) >= 0 else tuple(reversed(face)))
    return out


def blender_material(name):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    return mat


def build(name, chosen, textured=True, fire=False, components=False):
    """One mesh object from pieces. components: name each piece ComponentNN (collision LODs)."""
    verts, faces, uvs, mats, groups = [], [], [], [], {}
    slots = []
    for number, piece in enumerate(chosen, 1):
        base = len(verts)
        verts.extend(piece.verts)
        indices = list(range(base, base + len(piece.verts)))
        if components:
            groups.setdefault("Component%02d" % number, []).extend(indices)
        if piece.selection:
            groups.setdefault(piece.selection, []).extend(indices)
        key = piece.material if textured else ("fire_" + piece.material if fire else "plain")
        if key not in slots:
            slots.append(key)
        tile = MATERIALS[piece.material][2]
        for face in outward(piece):
            pts = [Vector(piece.verts[i]) for i in face]
            normal = (pts[1] - pts[0]).cross(pts[2] - pts[0]).normalized()
            if abs(normal.z) > 0.7:
                face_uv = [(p.x / tile, p.y / tile) for p in pts]
            elif abs(normal.x) > abs(normal.y):
                face_uv = [(p.y / tile, p.z / tile) for p in pts]
            else:
                face_uv = [(p.x / tile, p.z / tile) for p in pts]
            # P3D faces have at most four corners: larger ones (the vault wheel) become fans.
            corners = list(range(len(face)))
            parts = [corners] if len(face) <= 4 else [[0, k, k + 1] for k in range(1, len(face) - 1)]
            for part in parts:
                faces.append(tuple(base + face[c] for c in part))
                uvs.append([face_uv[c] for c in part])
                mats.append(slots.index(key))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    layer = mesh.uv_layers.new(name="UVMap")
    k = 0
    for face_uv in uvs:
        for uv in face_uv:
            layer.data[k].uv = uv
            k += 1
    for key in slots:
        mat = blender_material("af_cp_" + key)
        props = mat.a3ob_properties_material
        if textured:
            props.texture_path, props.material_path = MATERIALS[key][0], MATERIALS[key][1]
        elif fire:
            props.material_path = PENETRATION.get(key[5:], PENETRATION_DEFAULT)
        mesh.materials.append(mat)
    for polygon, slot in zip(mesh.polygons, mats):
        polygon.material_index = slot
        polygon.use_smooth = False
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for group, indices in groups.items():
        obj.vertex_groups.new(name=group).add(indices, 1.0, 'REPLACE')
    return obj


def add_mass(obj, per_vertex):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    layer = bm.verts.layers.float.new("a3ob_mass")
    for v in bm.verts:
        v[layer] = per_vertex
    bm.to_mesh(obj.data)
    bm.free()


p3d.new_scene()
# Visual LODs: detail d is drawn in LODs 1..d; detail -2 marks a stand-in used from LOD 2 on.
for lod in (1, 2, 3):
    chosen = [p for p in pieces if (p.detail >= lod) or (p.detail == -2 and lod >= 2)]
    obj = build("commandpost_lod%d" % lod, chosen)
    p3d.mark_lod(obj, p3d.LOD_VISUAL, lod)
    print("LOD", obj.name, "triangles", sum(len(p.vertices) - 2 for p in obj.data.polygons))

solid = [p for p in pieces if p.collide]
geometry = build("commandpost_geometry", solid, textured=False, components=True)
# autocenter 0 keeps the model's origin where it is here: the middle of the footprint at ground
# level. Without it the engine moved the origin to the middle of the bounding box, 3.8 m up
# (the mast counts), and the building placed at ground level sat buried to its roof.
p3d.mark_lod(geometry, p3d.LOD_GEOMETRY, 1, properties=(("class", "house"), ("map", "house"), ("autocenter", "0")))
add_mass(geometry, 150.0)
p3d.add_copy(geometry, p3d.LOD_VIEW_GEOMETRY)
fire = build("commandpost_fire", solid, textured=False, fire=True, components=True)
p3d.mark_lod(fire, p3d.LOD_FIRE_GEOMETRY, 1)

# Roadway: the surfaces a character can stand on.
road = bpy.data.meshes.new("commandpost_roadway")
road_verts = [v for quad in walkable for v in quad]
road.from_pydata(road_verts, [], [tuple(range(4 * k, 4 * k + 4)) for k in range(len(walkable))])
road_uv = road.uv_layers.new(name="UVMap")
for k, v in enumerate(road_verts):
    road_uv.data[k].uv = (v[0] / 3.0, v[1] / 3.0)
road_mat = blender_material("af_cp_roadway")
road_mat.a3ob_properties_material.texture_path = ROADWAY_TEXTURE
road.materials.append(road_mat)
road.update()
road_obj = bpy.data.objects.new("commandpost_roadway", road)
bpy.context.scene.collection.objects.link(road_obj)
p3d.mark_lod(road_obj, "11", 1)

# Shadow volume: closed, triangulated, sharp-edged hulls of the main masses.
shadow_pieces = [Piece(*_box_data((-W, -L, 0.0), (W, L, CEILING)), "concrete", 3, False, None),
                 Piece(*_box_data((-W - R, -L - R, CEILING), (W + R, L + R, PARAPET_TOP)), "concrete", 3, False, None)]
shadow = build("commandpost_shadow", shadow_pieces, textured=False)
bm = bmesh.new()
bm.from_mesh(shadow.data)
bmesh.ops.triangulate(bm, faces=bm.faces)
for edge in bm.edges:
    edge.smooth = False
bm.to_mesh(shadow.data)
bm.free()
p3d.mark_lod(shadow, "4", 0)

# Memory points: two per door axis (bottom, top) and one where its sound plays.
memory_points = {
    "doors1_axis": [(DOOR1_HINGE[0], DOOR1_HINGE[1], FLOOR), (DOOR1_HINGE[0], DOOR1_HINGE[1], DOOR_TOP)],
    "doors1_action": [((DOOR_X[0] + DOOR_X[1]) / 2, -L + 0.06, FLOOR + 1.0)],
    "doors2_axis": [(DOOR2_HINGE[0], DOOR2_HINGE[1], FLOOR), (DOOR2_HINGE[0], DOOR2_HINGE[1], VAULT_TOP)],
    "doors2_action": [(wheel_c[0], VAULT_SLAB_Y[0], wheel_c[1])],
}
mem_verts = [v for pts in memory_points.values() for v in pts]
memory = p3d.new_mesh_object("commandpost_memory", mem_verts, [])
index = 0
for group, pts in memory_points.items():
    memory.vertex_groups.new(name=group).add(list(range(index, index + len(pts))), 1.0, 'REPLACE')
    index += len(pts)
p3d.mark_lod(memory, "9", 1)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_dir, "commandpost.blend"))
p3d.export(os.path.join(out_dir, "AF_CommandPost.p3d"))
