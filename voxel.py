# -*- coding: utf-8 -*-

import bpy


class Voxel(object):

    FACES = ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 3, 7, 6), (4, 0, 3, 7))

    def __init__(self, name, vertices, color):
        self._name = name
        self._vertices = vertices
        self._color = color
        self._obj = None

    def create(self):
        # Create Shape
        mesh = bpy.data.meshes.new("cube_mesh_data")
        mesh.from_pydata(self._vertices, [], Voxel.FACES)
        mesh.update()

        # Apply color
        mesh.vertex_colors.new()
        j = 0
        for poly in mesh.polygons:
            for _ in poly.loop_indices:
                mesh.vertex_colors["Col"].data[j].color = self._color
                j += 1

        self._obj = bpy.data.objects.new(self._name, mesh)
        return self

    def add(self, scene, parent=None):
        scene.objects.link(self._obj)
        self._obj.select = True
        if parent:
            self._obj.parent = parent
