#!/usr/bin/env python
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

import sys
import random
import argparse
import subprocess
import time
from os.path import expanduser
from collections import Counter
import networkx as nx
import reducetopology
import olsrv1_util


def create_directory(dirname, testbed):
    '''Create a directory on the nodes of the testbed.
    dirname: the directory name that will be created on the nodes of the
    testbed.
    testbed: the name of the testbed (wilab or twist)
    '''

    print("Creating directory %s" % (dirname,))
    sys.stdout.flush()
    create_dir_cmd = 'ansible-playbook create-directory.yaml ' +\
                     '--extra-vars ' +\
                     '"testbed=' + testbed + ' ' +\
                     'dirname=' + dirname + '"'

    if verbose:
        print(create_dir_cmd)
    sys.stdout.flush()

    [rcode, cout, cerr] = run_command(create_dir_cmd)


def run_command(command):
    '''
    Method to start the shell commands
    and get the output as iterater object
    '''

    sp = subprocess.Popen(command, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, shell=True)
    out, err = sp.communicate()

    if err:
        raise Exception('An error occurred in while ' +
                        'executing command: %s' % err)

    return [sp.returncode, out.decode('utf-8'), err.decode('utf-8')]


def convert_nodes_id_to_hostname(strategy_str):
    '''
    Utility function that takes as input a kill/restart strategy string and
    convert the nodes IDs into the corresponding hostname.
    '''

    ret_strategy_str = ''
    nodeids_hostname_dict = {}
    nodeids_times = strategy_str.split(',')

    with open('/etc/hosts', 'r') as ifile:
        for line in ifile:
            ip_hostname = line.split(' ')
            ip = ip_hostname[0]
            hostname = ip_hostname[1]
            hostname = hostname.split('pop-')[1]
            nodeids_hostname_dict[ip] = hostname.strip('\n')

    for nt in nodeids_times:
        nodeid, nodetime = nt.split('@')
        node_strategy = nodeids_hostname_dict[nodeid] + '@' + nodetime
        if not ret_strategy_str:
            ret_strategy_str = node_strategy
        else:
            ret_strategy_str += ',' + node_strategy

    return ret_strategy_str


def compute_topology_dumper_times(strategy_string,
                                  start_guard_s,
                                  stop_guard_s):
    '''
    Utility function that computes the start/stop times of the topology dumper
    based on the current strategy string.
    '''

    now = int(time.time())
    start_time = now + start_guard_s

    nodes_max_start_stop_time = 0
    nodes_times = strategy_string.split(',')
    for nt in nodes_times:
        [node_id, node_time] = nt.split('@')
        node_seconds = int(node_time.split('.')[0])
        if node_seconds > nodes_max_start_stop_time:
            nodes_max_start_stop_time = node_seconds

    stop_time = start_time + nodes_max_start_stop_time + stop_guard_s

    return (start_time, stop_time)


def compare_shortest_paths(g1, g2):
    '''
    Compares the shortest paths in g1 and in g2.
    Returns True if the shortest paths match of False otherwise.
    '''

    n1sorted = sorted(g1.nodes())
    n2sorted = sorted(g2.nodes())
    sp_match = True

    # The two graphs must have the same nodes
    if n1sorted == n2sorted:
        sp1_dict = nx.all_pairs_dijkstra_path(g1)
        sp2_dict = nx.all_pairs_dijkstra_path(g2)

        for source_node in sp1_dict.keys():
            sp1 = sp1_dict[source_node]
            sp2 = sp2_dict[source_node]

            if not (set(sp1.keys()) - set(sp2.keys())):
                for dest_node in sp1.keys():
                    if not (sp1[dest_node] == sp2[dest_node]):
                        sp_match = False
                        if verbose:
                            print('%s -> %s:' % (source_node, dest_node))
                            path_list1 = sp1[dest_node]
                            w1 = 0
                            for i in range(1, len(path_list1)):
                                w1 += g1.get_edge_data(path_list1[i-1],
                                                       path_list1[i])['weight']
                            print('Previous: %s, cost: %f' %
                                  (path_list1, w1))
                            path_list2 = sp2[dest_node]
                            w1 = 0
                            w2 = 0
                            for i in range(1, len(path_list2)):
                                w2 += g2.get_edge_data(path_list2[i-1],
                                                       path_list2[i])['weight']
                            for i in range(1, len(path_list1)):
                                edata = g2.get_edge_data(path_list1[i-1],
                                                         path_list1[i])
                                if edata is None:
                                    print('Missing edge %s %s' %
                                          (path_list1[i-1],
                                           path_list1[i]))
                                    break
                                else:
                                    w1 += edata['weight']
                            print('Previous on current: %s, cost: %f' %
                                  (path_list1, w1))

                            print('Current: %s, cost: %f' %
                                  (path_list2, w2))

            else:
                sp_match = False

            if not sp_match:
                break

    else:
        sp_match = False

    return sp_match


# compare two routing tables defined as a set containing set of pairs:
# (destination_ip, next_hop_ip)
def compare_routing_table(rt1, rt2):
    if rt1 == rt2:
        return True
    else:
        print(rt1.symmetric_difference(rt2))
        return False


