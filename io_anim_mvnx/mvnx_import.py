#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""


__author__ = "Andres FR"  # inspired in the official Blender BVH importer

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
    :param joints: A list in the original MVNX ordering, in the form
      [((seg_ori, point_ori), (seg_dest, point_dest)), ...], where each element
      contains 4 strings summarizing the origin->destiny of a connection.
    :param list root_points: If a given bone/segment is root (has no parent),
      the first match in this list will be taken as bone.head.
    :param list leaf_points: If a given bone/segment is a leaf (has no
      children), the first match in this list will be taken as bone.tail.

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
      5. For a given bone, there aren't any possible collisions between the
         different root or head_points, i.e., the first match in the list
         will always be a good match (this happens e.g. if each leaf has
         a uniquely named leaf_point, which is usually the case).
    """
    b_name = bone.name
    # find head:
    if bone.parent is None:
        # if root, we assume a point in root_points exists
        bone.head = next(v for k, v in segment_points[b_name].items()
                         if k in root_points)
    else:
        bp_name = bone.parent.name
        # get first joint that contains both this bone and parent
        j = next(((c1, p1), (c2, p2)) for ((c1, p1), (c2, p2)) in joints
                 if c1 == bp_name and c2 == b_name)
        head_offs1 = segment_points[bp_name][j[0][1]]
        head_offs2 = segment_points[b_name][j[1][1]]  # usually 000
        bone.head = bone.parent.head + head_offs1 + head_offs2
        if bone.head == bone.parent.tail:
            bone.use_connect = True  # avoid connecting separated bones
    # find tail:
    if not bone.children:
        # if leaf, we assume a point in leaf_points exists
        tail_offs = next(v for k, v in segment_points[b_name].items()
                         if k in leaf_points)
    else:
        # get first joint that contains this bone as parent
        j = next(p1 for ((c1, p1), _) in joints if c1 == b_name)
        tail_offs = segment_points[b_name][j]
    bone.tail = bone.head + tail_offs


def glob_to_rel_quats(quaternions, joints, name_to_idx_map):
    """
    :param list quaternions: [q1, q2, ...]
    :param joints: A list of segment connections in the form
      [(c1_ori, c1_dest), (c2_ori, c2_dest), ...], where the connections reflect
      a tree and are giving in topological order.
    :param dict name_to_idx_map: A dict in the form {seg_name: idx, ...} where
      The quaternion for the segment seg_name can be found in quaternions[idx].

    Given the list of MVNX quaternions and their tree relations,
    return a list with same shape, but each quaternion has been rotated
    up its whole tree.

    .. warning::
      This function assumes that the joints are given topologically sorted,
      i.e. that all parents prior to the current connection have been already
      visited when iterating the joint list from left to right (starting with
      the roots, and going down the leafs in order).
    """
    result = [q.copy() for q in quaternions]

    for c_ori, c_dest in joints:
        q_ori = quaternions[name_to_idx_map[c_ori]]
        q_dest = result[name_to_idx_map[c_dest]]
        q_dest.rotate(q_ori.conjugated())
    return result

    # for c_ori, c_dest in joints:
    #     mat_ori = quaternions[name_to_idx_map[c_ori]].to_matrix()
    #     mat_dest = result[name_to_idx_map[c_dest]].to_matrix()
    #     m = mat_ori.inverted() @ mat_dest
    #     quaternions[name_to_idx_map[c_dest]] = m.to_quaternion()
    # return quaternions

    # print("\n\n\n")
    # for c_ori, c_dest in joints:
    #     q_ori = quaternions[name_to_idx_map[c_ori]]
    #     q_dest = quaternions[name_to_idx_map[c_dest]]
    #     print(">>>>>>>> rotating", c_dest, q_dest, " based on its parent", c_ori, q_ori)
    #     q_dest.rotate(q_ori.conjugated())
    #     print("       result:", quaternions[name_to_idx_map[c_dest]])
    # print("\n\n\n\n!!!!!!!!!!!", quaternions)

    # return quaternions


# #############################################################################
# ## IMPORTER
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
    """
    """
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

    _, joints = mvnx.extract_joints()
    joints_lite = [(ori, dest) for ((ori, _), (dest, _)) in joints]
    #
    num_segments = int(frames_metadata["segmentCount"])
    # num_sensors = frames_metadata["sensorCount"]
    # num_joints = frames_metadata["jointCount"]
    num_normal_frames = len (normal_frames)
    num_frames = num_normal_frames + 2  # f[0]=ident, f[1]=tpose, f[2:]=normal
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
    for parent_n, child_n in joints_lite: # conn1, conn2 in joints:
        # set parenthood
        edit_bones[seg2idx[child_n]].parent = edit_bones[seg2idx[parent_n]]
    # set heads and tails, as well as other edit bone properties:
    for b in edit_bones:
        set_bone_head_and_tail(b, segment_points, joints)
        # b.use_inherit_rotation = False  # True is better

    # Animation part:

    # prepare animation: create action and assign it to the armature
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    context.view_layer.update()
    arm_ob.animation_data_create()
    action = bpy.data.actions.new(name=mvnx_filename)
    arm_ob.animation_data.action = action
    pose_bones = [arm_ob.pose.bones[b.name] for b in edit_bones]
    pb_roots = {b for b in pose_bones if b.parent is None}

    # one we switched out of EDIT mode, bones with coordinates can be retrieved
    def get_edit_bone(eb_name):
        """
        Returns an EditBone by name in a way that matrix_local can be accessed.
        """
        return bpy.data.objects[mvnx_filename].data.bones[eb_name]

    def get_pose_bone(pb_name):
        """
        Returns a PoseBone by name in a way that matrix_basis and rotation
        datacan be accessed.
        """
        return bpy.data.objects[mvnx_filename].pose.bones[pb_name]

    # these matrices convert from the global coordinates to bone in rest pos.
    eb_matrices = {b.name: get_edit_bone(b.name).matrix_local.copy()
                   for b in edit_bones}
    # the inverses convert from rest bone coords to global (inverted_safe?)
    eb_matrices_inv = {k: v.inverted() for k, v in eb_matrices.items()}

    # MVNX gives positions and orientations with respect to a earth-based frame
    # where (x, y, z) == (north, west, up).
    # We assume that Blender's right-hand coord system also has that exact
    # meaning, but the PoseBone rotations have to be given WITH RESPECT TO
    # THE BONE. And the bone itself inherits the rotation from all its parents.
    # Therefore, these two closures handle the conversion of location and
    # orientation information from MVNX to Blender formats.
    def global_loc_to_bone(g_loc, bone_name):
        """
        :param Vector g_loc: (x, y, z) global position vector
        :returns: same vector expressed in terms of the bone basis. If the
          output is applied to the bone, it will appear in the global g_loc.
        """
        # this replicates the implementation in the BVH input plugin
        eb = get_edit_bone(bone_name)
        bone_transl_mat = Matrix.Translation(g_loc - eb.head)
        b_loc = (eb_matrices_inv[bone_name] @ bone_transl_mat).to_translation()
        return b_loc

    def global_quat_to_bone(g_quat, bone_name):
        """
        """
        g_quat_mat = g_quat.to_matrix().to_4x4()
        #
        b = eb_matrices_inv[bone_name] @ g_quat_mat @ eb_matrices[bone_name]
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
                kf_points.add(num_frames)  # f[0]=ident, f[1]=tpose
        # fill rotation fcurves
        pb.rotation_mode = "QUATERNION"
        rot_dp = 'pose.bones["%s"].rotation_quaternion' % pb.name
        for dim_rot in range(4):
            fcurve = action.fcurves.new(data_path=rot_dp, index=dim_rot)
            fcurves[pb.name]["ori"].append(fcurve)
            kf_points = fcurve.keyframe_points
            kf_points.add(num_frames)  # f[0]=ident, f[1]=tpose








    
    # # fill the identity as frame[0] and tpose as frame[1]s
    # identity_frame = [f for f in config_frames if f["type"] == "identity"][0]
    # id_quats_glob = [Quaternion(identity_frame["orientation"][i:i+4])
    #                  for i in range(0, 4*num_segments, 4)]
    # id_quats_rel = glob_to_rel_quats(id_quats_glob, joints_lite, seg2idx)
    # #
    # tpose_frame = [f for f in config_frames if f["type"] == "tpose"][0]
    # tp_quats_glob = [Quaternion(tpose_frame["orientation"][i:i+4])
    #                  for i in range(0, 4*num_segments, 4)]
    # tp_quats_rel = glob_to_rel_quats(tp_quats_glob, joints_lite, seg2idx)


    # # identity_frame["orientation"] = [Quaternion(identity_frame["orientation"][i:i+4])
    # #                                  for i in range(0, 4*num_segments, 4)]

    # # glob_to_rel_quaternions(quaternions, joints, name_to_idx_map): asdf

    
    # for b_name, fc_dd in fcurves.items():
    #     pb_idx = seg2idx[b_name]
    #     pb_idx_3, pb_idx_4 = pb_idx * 3, pb_idx * 4
    #     # set location, if existing:
    #     if fc_dd["loc"]:
    #         g_id_loc = Vector(identity_frame["position"][pb_idx_3: pb_idx_3+3])
    #         b_id_loc = global_loc_to_bone(g_id_loc, b_name)
    #         g_tp_loc = Vector(tpose_frame["position"][pb_idx_3: pb_idx_3+3])
    #         b_tp_loc = global_loc_to_bone(g_tp_loc, b_name)
    #         for loc_fc, loc_id, loc_tp in zip(fc_dd["loc"], b_id_loc, b_tp_loc):
    #             loc_fc.keyframe_points[0].co.x = 0
    #             loc_fc.keyframe_points[0].co.y = loc_id
    #             loc_fc.keyframe_points[1].co.x = 1
    #             loc_fc.keyframe_points[1].co.y = loc_tp

    #     # set orientation
    #     # g_id_q = Quaternion(identity_frame["orientation"][
    #     #     pb_idx_4: pb_idx_4+4])
    #     g_id_q = id_quats_rel[pb_idx]
    #     b_id_q = global_quat_to_bone(g_id_q, b_name)
    #     # g_tp_q = Quaternion(tpose_frame["orientation"][
    #     #     pb_idx_4: pb_idx_4+4])
    #     g_tp_q = tp_quats_rel[pb_idx]
    #     b_tp_q = global_quat_to_bone(g_tp_q, b_name)
    #     ### get_pose_bone(b_name).rotation_quaternion = b_tp_q
    #     for ori_fc, ori_id, ori_tp in zip(fc_dd["ori"], b_id_q, b_tp_q):
    #         ori_fc.keyframe_points[0].co.x = 0
    #         ori_fc.keyframe_points[0].co.y = ori_id
    #         ori_fc.keyframe_points[1].co.x = 1
    #         ori_fc.keyframe_points[1].co.y = ori_tp





    # fill frames (starting at 2 and incrementing by 1)
    for frame_i, frame in enumerate(normal_frames, 2):
        print("...filling frame", frame_i)
        frame_pos = [frame["position"][i: i+3]
                     for i in range(0, 3 * num_segments, 3)]
        frame_ori = [Quaternion(frame["orientation"][i:i+4])
                     for i in range(0, 4*num_segments, 4)]
        frame_ori_rel = glob_to_rel_quats(frame_ori, joints_lite, seg2idx)
        for pb, glob_loc, glob_ori in zip(pose_bones, frame_pos, frame_ori_rel):
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
                bone_ori = global_quat_to_bone(glob_ori, b_name)
                # get_pose_bone(b_name).rotation_quaternion = bone_ori
                for ori_fc, ori_entry in zip(ori_fcurves, bone_ori):
                    ori_fc.keyframe_points[frame_i].co.x = frame_i
                    ori_fc.keyframe_points[frame_i].co.y = ori_entry

    # finally config curves, apply matrix and return armature
    for c in action.fcurves:
        # if IMPORT_LOOP:
        #     pass  # 2.5 doenst have cyclic now?
        for ckfp in c.keyframe_points:
            ckfp.interpolation = "CONSTANT" #  "LINEAR"
    # arm_ob.matrix_world = global_matrix
    # bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    return arm_ob
