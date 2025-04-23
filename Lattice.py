import bpy

# Valeurs d'origine pour les points et handles
DEFAULT_POINTS = {
    "latticeCurveSwitchLeft_1": [
        {'co': (0.0, 0.0, 0.0), 'hl': (0.0, -1.0, 0.0), 'hr': (0.0, 12.0, 0.0)},
        {'co': (0.0, 32.0, 0.0), 'hl': (0.0, 20.0, 0.0), 'hr': (0.0, 33.0, 0.0)},
    ],
    "latticeCurveSwitchLeft_2": [
        {'co': (0.0, 0.0, 0.0), 'hl': (0.0, -1.0, 0.0), 'hr': (0.0, 12.0, 0.0)},
        {'co': (0.0, 32.0, 0.0), 'hl': (0.0, 20.0, 0.0), 'hr': (0.0, 33.0, 0.0)},
    ],
    "latticeCurveSwitchRight_1": [
        {'co': (0.0, 0.0, 0.0), 'hl': (0.0, -1.0, 0.0), 'hr': (0.0, 12.0, 0.0)},
        {'co': (0.0, 32.0, 0.0), 'hl': (0.0, 20.0, 0.0), 'hr': (0.0, 33.0, 0.0)},
    ],
    "latticeCurveSwitchRight_2": [
        {'co': (0.0, 0.0, 0.0), 'hl': (0.0, -1.0, 0.0), 'hr': (0.0, 12.0, 0.0)},
        {'co': (0.0, 32.0, 0.0), 'hl': (0.0, 20.0, 0.0), 'hr': (0.0, 33.0, 0.0)},
    ],
}

def update_curve_position_generic(self, context, axis, curve_name, property_name, point_index=0):
    value = getattr(context.scene, property_name)
    curve = bpy.data.objects.get(curve_name)
    if not curve or curve.type != 'CURVE':
        return

    points = curve.data.splines[0].bezier_points
    if len(points) <= point_index:
        return

    point = points[point_index]
    default = DEFAULT_POINTS.get(curve_name, [])[point_index]

    if axis == 'x':
        point.co.x = value
        point.handle_left.x = default['hl'][0] if value == default['co'][0] else value - 1.0
        point.handle_right.x = default['hr'][0] if value == default['co'][0] else value + 1.0
    elif axis == 'y':
        point.co.y = value
        point.handle_left.y = default['hl'][1] if value == default['co'][1] else value - 1.0
        point.handle_right.y = default['hr'][1] if value == default['co'][1] else value + 1.0
    elif axis == 'z':
        point.co.z = value
        point.handle_left.z = default['hl'][2] if value == default['co'][2] else value - 1.0
        point.handle_right.z = default['hr'][2] if value == default['co'][2] else value + 0.0

def make_update_curve(axis, switch_name, prop_name, point_index=0):
    def update_curve(self, context):
        update_curve_position_generic(self, context, axis, switch_name, prop_name, point_index)
    return update_curve

def create_lattice_with_curve_modifiers():
    bpy.ops.object.add(type='LATTICE', location=(16, 16, 0))
    lattice = bpy.context.object
    lattice.name = "DeformLattice"
    lattice.scale = (32, 32, 32)
    lattice.data.points_u, lattice.data.points_v, lattice.data.points_w = 2, 64, 2
    lattice.data.interpolation_type_u = lattice.data.interpolation_type_v = lattice.data.interpolation_type_w = 'KEY_LINEAR'

    vertex_groups = ["LeftBot1", "LeftTop1", "RightBot1", "RightTop1"]
    for group_name in vertex_groups:
        lattice.vertex_groups.new(name=group_name)

    def create_curve(name, location, scale, points):
        curve_data = bpy.data.curves.new(name=name, type='CURVE')
        curve_object = bpy.data.objects.new(name, curve_data)
        bpy.context.collection.objects.link(curve_object)
        spline = curve_data.splines.new(type='BEZIER')
        spline.bezier_points.add(count=1)
        for i, p in enumerate(points):
            point = spline.bezier_points[i]
            point.co = p['co']
            point.handle_left = p['hl']
            point.handle_right = p['hr']
        curve_data.resolution_u = 64
        curve_data.dimensions = '3D'
        curve_object.scale = scale
        curve_object.location = location
        curve_data.use_radius = curve_data.use_stretch = curve_data.use_deform_bounds = True
        return curve_object

    curves = {
        "LeftBot1": create_curve("latticeCurveSwitchLeft_1", (0, 0, -16), (1, 1, 1), DEFAULT_POINTS["latticeCurveSwitchLeft_1"]),
        "LeftTop1": create_curve("latticeCurveSwitchLeft_2", (0, 0, 16), (1, 1, 1), DEFAULT_POINTS["latticeCurveSwitchLeft_2"]),
        "RightBot1": create_curve("latticeCurveSwitchRight_1", (32, 0, -16), (1, 1, 1), DEFAULT_POINTS["latticeCurveSwitchRight_1"]),
        "RightTop1": create_curve("latticeCurveSwitchRight_2", (32, 0, 16), (1, 1, 1), DEFAULT_POINTS["latticeCurveSwitchRight_2"]),
    }

    vertex_indices = {
        "LeftBot1": list(range(0, 127, 2)),
        "RightBot1": list(range(1, 128, 2)),
        "LeftTop1": list(range(128, 255, 2)),
        "RightTop1": list(range(129, 256, 2)),
    }

    for group_name, indices in vertex_indices.items():
        vg = lattice.vertex_groups.get(group_name)
        if vg:
            for i in indices:
                vg.add([i], 1.0, 'REPLACE')

    for group_name, curve in curves.items():
        mod = lattice.modifiers.new(name=group_name, type='CURVE')
        mod.object = curve
        mod.deform_axis = 'POS_Y'
        mod.vertex_group = group_name