def wait_for_stable_topology():
    '''
    Request (dump_olsr_topology) the olsrd2 topology every second and compare
    it with the last obtained topology. If the topology does not change for
    stability_threshold seconds it is considered stable and the corresponding
    Graph is returned. If the topology des not converge within max_attempts
    seconds we return the last obtained graph. The function returns the tuple
    (Graph, stable), where Graph is the obtained graph and stable is a boolean
    equals True if the topology reched convergence.
    FIX  THIS: In the current implementation with give highest priority to the
    local routing table: if the local routing table does not change for
    stability_threshold seconds then the topology is considered stable even if
    the graph returned by olsrd2 changed
    '''

    previous_graph = None
    previous_routing_table = None
    # After max_attempts without reaching stability we raise an exception
    attempts_counter = 0
    max_attempts = 120
    # When stability_counter reaches stability_threshold we consider the
    # topology stable
    stability_counter = 0
    stability_threshold = 30

    # After max_attempts we continue the experiment even if the topology didn't
    # converge.
    while attempts_counter <= max_attempts:
        # Obtain topology and routing table from olsrd2 daemon
        print('Topology convergence check (attempt #%d / %d)' %
              (attempts_counter, max_attempts))
        print('stability_counter = %d / %d' %
              (stability_counter, stability_threshold))
        if verbose:
            print('Asking topology and routing table to olsrd2')

        sys.stdout.flush()

        # Build the current graph from olsrd topology
        current_graph = olsrv1_util.dump_olsr_topology()

        # build the current routing table set
        current_routing_table = olsrv1_util.dump_olsr_routing_table()

        # We skip this for the first iteration because we don't have a previous
        # graph
        if attempts_counter != 0:
            graph_changed = True
            nodes_changed = True
            edges_changed = True
            nodes_previous = previous_graph.nodes()
            nodes_current = current_graph.nodes()

            # If current and previous graph have the same nodes
            if Counter(nodes_previous) == Counter(nodes_current):
                nodes_changed = False

                if verbose:
                    print('Previous and current graphs have the same nodes')
                    sys.stdout.flush()

                graphs_diff1 = nx.difference(previous_graph, current_graph)
                graphs_diff2 = nx.difference(current_graph, previous_graph)

                # and if current and previous graph have the same edges
                if len(graphs_diff1.edges()) == 0 \
                   and len(graphs_diff2.edges()) == 0:
                    edges_changed = False

                    if verbose:
                        print('Previous and current graphs have the same '
                              'edges')
                        sys.stdout.flush()

                else:
                    print("Edges in current graph but not in previous one")
                    print(graphs_diff2.edges())
                    print("Edges in previous graph but not in current one")
                    print(graphs_diff1.edges())

                    sys.stdout.flush()

            else:
                print('Previous and current graphs have different nodes')
                if verbose:
                    print(nodes_previous)
                    print(nodes_current)

                sys.stdout.flush()

            if not nodes_changed and not edges_changed:
                # If also the shortest paths are the same then it means
                # that the graph didn't change
                if compare_shortest_paths(previous_graph, current_graph):
                    graph_changed = False
                    stability_counter += 1
                    print('Previous and current graphs have the same '
                          'shortest paths')

                    if verbose:
                        print('stability_counter = %d' % (stability_counter,))
                        sys.stdout.flush()

                    if stability_counter == stability_threshold:
                        # At this point we assume the topology is stable
                        if verbose:
                            print('Topology is stable')
                            sys.stdout.flush()
                        return (current_graph, True)

                    sys.stdout.flush()
                else:
                    print('Previous and current graphs have different '
                          'shortest paths')
                    sys.stdout.flush()

            if graph_changed:
                # As a last hope we compare the current routing table on the
                # master node with the previous one
                if not nodes_changed and not edges_changed and \
                    compare_routing_table(previous_routing_table,
                                          current_routing_table):
                    print('Routing table on master node haven\'t changed')

                    stability_counter += 1

                    if verbose:
                        print('stability_counter = %d' % (stability_counter,))
                        sys.stdout.flush()

                    if stability_counter == stability_threshold:
                        # At this point we assume the topology is stable
                        if verbose:
                            print('Topology is stable')
                            sys.stdout.flush()
                        return (current_graph, True)
                else:
                    if verbose:
                        print('Topology changed wrt previous iteration')
                        sys.stdout.flush()
                    stability_counter = 0

        attempts_counter += 1

        previous_graph = current_graph
        previous_routing_table = current_routing_table
        time.sleep(1)

    # If we reached this point it means the topology didn't converge after
    # max_attempts iterations
    return (current_graph, False)


def stop_one_node_1s_loop(start_graph, current_stable_graph,
                          strategy_list, strategy_idx, nrepeat):
    raise Exception('Strategy not implemented yet')


