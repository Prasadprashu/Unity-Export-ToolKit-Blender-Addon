bl_info = {
    "name": "PrashuExportToolKit",
    "author": "Prashu_2129",
    "version": (1, 7),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > PrashuExportToolKit",
    "description": "Comprehensive export tool for game engines with advanced options",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}

import bpy
import os
import math
import mathutils
from typing import List, Dict

class EXPORT_PT_prashu_toolkit_panel(bpy.types.Panel):
    bl_label = "PrashuExportToolKit"
    bl_idname = "EXPORT_PT_prashu_toolkit_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Export"

    def draw(self, context):
        layout = self.layout
        
        # Export Options Section
        box = layout.box()
        box.label(text="Export Settings", icon='EXPORT')
        
        # Export Format Selection
        row = box.row()
        row.prop(context.scene, "prashu_export_format", text="Format")
        
        # Export Mode Selection
        row = box.row()
        row.prop(context.scene, "prashu_export_mode", text="Mode")
        
        # Advanced Options Dropdown
        box.prop(context.scene, "show_advanced_options", 
                 text="Advanced Options", 
                 icon='DOWNARROW_HLT' if context.scene.show_advanced_options else 'RIGHTARROW')
        
        if context.scene.show_advanced_options:
            advanced_box = box.box()
            
            # Modifier Application
            advanced_box.prop(context.scene, "prashu_apply_modifiers", text="Apply Modifiers")
            
            # Transformation Options
            row = advanced_box.row()
            row.prop(context.scene, "prashu_apply_location", text="Apply Location")
            row.prop(context.scene, "prashu_apply_rotation", text="Apply Rotation")
            row.prop(context.scene, "prashu_apply_scale", text="Apply Scale")
            
            # Triangulation Option
            advanced_box.prop(context.scene, "prashu_triangulate", text="Triangulate Mesh")
            
            # Scale Normalization Option
            advanced_box.prop(context.scene, "prashu_normalize_scale", text="Normalize Scale")
        
        # Export Button
        layout.operator("export_scene.prashu_export_toolkit", text="Export to Game Engine", icon='EXPORT')

