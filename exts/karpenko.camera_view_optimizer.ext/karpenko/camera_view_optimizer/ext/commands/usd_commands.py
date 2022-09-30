from typing import List

import omni.kit.commands
import omni.timeline
import omni.usd
from pxr import UsdGeom


class HideSelectedPrimsCommand(omni.kit.commands.Command):
    """
    Hides the selected primitives undoable **Command**.

    Args:
        selected_paths (List[str]): Old selected prim paths.
    """

    def __init__(self, selected_paths: List[str]):
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()
        self._selected_paths = selected_paths.copy()

    def _hide(self):
        for selected_path in self._selected_paths:
            selected_prim = self._stage.GetPrimAtPath(selected_path)
            imageable = UsdGeom.Imageable(selected_prim)
            imageable.MakeInvisible()

    def _show(self):
        for selected_path in self._selected_paths:
            selected_prim = self._stage.GetPrimAtPath(selected_path)
            imageable = UsdGeom.Imageable(selected_prim)
            imageable.MakeVisible()

    def do(self):
        self._hide()

    def undo(self):
        self._show()
