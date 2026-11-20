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
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

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
# Roof ladder on the back wall. Measured on the game's own ladder buildings (ATC tower, fortified
# watchtower): the ladder is one vertical line; ladderN_bottom_front and ladderN_top_front are
# its ends; ladderN_dir is 0.32 m from the bottom on the climber's side; ladderN_con holds the
# points where it can be entered (bottom and top) and ladderN_con_dir the matching direction
# points; the view geometry has a thin box 0.48 m wide named ladderN that the player aims at.
LADDER_X = 2.55
LADDER_Y = HALF_L + BATTER[0] + 0.02
LADDER_GAP_X = (2.05, 3.05)   # opening in the back parapet where the ladder arrives
# Code lock keypad on the dividing wall beside the vault door (command-room face).
LOCK_X = 1.15
LOCK_Z = FLOOR + 1.35
LOCK_SLOT = "Att_CodeLock1_Metal"
# The mount is a placeholder model of our own with its own Proxy... class in config.cpp, as on
# the hauler. Pointing the mount at the game's lock model (\dz\gear_takistan\camping\codelock.p3d,
# as the vanilla houses do) left the attached lock undrawn: the build tools cannot see the
# game's proxy class on this PC, so the mount was not registered as an attachment point.
LOCK_PROXY = r"\AFItemPack\Structures\CommandPost\proxy\AF_proxy_codelock.p3d"
LOCK_TURN = Matrix.Identity(4)   # orientation of the keypad; set after looking at it in game
LOCK_STANDOFF = 0.03   # how far the mount is in front of the wall face

# name: (texture, material, metres per texture repeat[, True if the texture is one wall high])
# All textures are the game's own Nasdara structure textures, referenced by path.
DATA = r"AFItemPack\Structures\CommandPost\data" + "\\"
TEX = r"dz\structures_takistan\data" + "\\"
MATERIALS = {
    "wall": (TEX + r"brick\wallbrickplastered_co.paa", DATA + "af_wall.rvmat", 2.4),            # command room, outside
    "bunker": (TEX + r"concrete\concretebroken_paint_sandy_co.paa", DATA + "af_bunker.rvmat", 3.0),  # panic room, outside
    "interior": (TEX + r"plaster\walls_interior02_co.paa", DATA + "af_interior.rvmat", 1.5, True),   # command room, inside
    "cinder": (TEX + r"concrete\cinderblock_wall_01_co.paa", DATA + "af_cinder.rvmat", 2.5),     # panic room, inside
    "floor": (TEX + r"concrete\concrete_panel_floor_01_co.paa", DATA + "af_floor.rvmat", 3.0),
    "concrete": (TEX + r"concrete\concrete_bare01_co.paa", DATA + "af_concrete.rvmat", 2.5),     # ceilings, lintels, sills
    "roof": (TEX + r"roof\roof_bitumen_old_co.paa", DATA + "af_roof.rvmat", 3.0),
    "sheet": (TEX + r"metal\metal_plate_ind_rusty_02_co.paa", DATA + "af_sheet.rvmat", 1.2),     # shutters, awning, roof boxes
    "metal": (TEX + r"metal\metal_steel_01_co.paa", DATA + "af_metal.rvmat", 2.0),               # entrance door, ladder, plates
    "vault": (TEX + r"metal\steel_greasy_co.paa", DATA + "af_vault.rvmat", 2.0),                 # vault door
    "trim": (TEX + r"metal\scratched_industrial_metal_co.paa", DATA + "af_trim.rvmat", 1.5),     # vault fittings, frames
    # A flat sand colour: the sandy concrete texture made the bags read as stone slabs, and the
    # game's own sandbag texture is a laid-out sheet that repeats as green crates.
    "sandbag": ("#(argb,8,8,3)color(0.60,0.52,0.37,1.0,CO)", DATA + "af_sandbag.rvmat", 0.9),
    "paint": ("#(argb,8,8,3)color(0.07,0.07,0.06,1.0,CO)", "", 1.0),
}
# What a bullet meets in the fire geometry, per visual material.
IRON = r"dz\data\data\penetration\iron.rvmat"
PENETRATION = {"metal": IRON, "sheet": IRON, "trim": IRON, "vault": r"dz\data\data\penetration\armor_3mm_plate.rvmat"}
PENETRATION_DEFAULT = r"dz\data\data\penetration\concrete.rvmat"
ROADWAY_TEXTURE = MATERIALS["floor"][0]

