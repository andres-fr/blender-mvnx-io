#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module contains ubclasses from ``bpy.types.Operator`` defining
user-callable functors. Operators can also be embedded in Panels and
other UI elements.
"""


__author__ = "Andres FR"

# from mathutils import Vector  # mathutils is a blender package
import bpy
from bpy.types import Operator
#
from bpy.props import EnumProperty, StringProperty, CollectionProperty
# from bpy.props import FloatProperty, IntProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper  # , ExportHelper
from bpy_extras.io_utils import orientation_helper, axis_conversion
#
from .mvnx_import import load_mvnx_into_blender

from bpy.props import CollectionProperty
from .utils import ImportFilesCollection, resolve_path
files: CollectionProperty(type=ImportFilesCollection)


# #############################################################################
# ## IMPORT OPERATOR
# #############################################################################





# this decorator adds the axis entries as properties to the class.
@orientation_helper(axis_forward="-Z", axis_up="Y")
class ImportMVNX(bpy.types.Operator, ImportHelper):
    """
    Load an MVNX motion capture file. This Operator is heavily inspired in the
    oficially supported ImportBVH.
    """

    bl_idname = "import_anim.mvnx"
    bl_label = "Import MVNX"
    bl_options = {'REGISTER', 'UNDO'}

    # filename_ext = ".mvnx"
    filter_glob: StringProperty(default="*.mvnx", options={'HIDDEN'})


    # files: CollectionProperty(type=ImportFilesCollection)

    mvnx_schema_path: StringProperty(
        subtype="FILE_PATH",
        default=resolve_path("data", "mvnx_schema_mpiea.xsd"),
        name="MVNX Schema path",
        description="Validation schema for the MVNX file (optional)")

    # target: EnumProperty(
    #     items=(
    #         ('ARMATURE', "Armature", ""),
    #         ('OBJECT', "Object", ""),
    #     ),
    #     name="Target",
    #     description="Import target type",
    #     default='ARMATURE',
    # )
    # global_scale: FloatProperty(
    #     name="Scale",
    #     description="Scale the BVH by this value",
    #     min=0.0001, max=1000000.0,
    #     soft_min=0.001, soft_max=100.0,
    #     default=1.0,
    # )
    # frame_start: IntProperty(
    #     name="Start Frame",
    #     description="Starting frame for the animation",
    #     default=1,
    # )
    # use_fps_scale: BoolProperty(
    #     name="Scale FPS",
    #     description=(
    #         "Scale the framerate from the BVH to the current scenes, "
    #         "otherwise each BVH frame maps directly to a Blender frame"
    #     ),
    #     default=False,
    # )
    # update_scene_fps: BoolProperty(
    #     name="Update Scene FPS",
    #     description=(
    #         "Set the scene framerate to that of the BVH file (note that this "
    #         "nullifies the 'Scale FPS' option, as the scale will be 1:1)"
    #     ),
    #     default=False,
    # )
    # update_scene_duration: BoolProperty(
    #     name="Update Scene Duration",
    #     description="Extend the scene's duration to the BVH duration (never shortens the scene)",
    #     default=False,
    # )
    # use_cyclic: BoolProperty(
    #     name="Loop",
    #     description="Loop the animation playback",
    #     default=False,
    # )
    # rotate_mode: EnumProperty(
    #     name="Rotation",
    #     description="Rotation conversion",
    #     items=(
    #         ('QUATERNION', "Quaternion",
    #          "Convert rotations to quaternions"),
    #         ('NATIVE', "Euler (Native)",
    #          "Use the rotation order defined in the BVH file"),
    #         ('XYZ', "Euler (XYZ)", "Convert rotations to euler XYZ"),
    #         ('XZY', "Euler (XZY)", "Convert rotations to euler XZY"),
    #         ('YXZ', "Euler (YXZ)", "Convert rotations to euler YXZ"),
    #         ('YZX', "Euler (YZX)", "Convert rotations to euler YZX"),
    #         ('ZXY', "Euler (ZXY)", "Convert rotations to euler ZXY"),
    #         ('ZYX', "Euler (ZYX)", "Convert rotations to euler ZYX"),
    #     ),
    #     default='NATIVE',
    # )



    # def execute(self, context):
    #     print(len(self.files))
    #     for i, f in enumerate(self.files, 1):
    #         print("File %i: %s" % (i, f.name))
    #     return {'FINISHED'}

    def execute(self, context):
        """
        Passes the properties captured by the UI to the load_mvnx_into_blender
        function.
        :returns: ``{"FINISHED"}`` if everything went OK.
        """
        # as_keywords returns a copy of the properties as a dict.
        keywords = self.as_keywords(ignore=(
            "axis_forward", "axis_up", "filter_glob"))
        if not self.mvnx_schema_path:
            keywords["mvnx_schema_path"] = None
        # afwd = self.axis_forward
        # aup = self.axis_up
        # global_mat = axis_conversion(from_forward=afwd, from_up=aup).to_4x4()
        # keywords["global_matrix"] = global_mat
        load_mvnx_into_blender(context, report=self.report, **keywords)
        return({"FINISHED"})
