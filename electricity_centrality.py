# -*- coding: utf-8 -*-
from typing import Dict, Any

import networkx as nx
import nx_multi_shp
import os
import geopandas as gpd


#Hello world
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
    for edge in G.edges():
        for node in path_dict:
            path_edges = []
            path_list = path_dict[node]
            path_list.insert(0, node)
            for i in range(len(path_list) - 1):
                if tuple([tuple(path_list[i]), tuple(path_list[i + 1])]) == tuple(edge):
                    path_edges.append(edge)
                elif tuple([tuple(path_list[i + 1]), tuple(path_list[i])]) == tuple(edge):
                    path_edges.append(edge)
            new_graph = nx.MultiGraph()
            for edge in G.edges():
                if (edge[0], edge[1]) in path_edges:
                    new_graph.add_edge(edge[0], edge[1])
            if multy == 'true':
                nx_multi_shp.write_shp(new_graph, multy_attribute, output_workspace)
            else:
                nx.write_shp(new_graph, output_workspace)


os.chdir(r"D:\Projects\diploma\model")
G1 = nx.read_shp(r"_1993_points.shp")
G1 = G1.to_undirected()
dictionary_a = {}
nodes_a = G1.nodes
for node1 in nodes_a:
    t1 = nx.get_node_attributes(G1, 'Point_Type')
    dictionary_a[node1] = t1[node1]
    # Name1 = nx.get_node_attributes(G1, 'Name')
    # dictionary_a[node1] = t1[node1], Name1[node1]
G2 = convert_shp_to_graph("_1993_lines.shp", "false", "true", "Name")
nx.set_node_attributes(G2, dictionary_a, 'type')
nodes_g = nx.nodes(G2)
list = []
dict = {}
i=0
for n in nodes_g:
    t = nx.get_node_attributes(G2, 'type')
    if n in t:
        if t[n] == 'ЭС':
            list.append(n)
            path = nx.multi_source_dijkstra_path(G2, {n})
            print (path)
            shp=export_path_to_shp(path, "false", 'Name', r"1993", G2)
            i+=1
            if i >= 2:
                final = pd.concat([test,shp])
            test=shp.to_file('test.shp')


