#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""


__author__ = "Andres FR"

from os.path import basename
#
import bpy
from mathutils import Vector, Quaternion, Matrix # , Euler
#
from .mvnx import Mvnx
from .utils import str_to_vec, is_number


# #############################################################################
# ## TODO
# #############################################################################


# 3. details like rescaling, more UI, TIME PRECISION...

# #############################################################################
# ## GLOBALS
# #############################################################################


# Hips -> Pelvis: head=by_user, tail=pHipOrigin
# Chest -> L5: head = parent.tail, tail=head+ segment.path[joints.jL5S1.connector1].pos_b
# Chest2 -> L3: head = parent.tail, tail=head + segment.path[joints.jL4L3.connector1].pos_b

# how is the tree defined? in joints, the first part of each connector1->connector2 tells the parenthood.6

# 1. create hips as defined
# 2. joint jL5S1 corresponds to chest. its connector1 is the route

# <connector1>Pelvis/jL5S1</connector1>  # the tail
# <connector2>L5/jL5S1</connector2>  # zeros...


## IDEA:
# 1. for each segment by id order, create an editbone with its name. make a list comp with the bones, and a dict name->bone (with a ref to the bone).
# 2. The pelvis has head=user, tail=pHipOrigin.
# 3. Then, for each mvnx.joint, the bone is the name of connector2. The head is the tail of the bone in connector1, and the tail is the head plus the sum of both entries.
# 4. If the joints are followed in order, this will work. NO!! the leafs wont work...
# POSSIBLE SOLUTION: 1. Instead of the extra "tail" for hips, pick the vertical segment from zero to Chest as hips. The important thing is that moving or rotating there should move/rotate everything! including the zero->hips segments. i.e. the 3 segments that come out of the origin should behave like a single rigid one. If the same is done for the "collars", the remaining 23 bones should be identical to the BVH ones and therefore have the same angles? check that!

# #############################################################################
# ## HELPERS
# #############################################################################

