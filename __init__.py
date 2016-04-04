import os
import sys
import time

import bpy
import bmesh
from mathutils import Vector
from mathutils import bvhtree as bvh
from mathutils.kdtree import KDTree
import mathutils.geometry as mg
from multiprocessing import Process
from multiprocessing import Pool
from multiprocessing import Queue
from multiprocessing import Lock
from multiprocessing import Array
from multiprocessing import Manager

sys.path.append(os.path.dirname(__file__))

import mcpi.minecraft as minecraft
import mcpi.block as block

bl_info = {
    "name": "Blender2Minecraft",
    "category": "Object",
}


class Converter(object):

    TARGET_NUM_FACET = 2000

    def __init__(self, src):
        self.src = src
        self.decimated = None
        self.src_kd = None
        self.voxel_list = []
        self.voxel_list2 = Manager().list()
        self.queue = Queue()
        self.lock = Lock()
        self.color_dict = {}

        # Initial procedure
        self.__calc_decimated()
        self.__build_src_kd()
        self.__create_color_dict()

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

    def __post_procedure(self):
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

    def invoke_create_voxel(self, obj, box, max_depth):
        overlap = Converter.check_if_overlap(obj, box)
        if overlap:
            boxes = Converter.create_new_octree(box)
            jobs = []
            for child in boxes:
                p = Process(
                    target=self.create_voxel,
                    args=(obj, child, 1, self.voxel_list2, max_depth)
                )
                jobs.append(p)
                p.start()

            [job.join() for job in jobs]
            # self.queue.close()
            # self.queue.join_thread()

    def create_voxel(self, obj, box, depth, queue, max_depth=3):
        depth += 1

        overlap = Converter.check_if_overlap(obj, box)
        # overlap = True
        if overlap:
            if depth == max_depth:
                # lock.acquire()
                # print(box)
                # vl.append(box)
                # lock.release()
                # print(box.__class__)
                # queue.put([x.to_tuple() for x in box])
                queue.append([x.to_tuple() for x in box])

                # q.put(q.get().append(box))
                # self.queue.put(self.queue.get().append(box))
                # print(queue.__class__)
                # print("Inside of Queue: ", queue.get())
                # queue.put(queue.get().append(box))
            else:
                boxes = Converter.create_new_octree(box)
                for _child in boxes:
                    self.create_voxel(obj, _child, depth, queue, max_depth)

    def draw_voxel(self):
        # Add null object
        e = bpy.data.objects.new("Empty", bpy.data.meshes.new("Empty"))
        bpy.context.scene.objects.link(e)

        faces = ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                 (1, 5, 6, 2), (2, 3, 7, 6), (4, 0, 3, 7))
        for i, voxel in enumerate(self.voxel_list2):
            obj_name = "Cube.%06d" % i
            # print("  {}".format(obj_name))

            start = time.time()
            mesh = bpy.data.meshes.new("cube_mesh_data")
            mesh.from_pydata(voxel, [], faces)
            mesh.update()
            end = time.time()
            # print("    Elapsed time (Create box mesh): {}[milliseconds]".format((end - start) * 1000))

            # Find closest color
            # method1
            # total = Vector()
            # for vec in [Vector(x) for x in voxel]:
            #     total += vec
            # average = total / 8.0
            # co, index, dist = self.src_kd.find(average.to_tuple())

            # method2
            start = time.time()
            co, index, dist = self.src_kd.find(voxel[0])

            # loop_index = 0
            # for i, loop in enumerate(self.decimated.data.loops):
            #     if loop.vertex_index == index:
            #         loop_index = i
            #         break

            rgb = self.decimated.data.vertex_colors["Col"].data[self.color_dict[index]].color
            end = time.time()
            # print("    Elapsed time (Find color): {}[milliseconds]".format((end - start) * 1000))

            # Paint with specified color
            start = time.time()
            mesh.vertex_colors.new()
            i = 0
            for poly in mesh.polygons:
                for idx in poly.loop_indices:
                    mesh.vertex_colors["Col"].data[i].color = rgb
                    i += 1
            end = time.time()
            # print("    Elapsed time (Apply color): {}[milliseconds]".format((end - start) * 1000))

            start = time.time()
            cube_object = bpy.data.objects.new(obj_name, mesh)
            bpy.context.scene.objects.link(cube_object)
            cube_object.select = True
            cube_object.parent = e
            end = time.time()
            # print("    Elapsed time (Add object): {}[milliseconds]".format((end - start) * 1000))

        # Post procedure
        self.__post_procedure()


