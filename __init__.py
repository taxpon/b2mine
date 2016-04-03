import os
import sys
import time

import bpy
import bmesh
from mathutils import Vector
from mathutils import bvhtree as bvh
import mathutils.geometry as mg

sys.path.append(os.path.dirname(__file__))

import mcpi.minecraft as minecraft
import mcpi.block as block

bl_info = {
    "name": "Blender2Minecraft",
    "category": "Object",
}


class Converter(object):

    def __init__(self):
        self.voxel_list = []

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

    def create_voxel(self, obj, box, depth, max_depth=3):
        depth += 1
        overlap = Converter.check_if_overlap(obj, box)
        if overlap:
            if depth == max_depth:
                self.voxel_list.append(box)
            else:
                boxes = Converter.create_new_octree(box)
                for _child in boxes:
                    self.create_voxel(obj, _child, depth, max_depth)

    def draw_voxel(self):
        # Add null object
        e = bpy.data.objects.new("Empty", bpy.data.meshes.new("Empty"))
        bpy.context.scene.objects.link(e)

        for i, voxel in enumerate(self.voxel_list):
            obj_name = "Cube.%03d" % i

            mesh_data = bpy.data.meshes.new("cube_mesh_data")
            faces = [(0, 1, 2, 3),
                     (4, 7, 6, 5),
                     (0, 4, 5, 1),
                     (1, 5, 6, 2),
                     (2, 3, 7, 6),
                     (4, 0, 3, 7)]
            mesh_data.from_pydata([x.to_tuple() for x in voxel], [], faces)
            mesh_data.update()

            cube_object = bpy.data.objects.new(obj_name, mesh_data)
            bpy.context.scene.objects.link(cube_object)
            cube_object.select = True
            cube_object.parent = e


class MineManager(object):

    # _instance = None
    #
    # def __new__(cls, *args, **kwargs):
    #     if not cls._instance:
    #         cls._instance = super(MineManager, cls).__new__(cls, *args, **kwargs)
    #     return cls._instance

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
        obj.modifiers.new("Triangulate", "TRIANGULATE")
        bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Triangulate")

        initial_bb = [Vector(x) for x in obj.bound_box]
        cvt = Converter()
        cvt.create_voxel(obj, initial_bb, 0, 4)
        cvt.draw_voxel()
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
