from typing import List, Optional

from shapely.extension.functional import seq
from shapely.extension.geometry.straight_segment import StraightSegment
from shapely.extension.model.envelope import Envelope
from shapely.extension.model.vector import Vector
from shapely.extension.strategy.simplify_strategy import BufferSimplifyStrategy
from shapely.extension.util.func_util import lmap, lconcat, sign
from shapely.extension.util.iter_util import win_slice
from shapely.geometry import Polygon, LineString
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union


class Insertion:
    # TODO WIP
    # TODO this is an inner module, should be merged with another convolution-based insertion algorithm, forming a larger module to be used
    """
    insert a rectangular polygon into a polygon space, avoiding obstacles
    find insertion space, which is a list of polygons, where we can put this rectangle's centroid without collision
    rectangle should be totally inside the polygon space given
    """

    def __init__(self, inserter: Envelope, eps: float = 1e-3):
        """

        Parameters
        ----------
        inserter: a rectangular polygon to insert into some space
        eps
        """
        self._eps = eps
        self._inserter: Envelope = inserter
        self._inserter_width: float = self._inserter.width
        self._inserter_height: float = self._inserter.depth
        self._inserter_angle: float = self._inserter.angle.degree

    def of(self, space: Polygon, obstacle: Optional[BaseGeometry] = None) -> List[Polygon]:
        """
        valid insertion point of a rectangle into a space.
        CAUTION: obstacle should be valid and have no splits in polygon

        Parameters
        ----------
        space
        obstacle


        Returns
        -------

        """
        if not self._inserter.shape.area > 0:
            return [space]
        rotated_space = space.ext.rotate_ccw(-1.0 * self._inserter_angle, origin=(0, 0))
        rotated_obstacle = obstacle.ext.rotate_ccw(-1.0 * self._inserter_angle,
                                                   origin=(0, 0)) if obstacle else None

        rotated_insertion_space = self._orthogonal_insertion(space=rotated_space, obstacle=rotated_obstacle)
        insertion_spaces: List[Polygon] = lmap(
            lambda rotated_poly: rotated_poly.ext.rotate_ccw(self._inserter_angle, origin=(0, 0)),
            rotated_insertion_space)
        return insertion_spaces

    def _orthogonal_insertion(self, space: Polygon, obstacle: Optional[BaseGeometry] = None) -> List[Polygon]:
        """
        transform inserter to orthogonal plane, then find insertion spaces more easily

        Parameters
        ----------
        space
        obstacle

        Returns
        -------

        """

        genuine_obstacles: List[Polygon] = obstacle.ext.flatten(target_class_or_callable=Polygon) if obstacle else []
        hole_as_obstacles: List[Polygon] = lmap(Polygon, space.interiors)
        space_boundary_as_obstacles: List[Polygon] = (
            seq(space.exterior.ext.ccw().ext.segments())
            .map(lambda ccw_segment: ccw_segment.ext.buffer().single_sided().rect(-1e0))
            .map(lambda occupation: occupation.difference(space))
            .flat_map(lambda occupation: occupation.ext.flatten(Polygon))
            .to_list())

        all_obstacles: List[Polygon] = genuine_obstacles + hole_as_obstacles + space_boundary_as_obstacles
        convex_obstacles: List[Polygon] = (
            seq(all_obstacles)
            # simplify some splits in obstacle
            .flat_map(lambda poly: poly.ext.simplify(BufferSimplifyStrategy().mitre(self._eps)))
            .flat_map(lambda poly: poly.ext.flatten(Polygon))
            .flat_map(lambda poly: poly.ext.partitions())
            .to_list())

        invalid_space: BaseGeometry = unary_union(lmap(
            lambda convex_obs: self._invalid_insertion(convex_obstacle=convex_obs), convex_obstacles))
        valid_spaces: List[Polygon] = space.difference(invalid_space).ext.flatten(target_class_or_callable=Polygon)
        return valid_spaces

    def _invalid_insertion(self, convex_obstacle: Polygon) -> Polygon:
        """
        find invalid insertion space caused by a convex polygon obstacle

        Parameters
        ----------
        convex_obstacle


        Returns
        -------

        """

        bounce_segments = lmap(self._bounce_segment, convex_obstacle.exterior.ext.ccw().ext.segments())
        connected_bounce_segments: List[LineString] = self._connect_bounce_segments(bounce_segments, convex_obstacle)
        invalid_insertion = Polygon(lconcat(map(lambda seg: seg.coords, connected_bounce_segments))).simplify(0)
        return invalid_insertion

    def _bounce_segment(self, convex_ccw_segment: StraightSegment) -> LineString:
        """
        inserter is "bounced" by edges of a convex obstacle
        use these edges to construct an invalid insertion space

        Parameters
        ----------
        convex_ccw_segment

        Returns
        -------

        """
        segment_vec: Vector = Vector.from_endpoints_of(convex_ccw_segment)
        if segment_vec.x == 0:
            return (convex_ccw_segment
                    .ext.offset(dist=0.5 * self._inserter_width, towards='right')
                    .ext.prolong().from_ends(0.5 * self._inserter_height))
        if segment_vec.y == 0:
            return (convex_ccw_segment
                    .ext.offset(dist=0.5 * self._inserter_height, towards='right')
                    .ext.prolong().from_ends(0.5 * self._inserter_width))

        bounce_vec: Vector = (Vector(sign(segment_vec.y > 0) * 0.5 * self._inserter_width, 0) +
                              Vector(0, sign(segment_vec.x < 0) * 0.5 * self._inserter_height))
        bounce_seg = bounce_vec.apply(convex_ccw_segment)
        return bounce_seg

    def _connect_bounce_segments(self, bounce_segments: List[StraightSegment],
                                 convex_obstacle: Polygon) -> List[LineString]:
        """
        add connection lines between each two bounce segments
        these connection segments should be vertical or horizontal to inserter envelope's angle,
        and not colliding with obstacle

        Parameters
        ----------
        bounce_segments
        convex_obstacle

        Returns
        -------

        """
        connected_segments: List[LineString] = []
        for prev_seg, cur_seg in win_slice(bounce_segments, win_size=2, tail_cycling=True):
            connection_vec = Vector.from_origin_to_target(prev_seg.ext.end(), cur_seg.ext.start())
            if connection_vec.length < self._eps:
                connected_segments.append(cur_seg)
                continue

            horizontal_sub_vec = connection_vec.sub_vector(Vector(1, 0))
            vertical_sub_vec = connection_vec.sub_vector((Vector(0, 1)))
            horizontal_occupation = LineString([prev_seg.ext.end(), horizontal_sub_vec.apply(prev_seg.ext.end())]
                                               ).ext.rbuf(0.5 * self._inserter_height)
            vertical_occupation = LineString([horizontal_sub_vec.apply(prev_seg.ext.end()), cur_seg.ext.start()]
                                             ).ext.rbuf((0.5 * self._inserter_width))
            if horizontal_occupation.union(vertical_occupation).intersects(convex_obstacle.ext.rbuf(-self._eps)):
                first_vec = vertical_sub_vec
            else:
                first_vec = horizontal_sub_vec

            connection = [LineString([prev_seg.ext.end(), first_vec.apply(prev_seg.ext.end())]),
                          LineString([first_vec.apply(prev_seg.ext.end()), cur_seg.ext.start()])]
            connected_segments.extend(connection)
            connected_segments.append(cur_seg)

        return connected_segments