class MineManager(object):

    def __init__(self):
        self.mc = None

    def connect(self):
        self.mc = minecraft.Minecraft.create()

    def get_pos(self):
        return self.mc.player.getPos()

    def set_block(self):
        pos = self.mc.player.getPos()
        self.mc.setBlock(pos.x, pos.y + 1, pos.z + 1, block.STONE)

mm = MineManager()


class MineConnectOperator(bpy.types.Operator):
    bl_idname = "ws_takuro.mine_connect"
    bl_label = "Connect"

    def execute(self, context):
        mm.connect()
        print("Connected")
        return {"FINISHED"}


class MineGetPosOperator(bpy.types.Operator):
    bl_idname = "ws_takuro.mine_get_pos"
    bl_label = "getPos"

    def execute(self, context):
        print(mm.get_pos())
        return {"FINISHED"}


class MineSetBlockOperator(bpy.types.Operator):
    bl_idname = "ws_takuro.mine_set_block"
    bl_label = "setBlock"

    def execute(self, context):
        mm.set_block()
        return {"FINISHED"}


class Convert2BlockOperator(bpy.types.Operator):
    bl_idname = "ws_takuro.convert2block"
    bl_label = 'Convert to Block'

    def execute(self, context):
        obj = context.active_object
        # obj.modifiers.new("Triangulate", "TRIANGULATE")
        # bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Triangulate")

        u = max(obj.dimensions)/2.0
        total = Vector()
        for vec in [Vector(x) for x in obj.bound_box]:
            total += vec

        average = total / 8.0

        # initial_bb = [Vector(x) for x in obj.bound_box]

        initial_bb = [
            Vector((-u, -u, -u)) + average,
            Vector((-u, -u, u)) + average,
            Vector((-u, u, u)) + average,
            Vector((-u, u, -u)) + average,
            Vector((u, -u, -u)) + average,
            Vector((u, -u, u)) + average,
            Vector((u, u, u)) + average,
            Vector((u, u, -u)) + average
        ]

        cvt = Converter(obj)
        # return {"FINISHED"}

        import time
        start = time.time()
        cvt.invoke_create_voxel(cvt.decimated, initial_bb, 7)
        end = time.time()
        print("Elapsed time (Create Voxel): {}[milliseconds]".format((end - start) * 1000))

        start = time.time()
        cvt.draw_voxel()
        end = time.time()
        print("Elapsed time (Draw Voxel): {}[milliseconds]".format((end - start) * 1000))

        return {"FINISHED"}


class B2MinePanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "B2Mine"
    bl_idname = "OBJECT_PT_b2mine"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        row = layout.row()
        row.operator("ws_takuro.mine_connect")

        row = layout.row()
        row.operator("ws_takuro.mine_get_pos")

        row = layout.row()
        row.operator("ws_takuro.mine_set_block")

        row = layout.row()
        row.operator("ws_takuro.convert2block")
        # self.start_server()

    def start_server(self):
        mc = minecraft.Minecraft.create()
        pos = mc.player.getPos()
        print(pos)
        pass


def register():
    bpy.utils.register_class(MineConnectOperator)
    bpy.utils.register_class(MineGetPosOperator)
    bpy.utils.register_class(MineSetBlockOperator)
    bpy.utils.register_class(Convert2BlockOperator)
    bpy.utils.register_class(B2MinePanel)


def unregister():
    bpy.utils.unregister_class(MineConnectOperator)
    bpy.utils.unregister_class(MineGetPosOperator)
    bpy.utils.unregister_class(MineSetBlockOperator)
    bpy.utils.unregister_class(Convert2BlockOperator)
    bpy.utils.unregister_class(B2MinePanel)

# bpy.utils.register_module(__name__)
#
if __name__ == "__main__":
    register()
