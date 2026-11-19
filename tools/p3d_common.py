"""Helpers shared by the model build scripts (run inside Blender with the Arma 3 Object
Builder add-on). The hauler and cape scripts predate this file and carry their own copies."""
import os

import bmesh
import bpy
from mathutils import Vector

LOD_VISUAL, LOD_VIEW_PILOT, LOD_GEOMETRY, LOD_VIEW_GEOMETRY, LOD_FIRE_GEOMETRY = "0", "2", "6", "14", "15"


# ---- the Field Cape's shape, shared so other worn items can be fitted under it ----------
# Metres; Z up, the character faces -Y. build_cape_p3d.py builds the cloth from these numbers
# and build_vestpack_p3d.py keeps the pack inside cape_inner_y().
CAPE = {
    "TOP_Z": 1.52,          # top edge of the cloth at the back of the neck
    "TOP_DROP": 0.05,       # how much lower the top edge is at the shoulders than at the neck
    "HEM_Z": 0.52,          # bottom edge (just below the knee)
    "HALF_WIDTH_TOP": 0.17,
    "HALF_WIDTH_HEM": 0.33,
    "NECK_Y": 0.19,         # distance behind the spine line at the top edge
    "BLADE_Z": 1.41,        # height of the shoulder blades
    "BLADE_Y": 0.25,        # distance behind the spine line there
    "HEM_Y": 0.255,         # distance behind the spine line at the hem
    "WRAP": 0.012,          # how far the side edges curve toward the wearer at the hem (none at the top)
    "FOLD_DEPTH_TOP": 0.003,
    "FOLD_DEPTH_HEM": 0.016,   # 0.026 with even folds read as corrugated sheet when the cape was seen at an angle
    "THICKNESS": 0.004,
    "COLLAR": ((0.010, 0.016), (0.022, 0.028)),   # rolled top edge: rows (toward the wearer, up)
    # Bone mix by height. Above BLEND_Z[1] the cloth is all upper back; down to BLEND_Z[0] it
    # fades to the hips; below LEG_Z[0] it fades toward the thighs (left half to the left
    # thigh, right half to the right), reaching LEG_SHARE at LEG_Z[1] and below.
    # History: an even upper-back-to-hips mix over the whole length (0.52-1.40) stood well but
    # moved like a board: it tented when crouching and hovered over the legs when prone.
    "BLEND_Z": (1.05, 1.40),
    "LEG_Z": (0.95, 0.70),
    "LEG_SHARE": 0.6,
}


CAPE_BONES = ("Spine3", "Pelvis", "LeftUpLeg", "RightUpLeg")


def cape_weights(x, z):
    """Bone weights of the cape's cloth at (x, z), as {bone: share}; +X is the character's left.
    The vest pack's back uses the same function so the two deform together."""
    lo, hi = CAPE["BLEND_Z"]
    upper = min(1.0, max(0.0, (z - lo) / (hi - lo)))
    top, bottom = CAPE["LEG_Z"]
    legs = CAPE["LEG_SHARE"] * min(1.0, max(0.0, (top - z) / (top - bottom)))
    # Left/right split fades across the whole width: split over the middle 30 cm only, the two
    # halves parted at the hem when prone and one half stuck forward under the raised thigh when crouched.
    left = min(1.0, max(0.0, 0.5 + x / 0.60))
    weights = {"Spine3": upper, "Pelvis": 1.0 - upper - legs, "LeftUpLeg": legs * left, "RightUpLeg": legs * (1 - left)}
    return {bone: share for bone, share in weights.items() if share > 1e-4}


def set_weights(obj, weights_of):
    """Write bone weights to an object's vertex groups; weights_of(vertex) returns {bone: share}."""
    groups = {}
    for v in obj.data.vertices:
        for bone, share in weights_of(v).items():
            if bone not in groups:
                groups[bone] = obj.vertex_groups.new(name=bone)
            groups[bone].add([v.index], share, 'REPLACE')


def cape_centre_y(t):
    """Distance behind the spine line of the cloth's centre line; t = 0 at the top, 1 at the hem."""
    c = CAPE
    blade_t = (c["TOP_Z"] - c["BLADE_Z"]) / (c["TOP_Z"] - c["HEM_Z"])
    if t < blade_t:
        s = t / blade_t
        return c["NECK_Y"] + (c["BLADE_Y"] - c["NECK_Y"]) * s * s * (3 - 2 * s)
    return c["BLADE_Y"] + (c["HEM_Y"] - c["BLADE_Y"]) * (t - blade_t) / (1 - blade_t)


