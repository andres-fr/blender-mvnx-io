#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""


__author__ = "Andres FR"

import bpy
from mathutils import Vector  # , Euler  # mathutils is a blender package
#
from .mvnx import Mvnx


# #############################################################################
# ## GLOBALS
# #############################################################################


# #############################################################################
# ## HELPERS
# #############################################################################

def load_mvnx_into_blender(
        context,
        filepath,
        mvnx_schema_path=None,
        # target='ARMATURE',
        # rotate_mode='NATIVE',
        # global_scale=1.0,
        # use_cyclic=False,
        # frame_start=1,
        # global_matrix=None,
        # use_fps_scale=False,
        # update_scene_fps=False,
        # update_scene_duration=False,
        report=print):

    mvnx = Mvnx(filepath, mvnx_schema_path)
    print(mvnx)

    # import time
    # t1 = time.time()
    # print("\tparsing bvh %r..." % filepath, end="")

    # bvh_nodes, bvh_frame_time, bvh_frame_count = read_bvh(
    #     context, filepath,
    #     rotate_mode=rotate_mode,
    #     global_scale=global_scale,
    # )
    # # for k,v in bvh_nodes.items():
    #     # print(">>>>", v.name, [(s, getattr(v, s)) for s in v.__slots__ if s!="temp"])

    # print("%.4f" % (time.time() - t1))

    # scene = context.scene
    # frame_orig = scene.frame_current

    # # Broken BVH handling: guess frame rate when it is not contained in the file.
    # if bvh_frame_time is None:
    #     report(
    #         {'WARNING'},
    #         "The BVH file does not contain frame duration in its MOTION "
    #         "section, assuming the BVH and Blender scene have the same "
    #         "frame rate"
    #     )
    #     bvh_frame_time = scene.render.fps_base / scene.render.fps
    #     # No need to scale the frame rate, as they're equal now anyway.
    #     use_fps_scale = False

    # if update_scene_fps:
    #     _update_scene_fps(context, report, bvh_frame_time)

    #     # Now that we have a 1-to-1 mapping of Blender frames and BVH frames, there is no need
    #     # to scale the FPS any more. It's even better not to, to prevent roundoff errors.
    #     use_fps_scale = False

    # if update_scene_duration:
    #     _update_scene_duration(context, report, bvh_frame_count, bvh_frame_time, frame_start, use_fps_scale)

    # t1 = time.time()
    # print("\timporting to blender...", end="")

    # bvh_name = bpy.path.display_name_from_filepath(filepath)

    # if target == 'ARMATURE':
    #     bvh_node_dict2armature(
    #         context, bvh_name, bvh_nodes, bvh_frame_time,
    #         rotate_mode=rotate_mode,
    #         frame_start=frame_start,
    #         IMPORT_LOOP=use_cyclic,
    #         global_matrix=global_matrix,
    #         use_fps_scale=use_fps_scale,
    #     )

    # elif target == 'OBJECT':
    #     bvh_node_dict2objects(
    #         context, bvh_name, bvh_nodes,
    #         rotate_mode=rotate_mode,
    #         frame_start=frame_start,
    #         IMPORT_LOOP=use_cyclic,
    #         # global_matrix=global_matrix,  # TODO
    #     )

    # else:
    #     report({'ERROR'}, "Invalid target %r (must be 'ARMATURE' or 'OBJECT')" % target)
    #     return {'CANCELLED'}

    # print('Done in %.4f\n' % (time.time() - t1))

    # context.scene.frame_set(frame_orig)
