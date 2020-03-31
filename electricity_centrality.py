# -*- coding: utf-8 -*-
#from typing import Dict, Any

import networkx as nx
import nx_multi_shp
import os



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
        for edge in G.edges(keys=True):
            c = 0
            for i in range(len(path_list) - 1):
                identifier = str(a) + str(b) + str(c)
                if tuple([tuple(path_list[i]), tuple(path_list[i + 1])]) == tuple([edge[0], edge[1]]):
                    new_graph.add_edge(edge[0], edge[1], identifier, Name=edge[2], ident=identifier)
                elif tuple([tuple(path_list[i + 1]), tuple(path_list[i])]) == tuple([edge[0], edge[1]]):
                    new_graph.add_edge(edge[0], edge[1], identifier, Name=edge[2], ident=identifier)
                c += 1
            b += 1
        a += 1
    if multy == 'true':
        nx_multi_shp.write_shp(new_graph, 'ident', output_workspace)
    else:
        nx.write_shp(new_graph, output_workspace)


#output = r"D:\GitHub\elec_centrality"
output = r"D:\Projects\diploma\github\elec_centrality"
os.chdir(output)
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
gen = set()
i = 0
node_dict = nx.get_node_attributes(G2, 'type')
for node in nodes_g:
    if node in node_dict:
        if node_dict[node] == 'ЭС':
            print(node, ' is generation')
            gen.add(node)
path = nx.multi_source_dijkstra_path(G2, gen)
print(path)
export_path_to_shp(path, "true", 'Name', r"1993", G2)