repo = sys.argv[sys.argv.index("--") + 1]
out_dir = os.path.join(repo, "AFItemPack", "Structures", "CommandPost")
blend_dir = os.path.join(repo, "tools", "blend")
os.makedirs(out_dir, exist_ok=True)
os.makedirs(blend_dir, exist_ok=True)
p3d.require_addon()
rng = random.Random(11)   # fixed seed: the same building every build


class Piece:
    """One convex solid: 8 corners (or a prism), a material, and where it is used.
    face_materials overrides the material for faces pointing along an axis ("+x", "-z", ...);
    uv gives a decal its own texture coordinates per corner."""
    def __init__(self, verts, faces, material, detail, collide, selection, face_materials=None, uv=None):
        self.verts, self.faces, self.material = verts, faces, material
        self.detail, self.collide, self.selection = detail, collide, selection
        self.face_materials, self.uv = face_materials or {}, uv


pieces = []
walkable = []   # quads (four corners, counter-clockwise seen from above)


def _box_data(mn, mx):
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    return ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])


def box(mn, mx, material, detail=3, collide=True, selection=None, faces=None):
    """detail: the box is drawn in visual LODs 1..detail (3 = always, 1 = close up only).
    faces: other materials for single sides, e.g. {"+y": "interior"}."""
    pieces.append(Piece(*_box_data(mn, mx), material, detail, collide, selection, faces))


