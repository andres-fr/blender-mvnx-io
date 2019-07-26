#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module contains functionality concerning the adaption of the
XSENS MVN-XML format into our Python setup.

The official explanation can be found in section 14.4 of this document::
  https://usermanual.wiki/Document/MVNUserManual.1147412416.pdf

A copy is stored in this repository.

The following section introduces more informally the contents of the imported
MVN file and the way they can be accessed from Python::

  # MVNX schemata can be found in this package or in
  # https://www.xsens.com/mvn/mvnx/schema.xsd
  mvn_path = "XXX"
  mmvn = Mvnx(mvn_path)

  # These elements contain some small metadata:
  mmvn.mvnx.attrib
  mmvn.mvnx.comment.attrib
  mmvn.mvnx.securityCode.attrib["code"]
  mmvn.mvnx.subject.attrib

  # subject.segments contain 3D pos_b labels:
  for ch in mmvn.mvnx.subject.segments.iterchildren():
      ch.attrib, [p.attrib for p in ch.points.iterchildren()]

  # Segments can look as follows: ``['Pelvis', 'L5', 'L3', 'T12', 'T8', 'Neck',
  'Head', 'RightShoulder', 'RightUpperArm', 'RightForeArm', 'RightHand',
  'LeftShoulder', 'LeftUpperArm', 'LeftForeArm', 'LeftHand', 'RightUpperLeg',
  'RightLowerLeg', 'RightFoot', 'RightToe', 'LeftUpperLeg', 'LeftLowerLeg',
  'LeftFoot', 'LeftToe']``

  # sensors is basically a list of names
  for s in mmvn.mvnx.subject.sensors.iterchildren():
      s.attrib

  #  Joints is a list that connects segment points:
  for j in mmvn.mvnx.subject.joints.iterchildren():
      j.attrib["label"], j.getchildren()

  # miscellaneous:
  for j in mmvn.mvnx.subject.ergonomicJointAngles.iterchildren():
      j.attrib, j.getchildren()

  for f in mmvn.mvnx.subject.footContactDefinition.iterchildren():
      f.attrib, f.getchildren()

  # The bulk of the data is in the frames.
  frames_metadata, config_frames, normal_frames = mmvn.extract_frame_info()

  # Metadata looks like this:
  {'segmentCount': '23', 'sensorCount': '17', 'jointCount': '22'}

  # config frames have the following fields:
  ['orientation', 'position', 'time', 'tc', 'ms', 'type']

  # normal frames have the following fields:
  ['orientation', 'position', 'velocity', 'acceleration',
   'angularVelocity', 'angularAcceleration', 'footContacts',
   'sensorFreeAcceleration', 'sensorMagneticField', 'sensorOrientation',
   'jointAngle', 'jointAngleXZY', 'jointAngleErgo', 'centerOfMass', 'time',
   'index', 'tc', 'ms', 'type']

The following fields contain metadata about the frame:

:time: ms since start (integer). It is close to
  ``int(1000.0 * index / samplerate)``, being equal most of the times and
  at most 1 milisecond away. It is neither truncated nor rounded, maybe it
  is given by the hardware.
:index: starts with 0, +1 each normal frame
:tc: string like '02:23:28:164'
:ms: unix timestamp like 1515983008686 (used to compute time)
:type: one of "identity", "tpose", "tpose-isb", "normal"

# The following fields are float vectors of the following dimensionality:

:orientation: ``segmentCount*4 = 92`` Quaternion vector
:position, velocity, acceleration, angularVelocity, angularAcceleration:
  ``segmentCount*3 = 69`` 3D vectors in ``(x,y,z)`` format
:footContacts: ``4`` 4D boolean vector
:sensorFreeAcceleration, sensorMagneticField: ``sensorCount*3 = 51``
:sensorOrientation: ``sensorCount*4 = 68``
:jointAngle, jointAngleXZY: ``jointCount*3 = 66``
:jointAngleErgo: ``12``
:centerOfMass: ``3``

