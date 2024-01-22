import overpy
import json
from decimal import Decimal
import geojson

def build_query(city_name, tags, element_type="way"):
    query = f"""
    [out:json][timeout:25];
    area[name="{city_name}"]->.searchArea;
    (
    """

    if element_type == "way":
        for key, value in tags.items():
            query += f'way["{key}"="{value}"](area.searchArea);'
    
    elif element_type == "building":
        query += 'relation["building"](area.searchArea);'
        query += 'way["building"](area.searchArea);'
    
    query += """
    );
    (._;>;);
    out body;
    """
    return query

def download_data(query, element_type):
    api = overpy.Overpass()
    result = api.query(query)

    features = []

    if element_type == "way":  # Für Straßen
        for way in result.ways:
            coordinates = [(node.lon, node.lat) for node in way.nodes]
            linestring = geojson.LineString(coordinates)
            properties = way.tags
            feature = geojson.Feature(geometry=linestring, properties=properties)
            features.append(feature)
    
    elif element_type == "building":  # Für Gebäude
        for relation in result.relations:
            multipolygon = []
            for member in relation.members:
                if member.role == "outer" or member.role == "inner":
                    way = member.resolve()
                    coordinates = [(node.lon, node.lat) for node in way.nodes]
                    if coordinates[0] != coordinates[-1]:
                        coordinates.append(coordinates[0])
                    multipolygon.append(coordinates)

            properties = relation.tags
            feature = geojson.Feature(geometry=geojson.MultiPolygon([multipolygon]), properties=properties)
            features.append(feature)

        for way in result.ways:
            # Stellen Sie sicher, dass das Gebäude geschlossen ist (erster und letzter Punkt gleich)
            if way.nodes[0] != way.nodes[-1]:
                way.nodes.append(way.nodes[0])
            coordinates = [(node.lon, node.lat) for node in way.nodes]
            polygon = geojson.Polygon([coordinates])
            properties = way.tags
            feature = geojson.Feature(geometry=polygon, properties=properties)
            features.append(feature)

    return geojson.FeatureCollection(features)

def json_serial(obj):
    """JSON serializer für Objekte, die nicht serienmäßig serialisierbar sind."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Objekt vom Typ {type(obj).__name__} ist nicht JSON serialisierbar")

def save_to_file(geojson_data, filename):
    with open(filename, 'w') as outfile:
        json.dump(geojson_data, outfile, indent=2, default=json_serial)

def run_here():
    city_name = "Zittau"
    tags = {"highway": "primary"}
    query = build_query(city_name, tags)
    geojson_data = download_data(query)
    save_to_file(geojson_data, "osm_data/osm_data_script.geojson")

#run_here()