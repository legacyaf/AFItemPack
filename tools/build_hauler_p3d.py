"""Build the Jerrycan Hauler P3D models from the low-poly GLB.

Run headless (needs the Arma 3 Object Builder add-on enabled in Blender):

    blender -b --python tools/build_hauler_p3d.py -- <repo root>

Writes JerrycanHauler_m.p3d, _f.p3d and _g.p3d into AFItemPack/JerrycanHauler and
saves the working scenes next to this script (tools/blend/) so they can be opened
and refined by hand.

The fit numbers below are a first pass made without a reference character model.
Adjust them after looking at the pack in game.
"""
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

# ---- fit settings (metres, Blender axes: Z up; the character faces -Y) -----------
# The Y values below are written as if the character faced +Y; the worn model is
# turned half a turn afterwards, so FRAME_FACE_Y = -0.12 means 12 cm behind the spine.
PACK_HEIGHT = 0.75      # total height of the pack on the character
PACK_BOTTOM_Z = 0.86    # height of the lowest point (hip belt) above the feet
FRAME_FACE_Y = -0.12    # where the wearer-side face of the frame sits (character back)
# Position of the frame's wearer-side face and centre in the *unscaled* GLB:
SRC_FRAME_FACE_Y = 0.15
SRC_FRAME_CENTRE_X = 0.0
WORN_BONE = "Spine3"    # the frame and everything on it follows the upper back
BELT_BONE = "Pelvis"    # the hip belt follows the hips
# Hip belt region in the *unscaled* GLB (see flip_belt) and the plane it is mirrored across:
BELT_MAX_Z = -0.62
BELT_MAX_Y = -0.02
BELT_MAX_X = 0.62
BELT_MIRROR_Y = 0.08
# Shoulder straps: how far (metres, on the character) the arch over the shoulders is
# raised so it clears them. Seen in game: unraised, the straps cut through the shoulders; raising only the front left the part behind the shoulder inside the upper back.
# The two straps in the mesh are not the same shape. Confirmed in game: the right strap fits
# with a 5 cm lift, the left never did, so the left strap is replaced by a mirror image of
# the right one (mirror_right_strap) and both sides then use the same values.
# Strap region in the *unscaled* GLB used for that replacement:
STRAP_REGION_MIN_Y = 0.17
STRAP_REGION_MIN_Z = -0.62
STRAP_REGION_MIN_X = 0.24
# History: with 0.08 on both sides,
# with 0.08 on both, the character's right strap floated ~4 cm and the left still sank in.
STRAP_LIFT_RIGHT = 0.05   # character's right (scabbard side; +X in the unscaled GLB)
STRAP_LIFT_LEFT = 0.05    # character's left (-X in the unscaled GLB)
# Strap region in the *unscaled* GLB: the lift fades in between these Y values (frame ->
# shoulder ridge) and between these Z values (lower webbing stays put -> top of the arch).
STRAP_Y_RAMP = (0.15, 0.30)
# Top of the left strap: moved this far (metres) away from the neck, where its inner edge
# cut into the slope between neck and shoulder. Fades in over this Z range.
STRAP_TOP_OUT_LEFT = 0.0
STRAP_TOP_OUT_Z_RAMP = (0.10, 0.40)
# The bedroll overhangs the start of the straps; vertices above this height and closer to
# the frame than this Y are bedroll and stay put.
STRAP_BEDROLL_MIN_Z = 0.63
STRAP_BEDROLL_MAX_Y = 0.27
# Lower strap webbing: how far (metres) it is pushed sideways, away from the body's centre
# line, so it passes around the ribs instead of through them. Applies to strap vertices
# further than STRAP_SIDE_MIN_X from the centre; fades in over the Y ramp (frame ->
# body) and the first Z ramp (waist attachment -> ribs), and out over the second (chest).
STRAP_SIDE_PUSH = 0.045
STRAP_SIDE_MIN_X = 0.22
STRAP_SIDE_Y_RAMP = (0.15, 0.25)
STRAP_SIDE_Z_IN = (-0.62, -0.45)
STRAP_SIDE_Z_OUT = (-0.15, 0.20)
STRAP_Z_RAMP = (-0.20, 0.35)
# The leather scabbard, in the worn model's coordinates: everything further right than MAX_X
# and further back than MIN_Y between these heights. Its bottom half, below CUT_Z, is removed.
SCABBARD_MAX_X = -0.205
SCABBARD_MIN_Y = 0.135   # the brown panel still seen below the cut is the frame's own side (x about -0.19), not sleeve
SCABBARD_BOTTOM_Z = 0.86
SCABBARD_TOP_Z = 1.47
SCABBARD_CUT_Z = 1.18
GROUND_MASS_KG = 4.5

