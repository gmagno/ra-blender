
import bpy
import colorcet as cc
import numpy as np
import gpu
from gpu_extras.batch import batch_for_shader


class RenderingManager:
    def __init__(self):
        self.gldraw_handler = None
        self.sources = None
        self.max_order = 2

    def set_sources(self, sources):
        self.sources = sources
        self.dereg_draw_callback()
        # FIXME: using the first source refpts hist to set the maximum order
        # allowed, this is not ideal, a per source solution should be
        # considered...
        self.max_order = len(sources[0].rays[0].refpts_hist) + 1

        rays = []
        for si, s in enumerate(sources):
            nhist = len(s.rays[0].refpts_hist) + 1
            rays.append({
                'positions': np.zeros((len(s.rays)*nhist, 3), dtype=np.float32),
                'indices': np.zeros((len(s.rays)*(nhist-1), 2), dtype=np.int32)
            })
            for ri, r in enumerate(s.rays):
                rays[si]['positions'][ri*nhist] = s.coord
                fro, to = ri*nhist+1, ri*nhist+1 + nhist-1
                rays[si]['positions'][fro:to] = r.refpts_hist
                fro, to = ri*(nhist-1), ri*(nhist-1) + nhist-1
                rays[si]['indices'][fro:to, 0] = np.arange(
                    ri*nhist, ri*nhist + nhist-1
                )
                rays[si]['indices'][fro:to, 1] = np.arange(
                    ri*nhist + 1, ri*nhist + nhist
                )
        self.rays = rays

    def dereg_draw_callback(self):
        if self.gldraw_handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                self.gldraw_handler, 'WINDOW'
            )
            self.gldraw_handler = None

    def reg_draw_callback(self, order, render=True):
        if self.sources is None:
            return

        self.dereg_draw_callback()
        if render:
            indices_eff = []
            for si, s in enumerate(self.sources):
                nhist = len(s.rays[0].refpts_hist) + 1
                idx_eff = self.rays[si]['indices']
                idx_eff = idx_eff.reshape((idx_eff.shape[0]//(nhist-1), -1))
                idx_eff = idx_eff[:, :order*2].reshape((-1, 2))
                indices_eff.append(idx_eff)

            shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
            draw_data = []
            for ri, r in enumerate(self.rays):
                h = cc.glasbey[ri % len(cc.rainbow)].lstrip('#')
                draw_data.append({
                        'batch': batch_for_shader(
                            shader, 'LINES',
                            {'pos': r['positions']}, indices=indices_eff[ri]
                        ),
                        'color': tuple(
                            int(h[i:i+2], 16) / 256.0 for i in (0, 2, 4)
                        ) + (1,)
                })

            def draw():
                shader.bind()
                for d in draw_data:
                    shader.uniform_float("color", d['color'])
                    d['batch'].draw(shader)

            self.gldraw_handler = bpy.types.SpaceView3D.draw_handler_add(
                draw, (), 'WINDOW', 'POST_VIEW'
            )


rendering_man = RenderingManager()
