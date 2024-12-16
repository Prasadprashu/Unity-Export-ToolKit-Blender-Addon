bl_info = {
    "name": "Unity Export ToolKit Pro",
    "author": "Prashu_2129",
    "version": (2, 3),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Export",
    "description": "Advanced export tool for Unity with comprehensive optimization and features",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}

import bpy
import os
import time
import subprocess
import mathutils

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
        
        # Folder Selection for Batch Export
        if unity_props.export_mode == 'BATCH':
            box.prop(unity_props, "batch_export_folder", text="Export Folder")
            if not unity_props.batch_export_folder:
                box.label(text="Select a folder for batch export", icon='ERROR')
        else:
            # Single File Selection
            box.prop(unity_props, "single_export_file", text="Export File")
        
        # Rig and Animation Options
        box.prop(unity_props, "export_rig", text="Export Rig")
        box.prop(unity_props, "export_animation", text="Export Animation")
        
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
        
        # Export and Open Folder Buttons
        row = layout.row()
        row.operator("export_scene.unity_export_toolkit", text="Export to Unity", icon='EXPORT')
        row.operator("export_scene.open_export_folder", text="Open Export Folder", icon='FILE_FOLDER')

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
    
    batch_export_folder: bpy.props.StringProperty(
        name="Batch Export Folder",
        description="Folder to export batch files",
        subtype='DIR_PATH'
    )
    
    single_export_file: bpy.props.StringProperty(
        name="Single Export File",
        description="File path for single export",
        subtype='FILE_PATH'
    )
    
    show_advanced_options: bpy.props.BoolProperty(
        name="Show Advanced Options",
        description="Toggle advanced export options",
        default=False
    )
    
    export_rig: bpy.props.BoolProperty(
        name="Export Rig",
        description="Include armature in export",
        default=False
    )
    
    export_animation: bpy.props.BoolProperty(
        name="Export Animation",
        description="Include animation in export",
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

class OpenExportFolderOperator(bpy.types.Operator):
    bl_idname = "export_scene.open_export_folder"
    bl_label = "Open Export Folder"
    
    def execute(self, context):
        unity_props = context.scene.unity_export_props
        
        if unity_props.export_mode == 'SINGLE':
            filepath = unity_props.single_export_file
            folder_path = os.path.dirname(filepath) if filepath else None
        else:
            folder_path = unity_props.batch_export_folder
        
        if folder_path and os.path.exists(folder_path):
            # Cross-platform file browser opening
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS and Linux
                if bpy.system == 'Darwin':  # macOS
                    subprocess.Popen(['open', folder_path])
                else:  # Linux
                    subprocess.Popen(['xdg-open', folder_path])
        else:
            self.report({'ERROR'}, "Export folder not set or does not exist")
        
        return {'FINISHED'}

class UnityExportToolKitOperator(bpy.types.Operator):
    bl_idname = "export_scene.unity_export_toolkit"
    bl_label = "Unity Export ToolKit Pro"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        start_time = time.time()
        
        # Gather settings from scene properties
        unity_props = context.scene.unity_export_props
        export_format = unity_props.export_format
        export_mode = unity_props.export_mode
        
        # Validate export path
        if export_mode == 'SINGLE':
            if not unity_props.single_export_file:
                self.report({'ERROR'}, "Select a file for export")
                return {'CANCELLED'}
            filepath = self.ensure_file_extension(unity_props.single_export_file, export_format)
        else:  # BATCH mode
            if not unity_props.batch_export_folder:
                self.report({'ERROR'}, "Select a folder for batch export")
                return {'CANCELLED'}
            filepath = unity_props.batch_export_folder
        
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

    def export_single_file(self, context, top_level_parents, filepath, export_format):
        """Export all selected objects as a single file."""
        unity_props = context.scene.unity_export_props
        objects_to_export = self.get_hierarchy_objects(top_level_parents)
        
        self.prepare_objects_for_export(context, objects_to_export, unity_props)
        
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects_to_export:
            obj.select_set(True)
        
        self.perform_export(filepath, export_format, unity_props, use_selection=True)

    def export_batch(self, context, top_level_parents, export_dir, export_format):
        """Export each top-level object separately with its hierarchy."""
        unity_props = context.scene.unity_export_props
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
                path_mode='AUTO',  
                embed_textures=True, 
                use_selection=use_selection, 
                bake_space_transform=True,
                use_active_collection=False,
                use_mesh_modifiers=unity_props.apply_modifiers,
                global_scale=1.0,
                apply_unit_scale=True,
                use_mesh_edges=False,     
                axis_forward='-Z',        
                axis_up='Y',
                # New options for rig and animation export
                add_leaf_bones=False,
                bake_anim_use_all_bones=unity_props.export_animation,
                bake_anim_step=1,
                bake_anim_simplify_factor=1.0,
                use_armature_deform_only=not unity_props.export_rig
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
            
            for child in obj.children_recursive:  # Use children_recursive to capture all descendants
                collect_hierarchy(child)
        
        for parent in parent_objects:
            collect_hierarchy(parent)
        
        return hierarchy_objects

    def prepare_objects_for_export(self, context, objects_to_export, unity_props):
        """Prepare objects for export by applying modifiers, transformations, etc."""
        for obj in objects_to_export:
            if obj.type not in ['MESH', 'ARMATURE']:
                continue
            
            context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # Apply modifiers
            if unity_props.apply_modifiers and obj.type == 'MESH':
                bpy.ops.object.convert(target='MESH')
            
            # Triangulate
            if unity_props.triangulate and obj.type == 'MESH':
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                bpy.ops.object.mode_set(mode='OBJECT')
            
            # Apply transformations (now also applied to great-grandchildren)
            bpy.ops.object.transform_apply(
                location=unity_props.apply_location, 
                rotation=unity_props.apply_rotation, 
                scale=unity_props.apply_scale
            )
            
            obj.select_set(False)
        
        context.view_layer.objects.active = None

def register():
    """Register classes and properties for the addon."""

    # Register the custom property group
    bpy.utils.register_class(UnityExportToolkitProperties)
    
    # Add the property group to the scene
    bpy.types.Scene.unity_export_props = bpy.props.PointerProperty(type=UnityExportToolkitProperties)
    
    # Register classes
    bpy.utils.register_class(UnityExportToolKitOperator)
    bpy.utils.register_class(EXPORT_PT_unity_toolkit_panel)
    bpy.utils.register_class(OpenExportFolderOperator)
    
def unregister():
    """Unregister classes and properties for the addon."""
    # Unregister classes
    bpy.utils.unregister_class(UnityExportToolKitOperator)
    bpy.utils.unregister_class(EXPORT_PT_unity_toolkit_panel)
    bpy.utils.unregister_class(OpenExportFolderOperator)
    
    # Remove the property group from the scene
    del bpy.types.Scene.unity_export_props
    
    # Unregister the property group
    bpy.utils.unregister_class(UnityExportToolkitProperties)

if __name__ == "__main__":
    register()