TEXTURE = r"AFItemPack\JerrycanHauler\data\jerrycan_hauler_co.paa"
RVMAT = r"AFItemPack\JerrycanHauler\data\jerrycan_hauler.rvmat"

# Attachment points, in the worn model's coordinates (metres; +X is the character's left,
# +Y is behind the character, Z is up). The item's own origin is drawn at "at"; "turn"
# is (axis, degrees) rotations applied to the item in order. Proxy names must match the
# Proxy... classes in config.cpp. First-pass placements: adjust after looking in game.
PROXY_DIR = r"\AFItemPack\JerrycanHauler\proxy"
PROXIES = {
    "AF_Hauler_proxy_jerrycan": {"at": (0.0, 0.22, 1.28), "turn": ()},              # in the cradle, upright
    "AF_Hauler_proxy_shovel": {"at": (0.225, 0.18, 0.85), "turn": ()},              # left side, upright, blade up (at 1.20 the blade was above the head)
    # The scabbard is a leather sleeve on the character's right: x -0.275..-0.208, y 0.14..0.25, z 0.90..1.45.
    # A long gun hangs from its barrel line with its body (grip, magazine) on one side of it. Turned
    # only ("Y", -90), that side pointed outboard and the gun sat beside the sleeve, not in it.
    "AF_Hauler_proxy_weapon": {"at": (-0.242, 0.165, 1.33), "turn": (("Z", -90), ("Y", -90))},  # stock up, underside to the rear (1.18: a Mosin hung to the shins; 1.46: long rifles stood 25 cm above the head)
}

# Lower-detail visual LODs: (resolution, share of the full triangle count, method).
# The vanilla backpacks carry visual LODs 1-5 plus a first-person LOD and no shadow LOD;
# same here. "collapse" is Blender's edge-collapse decimator, which keeps the shape best but
# stalls near 4,600 triangles on this mesh (thin double-sided shells). "cluster" merges all
# vertices closer than a distance, searched to hit the target; cruder, but it has no floor
# and these LODs are only seen from far away.
# LOD 3 asks collapse for 25% and gets its floor (about 32%), which is clean; a clustered
# LOD 3 at 25% was visibly ragged.
# LODs 6-8 are for far distances: a few hundred triangles down to a few dozen, where the pack
# is a handful of pixels. They keep the silhouette and average colour and nothing else.
LOD_RATIOS = ((2, 0.50, "collapse"), (3, 0.25, "collapse"), (4, 0.10, "cluster"), (5, 0.04, "cluster"),
              (6, 0.016, "cluster"), (7, 0.006, "cluster"), (8, 0.0025, "cluster"))

LOD_VISUAL, LOD_VIEW_PILOT, LOD_GEOMETRY, LOD_VIEW_GEOMETRY, LOD_FIRE_GEOMETRY = "0", "2", "6", "14", "15"

repo = sys.argv[sys.argv.index("--") + 1]
glb = os.path.join(repo, "models", "jerrycan_hauler", "lowpoly", "jerrycan_hauler_15k.glb")
out_dir = os.path.join(repo, "AFItemPack", "JerrycanHauler")
blend_dir = os.path.join(repo, "tools", "blend")
os.makedirs(blend_dir, exist_ok=True)

if not hasattr(bpy.ops.a3ob, "export_p3d"):
    raise SystemExit("Arma 3 Object Builder add-on is not enabled in Blender")


def load_pack():
    bpy.ops.wm.read_homefile(use_empty=True)  # keeps the user's enabled add-ons
    bpy.ops.import_scene.gltf(filepath=glb)
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    for mat in obj.data.materials:
        props = mat.a3ob_properties_material
        props.texture_path = TEXTURE
        props.material_path = RVMAT
    flip_belt(obj)
    mirror_right_strap(obj)
    mn, mx = bounds(obj)
    obj["fit_scale"] = PACK_HEIGHT / (mx.z - mn.z)
    obj["src_min_z"] = mn.z
    lift_straps(obj, obj["fit_scale"])
    return obj


