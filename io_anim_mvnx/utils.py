# -*- coding:utf-8 -*-


"""
Utilities for interaction with Blender
"""


__author__ = "Andres FR"


import os
import argparse
import sys
import datetime
import pytz
from math import radians  # degrees
# mathutils is a blender package
from mathutils import Euler  # , Vector
from bpy.types import PropertyGroup
from bpy.props import StringProperty
#
from . import __path__ as PACKAGE_ROOT_PATH


# #############################################################################
# ## HELPERS
# #############################################################################

def make_timestamp(timezone="Europe/Berlin"):
    """
    Output example: day, month, year, hour, min, sec, milisecs:
    10_Feb_2018_20:10:16.151
    """
    ts = datetime.datetime.now(tz=pytz.timezone(timezone)).strftime(
        "%d_%b_%Y_%H:%M:%S.%f")[:-3]
    return "%s (%s)" % (ts, timezone)


# #############################################################################
# ## ENVIRONMENT
# #############################################################################

def resolve_path(*path_elements):
    """
    A convenience path wrapper to find elements in this package. Retrieves
    the absolute path, given the OS-agnostic path relative to the package
    root path (by bysically joining the path elements via ``os.path.join``).
    E.g., the following call retrieves the absolute path for
    ``<PACKAGE_ROOT>/a/b/test.txt``::

       resolve_path("a", "b", "test.txt")

    :params strings path_elements: From left to right, the path nodes,
       the last one being the filename.
    :rtype: str
    """
    p = tuple(PACKAGE_ROOT_PATH) + path_elements
    return os.path.join(*p)


class ArgumentParserForBlender(argparse.ArgumentParser):
    """
    This class is identical to its superclass, except for the parse_args
    method (see docstring). It resolves the ambiguity generated when calling
    Blender from the CLI with a python script, and both Blender and the script
    have arguments. E.g., the following call will make Blender crash because
    it will try to process the script's -a and -b flags:
    ::

       blender --python my_script.py -a 1 -b 2

    To bypass this issue this class uses the fact that Blender will ignore all
    arguments given after a double-dash ('--'). The approach is that all
    arguments before '--' go to Blender, arguments after go to the script.
    The following CLI calls work fine:
    ::

       blender --python my_script.py -- -a 1 -b 2
       blender --python my_script.py --
    """

    def get_argv_after_doubledash(self, argv):
        """
        :param list<str> argv: Expected to be sys.argv (or alike).
        :returns: The argv sublist after the first ``'--'`` element (if
           present, otherwise returns an empty list).
        :rtype: list of str

        .. note::
           Works with any *ordered* collection of strings (e.g. list, tuple).
        """
        try:
            idx = argv.index("--")
            return argv[idx+1:]  # the list after '--'
        except ValueError:  # '--' not in the list:
            return []

    # overrides superclass
    def parse_args(self):
        """
        This method is expected to behave identically as in the superclass,
        except that the sys.argv list will be pre-processed using
        get_argv_after_doubledash before. See the docstring of the class for
        usage examples and details.

        .. note::
           By default, `argparse.ArgumentParser` will call `sys.exit()` when
           encountering an error. Blender will react to that shutting down,
           making it look like a crash. Make sure the arguments are correct!
        """
        argv_after_dd = self.get_argv_after_doubledash(sys.argv)
        return super().parse_args(args=argv_after_dd)


# #############################################################################
# ## UI CONFIG HELPERS
# #############################################################################

class OperatorToMenuManager(list):
    """
    This class implements functionality for adding/removing operators
    into Blender UI menus. It also behaves like a regular list, holding
    the currently registered items. Usage example:
    ::

       omm = OperatorToMenuManager()
       # In register():
       omm.register(MyOperator, bpy.types.VIEW3D_MT_object)
       # ... in unregister():
       omm.unregister
    """

    def register(self, op_class, menu_class):
        """
        :param bpy.types.Operator op_class: (Sub)class handle with desired
           functionality.
        :param menu_class: Class handle for the Blender GUI where the
           functionality can be triggered.
        :type menu_class: bpy.types.{Header, Panel, ...}

        .. note::
           ``op_class`` must define the ``bl_idname`` and ``bl_label`` fields.
        """
        op_name, op_label = op_class.bl_idname, op_class.bl_label

        def menu_fn(self, context):
            """Small wrapper needed by the API"""
            self.layout.operator(op_name, text=op_label)

        menu_class.append(menu_fn)
        self.append((menu_class, menu_fn))

    def unregister(self):
        """
        Removes every mapped operator from every menu class in this collection,
        then empties the collection.
        """

        for menu_class, menu_fn in self:
            menu_class.remove(menu_fn)
        self.clear()