The units are SI for position, velocity and acceleration. Angular magnitudes
are in radians except the ``jointAngle...`` ones that are in degrees. All 3D
vectors are in ``(x,y,z)`` format, but the ``jointAngle...`` ones differ in
the Euler-rotation order by which they are computed (ZXY, standard or XZY,
for shoulders usually).
"""


__author__ = "Andres FR"


from lxml import etree, objectify  # https://lxml.de/validation.html
from .utils import make_timestamp  # , resolve_path


# #############################################################################
# ## GLOBALS
# #############################################################################


# #############################################################################
# ## HELPERS
# #############################################################################


# #############################################################################
# ## MVNX CLASS
# #############################################################################

class Mvnx:
    """
    This class imports and adapts an XML file (expected to be in MVNX format)
    to a Python-friendly representation. See this module's docstring for usage
    examples and more information.
    """
    def __init__(self, mvnx_path, mvnx_schema_path=None):
        """
        :param str mvnx_path: a valid path pointing to the XML file to load
        :param str mvnx_schema_path: (optional): if given, the given MVNX will
          be validated against this XML schema definition.
        """
        self.mvnx_path = mvnx_path
        #
        mvnx = etree.parse(mvnx_path)
        # if a schema is given, load it and validate mvn
        if mvnx_schema_path is not None:
            self.schema = etree.XMLSchema(file=mvnx_schema_path)
            self.schema.assertValid(mvnx)
        #
        self.mvnx = objectify.fromstring(etree.tostring(mvnx))

    def export(self, filepath, pretty_print=True, extra_comment=""):
        """
        Saves the current ``mvnx`` attribute to the given file path as XML and
        adds the ``self.mvnx.attrib["pythonComment"]`` attribute with
        a timestamp.
        """
        #
        with open(filepath, "w") as f:
            msg = "Exported from %s on %s. " % (
                self.__class__.__name__, make_timestamp()) + extra_comment
            self.mvnx.attrib["pythonComment"] = msg
            s = etree.tostring(self.mvnx,
                               pretty_print=pretty_print).decode("utf-8")
            f.write(s)
            print("[Mvnx] exported to", filepath)

    # EXTRACTORS: LIKE "GETTERS" BUT RETURN A MODIFIED COPY OF THE CONTENTS
    def extract_frame_info(self):
        """
        :returns: The tuple ``(frames_metadata, config_frames, normal_frames)``
        """
        f_meta, config_f, normal_f = self.extract_frames(self.mvnx)
        frames_metadata = f_meta
        config_frames = config_f
        normal_frames = normal_f
        #
        assert (int(frames_metadata["segmentCount"]) ==
                len(self.extract_segments())), "Inconsistent segmentCount?"
        return frames_metadata, config_frames, normal_frames

    @staticmethod
    def extract_frames(mvnx):
        """
        The bulk of the MVNX file is the ``mvnx->subject->frames`` section.
        This function parses it and returns its information in a
        python-friendly format.

        :param mvnx: An XML tree, expected to be in MVNX format

        :returns: a tuple ``(frames_metadata, config_frames, normal_frames)``
          where the metadata is a dict in the form ``{'segmentCount': '23',
          'sensorCount': '17', 'jointCount': '22'}``, the config frames are the
          first 3 frame entries (expected to contain special config info)
          and the normal_frames are all frames starting from the 4th. Both
          frame outputs are relational collections of dictionaries that can be
          formatted into tabular form.
        """
        def frame_to_dict(frame, is_normal):
            """
            A frame node has a dict of ``attribs`` and a dict of ``items``.
            This function merges both and returns a single python dict
            """
            def str_to_vec(x):
                """
                Converts a node with a text like '1.23, 2.34 ...' into a list
                like [1.23, 2.34, ...]
                """
                return [float(y) for y in x.text.split(" ")]

            d = {**{k: str_to_vec(v) for k, v in frame.__dict__.items()},
                 **frame.attrib}
            d["time"] = int(d["time"])  # ms since start, i.e. ms_i - ms_0
            d["ms"] = int(d["ms"])  # unix timestamp, ms since epoch
            if is_normal:  # only normal frames have index
                d["index"] = int(d["index"])  # starts by 0, increases by 1
            try:
                d["audio_sample"] = int(d["audio_sample"])
            except KeyError:
                pass
            return d
        #
        frames_metadata = mvnx.subject.frames.attrib
        all_frames = mvnx.subject.frames.getchildren()
        # first 3 frames are config. types: "identity", "tpose", "tpose-isb"
        # rest of frames contain proper data. type: "normal"
        config_frames = [frame_to_dict(f, False) for f in all_frames[:3]]
        normal_frames = [frame_to_dict(f, True) for f in all_frames[3:]]
        #
        return frames_metadata, config_frames, normal_frames

    def extract_segments(self):
        """
        :returns: A list of the segment names in ``self.mvnx.subject.segments``
          ordered by id (starting at 1 and incrementing +1).
        """
        segments = [ch.attrib["label"] if str(i) == ch.attrib["id"] else None
                    for i, ch in enumerate(
                            self.mvnx.subject.segments.iterchildren(), 1)]
        assert all([s is not None for s in segments]),\
            "Segments aren't ordered by id?"
        return segments
