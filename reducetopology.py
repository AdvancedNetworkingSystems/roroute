#
# Copyright (C) 2017 Michele Segata <msegata@disi.unitn.it>
# Copyright (C) 2017 Nicolo' Facchi <nicolo.facchi@unitn.it>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# Example usage:
# rules, score = get_firewall_rules(G, "random_regular_graph:d=4,seed=0")
#

import networkx as nx
import customtopo as ct
import sys
import scipy.sparse as sp
import random
from math import sqrt


def __get_matrix(m, mapping):
    """
    Given a matrix and a mapping indicating the permutation of the indexes,
    returns the permuted matrix
    :param m: input matrix
    :param mapping: permutation of indexes
    :return: input matrix after permutation
    """
    n = m.get_shape()[0]
    tmp_m = [[0 for x in range(n)] for x in range(n)]
    for r in range(n):
        for c in range(n):
            tmp_m[r][c] = m[mapping[r], mapping[c]]
    return sp.csr_matrix(tmp_m)


def __matrix_and(a, b):
    """
    Performs an element by element logical and between two matrices
    :param a: first matrix
    :param b: second matrix
    :return: a AND b
    """
    n = a.get_shape()[0]
    rm = sp.lil_matrix((n, n))
    for r in range(n):
        for c in range(n):
            rm[r, c] = a[r, c] and b[r, c]
    return rm


def __matching_score(a, b):
    """
    Computes a similarity score between two matrices. The matrices are
    adjacency matrices, so the entries are only 0s or 1s, and the elements on
    the diagonal are all 0. If the matrices are NxN, then the score is
    computed as
    1 - sum(|a - b|) / (N*N-N)
    A score of 1 indicates that all elements match, a score of 0 indicates
    that no element matches.
    :param a: first matrix
    :param b: second matrix
    :return: similarity score between a and b
    """
    n = a.get_shape()[0]
    # return 1 - (abs(a - b)).sum() / (n * n - n)
    return 1 - (abs(a - b)).sum() / b.sum()


def __get_links(m, sorted_map, nodes, disabled=True):
    """
    Given an adjacency matrix returns a dictionary mapping between each node
    and the nodes that are not able (or able) to communicate with it
    :param m: adjacency matrix
    :param sorted_map: map from the indexes in the adjacency matrix to the
    index of the nodes
    :param nodes: array of node names
    :param disabled: if set to true, the function returns the disabled links,
    otherwise the active topology links
    :return: disabled (or enabled) links dictionary. each entry of the
    dictionary is a list of tuples (destination, cost)
    """
    dl = dict()
    n = m.get_shape()[0]
    for r in range(n):
        node = nodes[sorted_map[r]]
        dl[node] = []
        for c in range(n):
            if r != c:
                if (disabled and m[r, c] == 0) or \
                   (not disabled and m[r, c] != 0):
                    dl[node].append((nodes[sorted_map[c]],
                                     0 if disabled else m[r, c]))
    return dl


def __get_graph(adjacency_matrix, mapping, nodes):
    """
    Given an adjancency matrix returns the corresponding networkx graph
    :param adjacency_matrix: the adjacency matrix
    :param mapping: mapping between the index of nodes in the adjaceny matrix
    and the index of nodes inside the list of node names
    :param nodes: list of node names
    :return: networkx graph of the given adjacency matrix
    """
    G = nx.from_scipy_sparse_matrix(adjacency_matrix)
    new_names = dict((i, nodes[mapping[i]]) for i in range(len(nodes)))
    nx.relabel_nodes(G, new_names, copy=False)
    return G


def __add_link_costs(enabled_links, seed, olsrv1=False, has_costs=False):
    """
    Given the dictionary of enabled links, return a dictionary of tuples
    where the first item of the tuple is the IP of the neighbor and the
    second a randomized link cost
    :param enabled_links: dictionary of enabled links
    :param seed: a seed used to initialize the PRNGs
    :param olsrv1: generate link costs for olsrv1 or olsrv2
    :param has_costs: if set to true, the costs are not randomly generated
    but automatically taken from enabled_links
    :return: the dictionary with randomized link costs
    """
    if has_costs:
        return enabled_links
    if olsrv1:
        link_step = 0.005
        n_costs = 100
        min_cost = 0.5
    else:
        link_step = 16
        n_costs = 100
        min_cost = 16
    random.seed(seed)
    lc = dict()
    for node, neighbors in enabled_links.iteritems():
        lc[node] = []
        for (neigh, c) in neighbors:
            r_cost = -1
            if neigh in lc:
                for (n, cost) in lc[neigh]:
                    if n == node:
                        r_cost = cost

            if r_cost == -1:
                r_cost = random.randint(0, n_costs) *\
                         link_step + min_cost

            lc[node].append((neigh, r_cost))
    return lc


