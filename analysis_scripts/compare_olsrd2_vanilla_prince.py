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

import networkx as nx
import argparse
import numpy as np
import matplotlib.pyplot as plt


def compute_sp_difference(sp1, sp2):
    only_sp1 = {}
    only_sp2 = {}
    sp1_diff = {}
    sp2_diff = {}
    tot_diff = 0
    tot_p = 0
    sp_l1 = []
    sp_l2 = []

    for src in sp1.keys():
        dst_dict = sp1[src]
        for dst in dst_dict.keys():
            if src == dst:
                continue

            sp_l1.append(len(dst_dict[dst]))

    for src in sp2.keys():
        dst_dict = sp2[src]
        for dst in dst_dict.keys():
            if src == dst:
                continue

            sp_l2.append(len(dst_dict[dst]))

    for src1 in sp1.keys():
        if not sp2.get(src1):
            # sp2 does not have src1 as source
            only_sp1[src1] = sp1[src1]
            tot_diff += 1
            tot_p += 1
        else:
            dst1_dict = sp1[src1]
            dst2_dict = sp2[src1]

            for dst1 in dst1_dict.keys():
                if dst1 == src1:
                    continue
                tot_p += 1
                if not dst2_dict.get(dst1):
                    # given src1 source, sp2 does not have dst1 destination
                    tot_diff += 1
                    if src1 in only_sp1:
                        only_sp1[src1][dst1] = dst1_dict[dst1]
                    else:
                        only_sp1[src1] = {dst1: dst1_dict[dst1]}
                else:
                    if set(dst1_dict[dst1]) != set(dst2_dict[dst1]):
                        tot_diff += 1
                        if src1 in sp1_diff:
                            sp1_diff[src1][dst1] = dst1_dict[dst1]
                            sp2_diff[src1][dst1] = dst2_dict[dst1]
                        else:
                            sp1_diff[src1] = {dst1: dst1_dict[dst1]}
                            sp2_diff[src1] = {dst1: dst2_dict[dst1]}

            only_dst2_keys = set(dst2_dict.keys()) - set(dst1_dict.keys())
            for dst2 in only_dst2_keys:
                if dst2 == src1:
                    continue
                tot_diff += 1
                tot_p += 1
                if src1 in only_sp2:
                    only_sp2[src1][dst2] = dst2_dict[dst2]
                else:
                    only_sp2[src1] = {dst1: dst2_dict[dst2]}

    only_src2_keys = set(sp2.keys()) - set(sp2.keys())
    for src2 in only_src2_keys:
        tot_p += 1
        tot_diff += 1
        only_sp2[src2] = sp2[src2]

    return (only_sp1, only_sp2, sp1_diff, sp2_diff, tot_diff, tot_p,
            (sum(sp_l1) / float(len(sp_l1))), max(sp_l1),
            (sum(sp_l2) / float(len(sp_l2))), max(sp_l2))


def compare_paths(paths_fn, v_dir, p_dir, verbose):
    vanilla_dir = v_dir
    prince_dir = p_dir
    vanilla_paths_fn = vanilla_dir + '/' + paths_fn
    prince_paths_fn = prince_dir + '/' + paths_fn
    vanilla_p = {}
    prince_p = {}

    with open(vanilla_paths_fn, 'r') as data_file:
        for line in data_file.readlines():
            p = line.rstrip().split(':')[1].split(',')
            src = p[0]
            dst = p[-1]
            if src in vanilla_p:
                vanilla_p[src][dst] = p
            else:
                vanilla_p[src] = {dst: p}

    with open(prince_paths_fn, 'r') as data_file:
        for line in data_file.readlines():
            p = line.rstrip().split(':')[1].split(',')
            src = p[0]
            dst = p[-1]
            if src in prince_p:
                prince_p[src][dst] = p
            else:
                prince_p[src] = {dst: p}

    only_sp_vanilla, only_sp_prince, sp_diff_vanilla, sp_diff_prince,\
        tot_d, tot_p, avg_l_vanilla, max_l_vanilla, avg_l_prince,\
        max_l_prince =\
        compute_sp_difference(vanilla_p, prince_p)

    print('Avg/Max SP length olsrd2_vanilla: %f/%f' %
          (avg_l_vanilla,
           max_l_vanilla))
    print('Avg/Max SP length prince: %f/%f' %
          (avg_l_prince,
           max_l_vanilla))

    if not only_sp_vanilla and not only_sp_prince and\
       not sp_diff_vanilla and not sp_diff_prince:
        print('Shortest paths match')
    else:
        print('WARNING: shortest paths do not match (%d/%d differences)' %
              (tot_d, tot_p))
        if verbose:
            if only_sp_vanilla:
                print('SPs only in olsrd2_vanilla:')
                for src in only_sp_vanilla.keys():
                    for dst in only_sp_vanilla[src].keys():
                        print('%s -> %s: %s' %
                              (src, dst, only_sp_vanilla[src][dst]))

            if only_sp_prince:
                print('SPs only in prince:')
                for src in only_sp_prince.keys():
                    for dst in only_sp_prince[src].keys():
                        print('%s -> %s: %s' %
                              (src, dst, only_sp_prince[src][dst]))

            if sp_diff_prince and sp_diff_vanilla:
                print('Different SPs:')
                for src in sp_diff_vanilla.keys():
                    for dst in sp_diff_vanilla[src].keys():
                        print('olsrd2_vanilla: %s -> %s: %s' %
                              (src, dst, sp_diff_vanilla[src][dst]))
                        print('prince: %s -> %s: %s' %
                              (src, dst, sp_diff_prince[src][dst]))

    return (vanilla_p, prince_p)


