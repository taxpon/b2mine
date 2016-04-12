import os
import sys
import time

import bpy
from bpy.props import *
import bmesh
from mathutils import bvhtree as bvh
from mathutils.kdtree import KDTree
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Manager

from functools import wraps

from . import block_def
from .block_def import BlockDef

from mathutils import Vector

if "BlockDef" in locals():
    import importlib
    importlib.reload(block_def)


def elapsed(func):
    @wraps(func)
    def _elapsed(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()

        print("Elapsed ({}) = {} [milliseconds]".format(
            func.__name__,
            (end - start) * 1000
        ))
        return result
    return _elapsed


class BlockInfo(object):

    def __init__(self, has_block, block_type, color=None):
        """
        :param bool has_block:
        :param int block_type:
        """
        self._has_block = has_block
        self._block_type = block_type
        self._color = color

    def update(self, has_block, block_type, color=None):
        self._has_block = has_block
        self._block_type = block_type
        self._color = color

    def to_dict(self):
        return {
            "has_block": self._has_block,
            "block_type": self._block_type
        }

    @property
    def has_block(self):
        return self._has_block

    @property
    def block_type(self):
        return self._block_type

    @property
    def color(self):
        return self._color


class Converter(object):

    TARGET_NUM_FACET = 2000
    DEFAULT_OCTREE = 3

    def __init__(self, src):
        self.src = src
        self.decimated = None
        self.src_kd = None
        self.voxel_list = Manager().list()
        self.mesh_list = Manager().list()
        self.queue = Queue()
        self.color_dict = {}
        self.parent = None
        self.block_map = []
        self.unit = None

        # Initial procedure
        self.__calc_decimated()
        self.__build_src_kd()
        self.__create_color_dict()

    @elapsed
    def __calc_decimated(self):
        num_facet = len(self.src.data.polygons)
        ratio = float(Converter.TARGET_NUM_FACET) / float(num_facet)

        mesh = bpy.data.meshes.new("Decimated")
        self.decimated = bpy.data.objects.new("Decimated", mesh)
        self.decimated.data = self.src.data.copy()
        self.decimated.scale = self.src.scale
        self.decimated.location = self.src.location

        bpy.context.scene.objects.link(self.decimated)
        self.decimated.select = True

        self.decimated.modifiers.new("Decimate", "DECIMATE")
        self.decimated.modifiers["Decimate"].ratio = ratio
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier="DECIMATE")

    def __build_src_kd(self):
        mesh = self.decimated.data
        size = len(mesh.vertices)
        self.src_kd = KDTree(size)

        for i, v in enumerate(mesh.vertices):
            self.src_kd.insert(v.co, i)
        self.src_kd.balance()

    def __create_color_dict(self):
        for i, loop in enumerate(self.decimated.data.loops):
            vi = loop.vertex_index
            if vi not in self.color_dict:
                self.color_dict[vi] = i

    def cleanup(self):
        bpy.context.scene.objects.unlink(self.decimated)

    @staticmethod
    def create_new_octree(box):
        box0 = (
            box[0],
            (box[0] + box[1])/2.0,
            (box[0] + box[2])/2.0,
            (box[0] + box[3])/2.0,
            (box[0] + box[4])/2.0,
            (box[0] + box[5])/2.0,
            (box[0] + box[6])/2.0,
            (box[0] + box[7])/2.0,
        )

        box1 = (
            # Left side
            (box[0] + box[1])/2.0,
            box[1],
            (box[1] + box[2])/2.0,
            (box[0] + box[2])/2.0,
            # Right side
            (box[0] + box[5])/2.0,
            (box[1] + box[5])/2.0,
            (box[1] + box[6])/2.0,
            (box[0] + box[6])/2.0,
        )

        box2 = (
            # Left side
            (box[0] + box[2])/2.0,
            (box[1] + box[2])/2.0,
            box[2],
            (box[2] + box[3])/2.0,
            # Right side
            (box[0] + box[6])/2.0,
            (box[1] + box[6])/2.0,
            (box[2] + box[6])/2.0,
            (box[3] + box[6])/2.0
        )

        box3 = (
            # Left side
            (box[0] + box[3])/2.0,
            (box[0] + box[2])/2.0,
            (box[2] + box[3])/2.0,
            box[3],
            # Right side
            (box[0] + box[7])/2.0,
            (box[0] + box[6])/2.0,
            (box[3] + box[6])/2.0,
            (box[3] + box[7])/2.0,
        )

        box4 = (
            # Left side
            (box[0] + box[4])/2.0,
            (box[0] + box[5])/2.0,
            (box[0] + box[6])/2.0,
            (box[0] + box[7])/2.0,
            # Right side
            box[4],
            (box[4] + box[5])/2.0,
            (box[4] + box[6])/2.0,
            (box[4] + box[7])/2.0,
        )

        box5 = (
            # Left side
            (box[0] + box[5])/2.0,
            (box[1] + box[5])/2.0,
            (box[1] + box[6])/2.0,
            (box[0] + box[6])/2.0,
            # Right side
            (box[4] + box[5])/2.0,
            box[5],
            (box[5] + box[6])/2.0,
            (box[4] + box[6])/2.0,
        )

        box6 = (
            # Left side
            (box[0] + box[6])/2.0,
            (box[1] + box[6])/2.0,
            (box[2] + box[6])/2.0,
            (box[3] + box[6])/2.0,
            # Right side
            (box[4] + box[6])/2.0,
            (box[5] + box[6])/2.0,
            box[6],
            (box[6] + box[7])/2.0,
        )

        box7 = (
            # Left side
            (box[0] + box[7])/2.0,
            (box[0] + box[6])/2.0,
            (box[3] + box[6])/2.0,
            (box[3] + box[7])/2.0,
            # Right side
            (box[4] + box[7])/2.0,
            (box[4] + box[6])/2.0,
            (box[6] + box[7])/2.0,
            box[7],
        )
        return box0, box1, box2, box3, box4, box5, box6, box7

    @staticmethod
    def get_bvhtree_from_box(box):
        mesh_data = bpy.data.meshes.new("cube_mesh_data")
        faces = [(0, 1, 2, 3),
                 (4, 7, 6, 5),
                 (0, 4, 5, 1),
                 (1, 5, 6, 2),
                 (2, 3, 7, 6),
                 (4, 0, 3, 7)]
        mesh_data.from_pydata([x.to_tuple() for x in box], [], faces)
        mesh_data.update()
        bm = bmesh.new()
        bm.from_mesh(mesh_data)
        return bvh.BVHTree.FromBMesh(bm)

    @staticmethod
    def check_if_overlap(obj, box):
        bvh_tree1 = bvh.BVHTree.FromObject(obj, bpy.context.scene)
        bvh_tree2 = Converter.get_bvhtree_from_box(box)
        return bvh_tree1.overlap(bvh_tree2)

    def invoke(self, obj, box, max_depth):
        try:
            self.invoke_create_voxel(obj, box, max_depth)
            self.draw_voxel(origin=box[0])
        finally:
            # Post procedure
            self.cleanup()
            return self.block_map

    @elapsed
    def invoke_create_voxel(self, obj, box, max_depth):
        # Create block map
        for z in range(2 ** max_depth):
            self.block_map.append([])
            for y in range(2 ** max_depth):
                self.block_map[z].append([])
                for x in range(2 ** max_depth):
                    self.block_map[z][y].append(BlockInfo(False, 1))

        # Calc unit length
        self.unit = (box[1].z - box[0].z) / float(2 ** max_depth)
        print("Unit length:{}", self.unit)

        overlap = Converter.check_if_overlap(obj, box)
        if overlap:
            boxes = Converter.create_new_octree(box)
            jobs = []
            for child in boxes:
                p = Process(
                    target=self.create_voxel,
                    args=(obj, child, 1, self.voxel_list, max_depth)
                )
                jobs.append(p)
                p.start()

            [job.join() for job in jobs]

    def create_voxel(self, obj, box, depth, queue, max_depth=3):
        depth += 1

        overlap = Converter.check_if_overlap(obj, box)
        if overlap:
            if depth == max_depth:
                queue.append([x.to_tuple() for x in box])
            else:
                boxes = Converter.create_new_octree(box)
                for _child in boxes:
                    self.create_voxel(obj, _child, depth, queue, max_depth)

    def calc_mesh_and_color(self, voxel_list, mesh_list):
        faces = ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                 (1, 5, 6, 2), (2, 3, 7, 6), (4, 0, 3, 7))

        for i, voxel in enumerate(voxel_list):
            mesh = bpy.data.meshes.new("cube_mesh_data")
            mesh.from_pydata(voxel, [], faces)
            mesh.update()

            # Find closest color
            co, index, dist = self.src_kd.find(voxel[0])
            if self.decimated.data.vertex_colors:
                rgb = self.decimated.data.vertex_colors["Col"].data[self.color_dict[index]].color
            else:
                rgb = (1.0, 1.0, 1.0)  # White

            mesh_list.append((voxel, tuple(rgb)))

    @elapsed
    def draw_voxel(self, origin):
        # Add null object
        self.parent = bpy.data.objects.new("Voxcel", bpy.data.meshes.new("Voxcel"))
        bpy.context.scene.objects.link(self.parent)

        faces = ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                 (1, 5, 6, 2), (2, 3, 7, 6), (4, 0, 3, 7))

        def chunks(l, n):
            """Yield successive n-sized chunks from l."""
            for i in range(0, len(l), n):
                yield l[i:i+n]

        parallels = 8
        chunk_list = chunks(
            self.voxel_list,
            len(self.voxel_list)//parallels
        )

        jobs = []
        for chunk in chunk_list:
            p = Process(
                target=self.calc_mesh_and_color,
                args=(chunk, self.mesh_list)
            )
            jobs.append(p)
            p.start()

        [job.join() for job in jobs]

        for i, item in enumerate(self.mesh_list):
            voxel = item[0]
            rgb = item[1]
            obj_name = "Cube.%06d" % i
            mesh = bpy.data.meshes.new("cube_mesh_data")
            mesh.from_pydata(voxel, [], faces)
            mesh.update()

            mesh.vertex_colors.new()
            j = 0
            for poly in mesh.polygons:
                for idx in poly.loop_indices:
                    mesh.vertex_colors["Col"].data[j].color = rgb
                    j += 1

            cube_object = bpy.data.objects.new(obj_name, mesh)
            bpy.context.scene.objects.link(cube_object)
            cube_object.select = True
            cube_object.parent = self.parent

            # Update block map
            ix = int(round((voxel[0][0] - origin.x) / self.unit))
            iy = int(round((voxel[0][1] - origin.y) / self.unit))
            iz = int(round((voxel[0][2] - origin.z) / self.unit))
            # print(ix, iy, iz)

            col_def = BlockDef.find_nearest_color_block(Vector(rgb))
            self.block_map[iz][iy][ix].update(True, col_def.block_def[0], col_def.block_def[1])
            # print(i, self.block_map[iz][iy][ix].to_dict())

