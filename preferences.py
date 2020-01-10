
import bpy
from bpy.props import StringProperty
from bpy.types import AddonPreferences


class RAPreferences(AddonPreferences):

    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Room Acoustics preferences...")
