#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""


__author__ = "Andres FR"

from os.path import basename
#
import bpy
from mathutils import Vector, Quaternion  # , Euler
#
from .mvnx import Mvnx
from .utils import str_to_vec, is_number

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

KEYPOINTS_TO_MVNX = {"Hips": ("Pelvis", "pHipOrigin"),  # 100y   100z   100x
                     #
                     "Chest": ("Pelvis", "jL5S1"),
                     "Chest2": ("L5", "jL4L3"),
                     "Chest3": ("L3", "jL1T12"),
                     "Chest4": ("T12", "jT9T8"),
                     "Neck": ("T8", "jT1C7"),
                     "Head": ("Neck", "jC1Head",
                              "Head", "pTopOfHead"),
                     #
                     "RightCollar": ("T8", "jRightT4Shoulder"),
                     "RightShoulder": ("RightShoulder", "jRightShoulder"),
                     "RightElbow": ("RightUpperArm", "jRightElbow"),
                     "RightWrist": ("RightForeArm", "jRightWrist",
                                    "RightHand", "pRightTopOfHand"),
                     #
                     "LeftCollar": ("T8", "jLeftT4Shoulder"),
                     "LeftShoulder": ("LeftShoulder", "jLeftShoulder"),
                     "LeftElbow": ("LeftUpperArm", "jLeftElbow"),
                     "LeftWrist": ("LeftForeArm", "jLeftWrist",
                                   "LeftHand", "pLeftTopOfHand"),
                     #
                     "RightHip": ("Pelvis", "jRightHip"),
                     "RightKnee": ("RightUpperLeg", "jRightKnee"),
                     "RightAnkle": ("RightLowerLeg", "jRightAnkle"),
                     "RightToe": ("RightFoot", "jRightBallFoot",
                                  "RightToe", "pRightToe"),
                     #
                     "LeftHip": ("Pelvis", "jLeftHip"),
                     "LeftKnee": ("LeftUpperLeg", "jLeftKnee"),
                     "LeftAnkle": ("LeftLowerLeg", "jLeftAnkle"),
                     "LeftToe": ("LeftFoot", "jLeftBallFoot",
                                 "LeftToe", "pLeftToe")}


FULL_BVH_HUMAN = {"Hips":
                  {"Chest":
                   {"Chest2":
                    {"Chest3":
                     {"Chest4":
                      {"Neck": "Head",
                       "RightCollar":
                       {"RightShoulder": {"RightElbow": "RightWrist"}},
                       "LeftCollar":
                       {"LeftShoulder": {"LeftElbow": "LeftWrist"}}
                      }
                     }
                    }
                   },
                   "RightHip": {"RightKnee": {"RightAnkle": "RightToe"}},
                   "LeftHip": {"LeftKnee": {"LeftAnkle": "LeftToe"}}}}

class BoneNode:
    """
    """
    def __init__(self, name, offsets, children=[]):
        """
        """
        self.parent = self
        self.name = name
        self.offsets = offsets
        self.children = children
        for ch in self.children:
            ch.parent = self

    def __str__(self):
        return "<BoneNode: %s=%s>" % (self.name, str(self.offsets))

def make_bonenode_forest(name_tree, offsets):
    """
    :param mvnx_segments: a dict
    """
    if isinstance(name_tree, str):
        return [BoneNode(name_tree,
                         [Vector(str_to_vec(x)) for x in offsets[name_tree]])]
    else:
        roots = [BoneNode(k, [Vector(str_to_vec(x)) for x in offsets[k]],
                          make_bonenode_forest(v, offsets))
                 for k, v in name_tree.items()]
        return roots


def parse_skeleton(mvnx, skeleton=FULL_BVH_HUMAN,
                   skel_to_mvnx_map=KEYPOINTS_TO_MVNX):
    """
    """
    segments = {s.attrib["id"]: s for s
                in mvnx.mvnx.subject.segments.iterchildren()}
    offsets = {(s.attrib["label"], p.attrib["label"]): p.pos_b.text
               for s in segments.values()
               for p in s.points.iterchildren()}
    # a dict in the form {"Head": ["1 2 3", "4 5 6"], "Hips": ["0 0 0"], ...}
    skel_to_offsets = {k: [offsets[v[i:i+2]] for i in range(0, len(v), 2)]
                       for k, v in skel_to_mvnx_map.items()}
    forest = make_bonenode_forest(skeleton, skel_to_offsets)
    return segments, forest