# This strategy selects a random nodes and stops it after 1 second
def stop_one_random_node_1s(start_graph, current_stable_graph,
                            stop_strategy_list, start_strategy_list,
                            strategy_idx, nrepeat):
    '''
    TODO: This documentation is obsolete. Fix it.
    This is an example of how to implement a function that must define a
    strategy for stopping and restarting nodes.
    The function is called for every even iteration of the main controller
    loop.

    Input:

    - start_graph: original stable topology obtained after the first setup of
      the network (iteration 0)
    - current_stable_graph: stable graph obtained during the current iteration.
      This function could use the new stable graph for deciding to change the
      strategy for stopping and restarting nodes
    - stop_strategy_list: a list of strings. Each string defines a strategy for
      stopping nodes. This list is the same as the last one
      returned by this function and could be used by this function for deciding
      it it make sense to change some strategy. This parameter is None the
      first time the function is called. Only elements after strategy_idx
      should be changed.
    - start_strategy_list: a list of strings. Each string defines a strategy
      for starting nodes. This list is the same as the last one returned by
      this function as for the stop_strategy_list parameter.
      start_strategy_list and stop_strategy_list have the same length.
    - strategy_idx: index of the next strategy that will be used (in
      strategy_list). This parameter makes sense only when stop_strategy_list
      is not None.

    Output: the function must return two lists of strategy strings.
    In the first list each string specify which nodes to stop and when to stop
    them. The list is a comma separated list of element with the following
    format: nodes_id@seconds.milliseconds. Where node_id is the id of the node
    as specified in the graphs passed as parameters the seconds and
    milliseconds specify when the node will be stopped (starting from when the
    topology_dumper is started.
    The list must contain at least one element.
    The second list must contain one element for each element of the first list
    (also an empty string is accepted) and must specify, using the same format,
    when a node must be restarted. A node can be restarted olny if the node
    appear also in the first list (one of the stopped nodes). The start time
    must come after the stop time.
    '''

    if stop_strategy_list:
        return (stop_strategy_list, start_strategy_list)

    ret_stop_strategy_list = []
    ret_start_strategy_list = ['']
    g = start_graph.copy()
    # Remove selfloop
    g.remove_edges_from(g.selfloop_edges())
    # maximal subgraph that contains nodes of degree 2
    g_k2 = nx.k_core(g, 2)
    # Find the articulation points of the graph. Removing articulation point
    # increases the number of connected components
    excluded_nodes = [n for n in nx.articulation_points(g_k2)]
    candidate_nodes = [n for n in g_k2.nodes() if n not in excluded_nodes]

    selected_node = random.choice(candidate_nodes)
    ret_stop_strategy_list.append(selected_node + '@1.000')

    return (ret_stop_strategy_list, ret_start_strategy_list)


# This strategy selects a random node, stops it after 1 second and restarts
# it after 61s
def stop_one_random_node_1s_start_61s(start_graph, current_stable_graph,
                                      stop_strategy_list, start_strategy_list,
                                      strategy_idx, nrepeat):
    if stop_strategy_list:
        return (stop_strategy_list, start_strategy_list)

    ret_stop_strategy_list = []
    ret_start_strategy_list = []
    g_nodes = start_graph.nodes()

    selected_node = random.choice(g_nodes)
    ret_stop_strategy_list.append(selected_node + '@1.000')
    ret_start_strategy_list.append(selected_node + '@61.000')

    return (ret_stop_strategy_list, ret_start_strategy_list)


# This function extract the two most central nodes (betweenness centrality)
# and produces two strategies:
# - Node with highest betweenness centrality is stopped at 1s and restarted
# at 61s
# - Node with the second highest betweenness centrality is stopped at 1s and
# restarted at 61s
# We assume the graph as at least two nodes
def one_node_stop_1s_start_61s_2mostcentral(start_graph, current_stable_graph,
                                            stop_strategy_list,
                                            start_strategy_list,
                                            strategy_idx,
                                            nrepeat):
    if stop_strategy_list:
        return (stop_strategy_list, start_strategy_list)

    ret_stop_strategy_list = []
    ret_start_strategy_list = []
    betcent_nodes = nx.betweenness_centrality(start_graph, weight='weight')
    betcent_sorted_nodes = sorted(betcent_nodes.items(),
                                  key=lambda x: x[1], reverse=True)

    ret_stop_strategy_list.append(betcent_sorted_nodes[0][0] + '@1.000')
    ret_start_strategy_list.append(betcent_sorted_nodes[0][0] + '@61.000')

    ret_stop_strategy_list.append(betcent_sorted_nodes[1][0] + '@1.000')
    ret_start_strategy_list.append(betcent_sorted_nodes[1][0] + '@61.000')

    return (ret_stop_strategy_list, ret_start_strategy_list)


# This function extract the five most central nodes (betweenness centrality)
# and produces the following strategy for each of the five nodes:
# - The node is stopped at 1s
# We assume the graph as at least five nodes (not articulation point nodes)
def one_node_stop_1s_5mostcentral(start_graph, current_stable_graph,
                                  stop_strategy_list,
                                  start_strategy_list,
                                  strategy_idx,
                                  nrepeat):
    if stop_strategy_list:
        return (stop_strategy_list, start_strategy_list)

    ret_stop_strategy_list = []
    ret_start_strategy_list = []
    g = start_graph.copy()
    # Remove selfloop
    g.remove_edges_from(g.selfloop_edges())
    # maximal subgraph that contains nodes of degree 2
    # g_k = nx.k_core(g, 2)
    # For the moment we keep also the leaves
    g_k = nx.k_core(g, 1)
    # Nodes ordered using betweenness centrality
    betcent_nodes = nx.betweenness_centrality(g_k, weight='weight')
    betcent_sorted_nodes = sorted(betcent_nodes.items(),
                                  key=lambda x: x[1], reverse=True)
    # Find the articulation points of the graph. Removing articulation point
    # increases the number of connected components
    excluded_nodes = [n for n in nx.articulation_points(g_k)]
    candidate_nodes = [n[0] for n in betcent_sorted_nodes
                       if n[0] not in excluded_nodes]

    for idx in range(0, min(5, len(candidate_nodes))):
        ret_stop_strategy_list.append(candidate_nodes[idx] + '@1.000')
        ret_start_strategy_list.append('')

    return (ret_stop_strategy_list, ret_start_strategy_list)


