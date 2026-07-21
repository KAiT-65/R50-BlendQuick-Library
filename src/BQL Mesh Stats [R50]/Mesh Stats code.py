bl_info = {
    "name": "BQL Mesh Stats [R50]",
    "author": "R50",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > N-Panel > BlendQuick > Mesh Stats",
    "description": "Display mesh statistics in N-Panel",
    "category": "BlendQuick",
}

import bpy


class VIEW3D_PT_mesh_stats(bpy.types.Panel):
    """Panel with mesh statistics"""
    bl_label = "Mesh Stats"
    bl_idname = "VIEW3D_PT_mesh_stats"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlendQuick"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            layout.label(text="Select a Mesh object", icon='INFO')
            return
        
        mesh = obj.data
        
        # Basic counts
        verts = len(mesh.vertices)
        edges = len(mesh.edges)
        faces = len(mesh.polygons)
        tris = sum(len(f.vertices) - 2 for f in mesh.polygons)
        
        # Display object name
        col = layout.column(align=True)
        col.label(text=obj.name, icon='MESH_DATA')
        
        # Basic stats
        row = col.row()
        row.label(text="Vertices:")
        row.label(text=f"{verts:,}")
        
        row = col.row()
        row.label(text="Edges:")
        row.label(text=f"{edges:,}")
        
        row = col.row()
        row.label(text="Faces:")
        row.label(text=f"{faces:,}")
        
        row = col.row()
        row.label(text="Triangles:")
        row.label(text=f"{tris:,}")
        
        # Additional info
        col.separator()
        
        # Memory usage
        try:
            memory_kb = mesh.calc_loop_triangles().nbytes / 1024
            col.label(text=f"Memory: {memory_kb:.1f} KB")
        except:
            col.label(text="Memory: N/A")
        
        # Bounding box info
        col.separator()
        bbox = mesh.bounds
        if bbox:
            size = bbox[1] - bbox[0]
            col.label(text=f"Size: {size.x:.2f} x {size.y:.2f} x {size.z:.2f}")
        
        # Material info
        if len(obj.material_slots) > 0:
            col.separator()
            col.label(text=f"Materials: {len(obj.material_slots)}")


def register():
    bpy.utils.register_class(VIEW3D_PT_mesh_stats)


def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_mesh_stats)


if __name__ == "__main__":
    register()