def cape_half_width(t):
    c = CAPE
    return (c["HALF_WIDTH_TOP"] + (c["HALF_WIDTH_HEM"] - c["HALF_WIDTH_TOP"]) * t ** 0.6) * (1 - 0.06 * t)


def cape_inner_y(x, z):
    """The furthest back a point at (x, z) may be and still be in front of the cape's lining,
    whatever fold it sits under. None where the cape does not cover (beside, above or below it)."""
    c = CAPE
    worst = None
    for u in (0.0, 1.0):   # the top edge is lower at the sides, so t differs across the width
        top = c["TOP_Z"] - c["TOP_DROP"] * u * u
        if z > top + c["COLLAR"][-1][1] or z < c["HEM_Z"]:
            continue
        t = max(0.0, (top - z) / (top - c["HEM_Z"]))
        if abs(x) > cape_half_width(t) + 0.02:
            continue
        y = cape_centre_y(t) - c["WRAP"] * t - (c["FOLD_DEPTH_TOP"] + (c["FOLD_DEPTH_HEM"] - c["FOLD_DEPTH_TOP"]) * t) - c["THICKNESS"]
        if z > top:
            y -= c["COLLAR"][-1][0]
        worst = y if worst is None else min(worst, y)
    return worst

def require_addon():
    if not hasattr(bpy.ops.a3ob, "export_p3d"):
        raise SystemExit("Arma 3 Object Builder add-on is not enabled in Blender")


def new_scene():
    bpy.ops.wm.read_homefile(use_empty=True)  # keeps the user's enabled add-ons


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


def add_copy(obj, lod, resolution=1):
    copy = obj.a3ob_properties_object.copies.add()
    copy.lod = lod
    copy.resolution = resolution


def new_mesh_object(name, verts=(), faces=()):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(list(verts), [], list(faces))
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def worn_geometry(name):
    """Character-attached models must not be re-centred by the engine."""
    geo = new_mesh_object(name)
    mark_lod(geo, LOD_GEOMETRY, 1, properties=(("autocenter", "0"),))
    return geo


def ground_geometry(name, mn, mx, mass_kg):
    """Box collision shape with mass; also used as the view and fire geometry."""
    x0, y0, z0 = mn
    x1, y1, z1 = mx
    geo = new_mesh_object(name, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                 (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
                          [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    mark_lod(geo, LOD_GEOMETRY, 1, properties=(("autocenter", "0"),))
    geo.vertex_groups.new(name="Component01").add(range(8), 1.0, 'REPLACE')
    bm = bmesh.new()
    bm.from_mesh(geo.data)
    layer = bm.verts.layers.float.new("a3ob_mass")
    for v in bm.verts:
        v[layer] = mass_kg / 8
    bm.to_mesh(geo.data)
    bm.free()
    for lod in (LOD_VIEW_GEOMETRY, LOD_FIRE_GEOMETRY):
        add_copy(geo, lod)
    return geo


def add_lower_lods(full_obj, name, ratios):
    """Add reduced copies of a finished LOD 1 object. ratios: (resolution, share of the full
    triangle count, "collapse" or "cluster"). Collapse is Blender's edge-collapse decimator;
    cluster merges all vertices closer than a distance searched to hit the target, which is
    cruder but has no floor. Vertex groups (bone weights) and UVs survive both."""
    full = len(full_obj.data.polygons)

    def clustered(source, distance):
        bm = bmesh.new()
        bm.from_mesh(source)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        return bm

    for resolution, ratio, method in ratios:
        obj = full_obj.copy()
        obj.data = full_obj.data.copy()
        obj.name = "%s_lod%d" % (name, resolution)
        bpy.context.scene.collection.objects.link(obj)
        props = obj.a3ob_properties_object
        props.resolution = resolution
        props.copies.clear()

        weld = 1e-4
        if method == "cluster":
            low, high = 1e-4, 1.0
            for _ in range(20):
                weld = (low + high) / 2
                trial = clustered(full_obj.data, weld)
                count = len(trial.faces)
                trial.free()
                if count > ratio * full:
                    low = weld
                else:
                    high = weld
            weld = high
        bm = clustered(full_obj.data, weld)
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
        for polygon in obj.data.polygons:
            polygon.use_smooth = method == "collapse"
        obj.data.update()
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        print("LOD", obj.name, method, "triangles", tris, "of", full)


def export(path):
    # The exporter switches to object mode first, which needs an active object.
    bpy.context.view_layer.objects.active = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    bpy.ops.a3ob.export_p3d(filepath=path, relative_paths=True, apply_transforms=True,
                            apply_modifiers=True, lod_collisions='FAIL')
    print("EXPORTED", path, os.path.getsize(path))
