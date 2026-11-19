"""Check that the worn vest pack and the worn cape do not intersect.

    blender -b --python tools/check_cape_clearance.py -- <repo root>

Loads every visual LOD of both models from tools/blend (written by the build scripts) and
tests the triangles of each vest pack LOD against the cape's LOD 1. Prints where any
intersections are and exits with an error if there are some.
"""
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

repo = sys.argv[sys.argv.index("--") + 1]
blend_dir = os.path.join(repo, "tools", "blend")


def lods(blend, prefix):
    with bpy.data.libraries.load(os.path.join(blend_dir, blend)) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(prefix)]
    out = {}
    for obj in dst.objects:
        verts = [obj.matrix_world @ v.co for v in obj.data.vertices]
        out[obj.name] = (verts, [tuple(p.vertices) for p in obj.data.polygons])
    return out


cape = lods("cape_worn.blend", "cape_worn_lod")
vest = lods("vestpack_worn.blend", "vestpack_worn_lod")
cape_verts, cape_polys = cape["cape_worn_lod1"]
cape_tree = BVHTree.FromPolygons(cape_verts, cape_polys)
bad = 0
for name in sorted(vest):
    verts, polys = vest[name]
    pairs = BVHTree.FromPolygons(verts, polys).overlap(cape_tree)
    if not pairs:
        print("CLEAR", name, "does not touch the cape")
        continue
    bad += len(pairs)
    centres = [sum((verts[i] for i in polys[a]), Vector()) / len(polys[a]) for a, _ in pairs]
    lo = Vector((min(c.x for c in centres), min(c.y for c in centres), min(c.z for c in centres)))
    hi = Vector((max(c.x for c in centres), max(c.y for c in centres), max(c.z for c in centres)))
    print("OVERLAP", name, len(pairs), "triangle pairs, between", tuple(round(v, 3) for v in lo), "and", tuple(round(v, 3) for v in hi))
if bad:
    raise SystemExit("the vest pack intersects the cape")