def set_bone_head_and_tail(bone, segment_points, joints,
                           root_points=["pHipOrigin"],
                           leaf_points=["pTopOfHead",
                                        "pRightTopOfHand", "pLeftTopOfHand",
                                        "pRightToe", "pLeftToe"]):
    """
    :param bone: an EditBone
    :param segment_points: A dict of dicts that allows to find an offset given a
      joint connector. Expected form: {seg_name: {p_name: 3d_vector, ...}, ...}.
    :param joints: A list with elements in the form (conn1, conn2) in the joint
      order given by the MVNX file.

    For a given bone, this function reads the information of its parent and,
    given some MVNX data and assumptions, calculates its head and tail
    positions.

    .. warning::
      This function assumes the following:
      1. If the bone has a parent, it can be found under bone.parent.
      2. The head and tail of the parent have been already properly set.
      3. If this bone is a root, its segment will have a point with
         a label in root_points.
      4. If this bone is a leaf, its segment will have a point with
         a label in leaf_points.
    """
    b_name = bone.name
    # find head:
    if bone.parent is None:
        # if root, we assume a point in root_points exists
        bone.head = [v for k, v in segment_points[b_name].items()
                     if k in root_points][0]
    else:
        bp_name = bone.parent.name
        # get first joint that contains both this bone and parent
        j = next((c1, c2) for (c1,c2) in joints if c1.split("/")[0] == bp_name
                 and c2.split("/")[0] == b_name)
        head_offs1 = segment_points[bp_name][j[0].split("/")[1]]
        head_offs2 = segment_points[b_name][j[1].split("/")[1]]  # usually 000
        bone.head = bone.parent.head + head_offs1 + head_offs2
        if bone.head == bone.parent.tail:
            bone.use_connect = True  # avoid connecting separated bones
    # find tail:
    if not bone.children:
        # if leaf, we assume a point in leaf_points exists
        tail_offs = [v for k, v in segment_points[bone.name].items()
                       if k in leaf_points][0]
    else:
        # get first joint that contains this bone as parent
        j = next((c1, c2) for (c1,c2) in joints if c1.split("/")[0] == b_name)
        tail_offs = segment_points[b_name][j[0].split("/")[1]]
    bone.tail = bone.head + tail_offs

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

    # load MVNX object and basic metadata
    mvnx_filename = basename(filepath)
    mvnx = Mvnx(filepath, mvnx_schema_path)
    #
    frames_metadata, config_frames, normal_frames = mvnx.extract_frame_info()
    #
    segments = sorted(mvnx.mvnx.subject.segments.iterchildren(),
                      key=lambda elt: int(elt.attrib["id"]))
    seg2idx = {s.attrib["label"]: i for i, s in enumerate(segments)}
    segment_points = {s: {p.attrib["label"]: Vector(str_to_vec(p.pos_b.text))
                          for p in segments[i].points.iterchildren()}
                      for s, i in seg2idx.items()}
    joints = [(j.connector1.text, j.connector2.text)
              for j in mvnx.mvnx.subject.joints.iterchildren()]

    #
    num_segments = int(frames_metadata["segmentCount"])
    # num_sensors = frames_metadata["sensorCount"]
    # num_joints = frames_metadata["jointCount"]
    num_frames = len(normal_frames) + 1  # +1 for the tpose
    frame_rate = int(mvnx.mvnx.subject.attrib["frameRate"])
    #
    assert len(segments) == num_segments, "Inconsistent segmentCount?"


    # create armature and prepare to fill it
    bpy.ops.object.select_all(action='DESELECT')
    arm_data = bpy.data.armatures.new(mvnx_filename)
    arm_ob = bpy.data.objects.new(mvnx_filename, arm_data)
    context.collection.objects.link(arm_ob)
    arm_ob.select_set(True)
    context.view_layer.objects.active = arm_ob
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    # create one bone per segment
    edit_bones = [arm_data.edit_bones.new(s.attrib["label"])
                  for s in segments]

    # create forest of bones using joints info:
    for conn1, conn2 in joints:
        parent_n = conn1.split("/")[0]
        child_n = conn2.split("/")[0]
        # set parenthood
        edit_bones[seg2idx[child_n]].parent = edit_bones[seg2idx[parent_n]]
    # set heads and tails:
    for b in edit_bones:
        set_bone_head_and_tail(b, segment_points, joints)
        b.use_inherit_rotation = False  # TODO: ADAPT FOR TRUE!


    # ANIMATION

    # prepare animation: create action and assign it to the armature
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    context.view_layer.update()
    arm_ob.animation_data_create()
    action = bpy.data.actions.new(name=mvnx_filename)
    arm_ob.animation_data.action = action
    pose_bones = [arm_ob.pose.bones[b.name] for b in edit_bones]
    pb_roots = {b for b in pose_bones if b.parent is None}

    # the bone coordinate converters can already be retrieved
    def get_edit_bone(eb_name):
        """
        """
        return bpy.data.objects[mvnx_filename].data.bones[eb_name]

    def get_pose_bone(pb_name):
        """
        """
        return bpy.data.objects[mvnx_filename].pose.bones[pb_name]


    # these matrices convert from the bone coordinates to global.
    eb_matrices = {b.name: get_edit_bone(b.name).matrix_local
                   for b in edit_bones}
    eb_matrices_inv = {k: v.inverted_safe() for k, v in eb_matrices.items()}
    # these matrices express the pose rotation, relative to the eb_matrix
    pb_matrices = {b.name: get_pose_bone(b.name).matrix_basis
                   for b in pose_bones}

    def global_loc_to_bone(g_loc, bone_name):
        """
        :param Vector g_loc: (x, y, z) global position vector
        :returns: same vector expressed in terms of the bone basis. If the
          output is applied to the bone, it will appear in the global g_loc.
        """
        # this was the impl in the BVH plugin
        eb = get_edit_bone(bone_name)
        bone_transl_mat = Matrix.Translation(g_loc - eb.head)
        b_loc = (eb_matrices_inv[bone_name] @ bone_transl_mat).to_translation()
        # # this was my naive impl, assuming bone is at origin:
        # g = g_loc.copy()
        # # since eb_mat rotates from global to bone coords, inv goes back.
        # g.rotate(eb_matrices_inv[bone_name])
        return b_loc

    def global_quat_to_bone(g_quat, bone_name):
        """
        This basically replicates the BVH importer, not sure if it is correct.
        From my calculations, b = g_quat @ eb_matrices_inv[b_name] should be
        correct (without inheriting rotations).
        TODO: IMPLEMENT WITH INHERITING ROTATIONS.
        """
        g_quat_mat = g_quat.to_matrix().to_4x4()
        #
        b = eb_matrices_inv[b_name] @ g_quat_mat @ eb_matrices[b_name]
        return b.to_quaternion()




    # set anim speed. actual_fps = scene.render.fps / scene.render.fps_base
    context.scene.render.fps_base = 1.0
    context.scene.render.fps = frame_rate

    # create one FCurve per data channel and fill them with empty <num_frames>
    fcurves = {pb.name: {"loc": [], "ori": []} for pb in pose_bones}
    for pb in pose_bones:
        has_location = pb in pb_roots
        #
        if has_location:
            loc_dp = 'pose.bones["%s"].location' % pb.name  # datapath
            for dim_loc in range(3):
                fcurve = action.fcurves.new(data_path=loc_dp, index=dim_loc)
                fcurves[pb.name]["loc"].append(fcurve)
                kf_points = fcurve.keyframe_points
                kf_points.add(num_frames)  # t-pose will be at frame 0
        # fill rotation fcurves
        pb.rotation_mode = "QUATERNION"
        rot_dp = 'pose.bones["%s"].rotation_quaternion' % pb.name
        for dim_rot in range(4):
            fcurve = action.fcurves.new(data_path=rot_dp, index=dim_rot)
            fcurves[pb.name]["ori"].append(fcurve)
            kf_points = fcurve.keyframe_points
            kf_points.add(num_frames)

    # fill the t-pose
    tpose_frame = [f for f in config_frames if f["type"] == "tpose"][0]
    print(tpose_frame)
    for b_name, fc_dd in fcurves.items():
        pb_idx = seg2idx[b_name]
        pb_idx_3, pb_idx_4 = pb_idx * 3, pb_idx * 4
        # set location, if existing:
        if fc_dd["loc"]:
            global_loc = Vector(tpose_frame["position"][pb_idx_3: pb_idx_3+3])
            bone_loc = global_loc_to_bone(global_loc, b_name)
            for loc_fc, loc_entry in zip(fc_dd["loc"], bone_loc):
                loc_fc.keyframe_points[0].co.x = 0
                loc_fc.keyframe_points[0].co.y = loc_entry
        # # set orientation
        IDENTITY_TPOSE = False
        if IDENTITY_TPOSE:
            bone_ori = Quaternion((1, 0, 0, 0))
        else:
            global_quat = Quaternion(tpose_frame["orientation"][
                pb_idx_4: pb_idx_4+4])
            bone_ori = global_quat_to_bone(global_quat, b_name)
        get_pose_bone(b_name).rotation_quaternion = bone_ori
        for ori_fc, ori_entry in zip(fc_dd["ori"], bone_ori):
            ori_fc.keyframe_points[0].co.x = 0
            ori_fc.keyframe_points[0].co.y = ori_entry


    # fill frames (starting at 1 and incrementing by 1)
    for frame_i, frame in enumerate(normal_frames, 1):
        print(">>> filling frame", frame_i)
        frame_pos = [frame["position"][i: i+3]
                     for i in range(0, 3 * num_segments, 3)]
        frame_ori = [frame["orientation"][i: i+4]
                     for i in range(0, 4 * num_segments, 4)]
        for pb, glob_loc, glob_ori in zip(pose_bones, frame_pos, frame_ori):
            b_name = pb.name
            # fill location curves
            loc_fcurves = fcurves[b_name]["loc"]
            if loc_fcurves:
                bone_loc = global_loc_to_bone(Vector(glob_loc), b_name)
                for loc_fc, loc_entry in zip(loc_fcurves, bone_loc):
                    # tpose_entry = loc_fc.keyframe_points[0].co.y
                    loc_fc.keyframe_points[frame_i].co.x = frame_i
                    loc_fc.keyframe_points[frame_i].co.y = loc_entry  # + tpose_entry
            # fill orientation curves
            ori_fcurves = fcurves[b_name]["ori"]
            if ori_fcurves:
                bone_ori = global_quat_to_bone(Quaternion(glob_ori), b_name)
                get_pose_bone(b_name).rotation_quaternion = bone_ori
                for ori_fc, ori_entry in zip(ori_fcurves, bone_ori):
                    ori_fc.keyframe_points[frame_i].co.x = frame_i
                    ori_fc.keyframe_points[frame_i].co.y = ori_entry


    # tpose_frame = [f for f in config_frames if f["type"] == "tpose"][0]
    # print(tpose_frame)
    # for b_name, fc_dd in fcurves.items():
    #     pb_idx = seg2idx[b_name]
    #     pb_idx_3, pb_idx_4 = pb_idx * 3, pb_idx * 4
    #     # set location, if existing:
    #     if fc_dd["loc"]:
    #         # for this bone, here we have a list of (x,y,z) fcurves.
    #         # each with normal_frames starting at 1.
    #         # so for each keyframe, go to the MVNX normal frame,
    #         # and grab the corresponding location info


    #         global_loc = Vector(tpose_frame["position"][pb_idx_3: pb_idx_3+3])
    #         bone_loc = global_loc_to_bone(global_loc, b_name)
    #         for loc_fc, loc_entry in zip(fc_dd["loc"], bone_loc):
    #             loc_fc.keyframe_points[0].co.y = loc_entry
    #     # set orientation
    #     global_quat =  Quaternion(tpose_frame["orientation"][
    #         pb_idx_4: pb_idx_4+4])
    #     bone_quat = global_quat_to_bone(global_quat, b_name)
    #     for ori_fc, ori_entry in zip(fc_dd["ori"], bone_quat):
    #         ori_fc.keyframe_points[0].co.y = ori_entry    

    # access existing blender fcurve by bone name?
    
    #     # iterate over all bones to fill the animation sequence:
    #     for bone_i, pb in enumerate(pose_bones):
    #         print("filling sequence for bone", bone_i, pb.name)
    #         # handle location info: only root bones have it
    #         has_location = pb in pb_roots
    #         if has_location:
    #             print(">>>>>>> has location:", pb.name)
    #             # report({'INFO'}, "Setting location data for " + pb.name)
    #             loc_dp = 'pose.bones["%s"].location' % pb.name  # datapath
    #             # iterate over 3 dimensions: x, y, z
    #             for dim_i in range(3):
    #                 curve = action.fcurves.new(data_path=loc_dp, index=dim_i)
    #                 kf_points = curve.keyframe_points
    #                 kf_points.add(num_frames)  # t-pose will be at frame 0
    #                 for frame_i, pos_frame in enumerate(positions, 1):  # normal frames begin at 1 (0 is for t-pose)
    #                     kf_points[frame_i].co = (frame_i, pos_frame[bone_i][dim_i])
    
    # #         # handle rotation info:
    # #         pb.rotation_mode = "QUATERNION"
    # #         rot_dp = 'pose.bones["%s"].rotation_quaternion' %  pb.name
    # #         for q_i in [3, 2, 1, 0]:  # [0, 1, 2, 3]:
    # #             curve = action.fcurves.new(data_path=rot_dp, index=q_i)
    # #             kf_points = curve.keyframe_points
    # #             kf_points.add(num_frames)
    # #             for frame_i, rot_frame in enumerate(orientations, 1):
    # #                 kf_points[frame_i].co = (frame_i, rot_frame[bone_i][q_i])
    
    # # #                 for frame_i in range(num_frame):
    # # #                     keyframe_points[frame_i].co = (
    # # #                         time[frame_i],
    # # #                         rotate[frame_i][axis_i],
    # # #                     )
    
    # #         # matts = [Quaternion(oo).to_matrix().to_4x4() for oo in o]
    # #         # print(matts)
    

    # finally config curves, apply matrix and return armature
    for c in action.fcurves:
        # if IMPORT_LOOP:
        #     pass  # 2.5 doenst have cyclic now?
        for ckfp in c.keyframe_points:
            ckfp.interpolation = "CONSTANT" #  "LINEAR"
    # arm_ob.matrix_world = global_matrix
    # bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    return arm_ob


