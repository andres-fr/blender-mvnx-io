#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Init file for the add-on.

To install it, make sure Blender's Python is able to find it under
addon_utils.paths(), and that the Blender version matches to make it
installable.

Alternatively, run this init file as a script from Blender.
"""


__author__ = "Andres FR"


import bpy
#
from .utils import OperatorToMenuManager, KeymapManager, ImportFilesCollection
from .operators import ImportMVNX
# #############################################################################
# ## CONFIG
# #############################################################################

name = "io_anim_mvnx"  # for packaging via setup.py
VERSION = "0.1.0"  # automatically managed by bumpversion

# required by blender plugins
# (see https://wiki.blender.org/wiki/Process/Addons/Guidelines/metainfo)
bl_info = {
    "name": "MVNX animation I/O addon",
    "author": "Andres FR",
    # "version"  # this triggered problems with bumpversion. help is appreciated
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "I/O functionality for MoCap data in MVNX format",
    # 'wiki_url': "",
    # "warning": "",
    "support": "TESTING",
    "category": "Import-Export"}

KEYMAPS = []
# KEYMAPS = [{"op_name": MaximizeAreaView3d.bl_idname,
#             "key": "THREE", "stroke_mode": "PRESS",
#             "ctrl": True, "shift": True, "alt": False},
#            {"op_name": CleanPurgeAndCreateBasicScene.bl_idname,
#             "key": "ZERO", "stroke_mode": "PRESS",
#             "ctrl": True, "shift": True, "alt": False}]


# #############################################################################
# ## MAIN ROUTINE
# #############################################################################

# the classes to be registered
classes = [ImportMVNX, ImportFilesCollection]  # , ExportMVNX]

# # add Operators to registered classes
# classes += [MaximizeAreaView3d,
#             MaximizeAreaConsole,
#             CleanAndPurgeScene,
#             CreateBasicScene,
#             CleanPurgeAndCreateBasicScene]

# # add Panels to registered classes
# classes += [MY_PANEL_PT_MyPanel1,
#             MY_PANEL_PT_MyPanel2,
#             ASDF_PT_ExportPanel]

register_cl, unregister_cl = bpy.utils.register_classes_factory(classes)
kmm = KeymapManager()
omm = OperatorToMenuManager()

def register():
    """
    Main register function, called on startup by Blender
    """
    register_cl()
    for km_dict in KEYMAPS:
        kmm.register(bpy.context, **km_dict)
    omm.register(ImportMVNX, bpy.types.TOPBAR_MT_file_import)
    # omm.register(ExportMVNX, bpy.types.TOPBAR_MT_file_export)


def unregister():
    """
    Main unregister function, called on shutdown by Blender
    """
    kmm.unregister()
    omm.unregister()
    unregister_cl()


if __name__ == "__main__":
    # This gets executed if calling `blender --python <THIS_FILE>.py`
    register()


print("[Add-on loaded]: ", bl_info["name"], "version", VERSION)