def compare_idx0_paths(g, p1, p2, verbose):
    only_sp1, only_sp2, sp_diff1, sp_diff2,\
        tot_d, tot_p, avg_l1, max_l1, avg_l2,\
        max_l2 =\
        compute_sp_difference(p1, p2)

    print('Avg/Max SP length sp1: %f/%f' %
          (avg_l1,
           max_l1))
    print('Avg/Max SP length sp1: %f/%f' %
          (avg_l2,
           max_l2))

    if not only_sp1 and not only_sp2 and\
       not sp_diff1 and not sp_diff2:
        print('Shortest paths match')
    else:
        print('WARNING: shortest paths do not match (%d/%d differences)' %
              (tot_d, tot_p))
        if verbose:
            if only_sp1:
                print('SPs only in sp1:')
                for src in only_sp1.keys():
                    for dst in only_sp1[src].keys():
                        print('%s -> %s: %s' %
                              (src, dst, only_sp1[src][dst]))

            if only_sp2:
                print('SPs only in sp1:')
                for src in only_sp2.keys():
                    for dst in only_sp2[src].keys():
                        print('%s -> %s: %s' %
                              (src, dst, only_sp2[src][dst]))

            if sp_diff2 and sp_diff1:
                print('Different SPs:')
                for src in sp_diff1.keys():
                    for dst in sp_diff1[src].keys():
                        spd1 = sp_diff1[src][dst]
                        spd2 = sp_diff2[src][dst]
                        c1 = 0
                        c2 = 0
                        for n in range(0, len(spd1)-1):
                            edata = g.get_edge_data(spd1[n],
                                                    spd1[n+1], 'weight')
                            c1 += edata['weight']
                        for n in range(0, len(spd2)-1):
                            edata = g.get_edge_data(spd2[n],
                                                    spd2[n+1], 'weight')
                            c2 += edata['weight']
                        print('sp1: %s -> %s: %s %d' %
                              (src, dst, spd1, c1))
                        print('sp2: %s -> %s: %s %d' %
                              (src, dst, spd2, c2))
                        print('')