def prism(profile, axis, a0, a1, material, detail=3, collide=True, selection=None):
    """Extrude a convex profile along X or Y. profile: (u, z) points in order around it."""
    def at(u, z, a):
        return (a, u, z) if axis == "X" else (u, a, z)
    n = len(profile)
    verts = [at(u, z, a0) for u, z in profile] + [at(u, z, a1) for u, z in profile]
    faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
    faces += [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
    pieces.append(Piece(verts, faces, material, detail, collide, selection))


def beam(p0, p1, width, material, detail=2, selection=None, height=None):
    """A straight bar of rectangular section between two points (wires, spokes, braces)."""
    a, b = Vector(p0), Vector(p1)
    along = (b - a).normalized()
    side = along.cross(Vector((0, 0, 1)))
    if side.length < 1e-4:
        side = along.cross(Vector((0, 1, 0)))
    side.normalize()
    up = side.cross(along).normalized()
    s, u = side * (width / 2), up * ((height or width) / 2)
    verts = [tuple(p + ds + du) for p in (a, b) for ds, du in ((-s, -u), (s, -u), (s, u), (-s, u))]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    pieces.append(Piece(verts, faces, material, detail, False, selection))


def wall(axis, thick, span, z, material, openings=(), faces=None):
    """A straight wall with rectangular openings. axis "X": the wall runs along X, thick is its
    (y0, y1); axis "Y": it runs along Y, thick is its (x0, x1). openings: (start, end, bottom, top)."""
    def piece(a0, a1, z0, z1):
        if a1 - a0 < 1e-6 or z1 - z0 < 1e-6:
            return
        if axis == "X":
            box((a0, thick[0], z0), (a1, thick[1], z1), material, faces=faces)
        else:
            box((thick[0], a0, z0), (thick[1], a1, z1), material, faces=faces)
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
b_out, b_top = BATTER
R = ROOF_OVERHANG
P = PARAPET_THICK
# Foundation and floor.
box((-W, -L, FOUNDATION), (W, L, FLOOR), "bunker", faces={"+z": "floor"})
walkable.append(((-W, -L, FLOOR), (W, -L, FLOOR), (W, L, FLOOR), (-W, L, FLOOR)))
# Command room: front wall with the entrance and two slit windows, two side walls with two each.
wall("X", (-L, -L + WALL), (-W, W), (FLOOR, CEILING), "wall",
     [(x0, x1, win[0], win[1]) for x0, x1 in FRONT_WINDOWS_X] + [(DOOR_X[0], DOOR_X[1], FLOOR, DOOR_TOP)],
     faces={"+y": "interior"})
side_windows = [(y0, y1, win[0], win[1]) for y0, y1 in SIDE_WINDOWS_Y]
wall("Y", (-W, -W + WALL), (-L + WALL, DIVIDE_Y[0]), (FLOOR, CEILING), "wall", side_windows, faces={"+x": "interior"})
wall("Y", (W - WALL, W), (-L + WALL, DIVIDE_Y[0]), (FLOOR, CEILING), "wall", side_windows, faces={"-x": "interior"})
# Panic room: thick windowless walls, and the dividing wall with the vault opening.
wall("Y", (-W, -W + VAULT_WALL), (DIVIDE_Y[0], L), (FLOOR, CEILING), "bunker", faces={"+x": "cinder"})
wall("Y", (W - VAULT_WALL, W), (DIVIDE_Y[0], L), (FLOOR, CEILING), "bunker", faces={"-x": "cinder"})
wall("X", (L - VAULT_WALL, L), (-W + VAULT_WALL, W - VAULT_WALL), (FLOOR, CEILING), "bunker", faces={"-y": "cinder"})
wall("X", DIVIDE_Y, (-W + VAULT_WALL, W - VAULT_WALL), (FLOOR, CEILING), "bunker",
     [(VAULT_X[0], VAULT_X[1], FLOOR, VAULT_TOP)], faces={"+y": "cinder"})
# Roof slab and parapet.
box((-W - R, -L - R, CEILING), (W + R, L + R, ROOF_TOP), "concrete", faces={"+z": "roof"})
walkable.append(((-W - R, -L - R, ROOF_TOP), (W + R, -L - R, ROOF_TOP), (W + R, L + R, ROOF_TOP), (-W - R, L + R, ROOF_TOP)))
box((-W - R, -L - R, ROOF_TOP), (W + R, -L - R + P, PARAPET_TOP), "bunker")
box((-W - R, L + R - P, ROOF_TOP), (LADDER_GAP_X[0], L + R, PARAPET_TOP), "bunker")   # back, with an
box((LADDER_GAP_X[1], L + R - P, ROOF_TOP), (W + R, L + R, PARAPET_TOP), "bunker")    # opening for the ladder
box((-W - R, -L - R + P, ROOF_TOP), (-W - R + P, L + R - P, PARAPET_TOP), "bunker")
box((W + R - P, -L - R + P, ROOF_TOP), (W + R, L + R - P, PARAPET_TOP), "bunker")


def sandbag_row(start, direction, count, base_z, layers=2):
    """Sandbags laid end to end on the parapet. Close up each bag is its own six-sided sack,
    a little uneven; further away (and for collision) one plain block stands in for the row."""
    length, width, height, c = 0.62, 0.36, 0.17, 0.07
    dx, dy = direction
    for layer in range(layers):
        for k in range(count - layer):
            along = (k + 0.5 * layer) * length + rng.uniform(-0.02, 0.02)
            shift = rng.uniform(-0.025, 0.025)
            z0 = base_z + layer * height
            z1 = z0 + height + rng.uniform(-0.01, 0.015)
            a0 = (start[0] if dx else start[1]) + along + 0.015
            u0 = (start[1] if dx else start[0]) + shift
            profile = [(u0 + c, z0), (u0 + width - c, z0), (u0 + width, (z0 + z1) / 2),
                       (u0 + width - c, z1), (u0 + c, z1), (u0, (z0 + z1) / 2)]
            prism(profile, "X" if dx else "Y", a0, a0 + length - 0.03, "sandbag", detail=1, collide=False)
    ex, ey = (count * length, width) if dx else (width, count * length)
    pieces.append(Piece(*_box_data((start[0], start[1], base_z), (start[0] + ex, start[1] + ey, base_z + layers * height)),
                        "sandbag", -2, True, None))


sandbag_row((-W - R, -L - R - 0.03, PARAPET_TOP), (1, 0), 5, PARAPET_TOP)
sandbag_row((W + R - 3.1, -L - R - 0.03, PARAPET_TOP), (1, 0), 5, PARAPET_TOP, layers=3)
sandbag_row((-W - R - 0.03, -L - R + 0.4, PARAPET_TOP), (0, 1), 4, PARAPET_TOP)
sandbag_row((W + R - 0.33, 1.5, PARAPET_TOP), (0, 1), 6, PARAPET_TOP)
sandbag_row((-W - R, L + R - 0.33, PARAPET_TOP), (1, 0), 6, PARAPET_TOP)

# Sloped wall base, left open at the entrance.
prism([(-L - b_out, 0.0), (-L, 0.0), (-L, b_top)], "X", -W - b_out, DOOR_X[0] - 0.25, "wall")
prism([(-L - b_out, 0.0), (-L, 0.0), (-L, b_top)], "X", DOOR_X[1] + 0.25, W + b_out, "wall")
prism([(L, 0.0), (L + b_out, 0.0), (L, b_top)], "X", -W - b_out, W + b_out, "bunker")
prism([(-W - b_out, 0.0), (-W, 0.0), (-W, b_top)], "Y", -L, DIVIDE_Y[0], "wall")
prism([(W, 0.0), (W + b_out, 0.0), (W, b_top)], "Y", -L, DIVIDE_Y[0], "wall")
prism([(-W - b_out, 0.0), (-W, 0.0), (-W, b_top)], "Y", DIVIDE_Y[0], L, "bunker")
prism([(W, 0.0), (W + b_out, 0.0), (W, b_top)], "Y", DIVIDE_Y[0], L, "bunker")
# Entrance step.
box((DOOR_X[0] - 0.25, -L - 0.7, FOUNDATION), (DOOR_X[1] + 0.25, -L, FLOOR), "bunker", faces={"+z": "floor"})
walkable.append(((DOOR_X[0] - 0.25, -L - 0.7, FLOOR), (DOOR_X[1] + 0.25, -L - 0.7, FLOOR), (DOOR_X[1] + 0.25, -L, FLOOR), (DOOR_X[0] - 0.25, -L, FLOOR)))

# Entrance: steel frame, concrete lintel, corrugated awning on braces, a caged lamp and its conduit.
for x0, x1 in ((DOOR_X[0] - 0.07, DOOR_X[0]), (DOOR_X[1], DOOR_X[1] + 0.07)):
    box((x0, -L - 0.03, FLOOR), (x1, -L + 0.12, DOOR_TOP + 0.07), "trim", detail=2, collide=False)
box((DOOR_X[0], -L - 0.03, DOOR_TOP), (DOOR_X[1], -L + 0.12, DOOR_TOP + 0.07), "trim", detail=2, collide=False)
box((DOOR_X[0] - 0.3, -L - 0.05, DOOR_TOP + 0.07), (DOOR_X[1] + 0.3, -L, DOOR_TOP + 0.27), "concrete", detail=2, collide=False)
prism([(-L - 1.0, 2.50), (-L - 1.0, 2.47), (-L, 2.74), (-L, 2.77)], "X", DOOR_X[0] - 0.4, DOOR_X[1] + 0.4, "sheet", detail=3, collide=False)
for x in (DOOR_X[0] - 0.33, DOOR_X[1] + 0.33):
    beam((x, -L - 0.92, 2.49), (x, -L - 0.02, 2.15), 0.035, "metal", detail=1)
    beam((x, -L - 0.98, 2.47), (x, -L - 0.02, 2.73), 0.035, "metal", detail=1)
lamp_x = DOOR_X[1] + 0.55
box((lamp_x - 0.07, -L - 0.16, 2.30), (lamp_x + 0.07, -L, 2.36), "trim", detail=1, collide=False)
box((lamp_x - 0.06, -L - 0.15, 2.14), (lamp_x + 0.06, -L - 0.03, 2.30), "paint", detail=1, collide=False)
box((lamp_x - 0.015, -L - 0.03, 2.36), (lamp_x + 0.015, -L, CEILING), "trim", detail=1, collide=False)
# Windows: steel shutters swung open against the wall, bars in the opening, a sill under it.
for x0, x1 in FRONT_WINDOWS_X:
    box((x0 - 0.47, -L - 0.03, win[0] - 0.03), (x0 - 0.02, -L, win[1] + 0.03), "sheet", detail=2, collide=False)
    box((x1 + 0.02, -L - 0.03, win[0] - 0.03), (x1 + 0.47, -L, win[1] + 0.03), "sheet", detail=2, collide=False)
    box((x0 - 0.06, -L - 0.06, win[0] - 0.07), (x1 + 0.06, -L, win[0]), "concrete", detail=2, collide=False)
    for k in range(1, 4):
        x = x0 + (x1 - x0) * k / 4
        box((x - 0.01, -L + 0.16, win[0]), (x + 0.01, -L + 0.18, win[1]), "trim", detail=1, collide=False)
for side in (-1, 1):
    for y0, y1 in SIDE_WINDOWS_Y:
        xa, xb = (-W - 0.03, -W) if side < 0 else (W, W + 0.03)
        box((xa, y0 - 0.47, win[0] - 0.03), (xb, y0 - 0.02, win[1] + 0.03), "sheet", detail=2, collide=False)
        box((xa, y1 + 0.02, win[0] - 0.03), (xb, y1 + 0.47, win[1] + 0.03), "sheet", detail=2, collide=False)
        sa, sb = (-W - 0.06, -W) if side < 0 else (W, W + 0.06)
        box((sa, y0 - 0.06, win[0] - 0.07), (sb, y1 + 0.06, win[0]), "concrete", detail=2, collide=False)
        bx = side * (W - 0.17)
        for k in range(1, 4):
            y = y0 + (y1 - y0) * k / 4
            box((bx - 0.01, y - 0.01, win[0]), (bx + 0.01, y + 0.01, win[1]), "trim", detail=1, collide=False)
# Steel plates on the panic room's outside corners and wall middles, with bolt heads.
for y in (DIVIDE_Y[0] + 0.1, 3.0, L - 0.7):
    for xa, xb in ((-W - 0.025, -W), (W, W + 0.025)):
        box((xa, y, b_top + 0.05), (xb, y + 0.6, CEILING - 0.05), "metal", detail=2, collide=False)
        for z in (b_top + 0.25, 1.75, CEILING - 0.25):
            for by in (y + 0.08, y + 0.47):
                bolt_x = (xa - 0.012, xa) if xa < 0 else (xb, xb + 0.012)
                box((bolt_x[0], by, z), (bolt_x[1], by + 0.05, z + 0.05), "trim", detail=1, collide=False)
for x in (-W + 0.1, -0.3, W - 0.7):
    box((x, L, b_top + 0.05), (x + 0.6, L + 0.025, CEILING - 0.05), "metal", detail=2, collide=False)
    for z in (b_top + 0.25, 1.75, CEILING - 0.25):
        for bx in (x + 0.08, x + 0.47):
            box((bx, L + 0.025, z), (bx + 0.05, L + 0.037, z + 0.05), "trim", detail=1, collide=False)
# Roof: antenna mast with guy wires, a vent, a cooling unit and a cable run.
mast = (-2.45, 4.15)
box((mast[0] - 0.15, mast[1] - 0.15, ROOF_TOP), (mast[0] + 0.15, mast[1] + 0.15, ROOF_TOP + 0.25), "concrete", detail=2, collide=False)
box((mast[0] - 0.04, mast[1] - 0.04, ROOF_TOP + 0.25), (mast[0] + 0.04, mast[1] + 0.04, ROOF_TOP + 5.5), "metal", detail=3, collide=False)
for k in range(3):   # cross arms near the top
    z = ROOF_TOP + 4.3 + 0.4 * k
    box((mast[0] - 0.35 + 0.08 * k, mast[1] - 0.012, z), (mast[0] + 0.35 - 0.08 * k, mast[1] + 0.012, z + 0.024), "trim", detail=1, collide=False)
for gx, gy in ((-W - R + 0.2, L + R - 0.2), (-W - R + 0.2, 0.6), (0.4, L + R - 0.2)):
    beam((mast[0], mast[1], ROOF_TOP + 3.9), (gx, gy, PARAPET_TOP), 0.012, "trim", detail=1)
box((1.2, -3.4, ROOF_TOP), (1.75, -2.85, ROOF_TOP + 0.45), "sheet", detail=2, collide=True)
box((1.15, -3.45, ROOF_TOP + 0.45), (1.80, -2.80, ROOF_TOP + 0.50), "trim", detail=2, collide=False)
box((-1.6, 0.9, ROOF_TOP + 0.12), (-0.6, 1.4, ROOF_TOP + 0.72), "sheet", detail=2, collide=True)
for lx, ly in ((-1.55, 0.95), (-0.7, 0.95), (-1.55, 1.3), (-0.7, 1.3)):
    box((lx, ly, ROOF_TOP), (lx + 0.05, ly + 0.05, ROOF_TOP + 0.12), "trim", detail=1, collide=False)
box((mast[0] - 0.02, -L - R + P, ROOF_TOP), (mast[0] + 0.02, mast[1] - 0.15, ROOF_TOP + 0.04), "trim", detail=1, collide=False)
# Roof ladder up the back wall.
for x in (LADDER_X - 0.25, LADDER_X + 0.21):
    box((x, LADDER_Y - 0.02, 0.0), (x + 0.04, LADDER_Y + 0.02, ROOF_TOP + 1.1), "metal", detail=2, collide=False)
    # handrail from the ladder onto the roof
    box((x, L + R - 0.6, ROOF_TOP + 1.06), (x + 0.04, LADDER_Y + 0.02, ROOF_TOP + 1.10), "metal", detail=1, collide=False)
    box((x, L + R - 0.6, ROOF_TOP), (x + 0.04, L + R - 0.56, ROOF_TOP + 1.10), "metal", detail=1, collide=False)
for k in range(12):
    z = 0.3 + k * 0.3
    box((LADDER_X - 0.21, LADDER_Y - 0.015, z), (LADDER_X + 0.21, LADDER_Y + 0.015, z + 0.03), "metal", detail=1, collide=False)
for z in (1.2, 2.6):   # stand-offs holding the ladder off the wall
    box((LADDER_X - 0.25, L, z), (LADDER_X - 0.21, LADDER_Y, z + 0.04), "metal", detail=1, collide=False)
    box((LADDER_X + 0.21, L, z), (LADDER_X + 0.25, LADDER_Y, z + 0.04), "metal", detail=1, collide=False)

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

# ---- doors -----------------------------------------------------------------------------
# Entrance door: a steel leaf in the opening with stiffening bands, a viewing slit and a handle.
DOOR1_HINGE = (DOOR_X[0], -L + 0.06)
dy0, dy1 = -L + 0.03, -L + 0.09
box((DOOR_X[0], dy0, FLOOR), (DOOR_X[1], dy1, DOOR_TOP), "metal", selection="doors1")
for z in (FLOOR + 0.25, FLOOR + 1.0, FLOOR + 1.85):
    box((DOOR_X[0] + 0.03, dy0 - 0.012, z), (DOOR_X[1] - 0.03, dy0, z + 0.07), "trim", detail=2, collide=False, selection="doors1")
box((DOOR_X[0] + 0.33, dy0 - 0.006, FLOOR + 1.50), (DOOR_X[1] - 0.33, dy0, FLOOR + 1.58), "paint", detail=1, collide=False, selection="doors1")
box((DOOR_X[1] - 0.16, dy0 - 0.05, FLOOR + 1.0), (DOOR_X[1] - 0.06, dy1 + 0.05, FLOOR + 1.06), "trim", detail=2, collide=False, selection="doors1")

# Vault door: a thick slab that seats against the command-room face of the dividing wall, with a
# raised centre panel, a ring of bolt heads, two locking bars and a spoked wheel. Around it on the
# wall, a steel surround; in the opening, a steel lining.
VAULT_SLAB_X = (VAULT_X[0] - 0.12, VAULT_X[1] + 0.12)
VAULT_SLAB_Y = (DIVIDE_Y[0] - 0.18, DIVIDE_Y[0])
VAULT_SLAB_Z = (FLOOR + 0.02, VAULT_TOP + 0.12)
DOOR2_HINGE = (VAULT_SLAB_X[0], VAULT_SLAB_Y[0] + 0.02)
sx0, sx1 = VAULT_SLAB_X
sy0, sy1 = VAULT_SLAB_Y
sz0, sz1 = VAULT_SLAB_Z
box((sx0, sy0, sz0), (sx1, sy1, sz1), "vault", selection="doors2")
box((sx0 + 0.14, sy0 - 0.03, sz0 + 0.14), (sx1 - 0.14, sy0, sz1 - 0.14), "trim", detail=2, collide=False, selection="doors2")
for k in range(7):   # bolt heads up both sides
    z = sz0 + 0.12 + k * (sz1 - sz0 - 0.29) / 6
    for x in (sx0 + 0.04, sx1 - 0.09):
        box((x, sy0 - 0.02, z), (x + 0.05, sy0, z + 0.05), "trim", detail=1, collide=False, selection="doors2")
for k in range(5):   # and along the top and bottom
    x = sx0 + 0.22 + k * (sx1 - sx0 - 0.49) / 4
    for z in (sz0 + 0.04, sz1 - 0.09):
        box((x, sy0 - 0.02, z), (x + 0.05, sy0, z + 0.05), "trim", detail=1, collide=False, selection="doors2")
for z in (sz0 + 0.42, sz1 - 0.48):   # locking bars with keepers at the latch side
    box((sx0 + 0.10, sy0 - 0.07, z), (sx1 - 0.02, sy0 - 0.03, z + 0.07), "metal", detail=2, collide=False, selection="doors2")
    box((sx1 - 0.14, sy0 - 0.09, z - 0.03), (sx1 - 0.06, sy0 - 0.03, z + 0.10), "trim", detail=1, collide=False, selection="doors2")
wheel_c = ((VAULT_X[0] + VAULT_X[1]) / 2, FLOOR + 1.15)
wheel_y = sy0 - 0.13
box((wheel_c[0] - 0.035, wheel_y, wheel_c[1] - 0.035), (wheel_c[0] + 0.035, sy0 - 0.03, wheel_c[1] + 0.035), "trim", detail=2, collide=False, selection="doors2")
box((wheel_c[0] - 0.07, wheel_y - 0.02, wheel_c[1] - 0.07), (wheel_c[0] + 0.07, wheel_y + 0.02, wheel_c[1] + 0.07), "metal", detail=2, collide=False, selection="doors2")
rim = [(wheel_c[0] + 0.27 * math.cos(math.radians(a)), wheel_y, wheel_c[1] + 0.27 * math.sin(math.radians(a))) for a in range(0, 360, 30)]
for k in range(12):
    beam(rim[k], rim[(k + 1) % 12], 0.04, "metal", detail=2, selection="doors2")
for a in (0, 45, 90, 135):
    ca, sa_ = 0.27 * math.cos(math.radians(a)), 0.27 * math.sin(math.radians(a))
    beam((wheel_c[0] - ca, wheel_y, wheel_c[1] - sa_), (wheel_c[0] + ca, wheel_y, wheel_c[1] + sa_), 0.03, "trim", detail=2, selection="doors2")
for z in (FLOOR + 0.30, FLOOR + 1.80):   # hinge barrels on the wall
    box((sx0 - 0.10, sy0 - 0.02, z), (sx0, sy1, z + 0.28), "metal", detail=2, collide=False)
    box((sx0 - 0.07, sy0 - 0.05, z + 0.04), (sx0 + 0.10, sy0 - 0.02, z + 0.24), "trim", detail=1, collide=False, selection="doors2")
# Steel surround on the wall (top and latch side; the hinges take the other side).
box((sx1, sy1 - 0.03, FLOOR), (sx1 + 0.12, sy1, sz1 + 0.12), "trim", detail=2, collide=False)
box((sx0 - 0.10, sy1 - 0.03, sz1), (sx1 + 0.12, sy1, sz1 + 0.12), "trim", detail=2, collide=False)
# Steel lining of the opening.
vy0, vy1 = DIVIDE_Y
box((VAULT_X[0] - 0.05, vy0 + 0.001, FLOOR), (VAULT_X[0], vy1 + 0.02, VAULT_TOP + 0.05), "vault", detail=2, collide=False)
box((VAULT_X[1], vy0 + 0.001, FLOOR), (VAULT_X[1] + 0.05, vy1 + 0.02, VAULT_TOP + 0.05), "vault", detail=2, collide=False)
box((VAULT_X[0], vy0 + 0.001, VAULT_TOP), (VAULT_X[1], vy1 + 0.02, VAULT_TOP + 0.05), "vault", detail=2, collide=False)


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
        for face in outward(piece):
            pts = [Vector(piece.verts[i]) for i in face]
            normal = (pts[1] - pts[0]).cross(pts[2] - pts[0]).normalized()
            # Which way the face points decides its material (walls differ inside and out).
            axis = max(range(3), key=lambda a: abs(normal[a]))
            direction = ("+" if normal[axis] > 0 else "-") + "xyz"[axis]
            material = piece.face_materials.get(direction, piece.material)
            key = material if textured else ("fire_" + piece.material if fire else "plain")
            if key not in slots:
                slots.append(key)
            spec = MATERIALS[material]
            tile = spec[2]
            if piece.uv:
                face_uv = [piece.uv[i] for i in face]
            elif axis == 2:
                face_uv = [(p.x / tile, p.y / tile) for p in pts]
            else:
                across = [p.y if axis == 0 else p.x for p in pts]
                if len(spec) > 3 and spec[3]:   # the texture is one wall high: floor at the bottom, ceiling at the top
                    face_uv = [(a / tile, (p.z - FLOOR) / (CEILING - FLOOR)) for a, p in zip(across, pts)]
                else:
                    face_uv = [(a / tile, p.z / tile) for a, p in zip(across, pts)]
            # P3D faces have at most four corners: larger ones become fans of triangles.
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


# The placeholder model the lock mount refers to: one small triangle.
p3d.new_scene()
os.makedirs(os.path.join(out_dir, "proxy"), exist_ok=True)
placeholder = p3d.new_mesh_object("AF_proxy_codelock", [(0, 0, 0), (0.01, 0, 0), (0, 0.01, 0)], [(0, 1, 2)])
p3d.mark_lod(placeholder, p3d.LOD_VISUAL, 1)
p3d.export(os.path.join(out_dir, "proxy", "AF_proxy_codelock.p3d"))

p3d.new_scene()
# Visual LODs: detail d is drawn in LODs 1..d; detail -2 marks a stand-in used from LOD 2 on.
for lod in (1, 2, 3):
    chosen = [p for p in pieces if (p.detail >= lod) or (p.detail == -2 and lod >= 2)]
    obj = build("commandpost_lod%d" % lod, chosen)
    p3d.mark_lod(obj, p3d.LOD_VISUAL, lod)
    print("LOD", obj.name, "triangles", sum(len(p.vertices) - 2 for p in obj.data.polygons))
    if lod <= 2:
        # Where an attached code lock is drawn: a proxy triangle on the wall beside the vault
        # door, carrying the slot name (which attachment it shows).
        tri = bpy.data.meshes.new("codelock_proxy_lod%d" % lod)
        tri.from_pydata([(0, 0, 0), (0, 0, 0.2), (0, 0.1, 0)], [], [(0, 1, 2)])
        tri.update(calc_edges=True)
        proxy = bpy.data.objects.new(tri.name, tri)
        proxy.hide_render = True
        bpy.context.scene.collection.objects.link(proxy)
        proxy.a3ob_properties_object_proxy.is_a3_proxy = True
        proxy.a3ob_properties_object_proxy.proxy_path = LOCK_PROXY
        proxy.a3ob_properties_object_proxy.proxy_index = 1
        proxy.parent = obj
        proxy.matrix_world = Matrix.Translation((LOCK_X, DIVIDE_Y[0] - 0.005 - LOCK_STANDOFF, LOCK_Z)) @ LOCK_TURN
        proxy.vertex_groups.new(name=LOCK_SLOT.lower()).add(range(3), 1.0, 'REPLACE')

solid = [p for p in pieces if p.collide]
geometry = build("commandpost_geometry", solid, textured=False, components=True)
# autocenter 0 keeps the model's origin where it is here: the middle of the footprint at ground
# level. Without it the engine moved the origin to the middle of the bounding box, 3.8 m up
# (the mast counts), and the building placed at ground level sat buried to its roof.
p3d.mark_lod(geometry, p3d.LOD_GEOMETRY, 1, properties=(("class", "house"), ("map", "house"), ("autocenter", "0")))
add_mass(geometry, 150.0)
# View geometry: the same solids plus the thin box a player aims at to use the ladder.
ladder_box = Piece(*_box_data((LADDER_X - 0.24, LADDER_Y - 0.02, 0.0), (LADDER_X + 0.24, LADDER_Y + 0.02, ROOF_TOP + 0.3)),
                   "metal", 3, True, "ladder1")
view = build("commandpost_view", solid + [ladder_box], textured=False, components=True)
p3d.mark_lod(view, p3d.LOD_VIEW_GEOMETRY, 1)
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
    "ladder1_bottom_front": [(LADDER_X, LADDER_Y, 0.0)],
    "ladder1_top_front": [(LADDER_X, LADDER_Y, ROOF_TOP)],
    "ladder1_dir": [(LADDER_X, LADDER_Y + 0.32, 0.0)],
    "ladder1_con": [(LADDER_X, LADDER_Y, 0.0), (LADDER_X, LADDER_Y, ROOF_TOP)],
    "ladder1_con_dir": [(LADDER_X, LADDER_Y + 0.32, 0.0), (LADDER_X, LADDER_Y - 0.37, ROOF_TOP)],
    "ladder1": [(LADDER_X, LADDER_Y, 0.28)],
    LOCK_SLOT.lower(): [(LOCK_X, DIVIDE_Y[0] - 0.005, LOCK_Z)],
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
