from typing import List

import omni.kit.commands
import omni.timeline
import omni.usd
from pxr import UsdGeom


class HideSelectedPrimsCommand(omni.kit.commands.Command):
    """
    Hides the selected primitives

    Args:
        selected_paths (List[str]): Prim paths.
    """

    def __init__(self, selected_paths: List[str]):
        """
        This function is called when the user clicks the button in the UI. It takes the list of selected 
        paths and stores it in the class
        
        :param selected_paths: List[str]
        :type selected_paths: List[str]
        """
        self._stage = omni.usd.get_context().get_stage()
        self._selected_paths = selected_paths.copy()

    def _hide(self):
        """
        This function takes the selected prims and makes them invisible
        """
        for selected_path in self._selected_paths:
            selected_prim = self._stage.GetPrimAtPath(selected_path)
            imageable = UsdGeom.Imageable(selected_prim)
            imageable.MakeInvisible()

    def _show(self):
        """
        It makes visible all the selected prims in the stage
        """
        for selected_path in self._selected_paths:
            selected_prim = self._stage.GetPrimAtPath(selected_path)
            imageable = UsdGeom.Imageable(selected_prim)
            imageable.MakeVisible()

    def do(self):
        self._hide()

    def undo(self):
        self._show()


class ShowSelectedPrimsCommand(omni.kit.commands.Command):
    """
    Shows the selected primitives

    Args:
        selected_paths (List[str]): Prim paths.
    """

    def __init__(self, selected_paths: List[str]):
        """
        This function is called when the user clicks the button in the UI. It takes the list of selected
        paths and stores it in the class
        
        :param selected_paths: List[str]
        :type selected_paths: List[str]
        """
        self._stage = omni.usd.get_context().get_stage()
        self._selected_paths = selected_paths.copy()

    def _hide(self):
        """
        This function takes the selected prims and makes them invisible
        """
        for selected_path in self._selected_paths:
            selected_prim = self._stage.GetPrimAtPath(selected_path)
            imageable = UsdGeom.Imageable(selected_prim)
            imageable.MakeInvisible()

    def _show(self):
        """
        It makes visible all the selected prims in the stage
        """
        for selected_path in self._selected_paths:
            selected_prim = self._stage.GetPrimAtPath(selected_path)
            imageable = UsdGeom.Imageable(selected_prim)
            imageable.MakeVisible()

    def do(self):
        self._show()

    def undo(self):
        self._hide()
