bl_info = {
    "name": "Prashu Unity Export ToolKit Pro",
    "author": "Prashu_2129",
    "version": (2, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Export",
    "description": "Advanced export tool for Unity with comprehensive optimization",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}

import bpy
import os
import math
import mathutils
import time
from typing import List, Dict

class EXPORT_PT_unity_toolkit_panel(bpy.types.Panel):
    bl_label = "Unity Export ToolKit Pro"
    bl_idname = "EXPORT_PT_unity_toolkit_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Export"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        unity_props = scene.unity_export_props
        
        # Export Options Section
        box = layout.box()
        box.label(text="Unity Export Settings", icon='EXPORT')
        
        # Export Format Selection
        row = box.row()
        row.prop(unity_props, "export_format", text="Format")
        
        # Export Mode Selection
        row = box.row()
        row.prop(unity_props, "export_mode", text="Mode")
        
        # Advanced Options Dropdown
        box.prop(unity_props, "show_advanced_options", 
                 text="Advanced Options", 
                 icon='DOWNARROW_HLT' if unity_props.show_advanced_options else 'RIGHTARROW')
        
        if unity_props.show_advanced_options:
            advanced_box = box.box()
            
            # Optimization and Transform Options
            advanced_box.prop(unity_props, "apply_modifiers", text="Apply Modifiers")
            
            row = advanced_box.row()
            row.prop(unity_props, "apply_location", text="Apply Location")
            row.prop(unity_props, "apply_rotation", text="Apply Rotation")
            row.prop(unity_props, "apply_scale", text="Apply Scale")
            
            # Advanced Mesh Processing
            advanced_box.prop(unity_props, "triangulate", text="Triangulate Mesh")
            advanced_box.prop(unity_props, "normalize_scale", text="Normalize Scale")
            advanced_box.prop(unity_props, "correct_rotation", text="Correct Unity Rotation")
        
        # Export Button
        layout.operator("export_scene.unity_export_toolkit", text="Export to Unity", icon='EXPORT')

class UnityExportToolkitProperties(bpy.types.PropertyGroup):
    export_format: bpy.props.EnumProperty(
        name="Export Format",
        description="Choose the export format",
        items=[
            ('FBX', "FBX", "Export as FBX"),
            ('OBJ', "OBJ", "Export as OBJ")
        ],
        default='FBX'
    )
    
    export_mode: bpy.props.EnumProperty(
        name="Export Mode",
        description="Choose the export mode",
        items=[
            ('SINGLE', "Single File", "Export as a single file"),
            ('BATCH', "Batch Export", "Export each object separately")
        ],
        default='SINGLE'
    )
    
    show_advanced_options: bpy.props.BoolProperty(
        name="Show Advanced Options",
        description="Toggle advanced export options",
        default=False
    )
    
    apply_modifiers: bpy.props.BoolProperty(
        name="Apply Modifiers", 
        default=True
    )
    
    apply_location: bpy.props.BoolProperty(
        name="Apply Location", 
        default=False
    )
    
    apply_rotation: bpy.props.BoolProperty(
        name="Apply Rotation", 
        default=True
    )
    
    apply_scale: bpy.props.BoolProperty(
        name="Apply Scale", 
        default=True
    )
    
    triangulate: bpy.props.BoolProperty(
        name="Triangulate", 
        default=True
    )
    
    normalize_scale: bpy.props.BoolProperty(
        name="Normalize Scale",
        description="Correct near-zero scaling issues for Unity export",
        default=True
    )
    
    correct_rotation: bpy.props.BoolProperty(
        name="Auto-Correct Unity Rotation",
        description="Automatically adjust rotation for Unity compatibility",
        default=True
    )

class UnityExportToolKitOperator(bpy.types.Operator):
    bl_idname = "export_scene.unity_export_toolkit"
    bl_label = "Unity Export ToolKit Pro"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        start_time = time.time()
        
        # Gather settings from scene properties
        unity_props = context.scene.unity_export_props
        export_format = unity_props.export_format
        export_mode = unity_props.export_mode
        
        # Validate export path
        if not self.filepath:
            self.report({'ERROR'}, "Export path not selected")
            return {'CANCELLED'}
        
        # Ensure correct file extension
        filepath = self.ensure_file_extension(self.filepath, export_format)
        
        # Store original scene state
        original_selected = context.selected_objects.copy()
        original_active = context.view_layer.objects.active
        original_transforms = {obj: (obj.location.copy(), obj.rotation_euler.copy(), obj.scale.copy()) for obj in original_selected}

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
                original_transforms, 
                original_active
            )
        
        export_time = time.time() - start_time
        self.report({'INFO'}, f"Export completed in {export_time:.2f} seconds")
        
        return {'FINISHED'}

    def normalize_scales(self, objects_to_export, unity_props):
        """Normalize object scales to prevent near-zero scaling issues."""
        for obj in objects_to_export:
            if obj.type == 'MESH' and unity_props.normalize_scale:
                # Round very small scale values to exactly 1.0
                scale = obj.scale
                corrected_scale = mathutils.Vector([
                    1.0 if abs(s - 1.0) < 0.0001 else s 
                    for s in scale
                ])
                if corrected_scale != scale:
                    obj.scale = corrected_scale
                    obj.update_tag()

    def correct_unity_rotation(self, objects_to_export, unity_props):
        """Correct rotation for Unity compatibility."""
        if not unity_props.correct_rotation:
            return
        
        for obj in objects_to_export:
            if obj.type == 'MESH':
                # Set X rotation exactly to -90 degrees, not 89.98
                # First store the current local rotation
                local_rotation = obj.rotation_euler.copy()
                
                # Reset rotation to precise -90 degrees around X
                obj.rotation_euler.x = math.radians(-90)
                
                # If the object has a parent, we need to handle its local rotation carefully
                if obj.parent:
                    # Apply the rotation while preserving world space
                    obj.update_tag()
                    bpy.context.view_layer.update()
                
                # Restore other rotation axes to maintain overall orientation
                obj.rotation_euler.y = local_rotation.y
                obj.rotation_euler.z = local_rotation.z

    def export_single_file(self, context, top_level_parents, filepath, export_format):
        """Export all selected objects as a single file."""
        unity_props = context.scene.unity_export_props
        objects_to_export = self.get_hierarchy_objects(top_level_parents)
        
        self.prepare_objects_for_export(context, objects_to_export, unity_props)
        
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects_to_export:
            obj.select_set(True)
        
        self.perform_export(filepath, export_format, unity_props, use_selection=True)

    def export_batch(self, context, top_level_parents, base_filepath, export_format):
        """Export each top-level object separately with its hierarchy."""
        unity_props = context.scene.unity_export_props
        export_dir = os.path.dirname(base_filepath)
        os.makedirs(export_dir, exist_ok=True)
        
        for parent in top_level_parents:
            objects_to_export = self.get_hierarchy_objects([parent])
            
            self.prepare_objects_for_export(context, objects_to_export, unity_props)
            
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects_to_export:
                obj.select_set(True)
            
            batch_filepath = os.path.join(
                export_dir, 
                f"{parent.name}.{export_format.lower()}"
            )
            
            self.perform_export(batch_filepath, export_format, unity_props, use_selection=True)

    def perform_export(self, filepath, export_format, unity_props, use_selection=True):
        """Perform the actual export based on the chosen format."""
        if export_format == 'FBX':
            bpy.ops.export_scene.fbx(
                filepath=filepath, 
                apply_scale_options='FBX_SCALE_ALL', 
                path_mode='AUTO',  # More flexible path handling
                embed_textures=True, 
                use_selection=use_selection, 
                bake_space_transform=True,
                use_active_collection=False,
                use_mesh_modifiers=unity_props.apply_modifiers,
                global_scale=1.0,
                apply_unit_scale=True,
                use_mesh_edges=False,     # Optimizations
                axis_forward='-Z',        # Better Unity compatibility
                axis_up='Y'               # Standard Unity axis orientation
            )
        elif export_format == 'OBJ':
            bpy.ops.export_scene.obj(
                filepath=filepath, 
                use_materials=True, 
                use_uvs=True, 
                use_selection=use_selection,
                global_scale=1.0
            )

    def ensure_file_extension(self, filepath, export_format):
        """Ensure the filepath has the correct file extension."""
        base, ext = os.path.splitext(filepath)
        correct_ext = f'.{export_format.lower()}'
        return base + correct_ext if not ext or ext.lower() != correct_ext else filepath

    def restore_scene_state(self, context, original_selected, original_transforms, original_active):
        """Restore the original scene state after export."""
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selected:
            obj.select_set(True)
            location, rotation, scale = original_transforms[obj]
            obj.location = location
            obj.rotation_euler = rotation
            obj.scale = scale
        
        context.view_layer.objects.active = original_active
        
        bpy.ops.ed.undo_push(message="Undo Export")
        bpy.ops.ed.undo()

    def get_hierarchy_objects(self, parent_objects):
        """Recursively collect all objects in the hierarchy of given parent objects."""
        hierarchy_objects = []
        processed_objects = set()
        
        def collect_hierarchy(obj):
            if obj in processed_objects:
                return
            
            processed_objects.add(obj)
            hierarchy_objects.append(obj)
            
            for child in obj.children:
                collect_hierarchy(child)
        
        for parent in parent_objects:
            collect_hierarchy(parent)
        
        return hierarchy_objects

    def prepare_objects_for_export(self, context, objects_to_export, unity_props):
        """Prepare objects for export by applying modifiers, transformations, etc."""
        # Normalize scales if option is enabled
        self.normalize_scales(objects_to_export, unity_props)
        self.correct_unity_rotation(objects_to_export, unity_props)
        
        for obj in objects_to_export:
            if obj.type != 'MESH':
                continue
            
            context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # Apply modifiers
            if unity_props.apply_modifiers:
                bpy.ops.object.convert(target='MESH')
            
            # Triangulate
            if unity_props.triangulate:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Apply transformations
            bpy.ops.object.transform_apply(
                location=unity_props.apply_location, 
                rotation=unity_props.apply_rotation, 
                scale=unity_props.apply_scale
            )
            
            obj.select_set(False)
        
        context.view_layer.objects.active = None

    def invoke(self, context, event):
        """Invoke file browser for export path selection."""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    """Register classes and properties for the addon."""
    # Register the custom property group
    bpy.utils.register_class(UnityExportToolkitProperties)
    
    # Add the property group to the scene
    bpy.types.Scene.unity_export_props = bpy.props.PointerProperty(type=UnityExportToolkitProperties)
    
    # Register classes
    bpy.utils.register_class(UnityExportToolKitOperator)
    bpy.utils.register_class(EXPORT_PT_unity_toolkit_panel)
    
def unregister():
    """Unregister classes and properties for the addon."""
    # Unregister classes
    bpy.utils.unregister_class(UnityExportToolKitOperator)
    bpy.utils.unregister_class(EXPORT_PT_unity_toolkit_panel)
    
    # Remove the property group from the scene
    del bpy.types.Scene.unity_export_props
    
    # Unregister the property group
    bpy.utils.unregister_class(UnityExportToolkitProperties)

if __name__ == "__main__":
    register()
