# -*- coding: utf-8 -*-
import pickle

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


bl_info = {
    "name": "Blender2Minecraft",
    'author': 'Takuro Wada',
    'version': (0, 1, 0),
    'blender': (2, 76, 0),
    'description': 'Blender add-on to convert object with into colored blocks and transfer it to minecraft',
    'tracker_url': 'https://github.com/taxpon/b2mine',
    'support': 'COMMUNITY',
    'category': 'Object'
}


class Global(object):
    ID_BLOCK_MAP = "block_map"


class MineManager(object):

    def __init__(self):
        self.mc = None
        self.connected = False

    def connect(self):
        self.mc = minecraft.Minecraft.create()

    def get_pos(self):
        return self.mc.player.getPos()

    def set_block(self):
        pos = self.mc.player.getPos()
        self.mc.setBlock(pos.x, pos.y + 1, pos.z + 1, block.STONE)

    def set_bunch_of_blocks(self):

        obj = bpy.context.active_object
        if Global.ID_BLOCK_MAP not in obj:
            raise Exception("No block data")

        block_map = pickle.loads(obj[Global.ID_BLOCK_MAP])

        pos = self.mc.player.getPos()
        for this_block in block_map:
            if this_block.color:
                self.mc.setBlock(
                    pos.x + this_block.pos[0]/2.0,
                    pos.y + this_block.pos[2]/2.0,
                    pos.z - this_block.pos[1]/2.0,
                    this_block.block_type,
                    this_block.color
                )
            else:
                self.mc.setBlock(
                    pos.x + this_block.pos[0]/2.0,
                    pos.y + this_block.pos[2]/2.0,
                    pos.z - this_block.pos[1]/2.0,
                    this_block.block_type
                )


mm = MineManager()


class MineConnectOperator(bpy.types.Operator):
    bl_idname = "ws_takuro.mine_connect"
    bl_label = "Connect"

    def __init__(self, *args, **kwargs):
        super(MineConnectOperator, self).__init__(*args, **kwargs)
        bpy.context.scene.McStatus = "DISCONNECTED"

    def execute(self, context):
        mm.connect()
        context.scene.McStatus = "CONNECTED"
        return {"FINISHED"}


class MCSendBlocksOperator(bpy.types.Operator):
    bl_idname = "ws_takuro.mc_send_blocks"
    bl_label = "Send blocks"

    def execute(self, context):
        mm.set_bunch_of_blocks()
        return {"FINISHED"}


class Convert2BlockOperator(bpy.types.Operator):
    bl_idname = "ws_takuro.convert2block"
    bl_label = 'Convert to Block'

    def execute(self, context):
        context.scene['NumOctree'] = 3

        obj = context.active_object
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

        block_map = cvt.invoke(cvt.decimated, initial_bb, octree)
        bpy.context.active_object["block_map"] = pickle.dumps(block_map)

        return {"FINISHED"}


sample_text = "aaaa"


class BlockConversionPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "BlockConversion"
    bl_idname = "OBJECT_PT_b2mine"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        row = layout.row()
        row.prop(obj, "Octree")
        row.operator("ws_takuro.convert2block")


class MinecraftPanel(bpy.types.Panel):
    bl_label = "Minecraft"
    bl_idname = "OBJECT_PT_mine"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        scene = context.scene

        box = layout.box()
        row = box.row()

        if scene.McStatus == "CONNECTED":
            row.label("Connected", icon="FILE_TICK")
        else:
            row.label("Disconnected", icon="ERROR")

        row = box.row()
        row.prop(scene, "McIpAddr", text="IP addr")
        row.prop(scene, "McPort", text="Port number")

        row = box.row()
        row.alignment = 'RIGHT'
        row.operator("ws_takuro.mine_connect")

        row = layout.row()
        row.operator("ws_takuro.mc_send_blocks")


def register():
    connection_status = [
        ("DISCONNECTED", "Disconnected", "", 0),
        ("CONNECTED", "Connected", "", 1),
        ("FAILED", "Failed", "", 2),
    ]

    bpy.types.Object.Octree = IntProperty(
        name="Octree",
        description="Enter an integer",
        min=1,
        max=99,
        default=3
    )

    bpy.types.Scene.McStatus = EnumProperty(
        items=connection_status,
        name='mc_status',
        description='Status of connection to Minecraft Server',
        default="DISCONNECTED"
    )

    bpy.types.Scene.McIpAddr = StringProperty(
        name='ip',
        description='IP address of server',
        default='127.0.0.1'
    )

    bpy.types.Scene.McPort = IntProperty(
        name='port',
        description='Port number of server',
        default=4711
    )

    bpy.utils.register_class(MineConnectOperator)
    bpy.utils.register_class(MCSendBlocksOperator)
    bpy.utils.register_class(Convert2BlockOperator)
    bpy.utils.register_class(BlockConversionPanel)
    bpy.utils.register_class(MinecraftPanel)


def unregister():
    bpy.utils.unregister_class(MineConnectOperator)
    bpy.utils.unregister_class(MCSendBlocksOperator)
    bpy.utils.unregister_class(Convert2BlockOperator)
    bpy.utils.unregister_class(BlockConversionPanel)
    bpy.utils.unregister_class(MinecraftPanel)

# bpy.utils.register_module(__name__)

if __name__ == "__main__":
    register()