def __stringify_disabled_links(disabled_links):
    """
    Transforms the dictionary computed by the __get_links method into a
    configuration string for the experiments
    :param disabled_links: disabled links dictionary
    :return: configuration string in the format "IP1:IPa,IPb,IPc;IP2:IPd,IPe"
    """
    no_costs = dict(map(lambda (n, l): (n, map(lambda y: y[0], l)),
                    disabled_links.iteritems()))
    merge_neighbors = dict((k, ','.join(v))
                           for k, v in no_costs.iteritems())
    merge_nodes = ["%s:%s" % (k, v) for k, v in merge_neighbors.iteritems()]
    merge_all = ";".join(merge_nodes)
    return merge_all


def __stringify_link_costs(link_costs, olsrv1=False):
    """
    Transforms the dictionary computed by the __add_link_costs method
    into a configuration string for the experiments
    :param link_costs: link costs dictionary
    :return: configuration string in the format "IP1:IPa-cost,IPb-cost;..."
    """
    costs = []
    for node, neighbors in link_costs.iteritems():
        if olsrv1:
            node_costs = ','.join(["%s-%.3f" % (neigh, cost)
                                   for (neigh, cost) in neighbors])
        else:
            node_costs = ','.join(["%s-%d" % (neigh, cost)
                                   for (neigh, cost) in neighbors])
        costs.append("%s:%s" % (node, node_costs))
    return ';'.join(costs)


def __stringify_intervals(intervals):
    """
    Transforms the dictionary of hello and tc intervals computed using the
    __compute_intervals function into a configuration string for the
    experiments
    :param intervals: dictionary of hello and tc intervals
    :return: configuration string
    """
    nodes = ["%s:%.3f,%.3f" % (n, h, t) for n, (h, t) in intervals.iteritems()]
    return ";".join(nodes)


def print_matrix(m, mapping=None):
    """
    Prints a matrix to stdout
    :param m: matrix
    :param mapping: permutation of the indexes. By default no permutation is
    used
    """
    n = m.get_shape()[0]
    if mapping is None:
        mapping = range(n)
    for r in range(n):
        if r == 0:
            sys.stdout.write("     ")
            for c in range(n):
                sys.stdout.write("%3d  " % mapping[c])
            sys.stdout.write("\n")
        sys.stdout.write("%3d: " % mapping[r])
        for c in range(n):
            sys.stdout.write("%3d, " % m[mapping[r], mapping[c]])
        sys.stdout.write("\n")


def __get_intervals(nodes, dg, r, bc):
    o_h = sum([v for k, v in dg.iteritems()]) / 2.0
    hello_const = 1/o_h * sum([sqrt(bc[node] * dg[node]) for node in nodes])
    o_lsa = len(nodes) * r / 5.0
    tc_const = 1/o_lsa * sum([sqrt(bc[node] * r) for node in nodes])
    return dict((node, (sqrt(dg[node] / bc[node]) * hello_const,
                        sqrt(r / bc[node]) * tc_const))
                for node in nodes)


def __compute_intervals(graph, return_bc=False, use_degree=True):
    """
    Given a networkx graph, returns the poprouting hello and tc intervals to
    be set for each node
    :param graph: graph
    :return: a dictionary in the form "node: (hello, tc)"
    """
    bc = nx.betweenness_centrality(graph, weight="weight", endpoints=True)

    dg = dict((v, 1) for v in graph.nodes())
    r = len(graph.nodes())
    ints_no_degree = __get_intervals(graph.nodes(), dg, r, bc)
    dg = dict((v, d) for v, d in graph.degree().iteritems())
    r = len(graph.edges())
    ints_degree = __get_intervals(graph.nodes(), dg, r, bc)

    # return a dictionary node -> (hello, tc)
    if not return_bc:
        if use_degree:
            return ints_degree
        else:
            return ints_no_degree
    else:
        ints = dict((node, (ints_degree[node][0], ints_degree[node][1],
                            ints_no_degree[node][0], ints_no_degree[node][1],
                            bc[node], graph.degree()[node]))
                    for node in graph.nodes())
    return ints


