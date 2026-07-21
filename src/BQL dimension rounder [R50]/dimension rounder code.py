bl_info = {
    "name": "BQL dimension rounder [R50]",
    "author": "R50 Studio",
    "version": (1, 1),
    "blender": (3, 0, 0),
    "location": "View3D > N-Panel > Dimensions",
    "description": "Rounds dimensions of all selected mesh objects to the specified step.",
    "category": "3D View",
}

import bpy

ROUND_ITEMS = [
    ('10', "10 (Tens)", "Round to multiples of 10 (e.g., 68 -> 70)"),
    ('9', "9 (Nines)", "Round to multiples of 9 (e.g., 30 -> 27)"),
    ('8', "8 (Eights)", "Round to multiples of 8"),
    ('7', "7 (Sevens)", "Round to multiples of 7"),
    ('6', "6 (Sixes)", "Round to multiples of 6"),
    ('5', "5 (Fives)", "Round to multiples of 5"),
    ('4', "4 (Fours)", "Round to multiples of 4"),
    ('3', "3 (Threes)", "Round to multiples of 3"),
    ('2', "2 (Twos)", "Round to multiples of 2"),
    ('1', "1 (Ones)", "Round to nearest integer"),
    ('0.1', "0.1 (Tenths)", "Round to 0.1"),
    ('0.01', "0.01 (Hundredths)", "Round to 0.01"),
]

class OBJECT_OT_round_dimensions(bpy.types.Operator):
    """Round selected dimensions for all selected objects"""
    bl_idname = "object.round_dimensions"
    bl_label = "Round Dimensions"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        props = context.scene.dim_rounder_props
        
        step = float(props.round_target)
        if step <= 0:
            self.report({'ERROR'}, "Round step must be greater than zero.")
            return {'CANCELLED'}

        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']
        count = 0

        for obj in selected_meshes:
            dims = obj.dimensions.copy()
            
            new_x = round(dims.x / step) * step if props.use_x else dims.x
            new_y = round(dims.y / step) * step if props.use_y else dims.y
            new_z = round(dims.z / step) * step if props.use_z else dims.z

            if props.use_x and dims.x != 0:
                obj.scale.x *= (new_x / dims.x)
            if props.use_y and dims.y != 0:
                obj.scale.y *= (new_y / dims.y)
            if props.use_z and dims.z != 0:
                obj.scale.z *= (new_z / dims.z)
                
            count += 1

        self.report({'INFO'}, f"Rounded dimensions for {count} objects (multiple of {step})")
        return {'FINISHED'}


class DimRounderProperties(bpy.types.PropertyGroup):
    round_target: bpy.props.EnumProperty(
        name="Target Step",
        description="Select the value to which dimensions should be rounded",
        items=ROUND_ITEMS,
        default='10'
    )
    use_x: bpy.props.BoolProperty(name="X Axis", default=True)
    use_y: bpy.props.BoolProperty(name="Y Axis", default=True)
    use_z: bpy.props.BoolProperty(name="Z Axis", default=True)


class VIEW3D_PT_dim_rounder(bpy.types.Panel):
    """Panel in N-Panel"""
    bl_label = "Dimension Rounder"
    bl_idname = "VIEW3D_PT_dim_rounder"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Dimensions"

    def draw(self, context):
        layout = self.layout
        props = context.scene.dim_rounder_props
        
        selected_meshes = [obj for obj in context.selected_objects if obj.type == 'MESH']

        layout.prop(props, "round_target", text="Target")

        box = layout.box()
        box.label(text="Select axes to round:")
        row = box.row(align=True)
        row.prop(props, "use_x", toggle=True)
        row.prop(props, "use_y", toggle=True)
        row.prop(props, "use_z", toggle=True)

        if selected_meshes:
            col = layout.column(align=True)
            if len(selected_meshes) == 1:
                obj = selected_meshes[0]
                col.label(text=f"Object: {obj.name}", icon='MESH_DATA')
                col.label(text=f"X: {obj.dimensions.x:.3f} | Y: {obj.dimensions.y:.3f} | Z: {obj.dimensions.z:.3f}")
            else:
                col.label(text=f"Selected meshes: {len(selected_meshes)}", icon='RESTRICT_SELECT_OFF')

            layout.separator()
            layout.operator("object.round_dimensions", text=f"Round ({len(selected_meshes)})", icon='MOD_LENGTH')
        else:
            layout.label(text="Select at least one MESH object", icon='INFO')


classes = (
    DimRounderProperties,
    OBJECT_OT_round_dimensions,
    VIEW3D_PT_dim_rounder,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.dim_rounder_props = bpy.props.PointerProperty(type=DimRounderProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    del bpy.types.Scene.dim_rounder_props

if __name__ == "__main__":
    register()