#             for frame_i in range(num_frame):
#                 bvh_rot = bvh_node.anim_data[frame_i + skip_frame][3:]

#                 # apply rotation order and convert to XYZ
#                 # note that the rot_order_str is reversed.
#                 euler = Euler(bvh_rot, bvh_node.rot_order_str[::-1])
#                 bone_rotation_matrix = euler.to_matrix().to_4x4()
#                 bone_rotation_matrix = (
#                     bone_rest_matrix_inv @
#                     bone_rotation_matrix @
#                     bone_rest_matrix
#                 )

#                 if len(rotate[frame_i]) == 4:
#                     rotate[frame_i] = bone_rotation_matrix.to_quaternion()
#                 else:
#                     rotate[frame_i] = bone_rotation_matrix.to_euler(
#                         pose_bone.rotation_mode, prev_euler)
#                     prev_euler = rotate[frame_i]

#             # For each euler angle x, y, z (or quaternion w, x, y, z).
#             for axis_i in range(len(rotate[0])):
#                 curve = action.fcurves.new(data_path=data_path, index=axis_i)
#                 keyframe_points = curve.keyframe_points
#                 keyframe_points.add(num_frame)

#                 for frame_i in range(num_frame):
#                     keyframe_points[frame_i].co = (
#                         time[frame_i],
#                         rotate[frame_i][axis_i],
#                     )

