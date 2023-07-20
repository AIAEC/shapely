from math import sqrt
from random import random

from shapely.ops import unary_union

try:
    from descartes import PolygonPatch
    from matplotlib import pyplot
    from matplotlib.font_manager import FontProperties
except ImportError:
    raise ImportError('This module requires matplotlib and descartes')

from shapely.geometry import LineString, Polygon, Point


class Draw:
    GM = (sqrt(5) - 1.0) / 2.0
    W = 8.0
    H = W * GM
    SIZE = (W, H)

    # color
    BLUE = '#6699cc'
    GRAY = '#999999'
    BLACK = '#000000'
    WHITE = '#ffffff'
    RED = '#ff3333'
    GREEN = '#339933'
    YELLOW = '#ffcc33'
    DARKGRAY = '#333333'
    PURPLE = '#660066'
    RANDOM = 'random'

    # line style
    SOLID = 'solid'
    DOTTED = 'dotted'

    def __init__(self, size=SIZE,
                 dpi: int = 90,
                 axis: bool = False,
                 margin=(0, 0),
                 use_gui: bool = True):
        if not use_gui and pyplot.get_backend() != 'agg':
            pyplot.switch_backend('agg')
        elif use_gui and pyplot.get_backend() != 'Tkagg':
            pyplot.switch_backend('Tkagg')
        self.fig = pyplot.figure(1, figsize=size, dpi=dpi, frameon=False)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.WHITE)
        self.ax.set_aspect('equal')
        self.ax.margins(*margin)
        if not axis:
            self.ax.axis('off')

    def save(self, filename, transparent=False, bbox_inches='tight', pad_inches=0):
        self.fig.savefig(filename, transparent=transparent, bbox_inches=bbox_inches, pad_inches=pad_inches)
        self.free()
        return self

    def show(self):
        pyplot.show()
        return self

    def free(self):
        pyplot.close(self.fig)

    def draw(self, geometry, color=BLUE, edge_color=BLACK, alpha=0.5, line_width=1.5, linestyle=SOLID, zorder=None):
        if not geometry:
            return self

        for geom in geometry.ext.flatten():
            if isinstance(geom, LineString):
                self.draw_line(geom, color=color, alpha=alpha, line_width=line_width, linestyle=linestyle,
                               zorder=zorder)
            elif isinstance(geom, Polygon):
                self.draw_polygon(geom, color=color, edge_color=edge_color, alpha=alpha, line_width=line_width,
                                  linestyle=linestyle, zorder=zorder)
            elif isinstance(geom, Point):
                self.draw_point(geom, color=color, zorder=zorder)

        return self

    @staticmethod
    def color(color_code: str) -> str:
        if color_code == 'random':
            return f'#{int(random() * 0x1000000):06x}'
        return color_code

    def draw_line(self, line: LineString, color=BLUE, line_width: float = 1.5, alpha=0.7, linestyle=SOLID, zorder=2):
        x, y = line.xy
        self.ax.plot(x, y, color=self.color(color), alpha=alpha, linewidth=line_width, solid_capstyle='round',
                     zorder=zorder, linestyle=linestyle)
        return self

    def draw_polygon(self, polygon: Polygon, color=GRAY, edge_color=BLACK, alpha=0.5, line_width=1.5, linestyle=SOLID,
                     zorder=1):
        if polygon.ext.holes:
            polygon = polygon.ext.shell.difference(unary_union([hole for hole in polygon.ext.holes]))

        patch = PolygonPatch(polygon,
                             facecolor=self.color(color),
                             edgecolor=self.color(edge_color),
                             linewidth=line_width,
                             alpha=alpha,
                             linestyle=linestyle,
                             zorder=zorder)
        self.ax.add_patch(patch)
        self.ax.autoscale_view()
        return self

    def draw_point(self, point: Point, color=RED, zorder=3):
        self.ax.plot(point.x, point.y, 'o',
                     color=self.color(color),
                     alpha=0.7,
                     zorder=zorder)
        return self

    def draw_text(self, text: str, origin: Point, fontsize: int = 12, fontstyle: str = "Noto Sans CJK JP", zorder=4):
        # draw text aligned middle
        self.ax.text(origin.x, origin.y, text,
                     horizontalalignment='center',
                     verticalalignment='center',
                     fontsize=fontsize,
                     color=self.BLACK,
                     zorder=zorder,
                     fontproperties=FontProperties(family=[fontstyle]))
        self.ax.autoscale_view()
        return self
