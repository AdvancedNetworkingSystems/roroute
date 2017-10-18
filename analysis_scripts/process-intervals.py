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

import argparse
import networkx as nx
import os


def get_name_all_nodes(exp_base_dir_name_str):
    '''Return a list with the names of all the nodes involved in the
    experiment'''
    nodes_name_list = []
    for d in os.listdir(exp_base_dir_name_str):
        if os.path.isdir(exp_base_dir_name_str + '/' + d):
            nodes_name_list.append(d.split('_')[0])

    return nodes_name_list


def get_strategies(path, node, exp):
    '''Return the list of repetitions of the experiment'''
    strategies = []
    for d in os.listdir("%s/%s_%s" % (path, node, exp)):
        if os.path.isdir("%s/%s_%s/%s" % (path, node, exp, d)):
            try:
                index = int(d)
                strategies.append(index)
            except ValueError:
                continue
    return strategies


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--masteridx', dest='masteridx', type=int,
                        help='Master node number')
    parser.add_argument('--expname', dest='expname', type=str,
                        help='''Name of the experiment. Thisparameter is used
                        by the script to find the experiment directory
                        (${resultsbdir}/${expname}_results. Moreover, the
                        script assumes that the names of all the results files
                        produced by the nodes involved in the experiment
                        (.int, .topo, .route) begin with ${expname}''')
    parser.add_argument('--resultsbdir', dest='resultsbdir', type=str,
                        help='''Base directory containint the experiments
                        results. The results of the experiment we want to
                        analyse are in ${resultsbdir/${expname}_results. Inside
                        this directory there must be a directory for each node
                        involved in the experiment and the name each of these
                        directories must begin with the node name (before the
                        '_' character. Inside the directory of a node there
                        must be one or more directories called 0, 1, 2..., one
                        for each kill strategy used during the experiment.
                        Inside the kill strategy directory there must be the
                        following two dorectories: olsrd2_vanilla and prince.
                        Finally, inside these two directories the script
                        assumes to find the actual results file (.int, .topo
                        and .route)''')

    parser.add_argument("-v", "--verbose", dest="verbose",
                        default=False, action="store_true")
    args = parser.parse_args()

    verbose = args.verbose
    expname = args.expname
    resultsbdir = args.resultsbdir
    masteridx = args.masteridx
    expdir = resultsbdir + '/' + expname + '_results'

    nodes_name_list = get_name_all_nodes(expdir)

    strategies = get_strategies(expdir, nodes_name_list[0], expname)

    out = open("%s_summary/intervals.csv" % expname, "w")
    out.write("node,ip,strategy,h,tc,killed,ap,bc\n")

    for stridx in strategies:

        start_graph_path = expdir + '/nuc0-' + str(masteridx) + '_' + expname +\
            '/' + str(stridx) + '/olsrd2_vanilla/start_graph.graphml'
        strategy_path = expdir + '/nuc0-' + str(masteridx) + '_' + expname +\
            '/' + str(stridx) + '/prince/strategies'

        deadnode_id = ''
        deadnode_name = ''
        with open(strategy_path, 'r') as df:
            line = df.read()
            deadnode_id = line.split('@')[0]

        sg = nx.read_graphml(start_graph_path)
        ap = [x for x in nx.articulation_points(sg)]
        no_leaves_nodes = nx.k_core(sg, 2).nodes()
        cn = [x for x in sg.nodes() if x not in ap and x in no_leaves_nodes]

        node_ip_to_name = {}
        node_name_to_ip = {}
        for i in range(1, 100):
            node_ip_to_name['10.1.0.' + str(i)] = 'nuc0-' + str(i)
            node_name_to_ip['nuc0-' + str(i)] = '10.1.0.' + str(i)

        deadnode_name = node_ip_to_name[deadnode_id]

        bcn = nx.betweenness_centrality(sg, weight='weight', endpoints=True)
        bcns = [(node_ip_to_name[n], bcn[n]) for (n, bcn[n]) in
                sorted(bcn.items(), key=lambda x: x[1], reverse=True)]

        tc_intervals = {}
        hello_intervals = {}
        for nn in nodes_name_list:
            res_path = expdir + '/' + nn + '_' + expname +\
                '/' + str(stridx) + '/prince/'
            intervals_files_list = []
            for root, dirs, files in os.walk(res_path):
                for file_name in files:
                    if file_name.endswith('.int'):
                        intervals_files_list.append(file_name)

            file_prefix = expname + '_' + nn + '_000000'
            for f in intervals_files_list:
                if f.startswith(file_prefix):
                    with open(res_path + '/' + f, 'r') as df:
                        for l in df.readlines():
                            if 'hello' in l:
                                hello_intervals[nn] = float(l.split(':')[1])
                            if 'tc' in l:
                                tc_intervals[nn] = float(l.split(':')[1])

        for nn in nodes_name_list:
            out.write("%s,%s,%d,%f,%f,%d,%d,%f\n" %
                      (nn, node_name_to_ip[nn], stridx, hello_intervals[nn],
                       tc_intervals[nn], 1 if deadnode_name == nn else 0,
                       0 if node_name_to_ip[nn] in cn else 1,
                       bcn[node_name_to_ip[nn]]))

    out.close()