class KeymapManager(list):
    """
    This class implements functionality for registering/deregistering keymaps
    into Blender. It also behaves like a regular list, holding the keymaps
    currently registered. To inspect the registered keymaps simply iterate
    the instance.
    """

    KEYMAP_NAME = "Object Mode"  # ATM not well documented in the API
    KEYMAP_SPACE_TYPE = "EMPTY"  # ATM not well documented in the API
    KEYMAP_REGION_TYPE = "WINDOW"  # ATM not well documented in the API

    def register(self, context, key, stroke_mode, op_name,
                 ctrl=True, shift=True, alt=False):
        """
        Adds a new keymap to this collection, and to the config in
        ``context.window_manager.keyconfigs.addon``. See the API for details:

        | https://docs.blender.org/api/blender2.8/bpy.types.KeyMap.html
        | https://docs.blender.org/api/blender2.8/bpy.types.KeyMapItem.html
        | https://docs.blender.org/manual/de/dev/advanced/keymap_editing.html

        .. warning:
           For the moment, the keymaps were confirmed to work only when the
           mouse cursor is on the ``VIEW_3D`` area, and for the parameters
           ``name="Object Mode", space_type="EMPTY"``

        Usage example:
        ::

           kmm = KeymapManager()
           kmm.register(bpy.context, "D", "PRESS", MyOperator.bl_idname)

        :param bpy.types.Context context: The Blender context to work in.
        :param str key: See bpy.types.KeyMapItem.key_modifier
        :param str stroke_mode: See bpy.types.KeyMapItem.value
        :param str op_name: Name of a valid operation in ``bpy.ops``
           (usually the ``bl_idname``)
        :param booleans ctrl, shift, alt: Modifiers of the ``key``
        :returns: None
        """
        wm = context.window_manager
        kc = wm.keyconfigs.addon  # this is None in background mode
        if kc:
            km = kc.keymaps.new(name=self.KEYMAP_NAME,
                                space_type=self.KEYMAP_SPACE_TYPE,
                                region_type=self.KEYMAP_REGION_TYPE)
            kmi = km.keymap_items.new(op_name, key, stroke_mode,
                                      ctrl=ctrl, shift=shift, alt=alt)
            self.append((km, kmi))

    def unregister(self):
        """
        Removes every mapped item from every keymap in this collection, and
        then empties the collection.
        """
        for km, kmi in self:
            km.keymap_items.remove(kmi)
        self.clear()


class ImportFilesCollection(PropertyGroup):
    """
    This property group allows to load multiple files from the UI file browser
    menu, by selecting them with shift pressed.
    Source and usage example::

      https://www.blender.org/forum/viewtopic.php?t=26470
    """
    name: StringProperty(name="File Path",
                         description="Filepath used for importing the file",
                         maxlen=1024,
                         subtype='FILE_PATH')


# #############################################################################
# ## MATH
# #############################################################################

def rot_euler_degrees(rot_x, rot_y, rot_z, order="XYZ"):
    """
    :param float rot_: Rotation angle in degrees.
    :returns: An Euler rotation object with the given rotations (converted to
      gradians) and rotation order.
    """
    return Euler((radians(rot_x), radians(rot_y), radians(rot_z)), order)


def str_to_vec(s):
    """
    Converts a string like '1.23, 2.34 ...' into a list
    like [1.23, 2.34, ...]
    """
    return [float(x) for x in s.split(" ")]


def is_number(s):
    """
    :returns: True iff s is a number.
    """
    try:
        float(s)
        return True
    except ValueError:
        return False
