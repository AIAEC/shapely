from operator import attrgetter
from typing import Optional, List

from shapely.extension.constant import LARGE_ENOUGH_DISTANCE, MATH_EPS
from shapely.extension.model.coord import Coord
from shapely.extension.typing import CoordType
from shapely.extension.util.easy_enum import EasyEnum
from shapely.extension.util.func_util import lmap
from shapely.extension.util.prolong import prolong
from shapely.geometry import LineString, Point, LinearRing
from shapely.ops import substring


class LineExtent:
    def __init__(self, merged_line: LineString,
                 extended_curve_ab: LineString,
                 extended_curve_cd: LineString,
                 joint: Point):
        self.merged_curve: LineString = merged_line
        self.extended_curve_ab: LineString = extended_curve_ab
        self.extended_curve_cd: LineString = extended_curve_cd
        self.joint: Point = joint

    @property
    def both_extended_curve_valid(self) -> bool:
        return (self.extended_curve_cd.is_valid
                and not self.extended_curve_cd.is_empty
                and self.extended_curve_ab.is_valid
                and not self.extended_curve_ab.is_empty)

    class ExtendingDirection(EasyEnum):
        TO_FRONT = 'to_front'
        TO_END = 'to_end'

    @classmethod
    def _curve_coords_extending_in_curve_dir(cls, curve: LineString,
                                             joint: Point,
                                             direction: ExtendingDirection) -> List[CoordType]:
        """
        将曲线按照给定方向extend到joint, 如果无法extend到joint, 则返回空list

        :param curve: 给定曲线
        :param joint: extend的目标点
        :param direction: extend的方向
        :return: extend之后的曲线的coords
        """
        if curve.ext.almost_intersects(joint, MATH_EPS):
            joint_pos_ratio = curve.project(joint, normalized=True)
            if direction == cls.ExtendingDirection.TO_END:
                # TODO what if joint_pos_ratio == 0?
                return list(substring(curve, 0.0, joint_pos_ratio, normalized=True).coords)
            else:  # TO_FRONT
                # TODO what if joint_pos_ratio == 1?
                return list(substring(curve, joint_pos_ratio, 1.0, normalized=True).coords)

        if direction == cls.ExtendingDirection.TO_FRONT:
            return list(joint.coords) + list(curve.coords)[1:]

        elif direction == cls.ExtendingDirection.TO_END:
            return list(curve.coords)[:-1] + list(joint.coords)

        return []

    @classmethod
    def of_sequence_curves(cls, curve_ab: LineString,
                           curve_cd: LineString,
                           extent_dist: float = LARGE_ENOUGH_DISTANCE,
                           make_closed: bool = False,
                           ignore_parallel: bool = False) -> Optional['LineExtent']:
        """
        将曲线ab和曲线cd延展(拉伸/裁剪), 直到他们'联合'在一起, 相交于交点e. 曲线aed会是'联合'起来的新曲线
        若曲线ab和曲线cd拉伸后也不相交, 则会返回None
        Parameters
        ----------
        curve_ab: 曲线ab, 注意直线为曲线的特殊形式
        curve_cd: 曲线cd, 注意直线为曲线的特殊形式
        extent_dist: curve_ab和curve_cd的拉伸距离, 默认为LARGE_ENOUGH_DISTANCE
        make_closed: 如果为False, 则沿着curve_ab延展到curve_cd上, 如果为True, 则除了将curve_ab延展到curve_cd上, curve_cd也会
            做延展到curve_ab上, 并尝试构建一个环, 如果失败则返回None
        ignore_parallel: 如果curve_ab和curve_cd拉伸后重合, 该参数为True是, 返回None, 若为False, 返回融合后的直线

        Returns
        -------
        LineExtend对象或者None
        """
        if not make_closed:
            return cls._of_sequence_curves_helper(curve_ab=curve_ab,
                                                  curve_cd=curve_cd,
                                                  extent_dist=extent_dist,
                                                  ignore_parallel=ignore_parallel)

        # try to extend curve_cd back to the curve_ab and make a closed ring
        ab_to_cd_extent = cls._of_sequence_curves_helper(curve_ab=curve_ab,
                                                         curve_cd=curve_cd,
                                                         extent_dist=extent_dist,
                                                         ignore_parallel=ignore_parallel)
        cd_to_ab_extent = cls._of_sequence_curves_helper(curve_ab=curve_cd,
                                                         curve_cd=curve_ab,
                                                         extent_dist=extent_dist,
                                                         ignore_parallel=ignore_parallel)

        if ab_to_cd_extent and cd_to_ab_extent:
            # TODO: bad fix
            return cls._make_ring_from_curve_cd_to_curve_ab(curve_ab=curve_ab,
                                                            curve_cd=curve_cd,
                                                            cd_to_ab_extent=cd_to_ab_extent,
                                                            ab_to_cd_extent=ab_to_cd_extent) or ab_to_cd_extent

        return ab_to_cd_extent

    @classmethod
    def _make_ring_from_curve_cd_to_curve_ab(cls, curve_ab: LineString,
                                             curve_cd: LineString,
                                             ab_to_cd_extent: 'LineExtent',
                                             cd_to_ab_extent: 'LineExtent') -> Optional['LineExtent']:
        """
        将curve ab和curve cd首尾两头进行延展, 直到组成一个环，如果不能组成则返回None

        Parameters
        ----------
        curve_ab: 原curve ab
        curve_cd: 原curve cd
        ab_to_cd_extent: 延射线ab方向和射线dc方向进行延展得到的line_extent
        cd_to_ab_extent: 延射线cd和射线ba方向进行延展得到的line_extent

        Returns
        -------
        LineExtend对象或者None
        """
        stretched_curve_ab = prolong(line=curve_ab,
                                     front_prolong_len=LARGE_ENOUGH_DISTANCE,
                                     end_prolong_len=LARGE_ENOUGH_DISTANCE)

        # cd_to_ab_extent decides the starting point of the segment
        # ab_to_cd_extent decides the ending point of the segment
        extended_curve_ab = substring(geom=stretched_curve_ab,
                                      start_dist=stretched_curve_ab.project(cd_to_ab_extent.joint),
                                      end_dist=stretched_curve_ab.project(ab_to_cd_extent.joint))
        curve_cd_coords = cls._curve_coords_extending_in_curve_dir(curve=curve_cd,
                                                                   joint=ab_to_cd_extent.joint,
                                                                   direction=cls.ExtendingDirection.TO_FRONT)
        curve_cd_coords = cls._curve_coords_extending_in_curve_dir(curve=LineString(curve_cd_coords),
                                                                   joint=cd_to_ab_extent.joint,
                                                                   direction=cls.ExtendingDirection.TO_END)
        curve_ab_coords = list(extended_curve_ab.coords)
        if len(curve_ab_coords) < 1 or len(curve_cd_coords) < 1:
            return None
        # try to calculate merged ring's coords
        extended_curve_cd = LineString(curve_cd_coords)
        if Coord.dist(curve_ab_coords[-1], curve_cd_coords[0]) < MATH_EPS:
            curve_cd_coords = curve_cd_coords[1:]
        if Coord.dist(curve_ab_coords[0], curve_cd_coords[-1]) < MATH_EPS:
            curve_cd_coords = curve_cd_coords[:-1]

        merged_ring_coords = curve_ab_coords + curve_cd_coords
        if merged_ring_coords[0] != merged_ring_coords[-1]:
            merged_ring_coords.append(merged_ring_coords[0])

        if len(merged_ring_coords) < 3:
            return None

        merged_ring = LinearRing(merged_ring_coords)
        return cls(extended_curve_ab=extended_curve_ab,
                   extended_curve_cd=extended_curve_cd,
                   merged_line=merged_ring,
                   joint=cd_to_ab_extent.joint)

    @classmethod
    def _of_sequence_curves_helper(cls, curve_ab: LineString,
                                   curve_cd: LineString,
                                   extent_dist: float = LARGE_ENOUGH_DISTANCE,
                                   ignore_parallel: bool = False) -> Optional['LineExtent']:
        """
        将曲线ab和曲线cd 拉伸/裁剪 直到他们'联合'在一起, 相交于交点e. 曲线aed会是'联合'起来的新曲线
        若曲线ab和曲线cd拉伸后也不相交, 则会返回None

        Parameters
        ----------
        curve_ab: 曲线ab, 注意直线为曲线的特殊形式
        curve_cd: 曲线cd, 注意直线为曲线的特殊形式
        extent_dist: curve_ab和curve_cd的拉伸距离, 默认为LARGE_ENOUGH_DISTANCE
        ignore_parallel: 如果curve_ab和curve_cd拉伸后重合, 该参数为True是, 返回None, 若为False, 返回融合后的直线

        Returns
        -------
        LineExtend对象或者None
        """
        if not (curve_ab and curve_cd):
            return None

        if ignore_parallel:
            end_seg_of_ab = LineString(list(curve_ab.coords)[-2:])
            front_seg_of_cd = LineString(list(curve_cd.coords)[:2])
            if end_seg_of_ab.ext.is_parallel_to(front_seg_of_cd):
                return None

        coords_cd = list(curve_cd.coords)
        end_stretched_curve_ab = prolong(curve_ab, end_prolong_len=extent_dist)
        front_stretched_curve_cd = prolong(curve_cd, front_prolong_len=extent_dist)

        if not end_stretched_curve_ab.intersects(front_stretched_curve_cd):
            # try to extend point d along curve cd, and get the stretched cd, if these ab and cd intersect at point e,
            # then we get extent_ab == ae and extent_cd == empty
            end_stretched_curve_cd = prolong(curve_cd, end_prolong_len=extent_dist)
            if (joint := end_stretched_curve_ab.intersection(end_stretched_curve_cd)).type == 'Point':
                extent_coords_ab = cls._curve_coords_extending_in_curve_dir(curve=curve_ab,
                                                                            joint=joint,
                                                                            direction=cls.ExtendingDirection.TO_END)
                ab_extent = LineString(extent_coords_ab)
                if not ab_extent:
                    return None
                return cls(merged_line=ab_extent,
                           extended_curve_ab=ab_extent,
                           extended_curve_cd=LineString(),
                           joint=joint)

            front_stretched_curve_ab = prolong(curve_ab, front_prolong_len=extent_dist)
            if (joint := front_stretched_curve_ab.intersection(front_stretched_curve_cd)).type == 'Point':
                # try to extend point a along curve ab, and get the stretched ab, if these ab and cd intersect at point e,
                # then we get extent_ab == empty and extent_cd == ed
                extent_coords_cd = cls._curve_coords_extending_in_curve_dir(curve=curve_cd,
                                                                            joint=joint,
                                                                            direction=cls.ExtendingDirection.TO_FRONT)
                cd_extent = LineString(extent_coords_cd)
                if not cd_extent:
                    return None
                return cls(merged_line=cd_extent,
                           extended_curve_ab=LineString(),
                           extended_curve_cd=cd_extent,
                           joint=joint)

            # curve ab and curve cd are either parallel(but not collinear) to each other
            # or line "AB" and line "DC" not touched!
            return None

        intersection = end_stretched_curve_ab.intersection(front_stretched_curve_cd)

        if intersection.type == 'LineString':
            joint = LineString([curve_ab.coords[-1], curve_cd.coords[0]]).centroid
        elif intersection.type == 'Point':  # intersection is Point
            joint = intersection.centroid
        else:  # if intersection.type == 'MultiPoint':
            point_c = Point(coords_cd[0])
            joint = min(lmap(attrgetter("centroid"), intersection.geoms), key=lambda p: point_c.distance(p))

        ab_extent_coords = cls._curve_coords_extending_in_curve_dir(curve=curve_ab,
                                                                    joint=joint,
                                                                    direction=cls.ExtendingDirection.TO_END)
        cd_extent_coords = cls._curve_coords_extending_in_curve_dir(curve=curve_cd,
                                                                    joint=joint,
                                                                    direction=cls.ExtendingDirection.TO_FRONT)
        if ab_extent_coords and cd_extent_coords:  # ab_extent and cd_extent are both non-empty
            # don't count joint twice, thus take the cd_extent_coords[1:]
            merged_line_coords = ab_extent_coords + cd_extent_coords[1:]
        elif not ab_extent_coords:  # ab_extent is empty
            merged_line_coords = cd_extent_coords
        else:  # cd_extent is empty
            merged_line_coords = ab_extent_coords

        merged_line = LineString(merged_line_coords)

        return cls(merged_line=merged_line,
                   extended_curve_ab=LineString(ab_extent_coords),
                   extended_curve_cd=LineString(cd_extent_coords),
                   joint=joint)
