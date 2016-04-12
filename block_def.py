# -*- coding: utf-8 -*-
from mathutils import Vector


class BlockDef(object):
    class _BlockItem(object):
        def __init__(self, name="", color=(0, 0, 0), block_def=(35, None)):
            self._name = name
            self._color = color
            self._block_def = block_def

        @property
        def color(self):
            return self._color

        @property
        def block_def(self):
            return self._block_def

    BLOCK_LIST = (
        _BlockItem(
            "White Wool",
            Vector((0.95, 0.95, 0.95)),
            (35, None)
        ),
        _BlockItem(
            "Orange Wool",
            Vector((0.92, 0.53, 0.25)),
            (35, 1)
        ),
        _BlockItem(
            "Magenta Wool",
            Vector((0.73, 0.31, 0.77)),
            (35, 2)
        ),
        _BlockItem(
            "Light Blue Wool",
            Vector((0.43, 0.55, 0.81)),
            (35, 3)
        ),
        _BlockItem(
            "Yellow Wool",
            Vector((0.77, 0.71, 0.11)),
            (35, 4)
        ),
        _BlockItem(
            "Lime Wool",
            Vector((0.23, 0.75, 0.18)),
            (35, 5)
        ),
        _BlockItem(
            "Pink Wool",
            Vector((0.84, 0.54, 0.62)),
            (35, 6)
        ),
        _BlockItem(
            "Grey Wool",
            Vector((0.26, 0.26, 0.26)),
            (35, 7)
        ),
        _BlockItem(
            "Light Grey Wool",
            Vector((0.62, 0.65, 0.65)),
            (35, 8)
        ),
        _BlockItem(
            "Cyan Wool",
            Vector((0.15, 0.46, 0.59)),
            (35, 9)
        ),
        _BlockItem(
            "Purple Wool",
            Vector((0.53, 0.23, 0.80)),
            (35, 10)
        ),
        _BlockItem(
            "Blue Wool",
            Vector((0.15, 0.20, 0.60)),
            (35, 11)
        ),
        _BlockItem(
            "Brown Wool",
            Vector((0.22, 0.30, 0.09)),
            (35, 12)
        ),
        _BlockItem(
            "Green Wool",
            Vector((0.22, 0.30, 0.09)),
            (35, 13)
        ),
        _BlockItem(
            "Red Wool",
            Vector((0.65, 0.17, 0.16)),
            (35, 14)
        ),
        _BlockItem(
            "Black Wool",
            Vector((0, 0, 0)),
            (35, 15)
        ),
        _BlockItem(
            "White Stained Clay",
            Vector((0.77, 0.65, 0.60)),
            (159, None)
        ),
        _BlockItem(
            "Orange Stained Clay",
            Vector((0.60, 0.31, 0.14)),
            (159, 1)
        ),
        _BlockItem(
            "Magenta Stained Clay",
            Vector((0.56, 0.33, 0.40)),
            (159, 2)
        ),
        _BlockItem(
            "Light Blue Stained Clay",
            Vector((0.44, 0.42, 0.54)),
            (159, 3)
        ),
        _BlockItem(
            "Yellow Stained Clay",
            Vector((0.69, 0.49, 0.13)),
            (159, 4)
        ),
        _BlockItem(
            "Lime Stained Clay",
            Vector((0.38, 0.44, 0.20)),
            (159, 5)
        ),
        _BlockItem(
            "Pink Stained Clay",
            Vector((0.63, 0.30, 0.31)),
            (159, 6)
        ),
        _BlockItem(
            "Gray Stained Clay",
            Vector((0.22, 0.16, 0.14)),
            (159, 7)
        ),
        _BlockItem(
            "Light Gray Stained Clay",
            Vector((0.53, 0.42, 0.38)),
            (159, 8)
        ),
        _BlockItem(
            "Cyan Stained Clay",
            Vector((0.34, 0.35, 0.36)),
            (159, 9)
        ),
        _BlockItem(
            "Purple Stained Clay",
            Vector((0.44, 0.25, 0.31)),
            (159, 10)
        ),
        _BlockItem(
            "Blue Stained Clay",
            Vector((0.27, 0.22, 0.33)),
            (159, 11)
        ),
        _BlockItem(
            "Brown Stained Clay",
            Vector((0.28, 0.19, 0.13)),
            (159, 12)
        ),
        _BlockItem(
            "Green Stained Clay",
            Vector((0.29, 0.32, 0.16)),
            (159, 13)
        ),
        _BlockItem(
            "Red Stained Clay",
            Vector((0.56, 0.24, 0.18)),
            (159, 14)
        ),
        _BlockItem(
            "Black Stained Clay",
            Vector((0.13, 0.08, 0.06)),
            (159, 15)
        ),
        _BlockItem(
            "Stone",
            Vector((0.47, 0.47, 0.47)),
            (1, None)
        ),
        _BlockItem(
            "Polished Granite",
            Vector((0.63, 0.44, 0.38)),
            (1, 2)
        ),
        _BlockItem(
            "Oak Wood Plank",
            Vector((0.66, 0.53, 0.34)),
            (5, None)
        ),
        _BlockItem(
            "Spruce Wood Plank",
            Vector((0.46, 0.34, 0.20)),
            (5, 1)
        ),
        _BlockItem(
            "Birch Wood Plank",
            Vector((0.79, 0.73, 0.49)),
            (5, 2)
        ),
        _BlockItem(
            "Jungle Wood Plank",
            Vector((0.64, 0.46, 0.31)),
            (5, 3)
        ),
        _BlockItem(
            "Acacia Wood Plank",
            Vector((0.59, 0.32, 0.17)),
            (5, 4)
        ),
        _BlockItem(
            "Sand",
            Vector((0.83, 0.78, 0.60)),
            (12, None)
        ),
        _BlockItem(
            "Red Sand",
            Vector((0.63, 0.32, 0.12)),
            (12, 1)
        ),
        _BlockItem(
            "Sponge",
            Vector((0.78, 0.78, 0.31)),
            (19, None)
        ),
        _BlockItem(
            "Sandstone",
            Vector((0.88, 0.85, 0.64)),
            (24, None)
        ),
        _BlockItem(
            "Gold Block",
            Vector((0.99, 0.99, 0.36)),
            (41, None)
        ),
        _BlockItem(
            "Iron Block",
            Vector((0.93, 0.93, 0.93)),
            (42, None)
        ),
    )

    @staticmethod
    def find_nearest_color_block(target_color):
        min_dist = 10
        min_index = 0
        print("Target_color: {}".format(target_color.to_tuple()))
        for i, block in enumerate(BlockDef.BLOCK_LIST):
            dist = (block.color - target_color).length
            print("    i = {}, dist = {}".format(i, dist))
            if dist < min_dist:
                min_index = i
                min_dist = dist
        print("    min_index is '{}'".format(min_index))
        return BlockDef.BLOCK_LIST[min_index]