def compare_graphs(graph_fn, v_dir, p_dir, verbose):
    vanilla_dir = v_dir
    prince_dir = p_dir
    vanilla_graph = nx.read_graphml(vanilla_dir + '/' + graph_fn)
    vanilla_graph_n = vanilla_graph.nodes()
    vanilla_graph_e = vanilla_graph.edges()
    vanilla_graph_sp = nx.all_pairs_dijkstra_path(vanilla_graph)
    # vanilla_graph_sp = nx.shortest_path(vanilla_graph, weight='weight')
    prince_graph = nx.read_graphml(prince_dir + '/' + graph_fn)
    prince_graph_n = prince_graph.nodes()
    prince_graph_e = prince_graph.edges()
    prince_graph_sp = nx.all_pairs_dijkstra_path(prince_graph)
    # prince_graph_sp = nx.shortest_path(prince_graph, weight='weight')

    print('olsrd2_vanilla: %d nodes, %d edges' %
          (len(vanilla_graph_n), len(vanilla_graph_e)))
    print('prince: %d nodes, %d edges' %
          (len(prince_graph_n), len(prince_graph_e)))

    if set(vanilla_graph_n) == set(prince_graph_n):
        print('Nodes matches')
    else:
        print('WARNING: olsrd2_vanilla and prince have different nodes')

    if set(vanilla_graph_e) == set(prince_graph_e):
        print('Edges matches')
    else:
        print('WARNING: olsrd2_vanilla and prince have different edges')

    only_sp_vanilla, only_sp_prince, sp_diff_vanilla, sp_diff_prince,\
        tot_d, tot_p, avg_l_vanilla, max_l_vanilla, avg_l_prince,\
        max_l_prince =\
        compute_sp_difference(vanilla_graph_sp, prince_graph_sp)

    print('Avg/Max SP length olsrd2_vanilla: %f/%f' %
          (avg_l_vanilla,
           max_l_vanilla))
    print('Avg/Max SP length prince: %f/%f' %
          (avg_l_prince,
           max_l_vanilla))

    if not only_sp_vanilla and not only_sp_prince and\
       not sp_diff_vanilla and not sp_diff_prince:
        print('Shortest paths match')
    else:
        print('WARNING: shortest paths do not match (%d/%d differences)' %
              (tot_d, tot_p))
        if verbose:
            if only_sp_vanilla:
                print('SPs only in olsrd2_vanilla:')
                for src in only_sp_vanilla.keys():
                    for dst in only_sp_vanilla[src].keys():
                        print('%s -> %s: %s' %
                              (src, dst, only_sp_vanilla[src][dst]))

            if only_sp_prince:
                print('SPs only in prince:')
                for src in only_sp_prince.keys():
                    for dst in only_sp_prince[src].keys():
                        print('%s -> %s: %s' %
                              (src, dst, only_sp_prince[src][dst]))

            if sp_diff_prince and sp_diff_vanilla:
                print('Different SPs:')
                for src in sp_diff_vanilla.keys():
                    for dst in sp_diff_vanilla[src].keys():
                        print('olsrd2_vanilla: %s -> %s: %s' %
                              (src, dst, sp_diff_vanilla[src][dst]))
                        print('prince: %s -> %s: %s' %
                              (src, dst, sp_diff_prince[src][dst]))

    return (vanilla_graph, vanilla_graph_sp, prince_graph, prince_graph_sp)


def graph_contains_at_least_one_node(g, n_set, node_name_to_id_dict):
    contains_at_least_one_node = False
    g_nodes = g.nodes()
    for n in n_set:
        n_id = node_name_to_id_dict[n]
        if n_id in g_nodes:
            print('WARNING: node %s in graph' % (n,))
            contains_at_least_one_node = True

    return contains_at_least_one_node


def compute_node_name_to_id_dict():
    # Use the etchost file to create a dictionary that maps the nodes names
    # to the corresponding ids
    node_names_to_id_dict = {}
    with open('etchosts', 'r') as hosts_file:
        for line in hosts_file.readlines():
            node_name = line.split(' ')[1].replace('pop-', '').rstrip()
            node_id = 'id_' + line.split(' ')[0]
            node_names_to_id_dict[node_name] = node_id

    return node_names_to_id_dict


