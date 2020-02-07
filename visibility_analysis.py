from shapely.geometry import Point,Polygon,LineString,MultiPoint,MultiPolygon
from pyproj import Proj, transform
from math import sqrt
from scipy import spatial

def distance(p1, p2):
    dx = p1[0]-p2[0]
    dy = p1[1]-p2[1]
    return sqrt(dx*dx+dy*dy)

def find_point_on_bound(ob_p, point, dx, dy):
    intersect_point = None

    if ob_p[0] != point[0]:
        alpha = (ob_p[1] - point[1]) / (ob_p[0] - point[0])
    else:
        alpha = 0
    beta = ob_p[1] - ob_p[0]*alpha

    if ob_p[0] != point[0]:
        if ob_p[0] > point[0]: kx = dx[0]
        elif ob_p[0] < point[0]: kx = dx[1]
        intersect_point = (kx, kx*alpha+beta)

    if ob_p[1] != point[1]:
        if ob_p[1] > point[1]: ky = dy[0]
        elif ob_p[1] < point[1]: ky = dy[1]
        if alpha:
            intersect_point_2 = ((ky-beta)/alpha, ky)
        else:
            intersect_point_2 = (ob_p[0], ky)

        if intersect_point:
            dist1 = distance(ob_p, intersect_point)
            dist2 = distance(ob_p, intersect_point_2)
            if dist2 < dist1:
                intersect_point = intersect_point_2
        else:
            intersect_point = intersect_point_2

    return intersect_point

def cut_build(ob_p, build, Area, dx, dy):
    Points_conv = []
    for p in build.exterior.coords:
        if not Points_conv or Points_conv[-1] != p:
            Points_conv.append(p)
    Building_conv_hull = MultiPoint(Points_conv).convex_hull # convex hull of buildings

    if Area.intersection(Building_conv_hull):
        Conv_hull = list(MultiPoint(list(Building_conv_hull.exterior.coords) + [ob_p]).convex_hull.boundary.coords)  # convex hull of buildings + points ob_p

        if Conv_hull[-1] == ob_p:
            p1 = Conv_hull[1]
            p2 = Conv_hull[-2]
            if len(Conv_hull) == 4:
                check_point = Conv_hull[0]
            else:
                check_point = Conv_hull[-3]
        else:
            ob_p_index = Conv_hull.index(ob_p)
            p1 = Conv_hull[ob_p_index+1]
            p2 = Conv_hull[ob_p_index-1]
            if len(Conv_hull) == 4:
                check_point = Conv_hull[0]
            elif ob_p_index == 1:
                check_point = Conv_hull[ob_p_index-3]
            else:
                check_point = Conv_hull[ob_p_index-2]

        line1 = [] # from start to first of p1, p2
        line2 = [] # from first of p1, p2 to second of p1, p2
        line3 = [] # from second of p1, p2 to finish
        line = line1
        prev_point = None
        for point in Points_conv:
            if point == prev_point and point != Points_conv[0]: continue
            if point in [p1, p2]:
                line.append(point)
                if line == line1:
                    line = line2
                else:
                    line = line3
            line.append(point)

        if check_point == ob_p:
            if len(line2) == 2:
                used_line = line2
            else:
                used_line = line3[:-1]+line1
        else:
            if check_point in line2:
                used_line = line3[:-1]+line1
            else:
                used_line = line2

        start_point = used_line.pop(0)
        intersect_point_2 = find_point_on_bound(ob_p, start_point, dx, dy)
        dist_to_point = distance(ob_p, start_point)
        dist_to_bound = distance(ob_p, intersect_point_2)
        new_line = [intersect_point_2]
        if dist_to_point < dist_to_bound:
            new_line.append(start_point)

        for point in used_line:
            intersect_point_1 = find_point_on_bound(ob_p, point, dx, dy)
            dist_to_point = distance(ob_p, point)
            dist_to_bound = distance(ob_p, intersect_point_1)

            if dist_to_point < dist_to_bound:
                new_line.append(point)
            new_line.append(intersect_point_1)

            if Area.intersection(LineString(new_line)):
                if intersect_point_1[0] != intersect_point_2[0] and intersect_point_1[1] != intersect_point_2[1]:
                    dx_1 = abs(intersect_point_1[0] - ob_p[0])
                    dx_2 = abs(intersect_point_2[0] - ob_p[0])
                    dy_1 = abs(intersect_point_1[1] - ob_p[1])
                    dy_2 = abs(intersect_point_2[1] - ob_p[1])
                    if dx_1 == dx_2 or dy_1 == dy_2:
                        if intersect_point_1[0] in dx:
                            if (intersect_point_1[1] + intersect_point_2[1]) / 2 > ob_p[1]:
                                additional_point_2 = (intersect_point_1[0], dy[1])
                                additional_point_1 = (intersect_point_2[0], dy[1])
                            else:
                                additional_point_2 = (intersect_point_1[0], dy[0])
                                additional_point_1 = (intersect_point_2[0], dy[0])
                        else:
                            if (intersect_point_1[0] + intersect_point_2[0]) / 2 > ob_p[0]:
                                additional_point_2 = (dx[1], intersect_point_1[1])
                                additional_point_1 = (dx[1], intersect_point_2[1])
                            else:
                                additional_point_2 = (dx[0], intersect_point_1[1])
                                additional_point_1 = (dx[0], intersect_point_2[1])
                        new_line.append(additional_point_2)
                        new_line.append(additional_point_1)
                    else:
                        if intersect_point_1[0] in dx:
                            additional_point = (intersect_point_1[0], intersect_point_2[1])
                        else:
                            additional_point = (intersect_point_2[0], intersect_point_1[1])
                        new_line.append(additional_point)

                if len(new_line)>2:
                    dark_block = Polygon(new_line)
                    Area = Area.difference(dark_block)
                    prev_dark_block = dark_block
                    if prev_dark_block.intersection(dark_block):
                        Area = Area.difference(prev_dark_block.intersection(dark_block))

            new_line = [intersect_point_1]
            if dist_to_point < dist_to_bound:
                new_line.append(point)
            intersect_point_2 = intersect_point_1
    return Area

def VA (ob_p ,Buildings,R,R_observation):
    Tree_Building = spatial.KDTree(list(Buildings.keys())) #  tree of centroids
    
    sub_tree = Tree_Building.query_ball_point(ob_p,R_observation*1.2)
    another_one_array = []
    for b in sub_tree:
        p = (Tree_Building.data[b][0],Tree_Building.data[b][1])
        dist = Point(ob_p).distance(Buildings[p])
        if dist < R_observation:
            another_one_array.append((Buildings[p], dist))

    another_one_array.sort(key=lambda x: x[1])

    dx = (ob_p[0] - R_observation, ob_p[0] + R_observation)
    dy = (ob_p[1] - R_observation, ob_p[1] + R_observation)

    for build in another_one_array:
        R = cut_build(ob_p, build[0], R, dx, dy)
    if R.geom_type == 'GeometryCollection':
        A=[]
        for r in R:
            if r.geom_type == 'Polygon':
                A.append(r)
        R=MultiPolygon(A)        
    return another_one_array, R

