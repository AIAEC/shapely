from math import sqrt

try:
    from descartes import PolygonPatch
    from matplotlib import pyplot
except ImportError:
    raise ImportError('This module requires matplotlib and descartes')

from shapely.geometry import LineString, Polygon, Point


class Draw:
    GM = (sqrt(5) - 1.0) / 2.0
    W = 8.0
    H = W * GM
    SIZE = (W, H)

    BLUE = '#6699cc'
    GRAY = '#999999'
    BLACK = '#000000'
    WHITE = '#ffffff'
    RED = '#ff3333'
    GREEN = '#339933'
    YELLOW = '#ffcc33'
    DARKGRAY = '#333333'
    PURPLE = '#660066'

    def __init__(self, size=SIZE, dpi=90):
        self.fig = pyplot.figure(1, figsize=size, dpi=dpi, frameon=False)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.WHITE)
        self.ax.set_aspect('equal')

    def save(self, filename):
        self.fig.savefig(filename)
        return self

    def show(self):
        pyplot.show()
        return self

    def free(self):
        pyplot.close(self.fig)

    def draw(self, geometry, color=BLUE, edge_color=BLACK, alpha=0.5):
        for geom in geometry.ext.flatten():
            if isinstance(geom, LineString):
                self.draw_line(geom, color)
            elif isinstance(geom, Polygon):
                self.draw_polygon(geom, color, edge_color, alpha)
            elif isinstance(geom, Point):
                self.draw_point(geom, color)

        return self

    def draw_line(self, line: LineString, color=BLUE):
        x, y = line.xy
        self.ax.plot(x, y, color=color, alpha=0.7, linewidth=1.5, solid_capstyle='round', zorder=2)
        return self

    def draw_polygon(self, polygon: Polygon, color=GRAY, edge_color=BLACK, alpha=0.5):
        patch = PolygonPatch(polygon.ext.shell,
                             facecolor=color,
                             edgecolor=edge_color,
                             linewidth=0.5,
                             alpha=alpha,
                             zorder=1)
        self.ax.add_patch(patch)

        for hole in polygon.ext.holes:
            patch = PolygonPatch(hole,
                                 facecolor=self.WHITE,
                                 edgecolor=edge_color,
                                 linewidth=0.5,
                                 alpha=1,
                                 zorder=1)
            self.ax.add_patch(patch)
        return self

    def draw_point(self, point: Point, color=RED):
        self.ax.plot(point.x, point.y, 'o',
                     color=color,
                     alpha=0.7,
                     zorder=2)
        return self