class PrashuExportToolKitOperator(bpy.types.Operator):
    bl_idname = "export_scene.prashu_export_toolkit"
    bl_label = "PrashuExportToolKit"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        # Gather settings from scene properties
        export_format = context.scene.prashu_export_format
        export_mode = context.scene.prashu_export_mode
        
        # Prepare export filepath
        if not self.filepath:
            self.report({'ERROR'}, "Export path not selected")
            return {'CANCELLED'}
        
        # Ensure correct file extension
        filepath = self.ensure_file_extension(self.filepath, export_format)
        
        # Store original scene state
        original_selected = context.selected_objects.copy()
        original_active = context.view_layer.objects.active
        original_rotations = {obj: obj.rotation_euler.copy() for obj in original_selected}
        original_scales = {obj: obj.scale.copy() for obj in original_selected}

        if not original_selected:
            self.report({'INFO'}, "No objects selected for export")
            return {'CANCELLED'}

        try:
            # Determine top-level parent objects
            top_level_parents = [obj for obj in original_selected if not obj.parent]
            if not top_level_parents:
                top_level_parents = original_selected

            # Perform export based on mode
            if export_mode == 'SINGLE':
                self.export_single_file(context, top_level_parents, filepath, export_format)
            else:  # BATCH mode
                self.export_batch(context, top_level_parents, filepath, export_format)

        except Exception as e:
            self.report({'ERROR'}, f"Export error: {str(e)}")
            return {'CANCELLED'}
        
        finally:
            # Restore original scene state
            self.restore_scene_state(
                context, 
                original_selected, 
                original_rotations, 
                original_scales, 
                original_active
            )
        
        return {'FINISHED'}

    def normalize_scales(self, objects_to_export):
        """Normalize object scales to prevent near-zero scaling issues."""
        for obj in objects_to_export:
            if obj.type == 'MESH' and bpy.context.scene.prashu_normalize_scale:
                # Round very small scale values to exactly 1.0
                scale = obj.scale
                corrected_scale = mathutils.Vector([
                    1.0 if abs(s - 1.0) < 0.0001 else s 
                    for s in scale
                ])
                if corrected_scale != scale:
                    obj.scale = corrected_scale
                    obj.update_tag()

    def export_single_file(self, context, top_level_parents, filepath, export_format):
        """Export all selected objects as a single file."""
        objects_to_export = self.get_hierarchy_objects(top_level_parents)
        
        self.prepare_objects_for_export(context, objects_to_export)
        
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects_to_export:
            obj.select_set(True)
        
        self.perform_export(filepath, export_format, use_selection=True)

    def export_batch(self, context, top_level_parents, base_filepath, export_format):
        """Export each top-level object separately with its hierarchy."""
        export_dir = os.path.dirname(base_filepath)
        
        for parent in top_level_parents:
            objects_to_export = self.get_hierarchy_objects([parent])
            
            self.prepare_objects_for_export(context, objects_to_export)
            
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects_to_export:
                obj.select_set(True)
            
            batch_filepath = os.path.join(
                export_dir, 
                f"{parent.name}.{export_format.lower()}"
            )
            
            self.perform_export(batch_filepath, export_format, use_selection=True)

    def perform_export(self, filepath, export_format, use_selection=True):
        """Perform the actual export based on the chosen format."""
        if export_format == 'FBX':
            bpy.ops.export_scene.fbx(
                filepath=filepath, 
                apply_scale_options='FBX_SCALE_ALL', 
                path_mode='COPY', 
                embed_textures=True, 
                use_selection=use_selection, 
                bake_space_transform=True,
                use_active_collection=False,
                use_mesh_modifiers=bpy.context.scene.prashu_apply_modifiers,
                global_scale=1.0,
                apply_unit_scale=True
            )
        elif export_format == 'OBJ':
            bpy.ops.export_scene.obj(
                filepath=filepath, 
                use_materials=True, 
                use_uvs=True, 
                use_selection=use_selection
            )

    def ensure_file_extension(self, filepath, export_format):
        """Ensure the filepath has the correct file extension."""
        base, ext = os.path.splitext(filepath)
        correct_ext = f'.{export_format.lower()}'
        return base + correct_ext if not ext or ext.lower() != correct_ext else filepath

    def restore_scene_state(self, context, original_selected, original_rotations, original_scales, original_active):
        """Restore the original scene state after export."""
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selected:
            obj.select_set(True)
            obj.rotation_euler = original_rotations[obj]
            obj.scale = original_scales[obj]
        context.view_layer.objects.active = original_active
        
        bpy.ops.ed.undo_push(message="Undo Export")
        bpy.ops.ed.undo()

    def get_hierarchy_objects(self, parent_objects):
        """Recursively collect all objects in the hierarchy of given parent objects."""
        hierarchy_objects = []
        for parent in parent_objects:
            hierarchy_objects.append(parent)
            
            def collect_children(obj):
                for child in obj.children:
                    if child not in hierarchy_objects:
                        hierarchy_objects.append(child)
                        collect_children(child)
            
            collect_children(parent)
        
        return hierarchy_objects

    def prepare_objects_for_export(self, context, objects_to_export):
        """Prepare objects for export by applying modifiers, transformations, etc."""
        # Normalize scales if option is enabled
        self.normalize_scales(objects_to_export)
        
        for obj in objects_to_export:
            if obj.type != 'MESH':
                continue
            
            context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # Apply modifiers
            if bpy.context.scene.prashu_apply_modifiers:
                bpy.ops.object.convert(target='MESH')
            
            # Triangulate
            if bpy.context.scene.prashu_triangulate:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Apply transformations
            bpy.ops.object.transform_apply(
                location=bpy.context.scene.prashu_apply_location, 
                rotation=bpy.context.scene.prashu_apply_rotation, 
                scale=bpy.context.scene.prashu_apply_scale
            )
            
            obj.select_set(False)
        
        context.view_layer.objects.active = None

    def invoke(self, context, event):
        """Invoke file browser for export path selection."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    """Register scene properties and classes for the addon."""
    # Register scene properties
    bpy.types.Scene.prashu_export_format = bpy.props.EnumProperty(
        name="Export Format",
        description="Choose the export format",
        items=[
            ('FBX', "FBX", "Export as FBX"),
            ('OBJ', "OBJ", "Export as OBJ")
        ],
        default='FBX'
    )
    
    bpy.types.Scene.prashu_export_mode = bpy.props.EnumProperty(
        name="Export Mode",
        description="Choose the export mode",
        items=[
            ('SINGLE', "Single File", "Export as a single file"),
            ('BATCH', "Batch Export", "Export each object separately")
        ],
        default='SINGLE'
    )
    
    bpy.types.Scene.show_advanced_options = bpy.props.BoolProperty(
        name="Show Advanced Options",
        description="Toggle advanced export options",
        default=False
    )
    
    bpy.types.Scene.prashu_apply_modifiers = bpy.props.BoolProperty(
        name="Apply Modifiers", 
        default=True
    )
    
    bpy.types.Scene.prashu_apply_location = bpy.props.BoolProperty(
        name="Apply Location", 
        default=False
    )
    
    bpy.types.Scene.prashu_apply_rotation = bpy.props.BoolProperty(
        name="Apply Rotation", 
        default=True
    )
    
    bpy.types.Scene.prashu_apply_scale = bpy.props.BoolProperty(
        name="Apply Scale", 
        default=True
    )
    
    bpy.types.Scene.prashu_triangulate = bpy.props.BoolProperty(
        name="Triangulate", 
        default=True
    )
    
    bpy.types.Scene.prashu_normalize_scale = bpy.props.BoolProperty(
        name="Normalize Scale",
        description="Correct near-zero scaling issues for Unity export",
        default=True
    )
    
    # Register classes
    bpy.utils.register_class(PrashuExportToolKitOperator)
    bpy.utils.register_class(EXPORT_PT_prashu_toolkit_panel)

def unregister():
    """Unregister scene properties and classes."""
    # Unregister scene properties
    del bpy.types.Scene.prashu_export_format
    del bpy.types.Scene.prashu_export_mode
    del bpy.types.Scene.show_advanced_options
    del bpy.types.Scene.prashu_apply_modifiers
    del bpy.types.Scene.prashu_apply_location
    del bpy.types.Scene.prashu_apply_rotation
    del bpy.types.Scene.prashu_apply_scale
    del bpy.types.Scene.prashu_triangulate
    del bpy.types.Scene.prashu_normalize_scale
    
    # Unregister classes
    bpy.utils.unregister_class(PrashuExportToolKitOperator)
    bpy.utils.unregister_class(EXPORT_PT_prashu_toolkit_panel)

if __name__ == "__main__":
    register()