def create_blender_figure(bone_node, arm_data, parent=None,
                          root_head=Vector((-0.01, 0, 0))):
    """
    """
    # if BoneNode has no children, we expect 2 offsets
    if not bone_node.children:
        # expect 2 offsets:
        offs1, offs2 = bone_node.offsets
        b = arm_data.edit_bones.new(bone_node.name + "Top")
        if parent is not None:
            b.use_connect = True
            b.parent = parent
            b.head = parent.tail
        else:  # handle the root-without-children case
            b.head = offs1
        b.tail = b.head + offs2
        return b
    else:
        # expect 1 offset only:
        offs = bone_node.offsets[0]
        # handle the root-with-children case:
        if parent is None:
            parent = arm_data.edit_bones.new(bone_node.name)
            parent.head = root_head
            parent.tail = offs
            #
        for ch in bone_node.children:
            b = arm_data.edit_bones.new(ch.name)
            b.use_connect = True
            b.parent = parent
            b.head = parent.tail
            b.tail = b.head + ch.offsets[0]
            #
            create_blender_figure(ch, arm_data, b, root_head)
        return parent




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
    frames_metadata, config_frames, normal_frames = mvnx.extract_frame_info()
    num_segments = int(frames_metadata["segmentCount"])
    # num_sensors = frames_metadata["sensorCount"]
    # num_joints = frames_metadata["jointCount"]
    num_frames = len(normal_frames) + 1  # +1 for the tpose
    frame_rate = int(mvnx.mvnx.subject.attrib["frameRate"])


    # create armature and prepare to fill it
    bpy.ops.object.select_all(action='DESELECT')
    arm_data = bpy.data.armatures.new(mvnx_filename)
    arm_ob = bpy.data.objects.new(mvnx_filename, arm_data)
    context.collection.objects.link(arm_ob)
    arm_ob.select_set(True)
    context.view_layer.objects.active = arm_ob
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    # fill the armature with the skeleton definition
    segments, forest = parse_skeleton(mvnx, FULL_BVH_HUMAN, KEYPOINTS_TO_MVNX)
    edit_bone_roots = [create_blender_figure(b, arm_data) for b in forest]


    ### SANDBOX

    # ANIMATION

    # prepare animation: create action and assign it to the armature
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    context.view_layer.update()
    arm_ob.animation_data_create()
    action = bpy.data.actions.new(name=mvnx_filename)
    arm_ob.animation_data.action = action
    pose_bones = arm_ob.pose.bones

    # set anim speed. actual_fps = scene.render.fps / scene.render.fps_base
    context.scene.render.fps_base = 1.0
    context.scene.render.fps = frame_rate

    # extract orientations and positions from normal frames, and tpose frame
    positions, orientations = [], []  # list of lists (frame->segment)
    for f in normal_frames:
        fp, fo = f["position"], f["orientation"]
        positions.append([fp[i:i + 3] for i in range(0, 3 * num_segments, 3)])
        orientations.append([fo[i:i + 4]
                             for i in range(0, 4 * num_segments, 4)])
    tpose_frame = [f for f in config_frames if f["type"] == "tpose"][0]


    # iterate over all bones:
    for bone_i, pb in enumerate(pose_bones): # PROBLEM: ARE POSE_BONES IN THE SAME ORDER AS OUR MVNX SEQUENCES???
        print(">>>>>>>>>>", bone_i, pb.name)
        pb.rotation_mode = "QUATERNION"
        rot_datapath = 'pose.bones["%s"].rotation_quaternion' %  pb.name

        # handle location info
        has_location = not pb.bone.use_connect
        if has_location:
            report({'INFO'}, "Setting location data for " + pb.name)
            loc_dp = 'pose.bones["%s"].location' %  pb.name  # datapath
            # iterate over 3 dimensions: x, y, z
            for dim_i in range(3):
                curve = action.fcurves.new(data_path=loc_dp, index=dim_i)
                kf_points = curve.keyframe_points
                kf_points.add(num_frames)  # t-pose will be at frame 0
                for frame_i, pos_frame in enumerate(positions, 1):  # normal frames begin at 1 (0 is for t-pose)
                    kf_points[frame_i].co = (frame_i, pos_frame[bone_i][dim_i])


        # matts = [Quaternion(oo).to_matrix().to_4x4() for oo in o]
        # print(matts)

        # asdf

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




    # TODO: 1. create the armature for the skeleton analogously to the BVH, in tpose
    # 2. create the keyframes and fill them with the quaternions, analogously to the BVH.
    # 3. details like rescaling, more UI, TIME PRECISION...

    # 1. load the armature.data.bones[...].matrix_local for each bone in order, in case needs to be inverted
    # 2. load the rotation quaternions from the MVNX and convert them to "matrix" using the API
    # 3??


    ### END OF SANDBOX
    ###







# def bvh_node_dict2armature(
#         context,
#         bvh_name,
#         bvh_nodes,
#         bvh_frame_time,
#         rotate_mode='XYZ',
#         frame_start=1,
#         IMPORT_LOOP=False,
#         global_matrix=None,
#         use_fps_scale=False,
# ):