# This function extract the most central node (betweenness centrality)
# and produces the following strategy:
# - The node is stopped at 1s
# The strategy is repeated 10 times
# We assume the graph as at least five nodes (not articulation point nodes)
def stop_mostcentral_1s_repeat(start_graph, current_stable_graph,
                               stop_strategy_list,
                               start_strategy_list,
                               strategy_idx,
                               nrepeat):
    if stop_strategy_list:
        return (stop_strategy_list, start_strategy_list)

    ret_stop_strategy_list = []
    ret_start_strategy_list = []
    g = start_graph.copy()
    # Remove selfloop
    g.remove_edges_from(g.selfloop_edges())
    # Nodes ordered using betweenness centrality
    betcent_nodes = nx.betweenness_centrality(g, weight='weight',
                                              endpoints=True)
    betcent_sorted_nodes = sorted(betcent_nodes.items(),
                                  key=lambda x: x[1], reverse=True)
    # Find the articulation points of the graph. Removing articulation point
    # increases the number of connected components
    excluded_nodes = [n for n in nx.articulation_points(g)]
    candidate_nodes = [n[0] for n in betcent_sorted_nodes
                       if n[0] not in excluded_nodes]

    for idx in range(0, nrepeat):
        ret_stop_strategy_list.append(candidate_nodes[0] + '@1.000')
        ret_start_strategy_list.append('')

    return (ret_stop_strategy_list, ret_start_strategy_list)


def stop_center_evenchain_1s_repeat(start_graph, current_stable_graph,
                                    stop_strategy_list,
                                    start_strategy_list,
                                    strategy_idx,
                                    nrepeat):
    if stop_strategy_list:
        return (stop_strategy_list, start_strategy_list)

    ret_stop_strategy_list = []
    ret_start_strategy_list = []
    g = start_graph.copy()
    ds = sorted(g.degree().items(), key=lambda x: x[1])
    n1 = ds[-1][0]
    n2 = ds[-2][0]
    p_n1_n2 = nx.shortest_path(g, n1, n2)
    n_to_kill = p_n1_n2[(len(p_n1_n2) - 1) / 2]

    for idx in range(0, nrepeat):
        ret_stop_strategy_list.append(n_to_kill + '@1.000')
        ret_start_strategy_list.append('')

    return (ret_stop_strategy_list, ret_start_strategy_list)


# This function produces a strategy where the two most central nodes
# (betweenness centrality) are stopped at 1s and restarted at 61s
# We assume the graph as at least two nodes
def two_node_stop_1s_start_61s_2mostcentral(start_graph, current_stable_graph,
                                            stop_strategy_list,
                                            start_strategy_list,
                                            strategy_idx,
                                            nrepeat):
    if stop_strategy_list:
        return (stop_strategy_list, start_strategy_list)

    ret_stop_strategy_list = []
    ret_start_strategy_list = []
    betcent_nodes = nx.betweenness_centrality(start_graph, weight='weight')
    betcent_sorted_nodes = sorted(betcent_nodes.items(),
                                  key=lambda x: x[1], reverse=True)

    ret_stop_strategy_list.append(betcent_sorted_nodes[0][0] + '@1.000,' +
                                  betcent_sorted_nodes[1][0] + '@1.000')
    ret_start_strategy_list.append(betcent_sorted_nodes[0][0] + '@61.000,' +
                                   betcent_sorted_nodes[1][0] + '@61.000')

    return (ret_stop_strategy_list, ret_start_strategy_list)