def flip_belt(obj):
    """Move the hip belt to the wearer's side.

    In the Meshy mesh the belt ring loops away from the wearer (toward -Y, behind the
    cargo cradle) while the shoulder straps loop toward the wearer (+Y). The belt faces
    are cut loose and mirrored across the lumbar pad so the ring wraps the waist.
    Works on the unscaled GLB coordinates. Tags the moved vertices in the "belt"
    integer attribute.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    layer = bm.verts.layers.int.new("belt")  # before collecting: adding a layer invalidates references

    def in_belt(co):
        return (co.z < BELT_MAX_Z and co.y < BELT_MAX_Y and abs(co.x) < BELT_MAX_X)

    faces = [f for f in bm.faces if all(in_belt(v.co) for v in f.verts)]
    result = bmesh.ops.split(bm, geom=faces)
    faces = [g for g in result["geom"] if isinstance(g, bmesh.types.BMFace)]
    verts = {v for f in faces for v in f.verts}
    for v in verts:
        v.co.y = 2 * BELT_MIRROR_Y - v.co.y
    bmesh.ops.reverse_faces(bm, faces=faces)
    for v in verts:
        v[layer] = 1
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    print("BELT faces moved", len(faces), "verts", len(verts))


def mirror_right_strap(obj):
    """Replace the left shoulder strap with a mirror image of the right one."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    belt = bm.verts.layers.int.get("belt")

    def in_strap(v, side):
        return (v.co.x * side > STRAP_REGION_MIN_X and v.co.y > STRAP_REGION_MIN_Y
                and v.co.z > STRAP_REGION_MIN_Z and not (belt and v[belt]))

    left = [f for f in bm.faces if all(in_strap(v, -1) for v in f.verts)]
    bmesh.ops.delete(bm, geom=left, context='FACES')
    right = [f for f in bm.faces if all(in_strap(v, 1) for v in f.verts)]
    copy = bmesh.ops.duplicate(bm, geom=right)["geom"]
    for v in (g for g in copy if isinstance(g, bmesh.types.BMVert)):
        v.co.x = -v.co.x
    faces = [g for g in copy if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.reverse_faces(bm, faces=faces)
    print("STRAP left faces removed", len(left), "mirrored from right", len(faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def lift_straps(obj, scale):
    """Raise the shoulder-strap arches (unscaled GLB coordinates, before fitting)."""
    def smooth(lo, hi, v):
        t = min(1.0, max(0.0, (v - lo) / (hi - lo)))
        return t * t * (3 - 2 * t)

    lift_right, lift_left = STRAP_LIFT_RIGHT / scale, STRAP_LIFT_LEFT / scale
    push = STRAP_SIDE_PUSH / scale
    belt = obj.data.attributes.get("belt")
    moved = 0
    for v in obj.data.vertices:
        if abs(v.co.x) < STRAP_SIDE_MIN_X or (belt and belt.data[v.index].value):
            continue
        w = (smooth(*STRAP_SIDE_Y_RAMP, v.co.y) * smooth(*STRAP_SIDE_Z_IN, v.co.z)
             * (1 - smooth(*STRAP_SIDE_Z_OUT, v.co.z)))
        if w > 0:
            v.co.x += push * w * (1 if v.co.x > 0 else -1)
    for v in obj.data.vertices:
        if v.co.z > STRAP_BEDROLL_MIN_Z and v.co.y < STRAP_BEDROLL_MAX_Y:
            continue
        w = smooth(*STRAP_Y_RAMP, v.co.y) * smooth(*STRAP_Z_RAMP, v.co.z)
        if w > 0:
            v.co.z += (lift_right if v.co.x > 0 else lift_left) * w
            if v.co.x < 0:
                v.co.x -= (STRAP_TOP_OUT_LEFT / scale) * smooth(*STRAP_Y_RAMP, v.co.y) * smooth(*STRAP_TOP_OUT_Z_RAMP, v.co.z)
            moved += 1
    obj.data.update()
    print("STRAPS verts raised", moved)


def cut_scabbard(obj, to_worn):
    """Cut the bottom half off the leather scabbard (the owner's choice: a gun then hangs from a
    short upper sleeve with its barrel free, instead of running through a full-length one).

    to_worn maps the object's current coordinates to the worn model's. The sleeve's faces are
    split along the cut height first so the new bottom edge is straight.
    """
    inverse = to_worn.inverted()
    obj.data.transform(to_worn)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    belt = bm.verts.layers.int.get("belt")

    def in_sleeve(v, low):
        return (v.co.x < SCABBARD_MAX_X and v.co.y > SCABBARD_MIN_Y and low < v.co.z < SCABBARD_TOP_Z
                and not (belt and v[belt]))

    faces = [f for f in bm.faces if all(in_sleeve(v, SCABBARD_BOTTOM_Z) for v in f.verts)]
    geom = list({e for f in faces for e in f.edges}) + faces + list({v for f in faces for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, SCABBARD_CUT_Z), plane_no=(0, 0, 1))
    lower = [f for f in bm.faces if all(in_sleeve(v, SCABBARD_BOTTOM_Z) for v in f.verts)
             and f.calc_center_median().z < SCABBARD_CUT_Z]
    bmesh.ops.delete(bm, geom=lower, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.transform(inverse)
    obj.data.update()
    print("SCABBARD faces removed below the cut", len(lower))


def belt_vertex_indices(obj):
    attr = obj.data.attributes.get("belt")
    return [i for i, d in enumerate(attr.data) if d.value] if attr else []


def apply_matrix(obj, matrix):
    obj.data.transform(matrix)
    obj.data.update()


def bounds(obj):
    cos = [v.co for v in obj.data.vertices]
    mn = Vector((min(c.x for c in cos), min(c.y for c in cos), min(c.z for c in cos)))
    mx = Vector((max(c.x for c in cos), max(c.y for c in cos), max(c.z for c in cos)))
    return mn, mx


def mark_lod(obj, lod, resolution=1, properties=()):
    props = obj.a3ob_properties_object
    props.is_a3_lod = True
    props.lod = lod
    props.resolution = resolution
    for name, value in properties:
        item = props.properties.add()
        item.name, item.value = name, value


def new_mesh_object(name, verts=(), faces=()):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(list(verts), [], list(faces))
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def box(name, mn, mx):
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return new_mesh_object(name, verts, faces)


def add_proxies(lod_obj, to_scene=Matrix.Identity(4), bone=None):
    """Add the attachment proxies to a visual LOD. to_scene maps worn coordinates to this scene."""
    import math
    for name, spec in PROXIES.items():
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([(0, 0, 0), (0, 0, 0.2), (0, 0.1, 0)], [], [(0, 1, 2)])
        mesh.update(calc_edges=True)
        obj = bpy.data.objects.new(name, mesh)
        obj.hide_render = True  # proxies are markers, not geometry
        bpy.context.scene.collection.objects.link(obj)
        props = obj.a3ob_properties_object_proxy
        props.is_a3_proxy = True
        props.proxy_path = PROXY_DIR + "\\" + name + ".p3d"
        props.proxy_index = 1
        local = Matrix.Translation(spec["at"])
        for axis, degrees in spec["turn"]:
            local = local @ Matrix.Rotation(math.radians(degrees), 4, axis)
        obj.parent = lod_obj
        obj.matrix_world = to_scene @ local
        obj.display_type = 'WIRE'
        obj.show_name = True
        if bone:
            obj.vertex_groups.new(name=bone).add(range(3), 1.0, 'REPLACE')


def add_lower_lods(pack, name, **proxy_args):
    """Add decimated copies of the finished LOD 1 object as visual LODs 2-5.

    The GLB mesh is split along every UV seam, which a decimator cannot collapse across,
    so each copy is welded first. Vertex groups (bone weights) and UVs survive both steps.
    """
    full = len(pack.data.polygons)
    def clustered(source, distance):
        bm = bmesh.new()
        bm.from_mesh(source)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        return bm

    for resolution, ratio, method in LOD_RATIOS:
        obj = pack.copy()
        obj.data = pack.data.copy()
        obj.name = "%s_lod%d" % (name, resolution)
        bpy.context.scene.collection.objects.link(obj)
        props = obj.a3ob_properties_object
        props.resolution = resolution
        props.copies.clear()

        weld = 1e-4
        if method == "cluster":
            # Bisect the merge distance until the triangle count is at or under the target.
            low, high = 1e-4, 1.0
            for _ in range(20):
                weld = (low + high) / 2
                trial = clustered(pack.data, weld)
                count = len(trial.faces)
                trial.free()
                if count > ratio * full:
                    low = weld
                else:
                    high = weld
            weld = high
        bm = clustered(pack.data, weld)
        welded = len(bm.faces)
        bm.to_mesh(obj.data)
        bm.free()
        normals = obj.data.attributes.get("custom_normal")
        if normals:
            obj.data.attributes.remove(normals)

        if method == "collapse":
            modifier = obj.modifiers.new("decimate", 'DECIMATE')
            modifier.ratio = min(1.0, ratio * full / max(welded, 1))
            depsgraph = bpy.context.evaluated_depsgraph_get()
            reduced = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph),
                                                      preserve_all_data_layers=True, depsgraph=depsgraph)
            obj.modifiers.clear()
            obj.data = reduced
        # Clustering leaves sliver triangles that shade as dark spikes when smoothed.
        for polygon in obj.data.polygons:
            polygon.use_smooth = method == "collapse"
        obj.data.update()
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        print("LOD", obj.name, method, "triangles", tris, "of", full, "merge distance %.1f mm" % (weld * 1000))
        add_proxies(obj, **proxy_args)


def export_proxy_models():
    """The proxy models themselves are placeholders: one small triangle each."""
    os.makedirs(os.path.join(out_dir, "proxy"), exist_ok=True)
    for name in PROXIES:
        bpy.ops.wm.read_homefile(use_empty=True)
        tri = new_mesh_object(name, [(0, 0, 0), (0.01, 0, 0), (0, 0.01, 0)], [(0, 1, 2)])
        mark_lod(tri, LOD_VISUAL, 1)
        export(os.path.join(out_dir, "proxy", name + ".p3d"))


def export(path):
    bpy.ops.a3ob.export_p3d(filepath=path, relative_paths=True, apply_transforms=True,
                            apply_modifiers=True, lod_collisions='FAIL')
    print("EXPORTED", path, os.path.getsize(path))


def scale_factor(obj):
    return obj["fit_scale"]  # measured in load_pack before the straps were raised


export_proxy_models()

# ---- worn model (male; the female file is the same mesh for now) -----------------
pack = load_pack()
s = scale_factor(pack)
offset = Vector((-SRC_FRAME_CENTRE_X * s,
                 FRAME_FACE_Y - SRC_FRAME_FACE_Y * s,
                 PACK_BOTTOM_Z - pack["src_min_z"] * s))
# Confirmed in game: the character faces -Y in Blender, so its back is toward +Y.
# The offset puts the pack behind a +Y-facing character; then it is turned half a turn.
worn_matrix = Matrix.Rotation(3.141592653589793, 4, 'Z') @ Matrix.Translation(offset) @ Matrix.Scale(s, 4)
apply_matrix(pack, worn_matrix)
cut_scabbard(pack, Matrix.Identity(4))
pack.name = "hauler_worn_lod1"
mark_lod(pack, LOD_VISUAL, 1)
belt = set(belt_vertex_indices(pack))
rest = [i for i in range(len(pack.data.vertices)) if i not in belt]
pack.vertex_groups.new(name=WORN_BONE).add(rest, 1.0, 'REPLACE')
pack.vertex_groups.new(name=BELT_BONE).add(sorted(belt), 1.0, 'REPLACE')
add_proxies(pack, bone=WORN_BONE)
# First-person view uses the full-detail mesh.
first_person = pack.a3ob_properties_object.copies.add()
first_person.lod = LOD_VIEW_PILOT
first_person.resolution = 1
add_lower_lods(pack, "hauler_worn", bone=WORN_BONE)

# Character-attached models must not be re-centred by the engine.
geo = new_mesh_object("hauler_worn_geometry")
mark_lod(geo, LOD_GEOMETRY, 1, properties=(("autocenter", "0"),))

print("WORN BOUNDS", [tuple(round(v, 3) for v in b) for b in bounds(pack)], "scale", round(s, 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_dir, "hauler_worn.blend"))
export(os.path.join(out_dir, "JerrycanHauler_m.p3d"))
export(os.path.join(out_dir, "JerrycanHauler_f.p3d"))

# ---- ground model ------------------------------------------------------------------
pack = load_pack()
s = scale_factor(pack)
# Lay it on its back: the wearer side (+Y) goes down, the top of the pack points +Y.
ground_matrix = Matrix.Rotation(-1.5707963267948966, 4, 'X') @ Matrix.Scale(s, 4)
apply_matrix(pack, ground_matrix)
mn, mx = bounds(pack)
centre = Matrix.Translation((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z))
apply_matrix(pack, centre)
ground_matrix = centre @ ground_matrix
cut_scabbard(pack, worn_matrix @ ground_matrix.inverted())
pack.name = "hauler_ground_lod1"
mark_lod(pack, LOD_VISUAL, 1)
add_proxies(pack, to_scene=ground_matrix @ worn_matrix.inverted())
add_lower_lods(pack, "hauler_ground", to_scene=ground_matrix @ worn_matrix.inverted())

mn, mx = bounds(pack)
geo = box("hauler_ground_geometry", mn, mx)
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

print("GROUND BOUNDS", [tuple(round(v, 3) for v in b) for b in (mn, mx)])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_dir, "hauler_ground.blend"))
export(os.path.join(out_dir, "JerrycanHauler_g.p3d"))