def generate_plots_routes_summary(b_dir, v_dir, p_dir):
    v_fn = v_dir + '/routes_summary'
    p_fn = p_dir + '/routes_summary'
    v_brk_list = []
    p_brk_list = []
    v_loop_list = []
    p_loop_list = []

    start_saving = False
    with open(v_fn, 'r') as data_file:
        for line in data_file.readlines():
            _, brk, loop = line.rstrip().split(' ')
            brk = int(brk)
            loop = int(loop)
            if not start_saving and ((brk > 0) or (loop > 0)):
                v_brk_list = [0] * 10
                v_loop_list = [0] * 10
                start_saving = True
            if start_saving:
                v_brk_list.append(brk)
                v_loop_list.append(loop)

    start_saving = False
    with open(p_fn, 'r') as data_file:
        for line in data_file.readlines():
            _, brk, loop = line.rstrip().split(' ')
            brk = int(brk)
            loop = int(loop)
            if not start_saving and ((brk > 0) or (loop > 0)):
                p_brk_list = [0] * 10
                p_loop_list = [0] * 10
                start_saving = True
            if start_saving:
                p_brk_list.append(brk)
                p_loop_list.append(loop)

    if len(v_brk_list) == 0 and len(p_brk_list) == 0:
        v_brk_list = [0] * 100
        v_loop_list = [0] * 100
        p_brk_list = [0] * 100
        p_loop_list = [0] * 100
    elif len(v_brk_list) == 0:
        v_brk_list = [0] * len(p_brk_list)
        v_loop_list = [0] * len(p_loop_list)
    elif len(p_brk_list) == 0:
        p_brk_list = [0] * len(v_brk_list)
        p_loop_list = [0] * len(v_loop_list)

    list_min_len = min([len(v_brk_list), len(p_brk_list)])
    # list_max_len = max([len(v_brk_list), len(p_brk_list)])
    max_idx_gt0 = 0
    for idx in range(0, list_min_len):
        if v_brk_list[idx] > 0 or v_loop_list[idx] > 0 or\
           p_brk_list[idx] > 0 or p_loop_list[idx] > 0:
            if idx > max_idx_gt0:
                max_idx_gt0 = idx

    max_idx_gt0 = min(max_idx_gt0 + 10, list_min_len)
    time_s = np.arange(0.0, max_idx_gt0 * 0.3, 0.3)
    time_s = time_s[:max_idx_gt0]

    plt.figure(1, figsize=(15, 5))
    plt.grid()
    # step = 10
    lines = plt.plot(time_s, v_brk_list[:max_idx_gt0], 'b',
                     # time_s[::step], v_brk_list[:max_idx_gt0:step], 'bo',
                     time_s, v_loop_list[:max_idx_gt0], 'g',
                     # time_s[::step], v_loop_list[:max_idx_gt0:step], 'go',
                     time_s, p_brk_list[:max_idx_gt0], 'r--',
                     # time_s[::step], p_brk_list[:max_idx_gt0:step], 'ro',
                     # time_s[::step], p_loop_list[:max_idx_gt0:step], 'ys')
                     time_s, p_loop_list[:max_idx_gt0], 'y--')

    plt.setp(lines[:2], linewidth=4)
    plt.setp(lines[2:], linewidth=3)
    axes = plt.gca()
    axes.set_xlim([0, time_s[-1]])
    plt.ylabel('#Failed Paths')
    plt.xlabel('Time [s]')
    plt.legend(['Broken paths olsrd',
                'Paths with loops olsrd',
                'Broken paths prince',
                'Paths with loops prince'], loc=1)
    plt.savefig(b_dir + '/routes_summary.eps')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--basedir', dest='basedir', type=str,
                        help='''Full path of the base directory where to find
                        the results summary. This direcoty must contains the
                        following two directories: olsrd2_vanilla and prince.
                        ''')
    parser.add_argument("-v", "--verbose", dest="verbose",
                        default=False, action="store_true")

    args = parser.parse_args()
    basedir = args.basedir
    verbose = args.verbose
    vanilla_dir = basedir + '/olsrd2_vanilla'
    prince_dir = basedir + '/prince'
    node_names_to_id_dict = compute_node_name_to_id_dict()

    # Check initial nodes desynchronization
    print('#' * 80)
    print('Checking initial desynchronization:')
    desync_idx0_fn = 'desync_idx0'
    with open(vanilla_dir + '/' + desync_idx0_fn, 'r') as data_file:
        vanilla_desync_idx0 = float(data_file.read().replace('s', ''))

    with open(prince_dir + '/' + desync_idx0_fn, 'r') as data_file:
        prince_desync_idx0 = float(data_file.read().replace('s', ''))

    print('olsrd2_vanilla desynchronization at index 0: %.3fs' %
          (vanilla_desync_idx0,))
    print('prince desynchronization at index 0: %.3fs' %
          (prince_desync_idx0,))

    if (vanilla_desync_idx0 > 0.5) or (prince_desync_idx0 > 0.5):
        print('WARNING: desyncronization at index 0 above 0.5s')

    # Check killed nodes and times
    print('#' * 80)
    print('Checking killed nodes:')
    killed_nodes_fn = 'killed_nodes_and_times'
    vanilla_killed_nodes_set = set()
    prince_killed_nodes_set = set()
    print('olsrd2_vanilla:')
    with open(vanilla_dir + '/' + killed_nodes_fn, 'r') as data_file:
        for line in data_file.readlines():
            line = line.rstrip()
            name, idx, ts = line.split(',')
            print('%s at dump index %s (%s)' % (name, idx, ts))
            vanilla_killed_nodes_set.add(name)

    print('prince:')
    with open(prince_dir + '/' + killed_nodes_fn, 'r') as data_file:
        for line in data_file.readlines():
            line = line.rstrip()
            name, idx, ts = line.split(',')
            print('%s at dump index %s (%s)' % (name, idx, ts))
            prince_killed_nodes_set.add(name)

    if vanilla_killed_nodes_set != prince_killed_nodes_set:
        print('WARNING: olsrd2_vanilla and prince have different killed nodes')

    # Check start_graph.graphml
    print('#' * 80)
    print('Checking master node start_graph.graphml:')
    graph_fn = 'start_graph.graphml'
    vanilla_start_graph, vanilla_start_graph_sp,\
        prince_start_graph, prince_start_graph_sp =\
        compare_graphs(graph_fn, vanilla_dir, prince_dir, verbose)

    # Check graph_idx0.graphml
    print('#' * 80)
    print('Checking master node graph_idx0.graphml:')
    graph_fn = 'graph_idx0.graphml'
    vanilla_graph_idx0, vanilla_graph_idx0_sp,\
        prince_graph_idx0, prince_graph_idx0_sp =\
        compare_graphs(graph_fn, vanilla_dir, prince_dir, verbose)

    # Check graph_idxend.graphml
    print('#' * 80)
    print('Checking master node graph_idxend.graphml:')
    graph_fn = 'graph_idxend.graphml'
    vanilla_graph_idxend, vanilla_graph_idxend_sp,\
        prince_graph_idxend, prince_graph_idxend_sp =\
        compare_graphs(graph_fn, vanilla_dir, prince_dir, verbose)

    # Check if graph_idxend.graphml on master node cotains one of the killed
    # nodes
    print('#' * 80)
    print('Checking if master node graph_idxend.graphml contains a '
          'killed node:')
    print('olsrd2_vanilla:')
    tmp = graph_contains_at_least_one_node(vanilla_graph_idxend,
                                           vanilla_killed_nodes_set,
                                           node_names_to_id_dict)
    if tmp:
        print('Graph contains killed nodes')
    print('prince:')
    tmp = graph_contains_at_least_one_node(prince_graph_idxend,
                                           prince_killed_nodes_set,
                                           node_names_to_id_dict)
    if tmp:
        print('Graph contains killed nodes')

    # Check paths_idx0
    print('#' * 80)
    print('Checking paths_idx0:')
    paths_fn = 'paths_idx0'
    vanilla_paths_idx0_sp, prince_paths_idx0_sp =\
        compare_paths(paths_fn, vanilla_dir, prince_dir, verbose)

    # Check paths_idx0
    print('#' * 80)
    print('Checking paths_idxend:')
    paths_fn = 'paths_idxend'
    compare_paths(paths_fn, vanilla_dir, prince_dir, verbose)

    # Check paths graph_idx0 and start_graph
    print('#' * 80)
    print('Checking SP in start_graph and SP in graph_idx0.graphml for '
          'olsrd2_vanilla:')
    compare_idx0_paths(vanilla_graph_idx0,
                       vanilla_start_graph_sp,
                       vanilla_graph_idx0_sp,
                       verbose)

    # Check paths graph_idx0 and start_graph
    print('#' * 80)
    print('Checking SP in start_graph and SP in graph_idx0.graphml for '
          'prince:')
    compare_idx0_paths(prince_graph_idx0,
                       prince_start_graph_sp,
                       prince_graph_idx0_sp,
                       verbose)

    # Check paths_idx0
    print('#' * 80)
    print('Checking paths_idx0 and SP in graph_idx0.graphml for '
          'olsrd2_vanilla:')
    compare_idx0_paths(vanilla_graph_idx0,
                       vanilla_paths_idx0_sp,
                       vanilla_graph_idx0_sp,
                       verbose)

    # Check paths_idx0
    print('#' * 80)
    print('Checking paths_idx0 and SP in graph_idx0.graphml for '
          'prince:')
    compare_idx0_paths(prince_graph_idx0,
                       prince_paths_idx0_sp,
                       prince_graph_idx0_sp,
                       verbose)

    # Check paths_idx0
    print('#' * 80)
    print('Generating plots for routes_summary')
    generate_plots_routes_summary(basedir, vanilla_dir, prince_dir)
    # TODO: compare paths_idx0 and path_idxend

    # TODO: compare routes_summary
