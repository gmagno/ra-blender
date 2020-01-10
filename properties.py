
import pathlib

import bpy
import toml

from .rendering import rendering_man


#    ___ _     _           _
#   /___\ |__ (_) ___  ___| |_
#  //  // "_ \| |/ _ \/ __| __|
# / \_//| |_) | |  __/ (__| |_
# \___/ |_.__// |\___|\___|\__|
#           |__/
#

class RAObjectProps(bpy.types.PropertyGroup):

    enable: bpy.props.BoolProperty(
        name="enable",
        description=(
            "Whether the object geometry should be considered in the simulation"
        ),
        default=True,
    )

    nature: bpy.props.EnumProperty(
        name="nature",
        description="The object acoustic nature: { GEOM, SOURCE, RECEIVER }",
        items={
            ('GEOM', "geometry", "Reflective geometry"),
            ('SOURCE', "source", "an acoustic source"),
            ('RECEIVER', "receiver", "an acoustic receiver"),
        },
        default='GEOM'
    )

    power_db: bpy.props.FloatVectorProperty(
        name="power_db", description="Source power in dB",
        step=100, size=8, default=(80.0,)*8
    )

    eq_db: bpy.props.FloatVectorProperty(
        name="eq_db", description="eq in dB",
        step=100, size=8, default=(0.0,)*8
    )

    delay: bpy.props.FloatProperty(
        name="delay",
        description="Delay",
        default=0.0,
    )


#               _            _       _
#   /\/\   __ _| |_ ___ _ __(_) __ _| |
#  /    \ / _` | __/ _ \ "__| |/ _` | |
# / /\/\ \ (_| | ||  __/ |  | | (_| | |
# \/    \/\__,_|\__\___|_|  |_|\__,_|_|
#

class RAMaterialsDB(bpy.types.PropertyGroup):
    """Group of properties representing an item in the list."""
    index: bpy.props.IntProperty(
        name="Id", description="Material reference index", default=0, min=0
    )
    alpha: bpy.props.FloatVectorProperty(
        name="Alpha", description="The material absorption coefficient",
        step=1, min=0.0, max=1.0, size=8, default=(0.0,)*8
    )
    description: bpy.props.StringProperty(
        name="Description", description="Longer material description",
        default="--"
    )


class RAMaterialProps(bpy.types.PropertyGroup):

    mat_id: bpy.props.IntProperty(
        name="MaterialId", description="The material Id", default=0, min=0
    )

    # scattering: bpy.props.FloatProperty(
    #     name="scattering",
    #     description="The material scattering coefficient. Represents the "
    #         "probability of a non-absorbed ray to be reflected as diffuse (as "
    #         "opposed to specular)",
    #     default=0.1,
    #     soft_min=0.0,
    #     soft_max=1.0,
    # )



#  __
# / _\ ___ ___ _ __   ___
# \ \ / __/ _ \ "_ \ / _ \
# _\ \ (_|  __/ | | |  __/
# \__/\___\___|_| |_|\___|
#

def update_sim_cfgs(cfg):
    bpy.context.scene.ra.temperature = cfg['air']['Temperature']
    bpy.context.scene.ra.title = cfg['title']
    bpy.context.scene.ra.nrays = cfg['controls']['Nrays']
    bpy.context.scene.ra.ht_length = cfg['controls']['ht_length']
    bpy.context.scene.ra.dt = cfg['controls']['Dt']
    bpy.context.scene.ra.allow_scattering = cfg['controls']['allow_scattering']
    bpy.context.scene.ra.transition_order = cfg['controls']['transition_order']
    bpy.context.scene.ra.rec_radius_init = cfg['controls']['rec_radius_init']
    bpy.context.scene.ra.allow_growth = cfg['controls']['allow_growth']
    bpy.context.scene.ra.rec_radius_final = cfg['controls']['rec_radius_final']
    bpy.context.scene.ra.hr = cfg['air']['hr']
    bpy.context.scene.ra.p_atm = cfg['air']['p_atm']


def update_sim_cfgs_callback(self, context):
    cfg = toml.loads(pathlib.Path(self.sim_cfgs).read_text())
    update_sim_cfgs(cfg)


def update_render_callback(self, context):
    rendering_man.reg_draw_callback(order=self.render_order, render=self.render)
    # context.area.tag_redraw()


class RASceneProps(bpy.types.PropertyGroup):

    render_order: bpy.props.IntProperty(
        name="Rendering order", default=2, min=2,
        update=update_render_callback
    )
    render: bpy.props.BoolProperty(
        name="Render",
        description="Whether rays should be rendered or not",
        default=True,
        update=update_render_callback
    )

    mat_db: bpy.props.CollectionProperty(type=RAMaterialsDB)
    mat_db_index: bpy.props.IntProperty(
        name="Material database index", default=-1
    )
    mat_db_max_index: bpy.props.IntProperty(
        name="Material database max index", default=-1
    )

    rtngn_running: bpy.props.BoolProperty(
        name="ray tracing engine is running",
        description="whether the ray tracing engine is running the simulation",
        default=False
    )

    sim_cfgs: bpy.props.StringProperty(
        name="Simulation configuration parameters",
        description="Path to the .toml file with config parameters",
        default="//", maxlen=1024, subtype="FILE_PATH",
        update=update_sim_cfgs_callback
    )

    title: bpy.props.StringProperty(
        name="Simulation title",
        description="Simulation title",
        default="noname", maxlen=1024,
    )

    nrays: bpy.props.IntProperty(
        name="nrays",
        description="Number of rays",
        default=100,
        min=0
    )

    ht_length: bpy.props.FloatProperty(
        name="ht_length",
        description="Impulse response duration",
        default=3.0,
        min=0.0
    )

    dt: bpy.props.FloatProperty(
        name="dt",
        description="Histogram resolution",
        default=0.001,
        precision=3,
        min=0.0
    )

    allow_scattering: bpy.props.BoolProperty(
        name="allow_scattering",
        description="Allow scattering of the rays on the walls",
        default=True
    )

    transition_order: bpy.props.IntProperty(
        name="transition_order",
        description="Transition order",
        default=2,
        min=0
    )

    rec_radius_init: bpy.props.FloatProperty(
        name="rec_radius_init",
        description="Receiver initial radius",
        default=0.1,
        min=0.0
    )

    allow_growth: bpy.props.BoolProperty(
        name="allow_growth",
        description="Allow receiver growth",
        default=True
    )

    rec_radius_final: bpy.props.FloatProperty(
        name="rec_radius_final",
        description="Receiver final radius (if `allow_growth` is checked)",
        default=1.0,
        min=0.0
    )

    temperature: bpy.props.FloatProperty(
        name="temperature",
        description="Room air temperature",
        default=20.0,
        min=0.0
    )

    hr: bpy.props.FloatProperty(
        name="hr",
        description="Relative humidity",
        default=50.0,
        min=0.0
    )

    p_atm: bpy.props.FloatProperty(
        name="p_atm",
        description="Atmospheric pressure",
        default=101325.0,
        min=0.0
    )
