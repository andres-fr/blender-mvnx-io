#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module contains subclasses from ``bpy.types.Operator`` defining
user-callable functors. Operators can also be embedded in Panels and
other UI elements.
"""


__author__ = "Andres FR"

import os
import lxml
import traceback
#
# from mathutils import Vector  # mathutils is a blender package
import bpy
#
from bpy.props import EnumProperty, StringProperty  # , CollectionProperty
from bpy.props import BoolProperty, FloatProperty  # , IntProperty
from bpy_extras.io_utils import ImportHelper  # , ExportHelper
#
from .mvnx_import import load_mvnx_into_blender
from .utils import resolve_path  # , ImportFilesCollection


# #############################################################################
# ## IMPORT OPERATOR
# #############################################################################

class MvnxSchemaManager_0_1_0:
    """
    """
    SCHEMATA_PATH = resolve_path("data")

    @classmethod
    def get_mvnx_schemata(cls):
        """
        """
        xsd_names = [(os.path.join(cls.SCHEMATA_PATH, x), x, "")
                     for x in os.listdir(cls.SCHEMATA_PATH)
                     if x.endswith("xsd")]
        result = (("NONE", "None", ""),) + tuple(xsd_names)
        return result

class ImportMVNX(bpy.types.Operator, ImportHelper):
    """
    Load an MVNX motion capture file. This Operator is heavily inspired in the
    oficially supported ImportBVH.
    """

    bl_idname = "import_anim.mvnx"
    bl_label = "Import MVNX"
    bl_options = {'REGISTER', 'UNDO'}

    MVNX_SCHEMA_MANAGER = MvnxSchemaManager_0_1_0
    VERBOSE_IMPORT = True  # print process info while importing

    # filename_ext = ".mvnx"
    filter_glob: StringProperty(default="*.mvnx", options={'HIDDEN'})

    # mvnx_schema_path: StringProperty(
    #     subtype="FILE_PATH",
    #     default=resolve_path("data", "mvnx_schema_mpiea.xsd"),
    #     name="MVNX Schema path",
    #     description="Validation schema for the MVNX file (optional)"
    # )
    mvnx_schema_path: EnumProperty(
        items = MvnxSchemaManager_0_1_0.get_mvnx_schemata(),
        name="Validation Schema for the MVNX file (optional)",
        description=("Validation schema for the MVNX file, located in " +
                     MvnxSchemaManager_0_1_0.SCHEMATA_PATH),
        default="NONE",
    )

    connectivity: EnumProperty(
        items=(('INDIVIDUAL', "Individual", ""),
               ('CONNECTED', "Connected", "")),
        name="Information to be imported, and structure to be generated.",
        description=("CONNECTED: A tree of connected bones. Position is only" +
                     " taken for roots. INDIVIDUAL: each bone is isolated " +
                     "and becomes position and orientation separately."),
        default='INDIVIDUAL',
    )

    scale: FloatProperty(
        name="Scale",
        description="Multiply every bone length by this value",
        min=0.00001, max=1000000.0,
        soft_min=0.001, soft_max=100.0,
        default=1.0,
    )

    frame_start: FloatProperty(
        name="Position of First Frame",
        description="First imported frame will be at this position",
        default=0.0,
    )

    inherit_rotations: BoolProperty(
        name="Inherit Rotations",
        description="If true, rotating a bone will rotate all its children",
        default=True,
    )

    add_identity_pose: BoolProperty(
        name="Add Identity Pose",
        description="Add a keyframe with zero rotations to the beginning",
        default=True,
    )

    add_t_pose: BoolProperty(
        name="Add T-Pose",
        description=("Add a keyframe with the t-pose definition to the " +
                     "beginning (but after identity if given)"),
        default=True,
    )

    def execute(self, context):
        """
        Passes the properties captured by the UI to the load_mvnx_into_blender
        function.

        :returns: ``{'FINISHED'}`` if everything went OK, ``{'CANCELLED'}``
          otherwise.
        """
        # as_keywords returns a copy of the properties as a dict.
        keywords = self.as_keywords(ignore=(
            "filter_glob",))
        print(">>>>>>>>>>>>>", self.mvnx_schema_path)
        if self.mvnx_schema_path == "NONE":
            keywords["mvnx_schema_path"] = None
        keywords["verbose"] = self.VERBOSE_IMPORT
        try:
            load_mvnx_into_blender(context, report=self.report, **keywords)
            return {'FINISHED'}
        except Exception as e:
            if isinstance(e, lxml.etree.DocumentInvalid):
                self.report({'ERROR'},
                            "MNVX didn't pass given validation schema. " +
                            "Remove schema path to bypass validation.")
            else:
                self.report({'ERROR'}, "Something went wrong: " + str(e))
            traceback.print_exc()
            return {'CANCELLED'}
