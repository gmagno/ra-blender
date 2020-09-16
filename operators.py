
import csv
import json
import pathlib

import bmesh
import bpy
from bpy.props import IntVectorProperty, StringProperty
from bpy.types import Operator, SpaceView3D
from bpy_extras.io_utils import ExportHelper, ImportHelper
import colorcet as cc
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
import numpy as np
from ra import simulation_api

from .rendering import rendering_man

gldraw_handler = None


class RA_OT_run(bpy.types.Operator):
    """Runs the simulation"""
    bl_idname = 'ra.run'
    bl_label = 'Run'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global gldraw_handler

        context.scene.ra.rtngn_running = not context.scene.ra.rtngn_running

        alg_configs = {
            'freq': [63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0],
            'n_rays': context.scene.ra.nrays,
            'ht_length': context.scene.ra.ht_length,
            'dt': context.scene.ra.dt,
            'allow_scattering': int(context.scene.ra.allow_scattering),
            'transition_order': context.scene.ra.transition_order,
            'rec_radius_init': context.scene.ra.rec_radius_init,
            'allow_growth': int(context.scene.ra.allow_growth),
            'rec_radius_final': context.scene.ra.rec_radius_final
        }
        air_properties = {
            'Temperature': context.scene.ra.temperature,
            'hr': context.scene.ra.hr,
            'p_atm': context.scene.ra.p_atm
        }

        planes = []
        recs = []
        srcs = []
        for obj in bpy.context.scene.objects:
            if obj.ra.enable:
                if obj.ra.nature == 'GEOM' and obj.type == 'MESH':
                    obj.data.calc_loop_triangles()
                    for i, tri in enumerate(obj.data.loop_triangles):
                        # convert from local to global coordinates
                        vertices = np.array(
                            [obj.matrix_world @ obj.data.vertices[i].co
                            for i in tri.vertices]
                        )
                        normal = np.array(
                            obj.matrix_world @ tri.normal,
                            dtype=np.float32
                        )
                        # compute triangle area using global coords vertices
                        a, b, c = vertices
                        area = np.linalg.norm(np.cross((b - a), (c-a))) * 0.5

                        alpha = None
                        # FIXME: raise exceptions instead of checking with `if`
                        if obj.active_material is None:
                            self.report(
                                {'ERROR'},
                                f"Object {obj.name} has no valid material"
                            )
                            return {'FINISHED'}

                        mat_idx = obj.active_material.ra.mat_id
                        scattering = obj.active_material.ra.scattering
                        for m in bpy.context.scene.ra.mat_db:
                            if m.index == mat_idx:
                                alpha = np.array(
                                    m.alpha,
                                    dtype=np.float32
                                )
                        if alpha is None:
                            self.report(
                                {'ERROR'},
                                f"Object {obj.name} has no valid material"
                            )
                            return {'FINISHED'}

                        planes.append({
                            'name': f"{obj.name}.{i}",
                            'bbox': False,
                            'vertices': vertices,
                            'normal': normal,
                            # 'alpha': np.array([0.14]*8, dtype=np.float32),
                            'alpha': alpha,
                            's': scattering,
                            # 'area': tri.area  # FIXME: should be computed by the engine
                            'area': area
                        })
                elif obj.ra.nature == 'SOURCE':
                    srcs.append({
                        'coord': tuple(obj.location),
                        'orientation': [0.0, 1.0, 0.0],
                        'power_dB': list(obj.ra.power_db),
                        'eq_dB': list(obj.ra.eq_db),
                        'delay': obj.ra.delay,
                    })
                elif obj.ra.nature == 'RECEIVER':
                    recs.append({
                        'coord': tuple(obj.location),
                        'orientation': [0.0, 1.0, 0.0]
                    })

        sims = simulation_api.Simulation()
        sims.set_configs(alg_configs)
        sims.set_air(air_properties)
        sims.set_geometry(planes)
        sims.set_raydir()
        sims.set_receivers(recs)
        sims.set_memory_init()
        sims.set_sources(srcs)
        sims.run_statistical_reverberation()
        sims.run_raytracing()

        rendering_man.set_sources(sims.sources)
        rendering_man.reg_draw_callback(
            order=context.scene.ra.render_order, render=context.scene.ra.render
        )

        context.area.tag_redraw()

        self.report({'INFO'}, "Simulation finished!")
        return {'FINISHED'}

class RA_OT_debug(bpy.types.Operator):
    """Debugging purposes only"""
    bl_idname = 'ra.debugra'
    bl_label = 'DebugRA'

    def execute(self, context):
        print("debug ra")
        return {'FINISHED'}

