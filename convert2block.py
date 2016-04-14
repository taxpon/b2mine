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

from . import voxel
from . import block_def
from .block_def import BlockDef

from mathutils import Vector

if "BlockDef" in locals():
    import importlib
    importlib.reload(block_def)
    importlib.reload(voxel)


elapsed_indent = 0


def elapsed(func):

    @wraps(func)
    def __elapsed(*args, **kwargs):
        global elapsed_indent
        print("{}Start ({})".format(
            "    " * elapsed_indent,
            func.__name__
        ))
        elapsed_indent += 1
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        elapsed_indent -= 1

        print("{}End   ({}) = {} [milliseconds]".format(
            "    " * elapsed_indent,
            func.__name__,
            (end - start) * 1000
        ))
        return result
    return __elapsed


class BlockInfo(object):

    def __init__(self, has_block, block_type, color=None, pos=None):
        """
        :param bool has_block:
        :param int block_type:
        """
        self._has_block = has_block
        self._block_type = block_type
        self._color = color
        self._pos = pos

    def update(self, has_block, block_type, color=None, pos=None):
        self._has_block = has_block
        self._block_type = block_type
        self._color = color
        self._pos = pos

    def to_dict(self):
        return {
            "has_block": self._has_block,
            "block_type": self._block_type,
            "color": self._color,
            "pos": self._pos
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

    @property
    def pos(self):
        return self._pos


class Converter(object):

    TARGET_NUM_FACET = 2000
    DEFAULT_OCTREE = 3

    @elapsed
    def __init__(self, src):
        self.src = src
        self.decimated = None
        self.src_kd = None
        self.voxel_list = Manager().list()
        self.mesh_list = Manager().list()
        self.color_dict = {}
        self.parent = None
        self.block_map = Manager().list()
        self.unit = None
        self.join = True

        # Initial procedure
        self.__calc_decimated()
        self.__build_src_kd()
        self.__create_color_dict()
        bpy.ops.object.select_all(action="DESELECT")

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

    @elapsed
    def __build_src_kd(self):
        mesh = self.decimated.data
        size = len(mesh.vertices)
        self.src_kd = KDTree(size)

        for i, v in enumerate(mesh.vertices):
            self.src_kd.insert(v.co, i)
        self.src_kd.balance()

    @elapsed
    def __create_color_dict(self):
        for i, loop in enumerate(self.decimated.data.loops):
            vi = loop.vertex_index
            if vi not in self.color_dict:
                self.color_dict[vi] = i

    @elapsed
    def apply_join(self):
        if self.join:
            bpy.ops.object.join()

    @elapsed
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

    @elapsed
    def invoke(self, obj, box, max_depth):
        try:
            self.invoke_create_voxel(obj, box, max_depth)
            self.draw_voxel(origin=box[0])
        finally:
            # Post procedure
            self.apply_join()
            self.cleanup()
            return list(self.block_map)

    @elapsed
    def invoke_create_voxel(self, obj, box, max_depth):
        # Calc unit length
        self.unit = (box[1].z - box[0].z) / float(2 ** max_depth)

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
        """For multiprocessing
        :param obj:
        :param box:
        :param depth:
        :param queue:
        :param max_depth:
        :return:
        """
        depth += 1

        overlap = Converter.check_if_overlap(obj, box)
        if overlap:
            if depth == max_depth:
                queue.append([x.to_tuple() for x in box])
            else:
                boxes = Converter.create_new_octree(box)
                for _child in boxes:
                    self.create_voxel(obj, _child, depth, queue, max_depth)

    def calc_mesh_and_color(self, voxel_list, mesh_list, block_list, origin):
        """For multiprocessing
        :param list voxel_list:
        :param list mesh_list:
        :param list block_list:
        :param mathutils.Vector origin:
        """
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

            ix = int(round((voxel[0][0] - origin.x) / self.unit))
            iy = int(round((voxel[0][1] - origin.y) / self.unit))
            iz = int(round((voxel[0][2] - origin.z) / self.unit))
            col_def = BlockDef.find_nearest_color_block(Vector(rgb))

            block_list.append(BlockInfo(
                has_block=True,
                block_type=col_def.block_def[0],
                color=col_def.block_def[1],
                pos=(ix, iy, iz)
            ))

    @elapsed
    def draw_voxel(self, origin):
        # Add null object
        self.parent = bpy.data.objects.new("Voxcel", bpy.data.meshes.new("Voxcel"))
        bpy.context.scene.objects.link(self.parent)
        bpy.context.scene.objects.active = self.parent
        self.parent.select = True

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
            job = Process(
                target=self.calc_mesh_and_color,
                args=(chunk, self.mesh_list, self.block_map, origin)
            )
            jobs.append(job)
            job.start()

        [job.join() for job in jobs]

        @elapsed
        def add_voxels():
            for i, item in enumerate(self.mesh_list):
                vertices = item[0]
                color = item[1]
                name = "Cube.%010d" % i

                voxel.Voxel(name, vertices, color).create().add(
                    scene=bpy.context.scene,
                    parent=self.parent
                )

        add_voxels()
