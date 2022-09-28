import math
import re

import omni.ext
import omni.kit.commands
import omni.kit.viewport_legacy
import omni.physx.scripts.utils as core_utils
import omni.ui as ui
import omni.usd
from omni.kit.viewport.utility import (get_active_viewport_camera_string,
                                       get_active_viewport_window,
                                       get_ui_position_for_prim)
from pxr import Gf, Sdf, Usd, UsdGeom

from .style import cvo_window_style


class CameraViewOptimizer(omni.ext.IExt):

    def optimize(self):
        """
        It's hiding all objects that are not visible from the camera
        """
        window = get_active_viewport_window()
        # Getting the camera path and prim from the stage.
        camera_path = get_active_viewport_camera_string()
        if not camera_path:
            return
        camera_prim = self.stage.GetPrimAtPath(camera_path)
        # get camera transform
        camera_translate = camera_prim.GetAttribute("xformOp:translate").Get()
        # It's a helper class that allows to get camera forward vector.
        camera_th = core_utils.CameraTransformHelper(camera_prim)
        # Get the vecotr of the camera forward direction.
        cameraForward = camera_th.get_forward()

        # It's creating a new translate location approximately 10 units forward from the camera.
        # It will be used to determinate if object is in front of the camera or not by comparing distances
        # between the camera and the object and the camera and the new translate location.
        camera_new_location = Gf.Vec3d(
            camera_translate[0]+(cameraForward[0] * 10),
            camera_translate[1]+(cameraForward[1] * 10),
            camera_translate[2]+(cameraForward[2] * 10)
        )

        # It's getting all visible objects from the stage.
        all_objects = self.get_all_objects()
        # return if there are no objects
        if not all_objects:
            return
        # It's creating a list of objects that not visible from the camera.
        not_visible = []
        # Get the camera focal length
        focal_length_param = Sdf.Path(f'{camera_path}.focalLength')
        focal_length = self.stage.GetPrimAtPath(Sdf.Path(camera_path)).GetAttribute('focalLength').Get()
        max_size = 150
        with omni.kit.undo.group():
            if all_objects:
                # Changing the value of the focal length parameter of the camera so we can scan more objects.
                omni.kit.commands.execute(
                    'ChangePropertyCommand',
                    prop_path=focal_length_param,
                    value=self._fov_slider.model.as_float,
                    prev=focal_length,
                    timecode=Usd.TimeCode.Default(),
                )

            for prim in all_objects:
                # Getting the position of the prim in the window.
                # Because it is a screen-space calculation, for some reason it returns is_visible=True when objects
                # is behind the camera.
                ui_position, is_visible = get_ui_position_for_prim(window, prim.GetPath(), alignment=None)
                # Getting the position of the prim in the world.
                prim_translate = prim.GetAttribute("xformOp:translate").Get()
                # Calculating the distance between the camera and the prim.
                distance_to_camera = self.get_distance_between_translations(camera_translate, prim_translate)
                # Calculating the distance between the camera and the new translate location.
                distance_to_cameraforward = self.get_distance_between_translations(camera_new_location, prim_translate)
                # If the distance between the camera and the prim is less than the distance between
                # the camera and the new translate location, which is 10 units forward from first locatio,
                #  it means that the prim is behind the camera.
                if is_visible:
                    if distance_to_cameraforward > distance_to_camera + 5:
                        is_visible = False

                is_distant = False
                # Hide if the object is too distant
                if distance_to_camera > self._max_distance_field.model.as_float:
                    is_visible = False
                    is_distant = True

                # Checking if the ignore_size_distant_objects is true and if the object is distant.
                if self._ignore_size_distant_objects.model.as_bool and is_distant:
                    pass
                else:
                    prim_size = self.get_prim_size(prim)
                    # If one of the dimensions of the prim is bigger than the limit, we will not consider to hide it.
                    if not is_visible and max_size != 0:
                        if max_size < prim_size[0] or max_size < prim_size[1] or max_size < prim_size[2]:
                            is_visible = True

                # Checking if the prim name matches the show or hide pattern.
                prim_name = prim.GetName()
                show_pattern = self._show_objects_field.model.as_string
                hide_pattern = self._hide_objects_field.model.as_string
                if show_pattern and (show_pattern.lower() in prim_name.lower() or re.match(show_pattern, prim_name)):
                    is_visible = True
                elif hide_pattern and (hide_pattern.lower() in prim_name.lower() or re.match(hide_pattern, prim_name)):
                    is_visible = False

                # Final checking if the prim is visible or not.
                if not is_visible:
                    not_visible.append({
                        "prim": prim,
                        "prim_path": prim.GetPath(),
                        "type": prim.GetTypeName(),
                    })
            # Creating a list of object types that are not allowed to be hidden.
            not_allowed_types = []
            # Check if we should hide lights as well
            if not self._hide_lights.model.as_bool:
                not_allowed_types.extend([
                    "DistantLight",
                    "SphereLight",
                    "DiskLight",
                    "RectLight",
                    "CylinderLight",
                    "ConeLight"]
                )
            if not_visible:
                omni.kit.commands.execute(
                    'ToggleVisibilitySelectedPrims',
                    selected_paths=[i["prim_path"] for i in not_visible if i["type"] not in not_allowed_types],
                )

            if focal_length:
                # Changing the focal length of the camera back to the value before the scan.
                omni.kit.commands.execute(
                    'ChangePropertyCommand',
                    prop_path=focal_length_param,
                    value=focal_length,
                    prev=self._fov_slider.model.as_float,
                    timecode=Usd.TimeCode.Default(),
                )

    def get_distance_between_translations(self, pos1, pos2):
        """
        It returns the distance between two translations

        :param pos1: The position of the first object
        :param pos2: The position of the object you want to measure the distance to
        :return: The distance between two points in 3D space.
        """
        if pos1 and pos2:
            return math.sqrt(
                (pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2 + (pos1[2] - pos2[2]) ** 2
            )
        return 0

    def get_prim_size(self, prim):
        """
        It returns the size of a prim in world space

        :param prim: The prim you want to get the size of
        :return: The size of the bounding box of the prim.
        """
        bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), includedPurposes=[UsdGeom.Tokens.default_])
        bbox_cache.Clear()
        prim_bbox = bbox_cache.ComputeWorldBound(prim)
        prim_range = prim_bbox.ComputeAlignedRange()
        return prim_range.GetSize()

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        print("[karpenko.camera_view_optimizer.ext] CameraViewOptimizer startup")
        self._usd_context = omni.usd.get_context()
        self.stage = self._usd_context.get_stage()
        self._window = ui.Window("Camera View Omptimizer", width=300, height=300)
        with self._window.frame:
            with ui.VStack(style=cvo_window_style):
                ui.Label("Camera View Optimizer", height=0, name="main_label")
                ui.Spacer(height=10)
                ui.Separator(height=6)
                ui.Spacer(height=10)
                with ui.ScrollingFrame(height=ui.Percent(63)):
                    with ui.VStack():
                        with ui.VStack():
                            with ui.HStack(height=0):
                                tooltip = "When checking the visibility of the object, the camera FOV will be set " \
                                            "to the value specified in the slider and then back once scan is complete"
                                ui.Label("Scan FOV (mm)", elided_text=True, tooltip=tooltip)
                                # Slider for the FOV value of the camera
                                self._fov_slider = ui.IntSlider(
                                    min=2,
                                    max=180,
                                    step=1,
                                    tooltip=tooltip,
                                )
                                self._fov_slider.model.set_value(8)

                        ui.Spacer(height=10)

                        with ui.HStack(height=0):
                            tooltip = "Ignore object if one of the three dimensions is greater than values provided," \
                                      "useful for walls, floors, etc."
                            ui.Label("Max size (mm)", elided_text=True, tooltip=tooltip)
                            # Slider for the max object size
                            self._max_size_slider = ui.IntField(
                                min=0,
                                max=100000,
                                step=1,
                                tooltip=tooltip,
                            )
                            self._max_size_slider.model.set_value(300)

                        ui.Spacer(height=10)

                        with ui.VStack():
                            tooltip = "Should the extension hide lights?"
                            # Available types of objects to hide
                            with ui.HStack(height=0):
                                ui.Label("Process Lights", elided_text=True, tooltip=tooltip, width=ui.Percent(50))
                                self._hide_lights = ui.CheckBox(tooltip=tooltip, width=ui.Percent(5))
                                ui.Line(name="default", width=ui.Percent(45))

                        ui.Spacer(height=10)

                        # max distance int field
                        with ui.VStack():
                            tooltip = "Max distance of the object from the camera. If the object is further than this" \
                                      "value, it will be hidden even if it is visible to the camera."
                            with ui.HStack(height=0):
                                ui.Label("Max distance (mm)", tooltip=tooltip)
                                self._max_distance_field = ui.IntField(tooltip=tooltip)
                                self._max_distance_field.model.set_value(10000)

                        ui.Spacer(height=10)

                        # ignore size settings for distant objects
                        with ui.VStack():
                            tooltip = "No matter the size of the object, if it is too far away, it will be hidden"
                            with ui.HStack(height=0):
                                ui.Label(
                                    "Ignore size for distant objects",
                                    elided_text=True,
                                    tooltip=tooltip,
                                    width=ui.Percent(50)
                                )
                                self._ignore_size_distant_objects = ui.CheckBox(tooltip=tooltip, width=ui.Percent(5))
                                self._ignore_size_distant_objects.model.set_value(False)
                                ui.Line(name="default", width=ui.Percent(45))

                        ui.Spacer(height=10)

                        # String field to hide objects by title
                        with ui.VStack():
                            tooltip = "Hide objects by title. Plain text match and regex is supported."
                            with ui.HStack(height=0):
                                ui.Label("Hide if contains in title", elided_text=True, tooltip=tooltip)
                                self._hide_objects_field = ui.StringField(tooltip=tooltip)

                        ui.Spacer(height=10)

                        # string field to show objects by title
                        with ui.VStack():
                            tooltip = "Show objects by title. Plain text match and regex is supported."
                            with ui.HStack(height=0):
                                ui.Label("Show if contains in title", elided_text=True, tooltip=tooltip)
                                self._show_objects_field = ui.StringField(tooltip=tooltip)

                        ui.Spacer(height=10)

                        # base path where to search for objects
                        with ui.VStack():
                            with ui.HStack(height=0):
                                tooltip = "Base path where to search for objects. If empty or invalid, " \
                                          "DefaultPrim will be used"
                                ui.Label("Base path", elided_text=True, tooltip=tooltip)
                                self._base_path_field = ui.StringField(tooltip=tooltip)
                                self._base_path_field.model.set_value(self.stage.GetDefaultPrim().GetPath().pathString)

                ui.Spacer()

                with ui.VStack(height=40):
                    with ui.HStack(height=40):
                        self._button_show_all = ui.Button(
                            "Show all",
                            height=40,
                            clicked_fn=self.show_all,
                        )

                        self._button_delete_hidden = ui.Button(
                            "Delete hidden",
                            height=40,
                            clicked_fn=self.delete_hidden,
                        )

                with ui.VStack(height=40):
                    # Button to execute the extension
                    self._button_optimize = ui.Button(
                        "Optimize",
                        height=40,
                        clicked_fn=self.optimize,
                    )

    def on_shutdown(self):
        """
        It deletes all the variables that were created in the extension
        """
        print("[karpenko.camera_view_optimizer.ext] CameraViewOptimizer shutdown")
        self._fov_slider = None
        self._max_size_slider = None
        self._max_distance_field = None
        self._hide_objects_field = None
        self._show_objects_field = None
        self._base_path_field = None
        self._delete_objects = None
        self._button_optimize = None
        self._button_show_all = None
        self._button_delete_hidden = None

    def get_default_prim(self):
        """
        If the base path field is empty, return the default prim, otherwise return the prim at the path in the base path
        field
        :return: The default prim.
        """
        if self._base_path_field.model.as_string == "":
            return self.stage.GetDefaultPrim()
        else:
            custom_default_prim = self.stage.GetPrimAtPath(self._base_path_field.model.as_string)
            if not custom_default_prim:
                return self.stage.GetDefaultPrim()
            else:
                return custom_default_prim

    def get_all_objects(self, only_visible=False):
        """
        It returns a list of all the objects in the scene, and if the only_visible parameter is set to True,
        it will only return objects that are visible

        :param only_visible: If True, only visible objects will be returned, defaults to True (optional)
        :return: A list of objects
        """
        if not self.stage:
            return []
        valid_objects = []
        default_prim = self.get_default_prim()
        for obj in default_prim.GetAllChildren():
            if obj:
                if only_visible:
                    visibility_attr = obj.GetAttribute("visibility")
                    if visibility_attr:
                        visibility = visibility_attr.Get()
                        if visibility != "invisible":
                            valid_objects.append(obj)
                else:
                    valid_objects.append(obj)
        return valid_objects

    def get_all_hidden_objects(self):
        """
        It returns a list of all the hidden objects in the scene

        :return: A list of objects
        """
        if not self.stage:
            return []
        valid_objects = []
        default_prim = self.get_default_prim()
        for obj in default_prim.GetAllChildren():
            if obj:
                visibility_attr = obj.GetAttribute("visibility")
                if visibility_attr:
                    visibility = visibility_attr.Get()
                    if visibility == "invisible":
                        valid_objects.append(obj)
        return valid_objects

    def show_all(self):
        """
        It gets all the hidden objects in the scene, and if there are any, it shows them
        :return: A list of objects that were hidden.
        """
        objects_to_show = self.get_all_hidden_objects()
        if objects_to_show:
            omni.kit.commands.execute(
                'ToggleVisibilitySelectedPrims',
                selected_paths=[i.GetPath() for i in objects_to_show],
            )
        return objects_to_show

    def delete_hidden(self):
        """
        It gets all the hidden objects in the scene, and if there are any, it deletes them
        :return: A list of objects that were deleted.
        """
        objects_to_delete = self.get_all_hidden_objects()

        if objects_to_delete:
            omni.kit.commands.execute(
                'DeletePrims',
                paths=[i.GetPath() for i in objects_to_delete],
            )
        return objects_to_delete