#     if frame_start < 1:
#         frame_start = 1

#     # Add the new armature,
#     scene = context.scene
#     for obj in scene.objects:
#         obj.select_set(False)

#     arm_data = bpy.data.armatures.new(bvh_name)
#     arm_ob = bpy.data.objects.new(bvh_name, arm_data)

#     context.collection.objects.link(arm_ob)

#     arm_ob.select_set(True)
#     context.view_layer.objects.active = arm_ob

#     bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
#     bpy.ops.object.mode_set(mode='EDIT', toggle=False)

#     bvh_nodes_list = sorted_nodes(bvh_nodes)

#     # Get the average bone length for zero length bones, we may not use this.
#     average_bone_length = 0.0
#     nonzero_count = 0
#     for bvh_node in bvh_nodes_list:
#         l = (bvh_node.rest_head_local - bvh_node.rest_tail_local).length
#         if l:
#             average_bone_length += l
#             nonzero_count += 1

#     # Very rare cases all bones could be zero length???
#     if not average_bone_length:
#         average_bone_length = 0.1
#     else:
#         # Normal operation
#         average_bone_length = average_bone_length / nonzero_count

#     # XXX, annoying, remove bone.
#     while arm_data.edit_bones:
#         arm_ob.edit_bones.remove(arm_data.edit_bones[-1])

#     ZERO_AREA_BONES = []
#     for bvh_node in bvh_nodes_list:

#         # New editbone
#         bone = bvh_node.temp = arm_data.edit_bones.new(bvh_node.name)

#         bone.head = bvh_node.rest_head_world
#         bone.tail = bvh_node.rest_tail_world

#         # Zero Length Bones! (an exceptional case)
#         if (bone.head - bone.tail).length < 0.001:
#             print("\tzero length bone found:", bone.name)
#             if bvh_node.parent:
#                 ofs = bvh_node.parent.rest_head_local - bvh_node.parent.rest_tail_local
#                 if ofs.length:  # is our parent zero length also?? unlikely
#                     bone.tail = bone.tail - ofs
#                 else:
#                     bone.tail.y = bone.tail.y + average_bone_length
#             else:
#                 bone.tail.y = bone.tail.y + average_bone_length

#             ZERO_AREA_BONES.append(bone.name)

#     for bvh_node in bvh_nodes_list:
#         if bvh_node.parent:
#             # bvh_node.temp is the Editbone

#             # Set the bone parent
#             bvh_node.temp.parent = bvh_node.parent.temp

#             # Set the connection state
#             if(
#                     (not bvh_node.has_loc) and
#                     (bvh_node.parent.temp.name not in ZERO_AREA_BONES) and
#                     (bvh_node.parent.rest_tail_local == bvh_node.rest_head_local)
#             ):
#                 bvh_node.temp.use_connect = True

#     # Replace the editbone with the editbone name,
#     # to avoid memory errors accessing the editbone outside editmode
#     for bvh_node in bvh_nodes_list:
#         bvh_node.temp = bvh_node.temp.name





#     # Now Apply the animation to the armature

#     # Get armature animation data
#     bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

#     pose = arm_ob.pose
#     pose_bones = pose.bones

#     if rotate_mode == 'NATIVE':
#         for bvh_node in bvh_nodes_list:
#             bone_name = bvh_node.temp  # may not be the same name as the bvh_node, could have been shortened.
#             pose_bone = pose_bones[bone_name]
#             pose_bone.rotation_mode = bvh_node.rot_order_str

#     elif rotate_mode != 'QUATERNION':
#         for pose_bone in pose_bones:
#             pose_bone.rotation_mode = rotate_mode
#     else:
#         # Quats default
#         pass

#     context.view_layer.update()

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

#         if 0 == num_frame:
#             num_frame = len(bvh_node.anim_data)

#     # Choose to skip some frames at the beginning. Frame 0 is the rest pose
#     # used internally by this importer. Frame 1, by convention, is also often
#     # the rest pose of the skeleton exported by the motion capture system.
#     skip_frame = 1
#     if num_frame > skip_frame:
#         num_frame = num_frame - skip_frame

#     # Create a shared time axis for all animation curves.
#     time = [float(frame_start)] * num_frame
#     if use_fps_scale:
#         dt = scene.render.fps * bvh_frame_time
#         for frame_i in range(1, num_frame):
#             time[frame_i] += float(frame_i) * dt
#     else:
#         for frame_i in range(1, num_frame):
#             time[frame_i] += float(frame_i)

#     # print("bvh_frame_time = %f, dt = %f, num_frame = %d"
#     #      % (bvh_frame_time, dt, num_frame]))

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