class RA_OT_new_mat(bpy.types.Operator):
    """Add a new item to the materials list"""

    bl_idname = 'ra.new_mat'
    bl_label = 'Add a new item'

    def execute(self, context):
        new_mat = context.scene.ra.mat_db.add()
        new_mat.index = context.scene.ra.mat_db_max_index + 1
        context.scene.ra.mat_db_max_index += 1
        bpy.context.scene.ra.mat_db_index = len(context.scene.ra.mat_db) - 1
        return{'FINISHED'}

class RA_OT_del_mat(bpy.types.Operator):
    """Delete the selected item from the materials list"""

    bl_idname = 'ra.del_mat'
    bl_label = 'Deletes an item'

    @classmethod
    def poll(cls, context):
        return context.scene.ra.mat_db

    def execute(self, context):
        mat_db = context.scene.ra.mat_db
        index = context.scene.ra.mat_db_index
        mat_db.remove(index)
        context.scene.ra.mat_db_index = min(max(0, index - 1), len(mat_db) - 1)
        return{'FINISHED'}

class RA_OT_mv_mat(bpy.types.Operator):
    """Move an item in the materials list"""

    direction: bpy.props.EnumProperty(
        items=(('UP', 'Up', ""), ('DOWN', 'Down', ""),)
    )

    bl_idname = 'ra.mv_mat'
    bl_label = 'Move an item in the list'

    @classmethod
    def poll(cls, context):
        return context.scene.ra.mat_db

    def move_index(self):
        """Move index of an item render queue while clamping it"""

        index = bpy.context.scene.ra.mat_db_index
        list_length = len(bpy.context.scene.ra.mat_db) - 1 # (index starts at 0)
        new_index = index + (-1 if self.direction == 'UP' else 1)
        bpy.context.scene.ra.mat_db_index = max(0, min(new_index, list_length))

    def execute(self, context):
        mat_db = context.scene.ra.mat_db
        index = context.scene.ra.mat_db_index
        neighbor = index + (-1 if self.direction == 'UP' else 1)
        mat_db.move(neighbor, index)
        self.move_index()
        return{'FINISHED'}


class RA_OT_save_mat(bpy.types.Operator, ExportHelper):
    """Save the materials list to the file system"""

    bl_idname = 'ra.save_mat'
    bl_label = 'save'
    filename_ext = ".csv"

    filter_glob: StringProperty(default="*.csv", options={'HIDDEN'}, maxlen=255)

    @classmethod
    def poll(cls, context):
        return context.scene.ra.mat_db

    def execute(self, context):
        mat_db = context.scene.ra.mat_db

        p = pathlib.Path(self.filepath)
        fieldnames = ['id', 'Description', 'alpha']
        with p.open(mode='w') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quotechar='"', delimiter=',')
            writer.writeheader()
            for m in mat_db:
                row = (
                    str(m.index),
                    m.description,
                    "[" + " ".join([str(a) for a in m.alpha]) + "]"
                )
                writer.writerow(dict(zip(fieldnames, row)))

        self.report({'INFO'}, f"Materials file saved to: {self.filepath}")
        return {'FINISHED'}


class RA_OT_load_mat(bpy.types.Operator, ImportHelper):
    """Load the materials list from the file system"""

    bl_idname = 'ra.load_mat'
    bl_label = 'Load'
    filename_ext = ".csv"

    filter_glob: StringProperty(default="*.csv", options={'HIDDEN'}, maxlen=255)

    def execute(self, context):
        p = pathlib.Path(self.filepath)
        with p.open() as f:
            reader = csv.DictReader(f, quotechar='"', delimiter=',')
            data = list(reader)

        # FIXME: should do this in a more efficient way
        # wipe entire list of materials
        for _ in range(len(context.scene.ra.mat_db)):
            context.scene.ra.mat_db.remove(0)
        context.scene.ra.mat_db_max_index = -1

        max_index = -1
        for row in data:
            max_index = max(max_index, int(row['id']))
            new_mat = context.scene.ra.mat_db.add()
            new_mat.index = int(row['id'])
            new_mat.description = row['Description']
            new_mat.alpha = [float(a) for a in row['alpha'].strip('[]').split()]

            context.scene.ra.mat_db_max_index = max_index
            context.scene.ra.mat_db_index = 0


        self.report({'INFO'}, f"Materials list loaded from {self.filepath}")
        return{'FINISHED'}