#     for cu in action.fcurves:
#         if IMPORT_LOOP:
#             pass  # 2.5 doenst have cyclic now?

#         for bez in cu.keyframe_points:
#             bez.interpolation = 'LINEAR'

#     # finally apply matrix
#     arm_ob.matrix_world = global_matrix
#     bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

#     return arm_ob















#     arm_ob.animation_data_create()
#     action = bpy.data.actions.new(name=bvh_name)
#     arm_ob.animation_data.action = action

#     # Replace the bvh_node.temp (currently an editbone)
#     # With a tuple  (pose_bone, armature_bone, bone_rest_matrix, bone_rest_matrix_inv)
#     num_frame = 0
#     for bvh_node in bvh_nodes_list:
#         bone_name = bvh_node.temp  # may not be the same name as the bvh_node, could have been shortened.
#         pose_bone = pose_bones[bone_name]
#         rest_bone = arm_data.bones[bone_name]
#         bone_rest_matrix = rest_bone.matrix_local.to_3x3()

#         bone_rest_matrix_inv = Matrix(bone_rest_matrix)
#         bone_rest_matrix_inv.invert()

#         bone_rest_matrix_inv.resize_4x4()
#         bone_rest_matrix.resize_4x4()
#         bvh_node.temp = (pose_bone, bone, bone_rest_matrix, bone_rest_matrix_inv)