def apply_loopcut(number_cuts, edge_index):
    bpy.ops.mesh.loopcut_slide(MESH_OT_loopcut={"number_cuts": number_cuts, "object_index": 0, "edge_index": edge_index})

class SimpleOperator(bpy.types.Operator):
    bl_idname = "object.create_plane"
    bl_label = "Create Plane"

    def execute(self, context):
        bpy.ops.mesh.primitive_plane_add(size=32, location=(16, 16, 0))
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        apply_loopcut(31, 0)
        apply_loopcut(7, 1)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.modifier_add(type='LATTICE')
        bpy.context.object.modifiers["Lattice"].object = bpy.data.objects["DeformLattice"]
        bpy.ops.object.shade_smooth()
        return {'FINISHED'}

class OBJECT_OT_ResetLatticeCurves(bpy.types.Operator):
    bl_idname = "object.reset_lattice_curves"
    bl_label = "Reset All Curve Points"
    bl_description = "Réinitialise toutes les courbes à leurs valeurs par défaut"

    def execute(self, context):
        for i in range(1, 9):
            for axis in ['X', 'Y', 'Z']:
                prop_name = f"{axis}_{i}"
                default_value = 32.0 if (i >= 5 and axis == 'Y') else 0.0
                setattr(context.scene, prop_name, default_value)
        self.report({'INFO'}, "Courbes remises à zéro ✅")
        return {'FINISHED'}

class LatticeAndPlanePanel(bpy.types.Panel):
    bl_label = "Create Plane and Lattice"
    bl_idname = "OBJECT_PT_lattice_and_plane"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LatticePlane'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.create_lattice", text="Create Lattice")
        layout.operator("object.create_plane", text="Create Plane")

        col = layout.column(align=True)
        labels = [
            "LeftBot1", "LeftTop1", "RightBot1", "RightTop1",
            "LeftBot2", "LeftTop2", "RightBot2", "RightTop2"
        ]

        for i, label in enumerate(labels, start=1):
            col.label(text=label)
            row = col.row(align=True)
            row.prop(context.scene, f"X_{i}", text="X")
            row.prop(context.scene, f"Y_{i}", text="Y")
            row.prop(context.scene, f"Z_{i}", text="Z")

        layout.separator()
        layout.operator("object.reset_lattice_curves", icon='FILE_REFRESH')

class OBJECT_OT_CreateLattice(bpy.types.Operator):
    bl_idname = "object.create_lattice"
    bl_label = "Create Lattice"

    def execute(self, context):
        create_lattice_with_curve_modifiers()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_CreateLattice)
    bpy.utils.register_class(SimpleOperator)
    bpy.utils.register_class(OBJECT_OT_ResetLatticeCurves)
    bpy.utils.register_class(LatticeAndPlanePanel)

    for i in range(1, 5):
        for axis in ['X', 'Y', 'Z']:
            curve_name = f"latticeCurveSwitchLeft_{i}" if i <= 2 else f"latticeCurveSwitchRight_{i - 2}"
            update_func = make_update_curve(axis.lower(), curve_name, f"{axis}_{i}", point_index=0)
            setattr(bpy.types.Scene, f"{axis}_{i}", bpy.props.FloatProperty(
                name=f"{axis}_{i}",
                default=0.0,
                update=update_func
            ))

    for i in range(5, 9):
        for axis in ['X', 'Y', 'Z']:
            curve_name = f"latticeCurveSwitchLeft_{i - 4}" if i <= 6 else f"latticeCurveSwitchRight_{i - 6}"
            update_func = make_update_curve(axis.lower(), curve_name, f"{axis}_{i}", point_index=1)
            default = 32.0 if axis == 'Y' else 0.0
            setattr(bpy.types.Scene, f"{axis}_{i}", bpy.props.FloatProperty(
                name=f"{axis}_{i}",
                default=default,
                update=update_func
            ))

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_CreateLattice)
    bpy.utils.unregister_class(SimpleOperator)
    bpy.utils.unregister_class(OBJECT_OT_ResetLatticeCurves)
    bpy.utils.unregister_class(LatticeAndPlanePanel)

    for i in range(1, 9):
        for axis in ['X', 'Y', 'Z']:
            if hasattr(bpy.types.Scene, f"{axis}_{i}"):
                delattr(bpy.types.Scene, f"{axis}_{i}")

if __name__ == "__main__":
    register()
