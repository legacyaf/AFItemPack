"""Check that the worn vest pack and the worn cape do not intersect.

    blender -b --python tools/check_cape_clearance.py -- <repo root>

Loads every visual LOD of both models from tools/blend (written by the build scripts) and
tests the triangles of each vest pack LOD against every LOD of the cape. Prints where any
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
cape_trees = {name: BVHTree.FromPolygons(*cape[name]) for name in sorted(cape)}
bad = 0
for name in sorted(vest):
    verts, polys = vest[name]
    tree = BVHTree.FromPolygons(verts, polys)
    touching = []
    for cape_name, cape_tree in cape_trees.items():
        pairs = tree.overlap(cape_tree)
        if not pairs:
            continue
        bad += len(pairs)
        centres = [sum((verts[i] for i in polys[a]), Vector()) / len(polys[a]) for a, _ in pairs]
        lo = Vector((min(c.x for c in centres), min(c.y for c in centres), min(c.z for c in centres)))
        hi = Vector((max(c.x for c in centres), max(c.y for c in centres), max(c.z for c in centres)))
        touching.append(cape_name)
        print("OVERLAP", name, "with", cape_name, len(pairs), "triangle pairs, between",
              tuple(round(v, 3) for v in lo), "and", tuple(round(v, 3) for v in hi))
    if not touching:
        print("CLEAR", name, "does not touch any of the cape's", len(cape_trees), "LODs")
if bad:
    raise SystemExit("the vest pack intersects the cape")