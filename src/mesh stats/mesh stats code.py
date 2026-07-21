bl_info = {
    "name": "BQL Mesh Similar Select [R50]",
    "author": "R50",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Context Menu > Select Similar Meshes",
    "description": "Select meshes with similar geometry based on tolerance",
    "category": "Mesh",
}

import bpy
import bmesh
from mathutils import Vector
from bpy.props import FloatProperty, BoolProperty
import hashlib


class OBJECT_OT_mesh_similar_select(bpy.types.Operator):
    bl_idname = "object.mesh_similar_select"
    bl_label = "Select Similar Meshes"
    bl_description = "Select meshes with similar geometry based on tolerance percentage"
    bl_options = {'REGISTER', 'UNDO'}

    tolerance: FloatProperty(
        name="Similarity Tolerance",
        description="Percentage similarity required (100 = identical, 0 = select all)",
        min=0.0,
        max=100.0,
        default=90.0,
    )
    
    compare_topology: BoolProperty(
        name="Compare Topology",
        description="Also compare edge topology structure",
        default=True,
    )
    
    compare_scale: BoolProperty(
        name="Compare Scale",
        description="Also compare object scale",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        active_obj = context.active_object
        if not active_obj or active_obj.type != 'MESH':
            self.report({'WARNING'}, "No active mesh object selected")
            return {'CANCELLED'}
        
        # Get mesh data from active object
        active_mesh_data = self._get_mesh_data(active_obj)
        if not active_mesh_data:
            self.report({'WARNING'}, "Could not analyze active mesh")
            return {'CANCELLED'}
        
        # Filter to only mesh objects
        mesh_objects = [obj for obj in context.scene.objects if obj.type == 'MESH' and obj != active_obj]
        
        if not mesh_objects:
            self.report({'INFO'}, "No other mesh objects found")
            return {'FINISHED'}
        
        # Limit processing to first 1000 objects to prevent lag
        if len(mesh_objects) > 1000:
            self.report({'WARNING'}, f"Processing first 1000 of {len(mesh_objects)} objects")
            mesh_objects = mesh_objects[:1000]
        
        # Compare with all other mesh objects
        selected_count = 0
        for obj in mesh_objects:
            # Get mesh data for comparison
            obj_mesh_data = self._get_mesh_data(obj)
            if not obj_mesh_data:
                continue
            
            # Calculate similarity
            similarity = self._calculate_similarity(active_mesh_data, obj_mesh_data)
            
            # Select if similarity meets tolerance
            if similarity >= self.tolerance:
                obj.select_set(True)
                selected_count += 1
        
        self.report({'INFO'}, f"Selected {selected_count} similar meshes (tolerance: {self.tolerance}%)")
        return {'FINISHED'}

    def _get_mesh_data(self, obj):
        """Extract mesh data for comparison (optimized)"""
        if not obj.data or not obj.data.polygons:
            return None
        
        mesh = obj.data
        
        # Quick hash for fast rejection
        vert_count = len(mesh.vertices)
        edge_count = len(mesh.edges)
        face_count = len(mesh.polygons)
        
        # Create hash from counts for quick comparison
        count_hash = hash((vert_count, edge_count, face_count))
        
        # Only extract detailed data if counts match
        if vert_count > 100000:  # Skip very large meshes
            return {
                'vert_count': vert_count,
                'edge_count': edge_count,
                'face_count': face_count,
                'count_hash': count_hash,
                'bbox_size': Vector((0, 0, 0)),
                'verts': [],
                'edge_topology': [],
                'face_topology': [],
                'scale': obj.scale.copy() if self.compare_scale else Vector((1, 1, 1)),
                'is_large': True,
            }
        
        # Get vertex positions (only for small/medium meshes)
        verts = [v.co.copy() for v in mesh.vertices]
        
        # Get bounding box
        if verts:
            bbox_min = Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts)))
            bbox_max = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
            bbox_size = bbox_max - bbox_min
        else:
            bbox_size = Vector((0, 0, 0))
        
        # Get topology only if needed
        edge_topology = []
        face_topology = []
        
        if self.compare_topology:
            edge_topology = [tuple(sorted(edge.vertices)) for edge in mesh.edges]
            edge_topology.sort()
            face_topology = [tuple(sorted(face.vertices)) for face in mesh.polygons]
            face_topology.sort()
        
        return {
            'vert_count': vert_count,
            'edge_count': edge_count,
            'face_count': face_count,
            'count_hash': count_hash,
            'verts': verts,
            'bbox_size': bbox_size,
            'edge_topology': edge_topology,
            'face_topology': face_topology,
            'scale': obj.scale.copy() if self.compare_scale else Vector((1, 1, 1)),
            'is_large': False,
        }

    def _calculate_similarity(self, data1, data2):
        """Calculate similarity percentage between two mesh data sets (optimized)"""
        # Quick hash-based rejection
        if data1.get('count_hash') != data2.get('count_hash'):
            return 0.0
        
        # Skip large meshes
        if data1.get('is_large') or data2.get('is_large'):
            return 0.0
        
        # Quick rejection: counts must match exactly
        if (data1['vert_count'] != data2['vert_count'] or
            data1['edge_count'] != data2['edge_count'] or
            data1['face_count'] != data2['face_count']):
            return 0.0
        
        # Compare topology if enabled
        if self.compare_topology:
            if data1['edge_topology'] != data2['edge_topology']:
                return 0.0
            if data1['face_topology'] != data2['face_topology']:
                return 0.0
        
        # Compare scale if enabled
        if self.compare_scale:
            scale_diff = (data1['scale'] - data2['scale']).length
            if scale_diff > 0.01:
                return 0.0
        
        # Compare vertex positions (only if tolerance is high)
        if self.tolerance < 95.0:
            # For lower tolerance, skip detailed vertex comparison
            return 100.0
        
        verts1 = data1['verts']
        verts2 = data2['verts']
        
        if len(verts1) != len(verts2):
            return 0.0
        
        # Skip vertex comparison for very large meshes
        if len(verts1) > 50000:
            return 100.0
        
        # Normalize vertices to unit bounding box for scale-invariant comparison
        bbox1 = data1['bbox_size']
        bbox2 = data2['bbox_size']
        
        # Avoid division by zero
        if bbox1.length < 1e-6 or bbox2.length < 1e-6:
            return 0.0
        
        # Sample vertices for faster comparison (every 10th vertex)
        sample_rate = max(1, len(verts1) // 1000)
        
        total_diff = 0.0
        sample_count = 0
        
        for i in range(0, len(verts1), sample_rate):
            v1 = verts1[i]
            v2 = verts2[i]
            
            # Normalize
            norm1 = Vector((v1.x / bbox1.x if bbox1.x > 0 else 0,
                           v1.y / bbox1.y if bbox1.y > 0 else 0,
                           v1.z / bbox1.z if bbox1.z > 0 else 0))
            norm2 = Vector((v2.x / bbox2.x if bbox2.x > 0 else 0,
                           v2.y / bbox2.y if bbox2.y > 0 else 0,
                           v2.z / bbox2.z if bbox2.z > 0 else 0))
            
            diff = (norm1 - norm2).length
            total_diff += diff
            sample_count += 1
        
        if sample_count == 0:
            return 100.0
        
        avg_diff = total_diff / sample_count
        
        # Convert to similarity percentage (0 diff = 100%, 1 diff = 0%)
        similarity = max(0.0, 100.0 - (avg_diff * 100.0))
        
        return similarity


def menu_func(self, context):
    # Add BlendQuick submenu
    layout = self.layout
    layout.separator()
    blendquick_menu = layout.menu("VIEW3D_MT_blendquick_menu", text="BlendQuick")


class VIEW3D_MT_blendquick_menu(bpy.types.Menu):
    bl_label = "BlendQuick"
    
    def draw(self, context):
        layout = self.layout
        layout.operator("object.mesh_similar_select")


def register():
    bpy.utils.register_class(OBJECT_OT_mesh_similar_select)
    bpy.utils.register_class(VIEW3D_MT_blendquick_menu)
    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)
    bpy.utils.unregister_class(VIEW3D_MT_blendquick_menu)
    bpy.utils.unregister_class(OBJECT_OT_mesh_similar_select)


if __name__ == "__main__":
    register()