# This function is called before beginning the actual experiment with the
# purpose of computing the most dense mesh network possible and deploy the
# proper firewall rules for obtaining a graph of type graph_type
def preliminary_net_setup_for_firewall_rules_deployment(testbed,
                                                        rate,
                                                        channel,
                                                        power,
                                                        graph_params,
                                                        metricsseed,
                                                        expdir):

    #######################################################################
    # Flush firewall rules
    print("Flush firewall rules")
    sys.stdout.flush()
    flush_cmd = 'ansible-playbook flush-firewall-rules.yaml ' +\
                '--extra-vars ' +\
                '"testbed=' + testbed + '"'

    if verbose:
        print(flush_cmd)
    sys.stdout.flush()

    [rcode, cout, cerr] = run_command(flush_cmd)

    #######################################################################
    # Kill olsrd2 and prince as a clean up procedure
    print("Killing prince")
    sys.stdout.flush()
    stop_prince_cmd = 'ansible-playbook stop-prince.yaml ' +\
                      '--extra-vars ' +\
                      '"testbed=' + testbed + '"'

    if verbose:
        print(stop_prince_cmd)
    sys.stdout.flush()

    [rcode, cout, cerr] = run_command(stop_prince_cmd)

    print("Killing olsr")
    sys.stdout.flush()
    stop_olsr_cmd = 'ansible-playbook stop-olsr.yaml ' +\
                    '--extra-vars ' +\
                    '"testbed=' + testbed + '"'

    if verbose:
        print(stop_olsr_cmd)
    sys.stdout.flush()

    [rcode, cout, cerr] = run_command(stop_olsr_cmd)

    print("Restore olsrd2 original configuration")
    sys.stdout.flush()
    restore_config_olsr_cmd = 'ansible-playbook ' +\
                              'restore-olsr-orig-config.yaml ' +\
                              '--extra-vars ' +\
                              '"testbed=' + testbed + '"'

    if verbose:
        print(restore_config_olsr_cmd)
    sys.stdout.flush()

    [rcode, cout, cerr] = run_command(restore_config_olsr_cmd)

    #######################################################################
    # Setup network interfaces
    print("Setting up network interfaces")
    setup_interfaces_cmd = 'ansible-playbook setup-interfaces.yaml ' +\
                           '--extra-vars ' +\
                           '"testbed=' + testbed + ' ' +\
                           'rate=' + str(legacyrate) + ' ' +\
                           'channel=' + str(channel) + ' ' +\
                           'power=' + str(txpower) + '"'

    if verbose:
        print(setup_interfaces_cmd)
    sys.stdout.flush()

    [rcode, cout, cerr] = run_command(setup_interfaces_cmd)

    # TODO: check for possible errors of setup_interfaces_cmd

    #######################################################################
    # Start olsrd
    print("Starting olsrd")
    sys.stdout.flush()
    start_olsr_cmd = 'ansible-playbook start-olsrv1.yaml ' +\
                     '--extra-vars ' +\
                     '"testbed=' + testbed + '"'

    if verbose:
        print(start_olsr_cmd)
    sys.stdout.flush()

    [rcode, cout, cerr] = run_command(start_olsr_cmd)

    # TODO: maybe here we should check that olsrd2 is really running on all
    # the nodes.

    #######################################################################
    # Wait for olsr convergence
    print("Sleep for 30 seconds...")
    sys.stdout.flush()
    time.sleep(30)
    print("Wait for olsr topology convergence...")
    current_graph, graph_stable = wait_for_stable_topology()

    #######################################################################
    # Save quasi-full-mesh graph
    quasi_full_mesh_graph_fn = expdir + '/quasi_full_mesh_graph.graphml'
    print('Saving stable graph without firewall rules: %s' %
          (quasi_full_mesh_graph_fn,))
    sys.stdout.flush()
    nx.write_graphml(current_graph, quasi_full_mesh_graph_fn)

    # if not graph_stable:
    #    probably we should rise an exception

    #######################################################################
    # Call the proper function based on the graph_type parameter
    # This function should return the string to pass to set-firewall-rules.yaml
    # nodes_rules = graph_type(current_graph)
    # nodes_rules = 'nuc0-20:nuc0-43,nuc0-21;nuc0-43:nuc0-20,nuc0-21'
    # nodes_rules = '10.1.0.20:10.1.0.43;10.1.0.43:10.1.0.20'
    nodes_rules, nodes_metrics, intervals, score =\
        reducetopology.get_firewall_rules(current_graph, graph_params,
                                          seed=metricsseed,
                                          olsrv1=True)

    #######################################################################
    # Deploy the actual firewall rules using set-firewall-rules.yaml
    # print("Setting firewall rules")
    # sys.stdout.flush()
    # firewall_cmd = 'ansible-playbook set-firewall-rules.yaml ' +\
    #                '--extra-vars ' +\
    #                '"testbed=' + testbed + ' ' +\
    #                'rules=' + nodes_rules + '"'

    # if verbose:
    #     print(firewall_cmd)
    # sys.stdout.flush()

    # [rcode, cout, cerr] = run_command(firewall_cmd)
    print("Firewall rules: %s" % (nodes_rules,))
    print("Constant metrics: %s" % (nodes_metrics,))

    return nodes_rules, nodes_metrics, intervals


