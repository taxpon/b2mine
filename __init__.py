import os
import sys
import time

import bpy
from mathutils import Vector
import mathutils.geometry as mg

sys.path.append(os.path.dirname(__file__))

import mcpi.minecraft as minecraft
import mcpi.block as block

bl_info = {
    "name": "Blender2Minecraft",
    "category": "Object",
}


class Converter(object):

    @staticmethod
    def check_if_points_exist_in_box(box, points):
        """
        :param list[Vector] box:
        :param list[Vector] points:
        :return:
        """
        exist = False
        for point in points:
            if box[0].z <= point.z < box[1].z and \
               box[0].y <= point.y < box[3].y and \
               box[0].x <= point.x < box[5].x:
                exist = True
                break
        return exist

    @staticmethod
    def define_grids(obj, level=6):
        dim = obj.dimensions
        unit = max(dim) / float(level)

        start = Vector(obj.bound_box[0])
        vec_list = []

        for dz in range(int(dim[2]/unit + 2)):
            # for dz in [2]:
            # for dy in range(int(dim[1]/unit + 2)):
            #     for dx in range(int(dim[0]/unit + 1)):
        # for dz in [0]:
            for dy in [0]:
                for dx in [0]:
                    nvec = start.copy()
                    nvec.x += dx * unit
                    nvec.y += dy * unit
                    nvec.z += dz * unit
                    vec_list.append(nvec)

        return vec_list, unit

    @staticmethod
    def _debug_place_points(obj, vec_list, unit):
        for vec in vec_list:
            print(vec)

            import time
            start = time.time()
            is_in = Converter.is_inside_polygon(obj.data, vec)
            elapsed_time = (time.time() - start) * 1000
            print("is_inside_polyton: elapsed_time:{0}".format(elapsed_time) + "[ms]")


            if is_in:
                bpy.ops.mesh.primitive_cube_add(
                    radius=4,
                    view_align=False,
                    enter_editmode=False,
                    location=vec.to_tuple())
                bpy.context.active_object.color = (1.0, 0, 0, 1.0)
                print("is_in")
            else:
                bpy.ops.mesh.primitive_cube_add(
                    radius=1,
                    view_align=False,
                    enter_editmode=False,
                    location=vec.to_tuple())
                bpy.context.active_object.color = (0, 0, 1.00, 1.0)

    @staticmethod
    def is_inside_polygon(mesh, point):
        inf = Vector((1e4, 1e4, 1e4))
        ray_vector = point - inf

        in_ins = {}
        out_ins = {}

        for i, poly in enumerate(mesh.polygons):
            vs = []
            for j in poly.loop_indices:
                vs.append(mesh.vertices[mesh.loops[j].vertex_index].co)

            # Ray Casting
            result = mg.intersect_ray_tri(vs[0], vs[1], vs[2], ray_vector, inf)
            if result:
                dot_val = poly.normal.dot(point - result)
                key = "{}:{}:{}".format(result[0], result[1], result[2])

                if dot_val < 0:
                    if key not in in_ins:
                        in_ins[key] = True
                else:
                    if key not in out_ins:
                        out_ins[key] = True

        # import pprint
        # print(pprint.pformat(in_ins))
        # print(pprint.pformat(out_ins))
        return len(in_ins) > len(out_ins)


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

        mesh = obj.data
        # vcols = mesh.vertex_colors
        # if len(vcols) == 0:
        #     vcols.new()
        # color_layer = vcols["Col"]
        #
        # inf_point = Vector((1e5, 1e5, 1e5))
        # target_point = Vector((-10, -10, -10))
        # ray_vector = target_point - inf_point
        #
        # print(len(mesh.vertices))
        # for i, poly in enumerate(mesh.polygons):
        #     print("Polygon number: {}".format(i))
        #
        #     v0 = mesh.vertices[mesh.loops[poly.loop_indices[0]].vertex_index].co
        #     v1 = mesh.vertices[mesh.loops[poly.loop_indices[1]].vertex_index].co
        #     v2 = mesh.vertices[mesh.loops[poly.loop_indices[2]].vertex_index].co
        #     # ray = Vector((0.0, 0.0, -1))
        #     # orig = Vector((-0, -0, 10.0))
        #     result = mg.intersect_ray_tri(v0, v1, v2, ray_vector, inf_point)
        #     if result:
        #         print("result:", result)
        #         print("normal:", poly.normal)
        #         print("vec:", target_point - result)
        #
        #         dot_val = poly.normal.dot(target_point - result)
        #         print(dot_val)
        #
        #         if dot_val < 0:
        #             # INTO
        #             for j in poly.loop_indices:
        #                 color_layer.data[j].color = 1, 0, 0
        #         else:
        #             # OUT
        #             for j in poly.loop_indices:
        #                 color_layer.data[j].color = 0, 0, 1

        ############################################
        # test_v = Vector((-0, -0, -0))
        # result = Converter.is_inside_polygon(mesh=mesh, point=test_v)
        # print("test_v({}) is in poly: {}".format(test_v, result))
        #
        # test_v = Vector((-0.5, -0, -0))
        # result = Converter.is_inside_polygon(mesh=mesh, point=test_v)
        # print("test_v({}) is in poly: {}".format(test_v, result))
        #
        # test_v = Vector((-0, -0.5, -0))
        # result = Converter.is_inside_polygon(mesh=mesh, point=test_v)
        # print("test_v({}) is in poly: {}".format(test_v, result))
        #
        # test_v = Vector((-0, -0, -0.5))
        # result = Converter.is_inside_polygon(mesh=mesh, point=test_v)
        # print("test_v({}) is in poly: {}".format(test_v, result))
        #
        # test_v = Vector((-10, -0, -0))
        # result = Converter.is_inside_polygon(mesh=mesh, point=test_v)
        # print("test_v({}) is in poly: {}".format(test_v, result))
        import time

        start = time.time()
        vec_list, unit = Converter.define_grids(obj)
        elapsed_time = (time.time() - start) * 1000
        print("elapsed_time:{0}".format(elapsed_time) + "[ms]")

        start = time.time()
        Converter._debug_place_points(obj, vec_list, unit)
        elapsed_time = (time.time() - start) * 1000
        print("elapsed_time:{0}".format(elapsed_time) + "[ms]")

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
