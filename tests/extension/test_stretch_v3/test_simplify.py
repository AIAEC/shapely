import pytest

from shapely.extension.model.stretch.stretch_v3 import Edge, Stretch
from shapely.extension.util.func_util import lfilter
from shapely.geometry import LinearRing, Point, LineString


class TestSimplify:
    def test_simplify_closure(self, stretch_exterior_offset_hit_hit_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_hit_with_reverse_closure
        closure = stretch.closures[0]
        another_closure = stretch.closures[1]

        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 12
        assert len(closure.exterior) == 6
        assert len(another_closure.exterior) == 6

        closure.simplify()

        assert len(stretch.pivots) == 6
        assert len(stretch.edges) == 8
        assert len(closure.exterior) == 4
        assert closure.exterior.shape.equals(LinearRing([(0, 0), (30, 0), (30, 20), (0, 20)]))

        assert len(another_closure.exterior) == 4
        assert another_closure.exterior.shape.equals(LinearRing([(0, 0), (0, -10), (30, -10), (30, 0)]))

    def test_simplify_closure_interior(self, stretch_interior_offset_hit_hit):
        stretch = stretch_interior_offset_hit_hit

        assert len(stretch.pivots) == 10
        assert len(stretch.edges) == 10
        assert len(stretch.closures) == 1

        closure = stretch.closures[0]
        assert len(closure.interiors) == 1
        interior = closure.interiors[0]
        assert len(interior) == 6

        closure.simplify()

        assert len(stretch.pivots) == 8
        assert len(stretch.edges) == 8
        assert len(stretch.closures) == 1

        assert len(closure.interiors) == 1
        interior = closure.interiors[0]
        assert len(interior) == 4
        assert interior.shape.equals(LinearRing([(5, 25), (25, 25), (25, 20), (5, 20)]))

    def test_simplify_stretch(self, stretch_exterior_offset_hit_out_with_reverse_closure):
        stretch = stretch_exterior_offset_hit_out_with_reverse_closure
        shapes = [c.shape for c in stretch.closures]

        stretch.simplify()
        assert len(stretch.closures) == 2
        assert stretch.closures[0].shape.equals(shapes[0])
        assert not stretch.closures[0].shape.almost_equals(shapes[0])
        assert stretch.closures[1].shape.equals(shapes[1])
        assert not stretch.closures[1].shape.almost_equals(shapes[1])

    def test_cargo_after_simplify_using_default_strategy(self, stretch_box_duplicate_pivots):
        stretch = stretch_box_duplicate_pivots

        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5
        assert len(stretch.closures) == 1

        stretch.edge('(0,4)').cargo['test'] = 0
        stretch.edge('(4,1)').cargo['test'] = 1

        stretch.simplify(consider_cargo_equality=False)

        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1

        edges = stretch.edges_by_query(Point(0.3, 0))
        assert len(edges) == 1
        assert edges[0].cargo['test'] == 0
        assert edges[0].shape.equals(LineString([(0, 0), (1, 0)]))

    def test_cargo_after_simplify_using_long_edge_inherit(self, stretch_box_duplicate_pivots):
        stretch = stretch_box_duplicate_pivots

        assert len(stretch.pivots) == 5
        assert len(stretch.edges) == 5
        assert len(stretch.closures) == 1

        stretch.edge('(0,4)').cargo['test'] = 0
        stretch.edge('(4,1)').cargo['test'] = 1

        def long_edge_inherit(edge0: Edge, edge1: Edge):
            if edge0.shape.length > edge1.shape.length:
                return edge0
            return edge1

        stretch.simplify(consider_cargo_equality=False, cargo_target=long_edge_inherit)

        assert len(stretch.pivots) == 4
        assert len(stretch.edges) == 4
        assert len(stretch.closures) == 1

        edges = stretch.edges_by_query(Point(0.3, 0))
        assert len(edges) == 1
        assert edges[0].cargo['test'] == 1
        assert edges[0].shape.equals(LineString([(0, 0), (1, 0)]))

    def test_simplify_stretch_with_cut(self, stretch_2_boxes):
        """
        ┌─────────────────────┬─────────────────────┐
        │                     │                     │
        │                     │                     │
        │                     │                     │
        │           ──────────┤                     │
        │                     │                     │
        │                     │                     │
        │                     │                     │
        └─────────────────────┴─────────────────────┘
        Parameters
        ----------
        stretch_2_boxes

        Returns
        -------

        """
        stretch = stretch_2_boxes
        stretch.add_pivot(Point(1, 0.5))
        assert len(stretch.edges) == 10
        stretch.simplify()
        assert len(stretch.edges) == 8

        stretch.closures[0].cut(LineString([(0.5, 0.5), (1.5, 0.5)]))
        assert len(stretch.edges) == 12
        assert sum(map(lambda closure: closure.shape.area, stretch.closures)) == pytest.approx(2.0)
        stretch.simplify()

        assert sum(map(lambda closure: closure.shape.area, stretch.closures)) == pytest.approx(2.0)
        assert len(stretch.edges) == 12

    def test_simplify_stretch_with_inner_continue_edges(self, stretch_with_inner_continue_edges):
        """
        input:
        6                   5
        o◄──────────────────o
        │                   ▲
        │         o 3       │
        │         ▲         │
        │         │         │
        │         ▼         │
        │         o 2       │
        │         ▲         │
        │         │         │
        │         │         │
        ▼         ▼         │
        o────────►o────────►o
        0         1         4
        Parameters
        ----------
        stretch_with_inner_continue_edges

        Returns
        -------
        expect result:
        6                   5
        o◄──────────────────o
        │                   ▲
        │         o 3       │
        │         ▲         │
        │         │         │
        │         │         │
        │         │         │
        │         │         │
        │         │         │
        │         │         │
        ▼         ▼         │
        o────────►o────────►o
        0         1         4

        """
        stretch = stretch_with_inner_continue_edges
        assert len(lfilter(lambda e: e.id == "(1,2)", stretch.edges)) == 1

        stretch.simplify(angle_tol=1e-4, consider_cargo_equality=True)

        assert len(lfilter(lambda e: e.id == "(1,2)", stretch.edges)) == 0
        assert len(lfilter(lambda e: e.id == "(2,1)", stretch.edges)) == 0
        assert len(lfilter(lambda e: e.id == "(2,3)", stretch.edges)) == 0
        assert len(lfilter(lambda e: e.id == "(3,2)", stretch.edges)) == 0
        assert len(lfilter(lambda e: e.id == "(1,3)", stretch.edges)) == 1
        assert len(lfilter(lambda e: e.id == "(3,1)", stretch.edges)) == 1

    def test_simplify_no_raise(self):
        stretch = Stretch.loads(
            """{"pivot": {"0": [36.09122283822344, -57.11936088796535], "1": [35.334287304749814, -49.10502694195556], "6": [-47.030736020824584, -46.1351445116751], "7": [-38.98073602082459, -46.135144511269736], "8": [-38.98073602320155, 1.0673409778466896], "9": [-33.855001298436186, 29.90037553693713], "10": [-41.7807360272973, 31.309357086754403], "12": [67.71936404730731, 17.599470702486702], "13": [67.71941381608077, -3.0787228695904574], "14": [64.2694138160908, -3.078731173133406], "15": [64.26949924384716, -38.57270782757577], "16": [72.31949924382387, -38.572688452642225], "17": [72.31926470108056, 58.876372708281124], "18": [64.26926470110384, 58.87635333334758], "19": [64.26936404731731, 17.599462398943757], "20": [19.581030657156504, 65.80714226040325], "21": [-4.7933405016035415, 63.48598869390341], "22": [-4.030197395316271, 55.47224346465344], "23": [20.344173763443774, 57.793397031153326], "27": [-46.25379851199796, -54.66000358393569], "28": [-47.14873516542821, -54.74460067311736], "29": [-46.11406110338521, -65.69583234048605], "76": [-34.3285752819652, 27.236450116176457], "83": [-45.219340537891775, -65.61025466244014], "95": [9.619263979169807, 27.236450116176457], "96": [9.619263979169805, 56.77207170407057], "105": [-38.98073602096822, -43.282754818242736], "109": [42.01926397916975, -33.83803261391415], "111": [64.26947615822843, -28.9809726907373], "112": [64.26929615997427, 45.80565522943545], "114": [42.01926397916976, -23.038031613913617], "115": [64.26946185461495, -23.038031613913617], "116": [29.51456097922259, -49.6546867989767], "117": [30.271040091862368, -57.669063852891604], "118": [-47.030736023237296, 1.7773115466699396], "119": [-47.03073602310249, -0.899657156917557], "120": [-38.9807360231025, -0.8996571565121716], "121": [-47.03073602096817, -43.283725549799385], "122": [-36.14443919863015, 64.29237865479212], "123": [-15.443867136254994, 62.471746819842224], "128": [15.206928232515011, -58.66460640787638], "129": [15.197468980922872, -58.4950908782003], "130": [15.180006126233964, -58.496401782927634], "131": [13.744004168414843, -43.28294651651292], "132": [-47.0307360208094, -46.43573444323522], "133": [-27.64639449017022, -63.9501811269397], "134": [-27.853426081983343, -61.75994379036774], "135": [-23.224060533059856, -61.32235426493469], "136": [-23.158192388049883, -62.019189319691804], "137": [8.822720956341097, -58.996214761970364], "138": [-22.77973602083027, -0.8996571556963145], "139": [-22.779736020830242, -43.28281372234856], "140": [12.852401924218071, -33.83703261391416], "141": [42.01926397916978, 37.36556055478136], "142": [9.619263979169817, 37.36556055478136], "143": [9.619263979169821, 52.46756055478143], "146": [59.85548527455603, 58.87714109854903], "147": [58.66848676874906, 69.98408789289203], "148": [55.28786703597416, 69.6215803810212], "149": [55.45775033267455, 68.03195349747949], "150": [50.18775964545648, 67.46875001870393], "151": [50.15490783718089, 67.76673952000095], "152": [50.124008368220984, 68.06528155692723], "153": [47.04131494056583, 67.73509043254984], "154": [47.072923048728626, 67.43624786044273], "155": [38.02521135287361, 66.46603111415266], "156": [37.854371430964875, 68.06006471570794], "157": [33.479194977483075, 67.5924899621387], "158": [33.617339226889726, 66.29985073643621], "159": [28.54621611300172, 65.75790021925684], "160": [28.579788678092445, 65.4531664735763], "161": [28.609813104011664, 65.16281236280514], "162": [23.53886200325769, 64.61925228794234], "163": [23.368816211557714, 66.2103996673178], "164": [64.26931647379705, 37.36556055478136], "165": [28.021622920237522, -33.83803261391416], "166": [53.46709952883566, -55.478249027518245], "167": [53.54226350323188, -56.27546163730449], "168": [56.030549597929166, -56.040261254563234], "169": [55.59767141687871, -51.46065663894149], "170": [61.67058497787184, -50.886592752936735], "171": [61.75528332058593, -51.78260053731799], "172": [65.14205355723789, -51.46245203568856], "173": [63.921761388302, -38.57268845264218], "174": [15.196936584099562, -58.66512696103847], "175": [25.29523070706591, -58.1390176826817], "176": [25.81926397916975, -33.83788742788636], "177": [25.819263979169705, 37.36556055478136], "178": [9.619263979169759, -43.28293151965269], "179": [-6.580736020830238, -43.28287261918271], "180": [-6.580736020830284, 27.236450116176457], "181": [-22.780736020830286, 27.236450116176457], "182": [49.58594679514563, 37.36556055478136], "183": [49.58594679514563, 53.61108319075812], "184": [-22.77973602083026, -17.09965715610421], "185": [-46.92073602228672, -17.09965715610422], "186": [16.369026042449022, -33.837264440197075], "187": [17.582240154954857, -46.690866615372805], "188": [-11.379503859408118, 27.236450116176457], "189": [-11.379503859408118, 40.482432292658444], "190": [-11.181564491881536, 43.225299406984696], "191": [9.619263979169821, 48.966560554781395], "192": [25.02028012847896, 48.966560554781395], "193": [-43.5307360213047, -39.350657156741306], "194": [-43.5307360213047, -36.600657156741306]}, "pivot_cargo": {"0": {}, "1": {}, "6": {}, "7": {}, "8": {}, "9": {}, "10": {}, "12": {}, "13": {}, "14": {}, "15": {}, "16": {}, "17": {}, "18": {}, "19": {}, "20": {}, "21": {}, "22": {}, "23": {}, "27": {}, "28": {}, "29": {}, "76": {}, "83": {}, "95": {}, "96": {}, "105": {}, "109": {}, "111": {}, "112": {}, "114": {}, "115": {}, "116": {}, "117": {}, "118": {}, "119": {}, "120": {}, "121": {}, "122": {}, "123": {}, "128": {}, "129": {}, "130": {}, "131": {}, "132": {}, "133": {}, "134": {}, "135": {}, "136": {}, "137": {}, "138": {}, "139": {}, "140": {}, "141": {}, "142": {}, "143": {}, "146": {}, "147": {}, "148": {}, "149": {}, "150": {}, "151": {}, "152": {}, "153": {}, "154": {}, "155": {}, "156": {}, "157": {}, "158": {}, "159": {}, "160": {}, "161": {}, "162": {}, "163": {}, "164": {}, "165": {}, "166": {}, "167": {}, "168": {}, "169": {}, "170": {}, "171": {}, "172": {}, "173": {}, "174": {}, "175": {}, "176": {}, "177": {}, "178": {}, "179": {}, "180": {}, "181": {}, "182": {}, "183": {}, "184": {}, "185": {}, "186": {}, "187": {}, "188": {}, "189": {}, "190": {}, "191": {}, "192": {}, "193": {}, "194": {}}, "edge_cargo": {"(12,13)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(13,14)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(15,16)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(16,17)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(17,18)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(19,12)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(20,21)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(27,28)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(28,29)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(29,83)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(83,27)": {"width": 0, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(22,96)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(96,23)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(21,22)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(23,20)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(14,115)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(115,111)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(111,15)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(18,112)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(1,116)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(116,117)": {"width": 0.0, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(117,0)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(0,1)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(118,119)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(119,120)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(120,8)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(8,76)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(76,9)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(9,10)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(10,118)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(7,105)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(121,6)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(6,7)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(122,10)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(10,9)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(9,76)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(96,22)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(22,21)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(21,123)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(123,122)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(128,129)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(129,130)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(105,7)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(7,6)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(6,132)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(132,27)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(27,83)": {"width": 0, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(83,133)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(133,134)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(134,135)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(135,136)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(136,137)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(139,105)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(95,142)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(8,120)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(120,138)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(131,140)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(109,114)": {"width": 2.4, "is_fixed": true, "is_starting": true, "moving_times": 0}, "(114,141)": {"width": 2.4, "is_fixed": true, "is_starting": true, "moving_times": 0}, "(142,95)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(76,8)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(143,96)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(96,143)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(112,18)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(18,146)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(146,147)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(147,148)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(148,149)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(149,150)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(150,151)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(151,152)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(152,153)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(153,154)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(154,155)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(155,156)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(156,157)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(157,158)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(158,159)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(159,160)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(160,161)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(161,162)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(162,163)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(163,20)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(20,23)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(23,96)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(112,164)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(164,19)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(19,164)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(141,114)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(114,115)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(115,14)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(14,13)": {"width": -0.04666040099349544, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(13,12)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(12,19)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(165,109)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(109,165)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(165,116)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(116,1)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(1,0)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(0,166)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(166,167)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(167,168)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(168,169)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(169,170)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(170,171)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(171,172)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(172,173)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(173,15)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(15,111)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(111,115)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(115,114)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(114,109)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(137,174)": {"width": 0, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(175,117)": {"width": 0.0, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(140,131)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(130,174)": {"width": 0.0, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(117,116)": {"width": 0.0, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(116,165)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(164,112)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(119,121)": {"width": 0.0, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(138,120)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(120,119)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(105,139)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(174,128)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(128,175)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(165,176)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(176,165)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(141,177)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(177,142)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(142,177)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(177,141)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(176,177)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(177,176)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(131,178)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(178,131)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(178,95)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(95,178)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(178,179)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(179,139)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(139,179)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(179,178)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(180,95)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(95,180)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(179,180)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(180,179)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(76,181)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(181,76)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(138,181)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(181,138)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(164,182)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(182,141)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(141,182)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(182,164)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(182,183)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(183,182)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(138,184)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(184,139)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(139,184)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(184,138)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(184,185)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(185,184)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(176,186)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(186,140)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(140,186)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(186,176)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(186,187)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(187,186)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(181,188)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(188,180)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(180,188)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(188,181)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(188,189)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(189,190)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(190,189)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(189,188)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(142,191)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(191,143)": {"width": 2.4, "is_fixed": true, "is_starting": false, "moving_times": 0}, "(143,191)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(191,142)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(191,192)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(192,191)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(105,193)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(193,194)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(194,193)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}, "(193,105)": {"width": 2.4, "is_fixed": false, "is_starting": false, "moving_times": 0}}, "closure": {"2": {"exterior": ["112", "164", "19", "12", "13", "14", "115", "111", "15", "16", "17", "18", "112"], "interiors": []}, "3": {"exterior": ["20", "21", "22", "96", "23", "20"], "interiors": []}, "76": {"exterior": ["27", "28", "29", "83", "27"], "interiors": []}, "155": {"exterior": ["0", "1", "116", "117", "0"], "interiors": []}, "156": {"exterior": ["10", "118", "119", "120", "8", "76", "9", "10"], "interiors": []}, "162": {"exterior": ["114", "115", "14", "13", "12", "19", "164", "182", "141", "114"], "interiors": []}, "163": {"exterior": ["0", "166", "167", "168", "169", "170", "171", "172", "173", "15", "111", "115", "114", "109", "165", "116", "1", "0"], "interiors": []}, "169": {"exterior": ["105", "7", "6", "132", "27", "83", "133", "134", "135", "136", "137", "174", "128", "129", "130", "174", "128", "175", "117", "116", "165", "176", "186", "140", "131", "178", "179", "139", "105"], "interiors": []}, "173": {"exterior": ["109", "114", "141", "177", "176", "165", "109"], "interiors": []}, "175": {"exterior": ["131", "140", "186", "176", "177", "142", "95", "178", "131"], "interiors": []}, "177": {"exterior": ["178", "95", "180", "179", "178"], "interiors": []}, "179": {"exterior": ["120", "138", "181", "76", "8", "120"], "interiors": []}, "180": {"exterior": ["138", "184", "139", "179", "180", "188", "181", "138"], "interiors": []}, "183": {"exterior": ["10", "9", "76", "181", "188", "189", "190", "189", "188", "180", "95", "142", "191", "143", "96", "22", "21", "123", "122", "10"], "interiors": []}, "184": {"exterior": ["112", "18", "146", "147", "148", "149", "150", "151", "152", "153", "154", "155", "156", "157", "158", "159", "160", "161", "162", "163", "20", "23", "96", "143", "191", "192", "191", "142", "177", "141", "182", "183", "182", "164", "112"], "interiors": []}, "185": {"exterior": ["105", "139", "184", "185", "184", "138", "120", "119", "121", "6", "7", "105", "193", "194", "193", "105"], "interiors": []}}, "closure_cargo": {"2": {"angle": 0, "region_type": "surrounding", "clamp": false}, "3": {"angle": 0, "region_type": "surrounding", "clamp": false}, "76": {"angle": 90, "region_type": "building", "clamp": false}, "155": {"angle": 0, "region_type": "surrounding", "clamp": false}, "156": {"angle": 0, "region_type": "surrounding", "clamp": false}, "162": {"angle": 90, "region_type": "building", "clamp": false}, "163": {"angle": 90, "region_type": "building", "clamp": false}, "169": {"angle": 90, "region_type": "building", "clamp": false}, "173": {"angle": 90, "region_type": "core", "clamp": false}, "175": {"angle": 90, "region_type": "core", "clamp": false}, "177": {"angle": 90, "region_type": "core", "clamp": false}, "179": {"angle": 90, "region_type": "core", "clamp": false}, "180": {"angle": 90, "region_type": "core", "clamp": false}, "183": {"angle": 90, "region_type": "building", "clamp": false}, "184": {"angle": 90, "region_type": "building", "clamp": false}, "185": {"angle": 0, "region_type": "surrounding", "clamp": false}}}""")
        stretch.simplify(consider_cargo_equality=True, angle_tol=2)
