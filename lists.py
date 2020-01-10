import bpy

class RA_UL_materialdb(bpy.types.UIList):
    """Table with available materials and respective acoustic properties."""
    def draw_item(
        self, context, layout, data, item, icon,
        active_data, active_propname, index
    ):
        custom_icon = 'MATERIAL_DATA'
        row = layout.row()
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row.label(text=str(item.index), icon=custom_icon)
            row.label(text=item.description)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)
