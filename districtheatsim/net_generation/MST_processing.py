import geopandas as gpd
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
import pandas as pd
import networkx as nx
from collections import defaultdict
import numpy as np

def add_intermediate_points(points_gdf, street_layer, max_distance=200, point_interval=10):
    new_points = []
    for point in points_gdf.geometry:
        # Sicherstellen, dass der Punkt eine valide Geometrie ist
        if point.is_empty:
            continue
        # Finde die nächstgelegene Straße
        distances = street_layer.distance(point)
        nearest_street_index = distances.idxmin()
        nearest_street = street_layer.iloc[nearest_street_index].geometry

        # Sicherstellen, dass nearest_street eine valide Geometrie ist
        if nearest_street.is_empty:
            continue

        # Berechne nächsten Punkt auf der Straße
        nearest_point_on_street = nearest_points(point, nearest_street)[1]

        print(nearest_point_on_street)

        # Füge Zwischenpunkte hinzu, wenn der Punkt in Reichweite ist
        if point.distance(nearest_point_on_street) <= max_distance:
            line = LineString([point, nearest_point_on_street])
            num_points = int(line.length / point_interval)
            for i in range(1, num_points):
                intermediate_point = line.interpolate(point_interval * i)
                print(intermediate_point)
                new_points.append(intermediate_point)
    
    # Erstelle ein GeoDataFrame mit allen neuen Punkten
    new_points_gdf = gpd.GeoDataFrame(geometry=new_points)
    return pd.concat([points_gdf, new_points_gdf], ignore_index=True)

def adjust_segments_to_roads(mst_gdf, street_layer, all_end_points_gdf, threshold=10):
    # Iterativer Anpassungsprozess
    iteration = 0
    changes_made = True

    while changes_made:
        print(f"Iteration {iteration}")

        adjusted_lines = []
        changes_made = False  # Flag, um zu verfolgen, ob Änderungen vorgenommen wurden

        for line in mst_gdf.geometry:
            midpoint = line.interpolate(0.5, normalized=True)  # Mittelpunkt des Segments
            nearest_line = street_layer.distance(midpoint).idxmin()  # Index des nächstgelegenen Straßensegments
            nearest_street = street_layer.iloc[nearest_line].geometry
            point_on_street = nearest_points(midpoint, nearest_street)[1]  # Nächster Punkt auf der Straße

            distance_to_street = midpoint.distance(point_on_street)

            if distance_to_street > threshold:
                # Segment aufteilen oder neu ausrichten
                new_line1 = LineString([line.coords[0], point_on_street.coords[0]])
                new_line2 = LineString([point_on_street.coords[0], line.coords[1]])
                adjusted_lines.extend([new_line1, new_line2])
                changes_made = True
            else:
                adjusted_lines.append(line)

        mst_gdf = gpd.GeoDataFrame(geometry=adjusted_lines)
    
        iteration += 1

    mst_gdf = simplify_network(mst_gdf)
    mst_gdf = extract_unique_points_and_create_mst(mst_gdf, all_end_points_gdf)

    return mst_gdf

def simplify_network(gdf, threshold=10):
    points = defaultdict(list)  # Dictionary zur Speicherung von Punkten und den zugehörigen Linienindices
    simplified_lines = []

    # Extrahieren der Endpunkte aller Linien und Indizieren
    for idx, line in enumerate(gdf.geometry):
        start, end = line.boundary.geoms
        points[start].append(idx)
        points[end].append(idx)

    # Suchen nach nahen Punkten und deren Vereinigung
    merged_points = {}
    for point in points:
        if point in merged_points:
            continue
        nearby_points = [p for p in points if p.distance(point) < threshold and p not in merged_points]
        if not nearby_points:
            merged_points[point] = point
        else:
            # Berechnen des geometrischen Mittels der nahen Punkte
            all_points = np.array([[p.x, p.y] for p in nearby_points])
            centroid = Point(np.mean(all_points, axis=0))
            for p in nearby_points:
                merged_points[p] = centroid

    # Erstellen neuer Linien mit angepassten Endpunkten
    for line in gdf.geometry:
        start, end = line.boundary.geoms
        new_start = merged_points.get(start, start)
        new_end = merged_points.get(end, end)
        simplified_lines.append(LineString([new_start, new_end]))

    return gpd.GeoDataFrame(geometry=simplified_lines)

def extract_unique_points_and_create_mst(gdf, all_end_points_gdf):
    # Extrahiere eindeutige Punkte aus den Liniengeometrien
    all_points = []
    for line in gdf.geometry:
        if isinstance(line, LineString):
            all_points.extend(line.coords)
    
    # Füge die Punkte aus all_end_points_gdf hinzu
    for point in all_end_points_gdf.geometry:
        if isinstance(point, Point):
            all_points.append((point.x, point.y))

    # Entferne doppelte Punkte
    unique_points = set(all_points)  # Entfernt Duplikate
    unique_points = [Point(pt) for pt in unique_points]  # Konvertiere wieder zu Point-Objekten
    
    # Erstelle ein GeoDataFrame aus den eindeutigen Punkten
    points_gdf = gpd.GeoDataFrame(geometry=unique_points)
    
    mst_gdf = generate_mst(points_gdf)
    
    return mst_gdf

# MST network generation
def generate_mst(points):
    g = nx.Graph()
    for i, point1 in points.iterrows():
        for j, point2 in points.iterrows():
            if i != j:
                distance = point1.geometry.distance(point2.geometry)
                g.add_edge(i, j, weight=distance)
    mst = nx.minimum_spanning_tree(g)
    lines = [LineString([points.geometry[edge[0]], points.geometry[edge[1]]]) for edge in mst.edges()]
    mst_gdf = gpd.GeoDataFrame(geometry=lines)
    return mst_gdf