#     for i, bvh_node in enumerate(bvh_nodes_list):
#         pose_bone, bone, bone_rest_matrix, bone_rest_matrix_inv = bvh_node.temp

#         if bvh_node.has_loc:
#             # Not sure if there is a way to query this or access it in the
#             # PoseBone structure.
#             data_path = 'pose.bones["%s"].location' % pose_bone.name

#             location = [(0.0, 0.0, 0.0)] * num_frame
#             for frame_i in range(num_frame):
#                 bvh_loc = bvh_node.anim_data[frame_i + skip_frame][:3]

#                 bone_translate_matrix = Matrix.Translation(
#                     Vector(bvh_loc) - bvh_node.rest_head_local)
#                 location[frame_i] = (bone_rest_matrix_inv @
#                                      bone_translate_matrix).to_translation()

#             # For each location x, y, z.
#             for axis_i in range(3):
#                 curve = action.fcurves.new(data_path=data_path, index=axis_i)
#                 keyframe_points = curve.keyframe_points
#                 keyframe_points.add(num_frame)

#                 for frame_i in range(num_frame):
#                     keyframe_points[frame_i].co = (
#                         time[frame_i],
#                         location[frame_i][axis_i],
#                     )

# asdf

#         if bvh_node.has_rot:
#             data_path = None
#             rotate = None
#             if 'QUATERNION' == rotate_mode:
#                 rotate = [(1.0, 0.0, 0.0, 0.0)] * num_frame
#                 data_path = ('pose.bones["%s"].rotation_quaternion'
#                              % pose_bone.name)
#             else:
#                 rotate = [(0.0, 0.0, 0.0)] * num_frame
#                 data_path = ('pose.bones["%s"].rotation_euler' %
#                              pose_bone.name)

#             prev_euler = Euler((0.0, 0.0, 0.0))
#             for frame_i in range(num_frame):
#                 bvh_rot = bvh_node.anim_data[frame_i + skip_frame][3:]

#                 # apply rotation order and convert to XYZ
#                 # note that the rot_order_str is reversed.
#                 euler = Euler(bvh_rot, bvh_node.rot_order_str[::-1])
#                 bone_rotation_matrix = euler.to_matrix().to_4x4()
#                 bone_rotation_matrix = (
#                     bone_rest_matrix_inv @
#                     bone_rotation_matrix @
#                     bone_rest_matrix
#                 )

#                 if len(rotate[frame_i]) == 4:
#                     rotate[frame_i] = bone_rotation_matrix.to_quaternion()
#                 else:
#                     rotate[frame_i] = bone_rotation_matrix.to_euler(
#                         pose_bone.rotation_mode, prev_euler)
#                     prev_euler = rotate[frame_i]

#             # For each euler angle x, y, z (or quaternion w, x, y, z).
#             for axis_i in range(len(rotate[0])):
#                 curve = action.fcurves.new(data_path=data_path, index=axis_i)
#                 keyframe_points = curve.keyframe_points
#                 keyframe_points.add(num_frame)

#                 for frame_i in range(num_frame):
#                     keyframe_points[frame_i].co = (
#                         time[frame_i],
#                         rotate[frame_i][axis_i],
#                     )

#     for cu in action.fcurves:
#         if IMPORT_LOOP:
#             pass  # 2.5 doenst have cyclic now?

#         for bez in cu.keyframe_points:
#             bez.interpolation = 'LINEAR'

#     # finally apply matrix
#     arm_ob.matrix_world = global_matrix
#     bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

#     return arm_ob


















