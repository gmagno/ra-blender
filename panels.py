
import bpy


class RASidebar():
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Acoustics'


class RA_PT_simulation(RASidebar, bpy.types.Panel):
    bl_label = 'Simulation'

    def draw(self, context):
        scene_ra = context.scene.ra
        layout = self.layout
        layout.use_property_split = True

        layout.prop(scene_ra, 'sim_cfgs', text="config toml")
        layout.prop(scene_ra, 'title', text="title")
        layout.prop(scene_ra, 'nrays', text="nrays")
        layout.prop(scene_ra, 'ht_length', text="htlen")
        layout.prop(scene_ra, 'dt', text="dt")
        layout.prop(scene_ra, 'allow_scattering', text="scattering")
        layout.prop(scene_ra, 'transition_order', text="transit order")
        layout.prop(scene_ra, 'rec_radius_init', text="rec init rad")
        layout.prop(scene_ra, 'allow_growth', text="rec grows")
        layout.prop(scene_ra, 'rec_radius_final', text="rec final rad")
        layout.prop(scene_ra, 'temperature', text="temp")
        layout.prop(scene_ra, 'hr', text="rel humidity")
        layout.prop(scene_ra, 'p_atm', text="atm press")

        layout.operator('ra.run', text="Run", icon='RADIOBUT_OFF')


class RA_PT_materialdb(RASidebar, bpy.types.Panel):
    bl_label = 'Materials'

    def draw(self, context):
        scene_ra = context.scene.ra
        layout = self.layout
        layout.use_property_split = True

        layout.template_list(
            "RA_UL_materialdb", "Materials",
            scene_ra, 'mat_db',
            scene_ra, 'mat_db_index',
            type='DEFAULT'
        )

        row = layout.row()
        col = row.column()
        col.operator('ra.new_mat', text='', icon='ADD')
        col.operator('ra.del_mat', text='', icon='REMOVE')
        col = row.column()
        col.operator('ra.mv_mat', text='', icon='SORT_DESC').direction = 'UP'
        col.operator('ra.mv_mat', text='', icon='SORT_ASC').direction = 'DOWN'
        col = row.column()
        col.operator('ra.save_mat', text='', icon='EXPORT')
        col.operator('ra.load_mat', text='', icon='IMPORT')

        if scene_ra.mat_db_index >= 0 and len(scene_ra.mat_db) > 0:
            item = scene_ra.mat_db[scene_ra.mat_db_index]

            col = row.column()
            col.prop(item, 'index')
            col.prop(item, 'name')
            col.prop(item, 'alpha')
            col.prop(item, 'description')


class RA_PT_rendering(RASidebar, bpy.types.Panel):
    bl_label = 'Rendering'

    def draw(self, context):
        scene_ra = context.scene.ra
        layout = self.layout
        layout.use_property_split = True

        col = layout.column()
        col.prop(scene_ra, 'render')
        col.prop(scene_ra, 'render_order')


class RA_PT_object(bpy.types.Panel):
    bl_idname = 'RA_PT_object'
    bl_label = 'Acoustics'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        criteria = (
            context.object is not None
        )
        return criteria

    def draw_header(self, context):
        layout = self.layout
        obj = context.object
        objs = context.selected_objects

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        ra_obj_props = context.object.ra

        col = layout.column()
        col.prop(ra_obj_props, 'enable', text="Enable")
        col.prop(ra_obj_props, 'nature', text="Nature")
        if ra_obj_props.nature == 'SOURCE':
            col.prop(ra_obj_props, 'power_db', text="Power [dB]")
            col.prop(ra_obj_props, 'eq_db', text="Eq [dB]")
            col.prop(ra_obj_props, 'delay', text="delay")


class RA_PT_material(bpy.types.Panel):
    bl_idname = 'RA_PT_material'
    bl_label = 'Acoustics'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        criteria = (
            context.object is not None and
            context.object.active_material is not None
        )
        return criteria

    def draw_header(self, context):
        layout = self.layout
        obj = context.object
        objs = context.selected_objects

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        ra_mat_props = context.object.active_material.ra

        col = layout.column()
        col.prop(ra_mat_props, 'mat_id', text='Material Id')
        for m in context.scene.ra.mat_db:
            if m.index == ra_mat_props.mat_id:
                col.prop(m, 'description')
                col.prop(m, 'alpha')
                col.prop(ra_mat_props, 'scattering')
                break