def get_firewall_rules(graph, generator_string, seed=0,
                       olsrv1=False, display=False, print_csv=False,
                       single_interface=False):
    """
    Given a networkx graph representing the real topology of a testbed, returns
    the firewall rules to be applied to obtain a synthetic topology with the
    generated using a given generator. In addition, the function returns a
    score between 0 and 1 which represents how close is the new topology to the
    synthetic topology. A score of 1 means that the testbed topology
    can be transformed to completely match the synthetic graph. A score of 0
    indicates that no link can be matched
    :param graph: networkx graph
    :param generator_string: a networkx function name (e.g.,
    "random_regular_graph") with the list of parameters. The generator
    function must accept the parameter n as the number of nodes, plus
    the additional parameters, and generate a networkx graph. The format of
    the string is like
    "generator_function_name:p1=v1,p2=v2,..."
    where p1 and p2 are the argument names and v1 and v2 their respective
    values. The arguments should not include the parameter n, which is
    automatically obtained from the given graph
    :param seed: seed used for random generators
    :param olsrv1: if set to true, generate olsrv1-compatible link costs
    :param display: if set to True, shows a plot with the overlapping desired
    topology and the experiment topology, for a graphical comparison of the two
    :param print_csv: if true, prints a csv table with node id, times,
    betweennes centrality and degree, to be used for plotting and analysis
    :param single_interface: if true, the degree d_i is forced to 1 to
    represent a single interface node
    :return: a pair where the first element is the firewall configuration of
    links to be disabled, while the second is the matching score
    """

    # remove "id_" from node names
    testbed_g = graph
    old_names = testbed_g.nodes()
    new_names = dict((i, i.replace('id_', '')) for i in old_names)
    nx.relabel_nodes(testbed_g, new_names, copy=False)

    n_nodes = len(testbed_g.nodes())
    testbed_am = nx.adj_matrix(testbed_g)

    # create a map from node id to its original position
    mp = dict((testbed_g.nodes()[i], i) for i in range(n_nodes))
    # sort the nodes by degree
    testbed_d = testbed_g.degree()
    sd = sorted(testbed_d.items(), key=lambda x: x[1], reverse=True)
    testbed_sd = map(lambda x: x[0], sd)
    # create the sorted map. testbed_sd is a vector of node names, and we
    # need a vector of indexes
    testbed_sm = [mp[testbed_sd[i]] for i in range(len(testbed_sd))]
    testbed_matrix = __get_matrix(testbed_am, testbed_sm)

    if generator_string.find(":") != -1:
        generator, parameters = generator_string.split(":")
        gen_args = dict()
        for p in parameters.split(","):
            key, value = p.split("=")
            try:
                v = int(value)
            except:
                v = value
            gen_args[key] = v
    else:
        generator = generator_string
        gen_args = dict()

    # create a synthetic graph by calling the given generator
    # search for the generator inside networkx. if not found, use one of our
    # custom generators
    try:
        gen_function = getattr(nx, generator)
    except AttributeError:
        gen_function = getattr(ct, generator)
    synt_g = gen_function(n=n_nodes, **gen_args)
    synt_am = nx.adj_matrix(synt_g)
    synt_d = synt_g.degree()
    # sort by degree as for the real graph
    sd = sorted(synt_d.items(), key=lambda x: x[1], reverse=True)
    synt_sm = map(lambda x: x[0], sd)
    synt_matrix = __get_matrix(synt_am, synt_sm)

    best_score = -1
    best_matrix = None
    best_mapping = None
    n_attempts = 10

    random.seed(0)
    # if the matching using the heuristic didn't work, simply try n times
    # with random shuffling
    while best_score < 1 and n_attempts > 0:
        n_attempts -= 1
        # transform the testbed topology in the synthetic topology by performing
        # a logical and
        experiment_matrix = __matrix_and(testbed_matrix, synt_matrix)
        # count the number of non matching entries. 1 means perfect match,
        # 0 means no link could be matched
        score = __matching_score(experiment_matrix, synt_matrix)
        if score > best_score:
            best_score = score
            best_matrix = experiment_matrix
            best_mapping = testbed_sm

        testbed_sm = range(len(testbed_g.nodes()))
        random.shuffle(testbed_sm)
        testbed_matrix = __get_matrix(testbed_am, testbed_sm)

    if display:
        # do this heretic thing to avoid installing matplotlib on testbed
        # nodes if not really required
        import matplotlib.pyplot as plt
        experiment_g = nx.from_scipy_sparse_matrix(best_matrix)
        nx.draw_circular(synt_g)
        nx.draw_circular(experiment_g, width=3, edge_color='r')
        plt.show()

    # given the experiment matrix and the nodes of the testbed, get the links
    # that must be disabled to obtain the desired topology
    disabled_links = __get_links(best_matrix, best_mapping, testbed_g.nodes())
    # transform this into a string usable by the scripts
    rules = __stringify_disabled_links(disabled_links)

    # check whether the edges in the synthetic topology have a weight
    u, v = synt_g.edges()[0]
    has_costs = False
    if "weight" in synt_g.get_edge_data(u, v).keys():
        has_costs = True
    link_costs = __add_link_costs(__get_links(best_matrix, best_mapping,
                                              testbed_g.nodes(),
                                              False), seed, olsrv1=olsrv1,
                                  has_costs=has_costs)
    costs = __stringify_link_costs(link_costs, olsrv1=olsrv1)

    graph = __get_graph(best_matrix, best_mapping, testbed_g.nodes())
    intervals = __stringify_intervals(__compute_intervals(graph,
                                                          use_degree=not
                                                          single_interface))

    if print_csv:
        intv = __compute_intervals(graph, return_bc=True)
        print("node,h,tc,hnd,tcnd,bc,d")
        for n, (h, tc, h2, tc2, bc, d) in intv.iteritems():
            print("%s,%f,%f,%f,%f,%f,%d" % (n, h, tc, h2, tc2, bc, d))

    # we return the configuration string and the measure of the match
    return rules, costs, intervals, best_score
