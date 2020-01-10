
import bpy
from bpy.props import IntVectorProperty


from .preferences import RAPreferences
from .properties import (
    RAMaterialProps, RAMaterialsDB, RAObjectProps, RASceneProps
)
from .lists import RA_UL_materialdb
from .panels import (
    RA_PT_material, RA_PT_simulation, RA_PT_object, RA_PT_materialdb,
    RA_PT_rendering
)
from .operators import (
    RA_OT_run, RA_OT_debug, RA_OT_new_mat, RA_OT_del_mat, RA_OT_mv_mat,
    RA_OT_save_mat, RA_OT_load_mat
)

bl_info = {
    "name" : "RA",
    "author" : "gmagno",
    "description" : ("Blender interface to Room Acoustics, for more info "
        "check: https://gmagno.dev"
    ),
    "version": (0, 1),
    "blender" : (2, 80, 0),
    "location" : 'View3D',
    "warning" : "",
    "category" : 'Generic',
    "tracker_url": "https://gmagno.dev",
    "support": 'COMMUNITY',
}


classes = (
    # preferences
    RAPreferences,

    # properties
    RAObjectProps,
    RAMaterialsDB,
    RAMaterialProps,
    RASceneProps,

    # operators
    RA_OT_run,
    RA_OT_debug,
    RA_OT_new_mat, RA_OT_del_mat, RA_OT_mv_mat, RA_OT_save_mat, RA_OT_load_mat,

    # panels
    RA_PT_material,
    RA_PT_simulation,
    RA_PT_object,
    RA_UL_materialdb,
    RA_PT_materialdb,
    RA_PT_rendering
)


def setup_properties():
    bpy.types.Object.ra = bpy.props.PointerProperty(type=RAObjectProps)
    bpy.types.Material.ra = bpy.props.PointerProperty(type=RAMaterialProps)
    bpy.types.Scene.ra = bpy.props.PointerProperty(type=RASceneProps)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    setup_properties()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
