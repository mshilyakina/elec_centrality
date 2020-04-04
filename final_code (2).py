# -*- coding: utf-8 -*-
import networkx as nx
import nx_multi_shp
import os
from osgeo import ogr


def convert_shp_to_graph(input_shp, directed, multigraph, parallel_edges_attribute):
    """Converts a shapefile to networkx graph object in accordance to the given parameters.
        It can directed or undirected, simple graph or multigraph

        Parameters
        ----------
        input_shp: shapefile path

        directed: 'true' or 'false'
            If value is true – directed graph will be created.
            If value is false - undirected graph will be created

        multigraph: 'true' or 'false'
            If value is true – multigraph will be created
            If value is false – simple graph will be created

        parallel_edges_attribute: string
            Field of the shapefile which allows to distinguish parallel edges.
            Note that it could be a field of different types, but all values of this attribute should be filled
        Returns
        -------
        Graph
        """
    if multigraph == 'true':
        G = nx_multi_shp.read_shp(r'{0}'.format(input_shp), parallel_edges_attribute, simplify=True,
                                  geom_attrs=True, strict=True)
    else:
        G = nx.read_shp(r'{0}'.format(input_shp))
    if directed == 'true':
        graph = G
    else:
        graph = G.to_undirected()
    return graph


def export_path_to_shp(path_dict, multy, multy_attribute, output_workspace, G):
    new_graph = nx.MultiGraph()
    a = 0
    for node in path_dict:
        path_list = path_dict[node]
        path_list.insert(0, node)
        b = 0
        for edge in G.edges(keys=True, data=True):
            data = new_graph.get_edge_data(*edge)
            Wkt = data['Wkt']
            c = 0
            for i in range(len(path_list) - 1):
                identifier = str(a) + str(b) + str(c)
                if tuple([tuple(path_list[i]), tuple(path_list[i + 1])]) == tuple([edge[0], edge[1]]):
                    new_graph.add_edge(edge[0], edge[1], identifier, Name=edge[2], ident=identifier, Wkt=Wkt)
                elif tuple([tuple(path_list[i + 1]), tuple(path_list[i])]) == tuple([edge[0], edge[1]]):
                    new_graph.add_edge(edge[0], edge[1], identifier, Name=edge[2], ident=identifier, Wkt=Wkt)
                c += 1
            b += 1
        a += 1
    if multy == 'true':
        nx_multi_shp.write_shp(new_graph, 'ident', output_workspace)
    else:
        nx.write_shp(new_graph, output_workspace)


def create_cpg(shapefile):
    with open('{}.cpg'.format(shapefile), 'w') as cpg:
        cpg.write('cp1251')


def process_layer(layer):
    grouped_features = {}
    for feature in layer:
        feature_name = feature.GetField('NAME')
        if feature_name in grouped_features:
            grouped_features[feature_name] += [feature]
        else:
            grouped_features[feature_name] = [feature]
    records = []
    for feature_name in grouped_features:
        record = {}
        record['name'] = feature_name
        record['geometry'] = merge_features_geometry(grouped_features[feature_name])
        record['count'] = len(grouped_features[feature_name])
        records.append(record)
    return records


def simplify(features):
    threshold = 10
    for x in range(len(features) - 1):
        if not features[x]:
            continue
        for y in range(x + 1, len(features)):
            if not features[y]:
                continue
            coord_lst = features[x].GetGeometryRef().GetPoints() + features[y].GetGeometryRef().GetPoints()
            points = []
            for coords in coord_lst:
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*coords)
                points.append(point)
            if (points[0].Distance(points[2]) < threshold and points[1].Distance(points[3]) < threshold) or (
                    points[1].Distance(points[2]) < threshold and points[0].Distance(points[3]) < threshold):
                features[y] = None
    features = list(filter(lambda a: a, features))
    return features


def merge_features_geometry(features):
    features = simplify(features)
    multiline = ogr.Geometry(ogr.wkbMultiLineString)
    for feature in features:
        multiline.AddGeometry(feature.GetGeometryRef())
    return multiline


year = 1993
path_to_model = r'D:\Projects\diploma\model'
path_f = os.path.join(path_to_model, '{}'.format(year))
path_e = os.path.join(path_to_model, '{}_e'.format(year))
file_path = os.path.join(path_e, 'edges')
G = convert_shp_to_graph(os.path.join(path_to_model, 'shapefiles',"_{}_lines.shp".format(year)), "false", "true", "Name")
# электросетевая центральность
G1 = nx.read_shp(os.path.join(path_to_model, 'shapefiles',"_{}_points.shp".format(year)))
G1 = G1.to_undirected()
dictionary_a = {}
nodes_a = G1.nodes
for node1 in nodes_a:
    t1 = nx.get_node_attributes(G1, 'Point_Type')
    dictionary_a[node1] = t1[node1]
nx.set_node_attributes(G, dictionary_a, 'type')
nodes_g = nx.nodes(G)
gen = set()
node_dict = nx.get_node_attributes(G, 'type')
for node in nodes_g:
    if node in node_dict:
        if node_dict[node] == 'ЭС':
            print(node, ' is generation')
            gen.add(node)
path = nx.multi_source_dijkstra_path(G, gen)
export_path_to_shp(path, "true", 'Name', path_e, G)

create_cpg(file_path)
driver = ogr.GetDriverByName('ESRI Shapefile')
dataSource = driver.Open('{}.shp'.format(file_path))
src_layer = dataSource.GetLayer()
records = process_layer(src_layer)

data_source = driver.CreateDataSource(os.path.join(path_e, 'el_centrality{}.shp'.format(year)))
dst_layer = data_source.CreateLayer(file_path, None, ogr.wkbMultiLineString, options=["ENCODING=CP1251"])
field_name = ogr.FieldDefn('name', ogr.OFTString)
field_name.SetWidth(80)
dst_layer.CreateField(field_name)
dst_layer.CreateField(ogr.FieldDefn('count', ogr.OFTInteger))

for record in records:
    feature = ogr.Feature(dst_layer.GetLayerDefn())
    for key in record.keys():
        if key == 'geometry':
            feature.SetGeometry(record[key])
        else:
            feature.SetField(key, record[key])
    dst_layer.CreateFeature(feature)

# degree centrality
DC = nx.degree_centrality(G)
nx.set_node_attributes(G, DC, 'centr')
nodes = nx.nodes(G)
d_eff = {}
for node1 in nodes:
    eff = []
    for node2 in nodes:
        if node1 != node2:
            e = nx.efficiency(G, node1, node2)
            eff.append(e)
    ave = float(sum(eff) / len(eff))
    d_eff[node1] = ave
nx.set_node_attributes(G, d_eff, 'Effic')
# nx.write_shp(G,r"D:\Projects\diploma\model\1993")

# local_edge_connectivity
le = {}
for n in nodes_g:
    if n in node_dict:
        l = []
        for k in gen:
            if k != n:
                ec = nx.edge_connectivity(G, k, n)
                l.append(ec)
        ave1 = float(sum(l) / len(l))
        le[n] = ave1
nx.set_node_attributes(G, le, 'connect')
nx_multi_shp.write_shp(G, 'Name', path_f)
# current_flow
# edges = nx.edges(G)
# edg_dict = nx.get_edge_attributes(G, 'Weight')
# for n2 in nodes_g:
# if n2 in node_dict:
# for m in gen:
# if m != n2:
# subs = nx.edge_current_flow_betweenness_centrality_subset(G,m,n2,'True','Weight')