verbose = False
strategy_functions = [
                    'stop_mostcentral_1s_repeat',
                    'stop_center_evenchain_1s_repeat',
                    'stop_one_random_node_1s',
                    'one_node_stop_1s_5mostcentral',
                    'stop_one_node_1s_loop',
                    'stop_one_random_node_1s_start_61s',
                    'one_node_stop_1s_start_61s_2mostcentral',
                    'two_node_stop_1s_start_61s_2mostcentral',
        ]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    allowed_channels_24ghz = range(1, 14)
    allowed_channels_5ghz = [36, 40, 44, 48, 52, 56, 60, 149, 153, 157, 161]
    parser.add_argument('--chan', dest='chan',
                        choices=allowed_channels_24ghz + allowed_channels_5ghz,
                        type=int, help='Channel',
                        required=True)
    parser.add_argument('--legacyrate', dest='legacyrate',
                        choices=[6, 9, 12, 18, 24, 36, 48, 54], type=int,
                        help='Transmission legacy rate', required=True)
    parser.add_argument('--txpower', dest='txpower', type=int,
                        choices=range(0, 3001), metavar='[1-3001]',
                        help='TX power in millibel-milliwatts (mBm) '
                             '(<power in mBm> = 100 * <power in dBm>)',
                        required=True)
    parser.add_argument('--killstrategy', dest='killstrategy',
                        choices=strategy_functions,
                        type=str,
                        help='Name of the strategy that must be used to '
                             'decide which nodes to kill and when to kill '
                             'them',
                             required=True)
    parser.add_argument('--graphparams', dest='graphparams',
                        type=str,
                        help='Graph type to create by deploying firewall '
                             'rules',
                        required=True)
    parser.add_argument('--testbed', dest='testbed',
                        choices=['twist', 'wilab'], type=str,
                        help='Specify in which testbed the experiment is going'
                             ' to be executed')
    parser.add_argument('--resultsdir', dest='resultsdir',
                        type=str,
                        help='Full path of the base directory where the '
                             'experiments results will be collected on the '
                             'ansible master node')
    parser.add_argument('--expname', dest='expname', type=str,
                        help='Name of the experiment used to create the'
                        ' output directory. WARNING: any existing directory'
                        ' with the same name will be destroyed. '
                        '(e.g., for w.ILabt '
                        '/proj/wall2-ilabt-iminds-be/exp/olsrprince1/)')
    parser.add_argument('--metricsseed', dest='metricsseed',
                        type=int,
                        help='Seed used to initialize the PRNG for extracting '
                             'the links constant metrics')
    parser.add_argument('--nrepeat', dest='nrepeat',
                        type=int,
                        help='How many times to repeat the selected kill '
                             'strategy. The kill strategy function can '
                             'ignore this parameter')
    parser.add_argument("--weights", dest="weights",
                        default=False, action="store_true")
    parser.add_argument("--fixedintervals", dest="fixedintervals",
                        default=False, action="store_true")
    parser.add_argument("-v", "--verbose", dest="verbose",
                        default=False, action="store_true")
    args = parser.parse_args()

    channel = args.chan
    legacyrate = args.legacyrate
    txpower = args.txpower
    killstrategy = args.killstrategy
    graphparams = args.graphparams
    testbed = args.testbed
    resultsdir = args.resultsdir
    expname = args.expname
    metricsseed = args.metricsseed
    nrepeat = args.nrepeat
    fixedintervals = args.fixedintervals
    weights = args.weights
    verbose = args.verbose

    print('Experiment configuration for testbed %s:' % (testbed,))
    print('Experiment name %s:' % (expname,))
    print('Network configuration: '
          'channel %d, rate %d, tx power %d, kill strategy %s' %
          (channel, legacyrate, txpower, killstrategy))
    print('graph params: %s (metrics seed %d)' % (graphparams, metricsseed))
    print('Kill strategy repetitions: %d' % (nrepeat,))

    #######################################################################
    # State variables initialization
    original_start_graph = None
    stop_strategy_list = None
    start_strategy_list = None
    strategy_idx = 0
    prince_running = False
    start_dumper_guard_time_seconds = 60
    stop_dumper_guard_time_seconds = 90
    homedir = expanduser("~")

    possibles = globals().copy()
    possibles.update(locals())
    strategy_func = possibles.get(killstrategy)

    create_directory(homedir + '/' + expname, testbed)

    #######################################################################
    # Deploy firewall rules
    nodes_rules, nodes_metrics, intervals =\
        preliminary_net_setup_for_firewall_rules_deployment(testbed,
                                                            legacyrate,
                                                            channel,
                                                            txpower,
                                                            graphparams,
                                                            metricsseed,
                                                            homedir + '/' +
                                                            expname)

    # Loop index
    while True:
        # This is the main loop that control the experiment
        # For each iteration the following steps are performed:
        # - Setup network interfaces by using the ansible-playbook
        #   setup-interfaces.yaml
        # - Start olsr by using the ansible-playbook start-olsr.yaml
        # - Start prince with the correcto configuration if we are in the
        #   second or third sub-interation.
        # - Waiting for the toplogy to be stable.
        # - Call the selected killing strategy that produces the sequence of
        #   nodes to be killed for each iteration
        # - Schedule topology_dumper and nodes death by using the
        #   olsr_experiment.yaml and kill_myself.yaml playbooks.
        # - Wait for the estimate end of the experiment
        # - Collect the results
        #

        #######################################################################
        # Kill olsrd2 and prince as a clean up procedure
        print("Killing prince")
        sys.stdout.flush()
        stop_prince_cmd = 'ansible-playbook stop-prince.yaml ' +\
                          '--extra-vars ' +\
                          '"testbed=' + testbed + '"'

        if verbose:
            print(stop_prince_cmd)
        sys.stdout.flush()

        [rcode, cout, cerr] = run_command(stop_prince_cmd)

        print("Killing olsr")
        sys.stdout.flush()
        stop_olsr_cmd = 'ansible-playbook stop-olsr.yaml ' +\
                        '--extra-vars ' +\
                        '"testbed=' + testbed + '"'

        if verbose:
            print(stop_olsr_cmd)
        sys.stdout.flush()

        [rcode, cout, cerr] = run_command(stop_olsr_cmd)

        #######################################################################
        # Flush firewall rules
        print("Flush firewall rules")
        sys.stdout.flush()
        flush_cmd = 'ansible-playbook flush-firewall-rules.yaml ' +\
                    '--extra-vars ' +\
                    '"testbed=' + testbed + '"'

        if verbose:
            print(flush_cmd)
        sys.stdout.flush()

        [rcode, cout, cerr] = run_command(flush_cmd)

        #######################################################################
        # Check if prince is required (prince_running == True)
        # TODO: Renato suggested to remove prince with heuristic because it
        # doesn't make any difference in small networks.
        #
        # For this reason right now we start prince with prince_conf_c.json

        prince_configuration_file = ''
        if prince_running:
            prince_configuration_file = 'prince_conf_c_olsrv1.json'
            prince_running = True

        #######################################################################
        # Create results directory for this loop iteration
        #
        # WARNING: here we are ssuming that even iterations run olsrd2 vanilla
        # and odd iterations run olsrd2 + prince (without heuristic)
        iter_results_dir_name = homedir + '/' + expname
        if prince_running:
            iter_results_dir_name += '/' +\
                                     str((strategy_idx)) +\
                                     '/prince'
        else:
            iter_results_dir_name += '/' +\
                                     str(strategy_idx) +\
                                     '/olsrd2_vanilla'

        create_directory(iter_results_dir_name, testbed)

        #######################################################################
        # Setup network interfaces
        print("Setting up network interfaces")
        setup_interfaces_cmd = 'ansible-playbook setup-interfaces.yaml ' +\
                               '--extra-vars ' +\
                               '"testbed=' + testbed + ' ' +\
                               'rate=' + str(legacyrate) + ' ' +\
                               'channel=' + str(channel) + ' ' +\
                               'power=' + str(txpower) + '"'

        if verbose:
            print(setup_interfaces_cmd)
        sys.stdout.flush()

        [rcode, cout, cerr] = run_command(setup_interfaces_cmd)

        # TODO: check for possible errors of setup_interfaces_cmd

        #######################################################################
        # Deploy the actual firewall rules using set-firewall-rules.yaml
        print("Setting firewall rules")
        sys.stdout.flush()
        firewall_cmd = 'ansible-playbook set-firewall-rules.yaml ' +\
                       '--extra-vars ' +\
                       '"testbed=' + testbed + ' ' +\
                       'rules=' + nodes_rules + '"'

        if verbose:
            print(firewall_cmd)
        sys.stdout.flush()

        [rcode, cout, cerr] = run_command(firewall_cmd)

        #######################################################################
        # Deploy the new olsrd configuration files with the constant
        # link metrics (and optionally tx and hello intervals
        print("Setting constant metrics")
        sys.stdout.flush()
        metrics_cmd = 'ansible-playbook set-constant-metrics-olsrv1.yaml ' +\
                      '--extra-vars ' +\
                      '"testbed=' + testbed

        if weights:
            metrics_cmd += ' metrics=' + nodes_metrics + '"'
        else:
            metrics_cmd += ' metrics=undefined"'

        if fixedintervals and prince_running:
            metrics_cmd = metrics_cmd.rstrip('"')
            metrics_cmd += ' intervals=' + intervals + '"'

        if verbose:
            print(metrics_cmd)
        sys.stdout.flush()

        [rcode, cout, cerr] = run_command(metrics_cmd)

        #######################################################################
        # Start olsrd
        print("Starting olsrd")
        sys.stdout.flush()
        start_olsr_cmd = 'ansible-playbook start-olsrv1.yaml ' +\
                         '--extra-vars ' +\
                         '"testbed=' + testbed + '"'

        if verbose:
            print(start_olsr_cmd)
        sys.stdout.flush()

        [rcode, cout, cerr] = run_command(start_olsr_cmd)

        # TODO: maybe here we should check that olsrd2 is really running on all
        # the nodes.

        #######################################################################
        # Wait for olsr convergence
        print("Sleep for 30 seconds...")
        sys.stdout.flush()
        time.sleep(30)
        print("Wait for olsr topology convergence...")
        current_start_graph, start_graph_stable = wait_for_stable_topology()

        #######################################################################
        # Save the starting graph
        current_start_graph_fn = iter_results_dir_name + '/start_graph.graphml'
        print('Saving current stable graph: %s' % (current_start_graph_fn,))
        sys.stdout.flush()
        nx.write_graphml(current_start_graph, current_start_graph_fn)

        with open(iter_results_dir_name + '/start_graph_stable', 'w') as of:
            if start_graph_stable:
                of.write('True')
            else:
                of.write('False')

        #######################################################################
        #  Check if original_start_graph is equals to current_start_graph
        if original_start_graph is None:
            original_start_graph = current_start_graph
        else:
            graph_changed = True
            nodes_original = original_start_graph.nodes()
            nodes_current = current_start_graph.nodes()

            # If current and previous graph have the same nodes
            if Counter(nodes_original) == Counter(nodes_current):
                graphs_diff1 = nx.difference(original_start_graph,
                                             current_start_graph)
                graphs_diff2 = nx.difference(current_start_graph,
                                             original_start_graph)

                # and if current and previous graph have the same edges
                if len(graphs_diff1.edges()) == 0 \
                   and len(graphs_diff2.edges()) == 0:
                    graph_changed = False

            if graph_changed:
                print("WARNING: current stable topology is different from the "
                      "original stable topology")
            else:
                print("Current stable topology is the same as original "
                      "stable topology")

        sys.stdout.flush()

        #######################################################################
        # Obtain the kill strategy
        if not prince_running:
            stop_strategy_list, start_strategy_list =\
                                    strategy_func(original_start_graph,
                                                  current_start_graph,
                                                  stop_strategy_list,
                                                  start_strategy_list,
                                                  strategy_idx,
                                                  nrepeat)

        if len(stop_strategy_list) != len(start_strategy_list):
            raise Exception('stop_strategy_list and start_strategy_list ' +
                            'have different lengths: %d != $d' %
                            (len(stop_strategy_list),
                             len(start_strategy_list)))

        print('Current strategies:')
        print('Stop: %s' % (stop_strategy_list[strategy_idx],))
        print('Start: %s' % (start_strategy_list[strategy_idx],))
        sys.stdout.flush()

        #######################################################################
        # Start prince if required

        if prince_configuration_file and not fixedintervals:
            print("Starting prince (%s)" % (prince_configuration_file,))
            sys.stdout.flush()
            start_prince_cmd = 'ansible-playbook start-prince.yaml ' +\
                               '--extra-vars ' +\
                               '"testbed=' + testbed + ' ' +\
                               'prince_log=' + iter_results_dir_name +\
                               '/prince.log ' +\
                               'prince_conf=' + prince_configuration_file + '"'

            if verbose:
                print(start_prince_cmd)
            sys.stdout.flush()

            [rcode, cout, cerr] = run_command(start_prince_cmd)
        else:
            print("Olsr will run without prince enabled")


        # Now the topology is stable. Let's kill prince for avoidind tc and
        # hello timets fluctuations
        if prince_configuration_file and not fixedintervals:
            print("Killing prince (TC and HELLO timers are fixed)")
            sys.stdout.flush()
            time.sleep(12)
            stop_prince_cmd = 'ansible-playbook stop-prince.yaml ' +\
                              '--extra-vars ' +\
                              '"testbed=' + testbed + '"'

            if verbose:
                print(stop_prince_cmd)
            sys.stdout.flush()

            [rcode, cout, cerr] = run_command(stop_prince_cmd)

        #######################################################################
        # Schedule topology_dumper
        stop_start_strategy_str = stop_strategy_list[strategy_idx]
        if start_strategy_list[strategy_idx]:
            stop_start_strategy_str += ',' + start_strategy_list[strategy_idx]

        dumper_start_time, dumper_stop_time = \
            compute_topology_dumper_times(stop_start_strategy_str,
                                          start_dumper_guard_time_seconds,
                                          stop_dumper_guard_time_seconds)

        print('Scheduling start/stop topology dumper')
        sched_topodump_cmd = 'ansible-playbook ' +\
                             'start-topology-dumper.yaml ' +\
                             '--extra-vars ' +\
                             '"testbed=' + testbed + ' ' +\
                             'start=' + str(dumper_start_time) + ' ' +\
                             'stop=' + str(dumper_stop_time) + ' ' +\
                             'prefix=' + expname + ' ' +\
                             'interval=' + '300' + ' ' +\
                             'version=1' + ' ' +\
                             'workdir=' + iter_results_dir_name + '"'

        if verbose:
            print(sched_topodump_cmd)
        sys.stdout.flush()

        [rcode, cout, cerr] = run_command(sched_topodump_cmd)

        #######################################################################
        # Schedule nodes stop
        print('Scheduling nodes stop')
        sys.stdout.flush()

        stop_strategy_converted_str = \
            convert_nodes_id_to_hostname(stop_strategy_list[strategy_idx])
        sched_stop_cmd = 'ansible-playbook ' +\
                         'kill-my-wifi-olsrv1.yaml ' +\
                         '--extra-vars ' +\
                         '"testbed=' + testbed + ' ' +\
                         'start=' + str(dumper_start_time) + ' ' +\
                         'nodes=' +\
                         stop_strategy_converted_str + '"'

        if verbose:
            print(sched_stop_cmd)
        sys.stdout.flush()

        [rcode, cout, cerr] = run_command(sched_stop_cmd)

        #######################################################################
        # Schedule nodes start
        if start_strategy_list[strategy_idx]:
            if fixedintervals:
                raise Exception('Node restart not supported with '
                                'fixed intervals')
            print('Scheduling nodes start')
            sys.stdout.flush()

            restart_prince_conf_file = "none"
            if prince_configuration_file:
                restart_prince_conf_file = prince_configuration_file

            start_strategy_converted_str = \
                convert_nodes_id_to_hostname(start_strategy_list[strategy_idx])
            sched_start_cmd = 'ansible-playbook ' +\
                              'restart-my-wifi-olsrv1.yaml ' +\
                              '--extra-vars ' +\
                              '"testbed=' + testbed + ' ' +\
                              'rate=' + str(legacyrate) + ' ' +\
                              'channel=' + str(channel) + ' ' +\
                              'power=' + str(txpower) + ' ' +\
                              'prince_conf=' + \
                              restart_prince_conf_file + ' ' +\
                              'start=' + str(dumper_start_time) + ' ' +\
                              'nodes=' + start_strategy_converted_str + '"'

            if verbose:
                print(sched_start_cmd)
            sys.stdout.flush()

            [rcode, cout, cerr] = run_command(sched_start_cmd)
        else:
            print('Current strategy does not require to restart any node')
            sys.stdout.flush()

        #######################################################################
        # Wait end of experiment
        seconds_before_exp_ends = dumper_stop_time - time.time()
        print('Sleeping for %s seconds' % (seconds_before_exp_ends,))
        sys.stdout.flush()
        time.sleep(seconds_before_exp_ends)

        with open(iter_results_dir_name + '/strategies', 'w') as of:
            of.write(stop_strategy_list[strategy_idx])
            of.write('\n')

        if prince_running:
            strategy_idx += 1

        if strategy_idx == len(stop_strategy_list):
            break

        if prince_running:
            prince_running = False
        else:
            prince_running = True

    #######################################################################
    # Collect results on master node
    print('Collecting results on master node')
    sys.stdout.flush()

    sched_fetch_cmd = 'ansible-playbook ' +\
                      'collect-olsr-results.yaml ' +\
                      '--extra-vars ' +\
                      '"testbed=' + testbed + ' ' +\
                      'rootdirname=' + resultsdir + ' ' +\
                      'expname=' + expname + '"'

    if verbose:
        print(sched_fetch_cmd)
    sys.stdout.flush()

    [rcode, cout, cerr] = run_command(sched_fetch_cmd)
