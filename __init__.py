# -*- coding: utf-8 -*-
import os
import sys
import time

if "bpy" in locals():
    import importlib
    importlib.reload(convert2block)
    importlib.reload(mcpi)
    print("Reloaded multifiles")
else:
    from . import convert2block
    from .mcpi import minecraft
    from .mcpi import block
    print("Imported multifiles")

import bpy  # noqa
from bpy.props import *  # noqa
from mathutils import Vector  # noqa

# sys.path.append(os.path.dirname(__file__))
# import mcpi.minecraft as minecraft  # noqa
# import mcpi.block as block  # noqa

bl_info = {
    "name": "Blender2Minecraft",
    "category": "Object",
}


block_map = None


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

    def set_bunch_of_blocks(self):
        global block_map
        pos = self.mc.player.getPos()
        for z in range(len(block_map)):
            for y in range(len(block_map[0])):
                for x in range(len(block_map[0][0])):
                    this_block = block_map[z][y][x]
                    if this_block.has_block:
                        if this_block.color:
                            self.mc.setBlock(
                                pos.x + x/2.0,
                                pos.y + y/2.0,
                                pos.z + z/2.0,
                                this_block.block_type,
                                this_block.color
                            )
                        else:
                            self.mc.setBlock(
                                pos.x + x/2.0,
                                pos.y + y/2.0,
                                pos.z + z/2.0,
                                this_block.block_type
                            )
                        print(x/2.0, y/2.0, z/2.0, this_block.block_type, this_block.color)




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


class MineSetMultipleBlocksOperator(bpy.types.Operator):
    bl_idname = "ws_takuro.mine_set_multiple_blocks"
    bl_label = "setMultiBlocks"

    def execute(self, context):
        mm.set_bunch_of_blocks()
        return {"FINISHED"}


class Convert2BlockOperator(bpy.types.Operator):
    bl_idname = "ws_takuro.convert2block"
    bl_label = 'Convert to Block'

    def execute(self, context):
        context.scene['NumOctree'] = 3

        obj = context.active_object
        scene = context.scene
        # obj.modifiers.new("Triangulate", "TRIANGULATE")
        # bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Triangulate")

        u = max(obj.dimensions)/2.0
        total = Vector()
        for vec in [Vector(x) for x in obj.bound_box]:
            total += vec

        average = total / 8.0

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
        cvt = convert2block.Converter(obj)
        octree = obj["Octree"] if "Octree" in obj else convert2block.Converter.DEFAULT_OCTREE

        global block_map
        block_map = cvt.invoke(cvt.decimated, initial_bb, octree)

        return {"FINISHED"}


class B2MinePanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "B2Mine"
    bl_idname = "OBJECT_PT_b2mine"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    INITIALIZED = False

    def draw(self, context):
        layout = self.layout

        obj = context.object
        row = layout.row()
        row.prop(obj, "Octree")
        row.operator("ws_takuro.convert2block")

        row = layout.row()
        row.operator("ws_takuro.mine_connect")
        row.operator("ws_takuro.mine_get_pos")

        row = layout.row()
        row.operator("ws_takuro.mine_set_block")

        row = layout.row()
        row.operator("ws_takuro.mine_set_multiple_blocks")

    def start_server(self):
        mc = minecraft.Minecraft.create()
        pos = mc.player.getPos()
        print(pos)
        pass


def register():
    bpy.types.Object.Octree = IntProperty(
        name="Octree",
        description="Enter an integer",
        min=1,
        max=99,
        default=3
    )

    bpy.utils.register_class(MineConnectOperator)
    bpy.utils.register_class(MineGetPosOperator)
    bpy.utils.register_class(MineSetBlockOperator)
    bpy.utils.register_class(MineSetMultipleBlocksOperator)

    bpy.utils.register_class(Convert2BlockOperator)
    bpy.utils.register_class(B2MinePanel)


def unregister():
    bpy.utils.unregister_class(MineConnectOperator)
    bpy.utils.unregister_class(MineGetPosOperator)
    bpy.utils.unregister_class(MineSetBlockOperator)
    bpy.utils.unregister_class(MineSetMultipleBlocksOperator)
    bpy.utils.unregister_class(Convert2BlockOperator)
    bpy.utils.unregister_class(B2MinePanel)

# bpy.utils.register_module(__name__)

if __name__ == "__main__":
    register()
