from math import ceil
from typing import List, Tuple, Optional

import cv2
from PIL import Image
from PIL.Image import Image as Img
from PIL.ImageDraw import Draw
from numpy import ndarray, array

from shapely.affinity import translate, scale
from shapely.extension.util.flatten import flatten

from shapely.ops import unary_union

from shapely.extension.util.func_util import lmap

from shapely.geometry.base import BaseGeometry, BaseMultipartGeometry

from shapely.geometry import Point, Polygon, LineString

DEFAULT_SCALE_FACTOR = 10


class AssembleGeom:
    def __init__(self, exterior_arr: ndarray):
        self.exterior = exterior_arr.reshape((exterior_arr.shape[1],
                                              exterior_arr.shape[0],
                                              exterior_arr.shape[2]))[0]
        self.interiors = []

    def add_interior(self, interior_arr: ndarray):
        interior_arr = interior_arr.reshape((interior_arr.shape[1],
                                             interior_arr.shape[0],
                                             interior_arr.shape[2]))[0]
        self.interiors.append(interior_arr)


class Raster:

    """
    位图
    origin: 原图左下角点,用于还原原本位置
    """
    def __init__(self, array: ndarray, origin: Point, scale_factor: float = DEFAULT_SCALE_FACTOR):

        self.array = array
        self.origin = origin
        self.scale_factor = scale_factor

    def vectorize(self) -> List[BaseGeometry]:
        contours, hierarchy = cv2.findContours(self.array, mode=cv2.RETR_CCOMP, method=cv2.CHAIN_APPROX_SIMPLE)
        geom_list: List[Optional[AssembleGeom]] = []
        # hierarchy[2]为-1则代表对应contour为hole,并且从属于hierarchy[3]所记录的数值为index的contour
        # 顺序上是exterior之后就是所有的interiors TODO 尝试不依赖此特性重构一个更稳定的方法
        # 全部没孔的话为全-1
        for i, cnt in enumerate(contours):
            if hierarchy[0][i][2] != -1:
                geom_list.append(AssembleGeom(exterior_arr=cnt))
                continue
            if hierarchy[0][i][3] == -1:
                geom_list.append(AssembleGeom(exterior_arr=cnt))
                continue
            geom_list.append(None)
            geom_list[hierarchy[0][i][3]].add_interior(cnt)

        shapely_geoms: List[BaseGeometry] = []
        for geom in geom_list:
            if not geom:
                continue
            if geom.exterior.shape == (1, 2):
                result = Point(geom.exterior[0])
            elif geom.exterior.shape == (2, 2):
                result = LineString(geom.exterior)
            else:
                result = Polygon(shell=geom.exterior, holes=geom.interiors)
            shapely_geoms.append(result)

        union_shape = unary_union(shapely_geoms)
        scaled_shape = scale(union_shape, xfact=1 / self.scale_factor, yfact=1 / self.scale_factor, origin=Point(0, 0))
        moved_shape = translate(scaled_shape, self.origin.x, self.origin.y)
        return flatten(moved_shape).list()

    def convolution(self, kernel: 'Raster') -> 'Raster':
        result = cv2.filter2D(src=self.array, ddepth=-1, kernel=kernel.array)  # ddepth指定输出元素的类型,-1为保持原状,此处为uint8
        return Raster(array=result, origin=self.origin, scale_factor=self.scale_factor).reverse()

    def reverse(self):
        """
        0变1,非0变0
        255在灰度图填充对应fill='WHITE',若使用WHITE则在此处可能产生bug
        """
        self.array[self.array > 0] = 255
        self.array[self.array == 0] = 1
        self.array[self.array == 255] = 0
        return self


class RasterFactory:
    def __init__(self, scale_factor: float = DEFAULT_SCALE_FACTOR):
        self.scale_factor = scale_factor

    def from_geom(self, geom: BaseGeometry) -> Raster:
        bounds = geom.bounds
        anchor_point = Point(bounds[0], bounds[1])
        moved_geom = self._move_to_origin(geom, anchor_point)
        scaled_geom = self._scale(moved_geom)
        # 假如某直线坐标为(0, 0), (10, 0),可以知道事实上这个直线会占据11个点
        image_size = self._cal_size(bounds)
        img = Image.new(mode='L', size=image_size)  # L代表灰度图,数据类型uint8,取值0~255
        self._draw_on(img, scaled_geom)
        matrix = array(img)
        return Raster(array=matrix,
                      origin=anchor_point,
                      scale_factor=self.scale_factor)

    def _cal_size(self, bounds: Tuple[Point, Point, Point, Point]) -> Tuple[int, int]:
        pre_x = (bounds[2] - bounds[0]) * self.scale_factor
        pre_y = (bounds[3] - bounds[1]) * self.scale_factor
        if pre_x == ceil(pre_x):
            pre_x = pre_x + 1
        if pre_y == ceil(pre_y):
            pre_y = pre_y + 1
        return ceil(pre_x), ceil(pre_y)

    def _move_to_origin(self, geom: BaseGeometry, anchor_point: Point) -> BaseGeometry:
        moved_geom = translate(geom, xoff=-anchor_point.x, yoff=-anchor_point.y)
        return moved_geom

    def _scale(self, geom: BaseGeometry) -> BaseGeometry:
        return scale(geom, xfact=self.scale_factor, yfact=self.scale_factor, origin=Point(0, 0))

    def _draw_on(self, img: Img, geom: BaseGeometry):
        # 当斜线的中间某个点距离两边像素点距离相同时,总是画靠近该线终点方向的那边的像素点
        if isinstance(geom, BaseMultipartGeometry):
            lmap(lambda geom_: self._draw_on(img, geom_), geom)
        elif isinstance(geom, Polygon):
            Draw(img).polygon(geom.exterior.coords, fill=1, outline=1)
            for interior in geom.interiors:
                Draw(img).polygon(interior.coords, fill=0, outline=1)  # outline=1让polygon占位尽量大
        elif isinstance(geom, LineString):
            Draw(img).line(geom.coords, fill=1)
        elif isinstance(geom, Point):
            Draw(img).point(geom.coords, fill=1)
        else:
            raise TypeError(f'expect BaseGeometry, but got {type(geom)}')
