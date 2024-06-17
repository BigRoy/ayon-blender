import os

import bpy

from ayon_core.lib import BoolDef
from ayon_core.pipeline import publish
from ayon_blender.api import plugin


class ExtractABC(plugin.BlenderExtractor, publish.OptionalPyblishPluginMixin):
    """Extract as ABC."""

    label = "Extract ABC"
    hosts = ["blender"]
    families = ["pointcache"]

    def process(self, instance):
        if not self.is_active(instance.data):
            return

        attr_values = self.get_attr_values_from_data(instance.data)

        # Define extract output file path
        stagingdir = self.staging_dir(instance)
        folder_name = instance.data["folderEntity"]["name"]
        product_name = instance.data["productName"]
        instance_name = f"{folder_name}_{product_name}"
        filename = f"{instance_name}.abc"
        filepath = os.path.join(stagingdir, filename)

        # Perform extraction
        self.log.debug("Performing extraction..")

        plugin.deselect_all()

        asset_group = instance.data["transientData"]["instance_node"]

        selected = []
        for obj in instance:
            if isinstance(obj, bpy.types.Object):
                obj.select_set(True)
                selected.append(obj)

        context = plugin.create_blender_context(
            active=asset_group, selected=selected)

        scene = bpy.context.scene
        frame_start = scene.frame_start
        frame_end = scene.frame_end
        frame_step = scene.frame_step
        fps = scene.render.fps
        fps_base = scene.render.fps_base
        scene.frame_start = instance.data.get("frameStart", frame_start)
        scene.frame_end = instance.data.get("frameEnd", frame_end)
        scene.frame_step = instance.data.get("frameStep", frame_step)
        inst_fps = instance.data.get("fps")
        if inst_fps:
            scene.render.fps = inst_fps
            scene.render.fps_base = 1

        with bpy.context.temp_override(**context):
            # We export the abc
            bpy.ops.wm.alembic_export(
                filepath=filepath,
                selected=True,
                flatten=False,
                subdiv_schema=attr_values.get("subdiv_schema", False)
            )

        scene.frame_start = frame_start
        scene.frame_end = frame_end
        scene.frame_step = frame_step
        scene.render.fps = fps
        scene.render.fps_base = fps_base

        plugin.deselect_all()

        if "representations" not in instance.data:
            instance.data["representations"] = []

        representation = {
            'name': 'abc',
            'ext': 'abc',
            'files': filename,
            "stagingDir": stagingdir,
        }
        instance.data["representations"].append(representation)

        self.log.debug("Extracted instance '%s' to: %s",
                       instance.name, representation)

    @classmethod
    def get_attribute_defs(cls):
        return [
            BoolDef(
                "subdiv_schema",
                label="Alembic Mesh Subdiv Schema",
                tooltip="Export Meshes using Alembic's subdivision schema.\n"
                        "Enabling this includes creases with the export but "
                        "excludes the mesh's normals.\n"
                        "Enabling this usually result in smaller file size "
                        "due to lack of normals.",
                default=False
            )
        ]


class ExtractModelABC(ExtractABC):
    """Extract model as ABC."""

    label = "Extract Model ABC"
    hosts = ["blender"]
    families = ["model"]
    optional = True
