from shapely.extension.constant import MATH_MIDDLE_EPS
from shapely.extension.model.angle import Angle
from shapely.extension.strategy.angle_strategy import PolygonAngleStrategy
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry


class Rect(Polygon):
    """
    child type of Polygon that represent a rectangle.
    """

    def __init__(self, shell=None):
        super().__init__(shell, None)
        if not self.is_rect(self):
            raise ValueError('shell cannot form a rectangle')

    @classmethod
    def is_rect(cls, geom: BaseGeometry, area_tol: float = MATH_MIDDLE_EPS):
        return geom.minimum_rotated_rectangle.symmetric_difference(geom).area <= area_tol

    @property
    def angle(self) -> Angle:
        return self.ext.angle(PolygonAngleStrategy(0).by_bounding_box_width())
