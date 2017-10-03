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
import os
import sys
import inspect
import json
import shutil
import networkx as nx
currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from olsr import OlsrParser # noqa


class RoutingTable:
    '''
    This class represents a single routing table of a node
    '''

    def __init__(self, idx, ts, rt_json, node_name):
        self.idx = idx
        self.ts = ts
        self.rt_json = rt_json
        self.node_name = node_name

    def get_rt_json(self):
        return self.rt_json

    def get_ts_s_ms(self):
        return (self.idx, self.ts)

    def get_nh_for_dst(self, dst_node_id):
        '''
        Returns the next hope node id (<ip>)
        '''
        if not self.rt_json:
            return None

        # dst_ip = dst_node_id.replace('id_', '')
        dst_ip = dst_node_id

        for r in self.rt_json['routes']:
            dst = r['destination']
            if dst == dst_ip:
                nh_ip = r['gateway']
                if nh_ip == '-':
                    return dst_node_id
                else:
                    return nh_ip

        return None


class Topology:
    '''
    This class represents a single olsrd2 topology
    '''

    def __init__(self, idx, ts, topo_json, topo_g, node_name):
        self.idx = idx
        self.ts = ts
        self.topo_json = topo_json
        self.topo_g = topo_g
        self.node_name = node_name

    def get_topo_json(self):
        return self.topo_json

    def get_topo_g(self):
        return self.topo_g

    def get_ts_s_ms(self):
        return (self.idx, self.ts)


class Intervals:
    '''
    This class represents the pair of (hello, tc) intervals
    '''

    def __init__(self, idx, ts, hello_int, tc_int, node_name):
        self.idx = idx
        self.ts = ts
        self.hello_int = hello_int
        self.tc_int = tc_int
        self.node_name = node_name

    def get_hello_interval(self):
        return self.hello_int

    def get_tc_interval(self):
        return self.tc_int

    def get_ts_s_ms(self):
        return (self.idx, self.ts)


class OlsrPrinceExp:
    '''
    This class represents a single experiment (vanilla olsr or olsr+prince)
    '''

    def __init__(self, expname, expdir, strategy_idx, nodes_names_list,
                 master_node_name, highest_res_idx, typedir='olsrd2_vanilla'):
        self.exp_name = expname
        self.exp_base_dir_name_str = expdir
        self.nodes_names_list = nodes_names_list
        self.master_node_name = master_node_name
        self.highest_res_index = highest_res_idx
        self.strategy_idx = strategy_idx
        self.type_dir = typedir
        # node_name: {rt_list, intervals_list, topo_list)
        self.nodes_exp_data_dict = {}
        # keeps the desynchronization in seconds based on topologies results
        # at idx 0
        self.topo_desync_idx0 = 0
        # each element: (tot_route, broken_routes, loop_routes)
        self.routes_results_summary = []
        # one dict for each result index
        # src_id_dst_id: [src_id, id2,..., dst_id]
        self.paths_list = []

    def load_experiment_data(self):
        for node_name in self.nodes_names_list:
            print('Loading experiment data for node %s (%s, %s)' %
                  (node_name, self.type_dir, self.strategy_idx))
            results_dir = self.exp_base_dir_name_str + '/' + node_name +\
                '_' + self.exp_name + '/' + self.strategy_idx +\
                '/' + self.type_dir

            if os.path.isdir(results_dir):
                print(results_dir)

            print('Loading routing tables')
            rt_list = self.load_routing_tables(node_name, results_dir)
            intervals_list = self.load_intervals(node_name, results_dir)
            if node_name == self.master_node_name:
                topo_list = self.load_topologies(node_name, results_dir)
            else:
                topo_list = None
            self.nodes_exp_data_dict[node_name] = (rt_list,
                                                   intervals_list,
                                                   topo_list)

    def load_routing_tables(self, node_name, result_dir):
        rt_list = []
        route_files_list = []
        for root, dirs, files in os.walk(result_dir):
            for file_name in files:
                # if file_name.endswith('.pyroute'):
                if file_name.endswith('.route'):
                    route_files_list.append(file_name)

        route_files_list.sort()
        last_rt_json = None
        for res_idx in range(0, self.highest_res_index + 1):
            res_idx_str = '%06d' % (res_idx,)
            file_prefix = self.exp_name + '_' + node_name + '_' +\
                res_idx_str
            file_exist_name = ''
            for file_name in route_files_list:
                if file_name.startswith(file_prefix):
                    file_exist_name = file_name
                    break

            if res_idx == 0 and not file_exist_name:
                raise Exception('Results file for index 0 does not exist')

            if file_exist_name:
                res_timestamp = file_exist_name.split('.')[0]
                res_timestamp = res_timestamp.split(res_idx_str)[1]
                res_seconds = res_timestamp.split('_')[1]
                res_milliseconds = res_timestamp.split('_')[2]
                ts = float("%s.%s" % (res_seconds, res_milliseconds))

                rt_json = None
                file_exist_path = result_dir + '/' + file_exist_name
                # print(file_exist_path)
                with open(file_exist_path, 'r') as data_file:
                    file_content = data_file.read()
                    if not file_content:
                        rt_json = None
                    else:
                        rt_json = json.loads(file_content)

                rt = RoutingTable(res_idx, ts, rt_json, node_name)
                rt_list.append(rt)

                last_rt_json = rt_json
            else:
                rt = RoutingTable(res_idx, 0, last_rt_json, node_name)
                rt_list.append(rt)

        return rt_list

    def load_topologies(self, node_name, result_dir):
        topo_list = []
        topo_files_list = []
        for root, dirs, files in os.walk(result_dir):
            for file_name in files:
                if file_name.endswith('.topo'):
                    topo_files_list.append(file_name)

        topo_files_list.sort()
        last_topo_json = None
        last_topo_g = None
        for res_idx in range(0, self.highest_res_index + 1):
            res_idx_str = '%06d' % (res_idx,)
            file_prefix = self.exp_name + '_' + node_name + '_' +\
                res_idx_str
            file_exist_name = ''
            for file_name in topo_files_list:
                if file_name.startswith(file_prefix):
                    file_exist_name = file_name
                    break

            if res_idx == 0 and not file_exist_name:
                raise Exception('Results file fo index 0 does not exist')

            if file_exist_name:
                res_timestamp = file_exist_name.split('.')[0]
                res_timestamp = res_timestamp.split(res_idx_str)[1]
                res_seconds = res_timestamp.split('_')[1]
                res_milliseconds = res_timestamp.split('_')[2]
                ts = float("%s.%s" % (res_seconds, res_milliseconds))

                topo_json = None
                topo_g = None
                file_exist_path = result_dir + '/' + file_exist_name
                # print(file_exist_path)
                with open(file_exist_path, 'r') as data_file:
                    file_content = data_file.read()
                    if not file_content:
                        topo_json = None
                    else:
                        topo_json = json.loads(file_content)

                if topo_json:
                    topo_g = OlsrParser(file=file_exist_path).graph
                else:
                    topo_g = None

                topo = Topology(res_idx, ts, topo_json, topo_g, node_name)
                topo_list.append(topo)

                last_topo_json = topo_json
                last_topo_g = topo_g
            else:
                topo = Topology(res_idx, 0, last_topo_json,
                                last_topo_g, node_name)
                topo_list.append(topo)

        return topo_list

    def load_intervals(self, node_name, result_dir):
        intervals_list = []
        intervals_files_list = []
        for root, dirs, files in os.walk(result_dir):
            for file_name in files:
                if file_name.endswith('.int'):
                    intervals_files_list.append(file_name)

        intervals_files_list.sort()
        last_tc_int = -1
        last_hello_int = -1
        for res_idx in range(0, self.highest_res_index + 1):
            res_idx_str = '%06d' % (res_idx,)
            file_prefix = self.exp_name + '_' + node_name + '_' +\
                res_idx_str
            file_exist_name = ''
            for file_name in intervals_files_list:
                if file_name.startswith(file_prefix):
                    file_exist_name = file_name
                    break

            if res_idx == 0 and not file_exist_name:
                raise Exception('Results file fo index 0 does not exist')

            if file_exist_name:
                res_timestamp = file_exist_name.split('.')[0]
                res_timestamp = res_timestamp.split(res_idx_str)[1]
                res_seconds = res_timestamp.split('_')[1]
                res_milliseconds = res_timestamp.split('_')[2]
                ts = float("%s.%s" % (res_seconds, res_milliseconds))

                tc_int = -1
                hello_int = -1
                file_exist_path = result_dir + '/' + file_exist_name
                # print(file_exist_path)
                with open(file_exist_path, 'r') as data_file:
                    file_lines = data_file.readlines()
                    if not file_lines:
                        tc_int = -1
                        hello_int = -1
                    else:
                        for line in file_lines:
                            if 'hello' in line:
                                hello_int = float(line.split(':')[1])
                            elif 'tc' in line:
                                tc_int = float(line.split(':')[1])
                            else:
                                print('WARNING: .int file does contain an '
                                      'unknown line')

                interval = Intervals(res_idx, ts, hello_int, tc_int, node_name)
                intervals_list.append(interval)

                last_hello_int = hello_int
                last_tc_int = tc_int
            else:
                interval = Intervals(res_idx, 0, last_hello_int,
                                     last_tc_int, node_name)
                intervals_list.append(interval)

        return intervals_list

    def get_node_topologies(self, node_name):
        return self.nodes_exp_data_dict[node_name][2]

    def get_killed_nodes_and_times(self):
        '''
        Return a dictionary whose keys are the nodes that are killed during an
        experiment and the values are tuples containing (index, ts)
        '''
        killed_nodes_dict = {}
        for node_name in self.nodes_exp_data_dict.keys():
            rt_list = self.nodes_exp_data_dict[node_name][0]
            for rt in rt_list:
                rt_json = rt.get_rt_json()
                if not rt_json:
                    killed_nodes_dict[node_name] = rt.get_ts_s_ms()
                    break

        return killed_nodes_dict

    def compute_desynchronization_rt_at_idx0(self):
        times_at_idx0_list = []
        for node_name in self.nodes_names_list:
            rt = self.nodes_exp_data_dict[node_name][0]
            idx, ts = rt[0].get_ts_s_ms()
            times_at_idx0_list.append(ts)

        self.topo_desync_idx0 = abs(min(times_at_idx0_list) -
                                    max(times_at_idx0_list))

    def get_desynchronization_rt_at_idx0(self):
        return self.topo_desync_idx0

    def navigate_routing_tables(self, nodes_names_to_id_dict, killed_nodes):
        '''
        killed_nodes is a dictionary node_name: (idx, ts)
        '''
        # for every result index we keep a tuple (tot_routes, broken_routes and
        # loop_routes).
        # print(killed_nodes)
        self.paths_list = [{}] * (self.highest_res_index + 1)
        routes_results_summary = []
        last_tot_r_ctr = 0
        last_brk_r_ctr = 0
        last_loop_r_ctr = 0
        last_paths_dict = {}
        for res_idx in range(0, self.highest_res_index + 1):
            # check if routing tables chaged wrt the previous res_idx
            # print(res_idx)
            rts_changed = False
            for tmp_node_name in self.nodes_names_list:
                tmp_ts = self.nodes_exp_data_dict[
                    tmp_node_name][0][res_idx].get_ts_s_ms()
                if tmp_ts[1] != 0:
                    rts_changed = True
                    # print("CHANGED %s" % (tmp_node_name,))
                    break

            if not rts_changed:
                routes_results_summary.append((last_tot_r_ctr,
                                               last_brk_r_ctr,
                                               last_loop_r_ctr))
                self.paths_list[res_idx] = last_paths_dict
                continue

            # print("INDEX %d" % (res_idx,))
            tot_r_ctr = 0
            brk_r_ctr = 0
            loop_r_ctr = 0
            paths_dict = {}
            for src_node_name in self.nodes_names_list:
                src_node_id = nodes_names_to_id_dict[src_node_name]
                for dst_node_name in self.nodes_names_list:
                    if src_node_name == dst_node_name:
                        continue

                    if src_node_name in killed_nodes.keys():
                        if killed_nodes[src_node_name][0] <= res_idx:
                            # Dead node cannot be a route source
                            continue

                    if dst_node_name in killed_nodes.keys():
                        if killed_nodes[dst_node_name][0] <= res_idx:
                            # Dead node cannot be a destination
                            continue

                    tot_r_ctr += 1

                    dst_node_id = nodes_names_to_id_dict[dst_node_name]

                    # print("src: %s (%s), dst: %s (%s)" % (src_node_name,
                    #                                       src_node_id,
                    #                                       dst_node_name,
                    #                                       dst_node_id))

                    cur_node_name = ''
                    nh_node_id = ''
                    route_ids_list = []
                    save_route_ids_list = True
                    while True:

                        if not cur_node_name:
                            cur_node_name = src_node_name
                            route_ids_list.append(src_node_id)
                        else:
                            for node_name in nodes_names_to_id_dict:
                                node_id = nodes_names_to_id_dict[node_name]
                                if node_id == nh_node_id:
                                    cur_node_name = node_name
                                    break

                            route_ids_list.append(nh_node_id)

                        # if cur_node_name in killed_nodes.keys():
                        #     print(cur_node_name)

                        # print(cur_node_name)
                        cur_rt = self.nodes_exp_data_dict[
                            cur_node_name][0][res_idx]
                        nh_node_id = cur_rt.get_nh_for_dst(dst_node_id)
                        # print(nh_node_id)

                        if not nh_node_id:
                            # Broken route
                            # cur_node_name does not have dst_node_id in its
                            # routing table
                            if (cur_node_name == src_node_name
                               and (cur_node_name not in killed_nodes.keys()
                                or (cur_node_name in killed_nodes.keys()
                                and killed_nodes[cur_node_name][0] > res_idx))
                                and dst_node_name in killed_nodes.keys() and
                                    killed_nodes[dst_node_name][0] <= res_idx):
                                tot_r_ctr -= 1
                                save_route_ids_list = False
                                break

                            brk_r_ctr += 1
                            # print(cur_node_name, route_ids_list[-1])
                            break

                        # print(nh_node_id)
                        # print(route_ids_list)

                        if nh_node_id == dst_node_id:
                            # route complete
                            # we must check if the destination node is dead
                            # at this res_idx
                            if dst_node_name in killed_nodes.keys() and\
                              killed_nodes[dst_node_name][0] <= res_idx:
                                # Broken route
                                brk_r_ctr += 1
                            else:
                                route_ids_list.append(dst_node_id)
                            break

                        if nh_node_id in route_ids_list:
                            # Loop route
                            # we already traverse nh_node_id
                            loop_r_ctr += 1
                            break

                    if save_route_ids_list:
                        paths_dict[src_node_id + '-' + dst_node_id] =\
                            route_ids_list

            last_tot_r_ctr = tot_r_ctr
            last_brk_r_ctr = brk_r_ctr
            last_loop_r_ctr = loop_r_ctr
            last_paths_dict = paths_dict
            routes_results_summary.append((tot_r_ctr, brk_r_ctr, loop_r_ctr))
            self.paths_list[res_idx] = paths_dict

        self.routes_results_summary = routes_results_summary

    def get_routes_results_summary(self):
        return self.routes_results_summary

    def get_paths_list(self):
        return self.paths_list


class OlsrPrinceAnalyzer:

    def __init__(self, expname, expdir, summarydir, verbose=False):
        self.exp_name = expname
        self.exp_base_dir_name_str = expdir
        self.summary_dir = summarydir
        self.verbose = verbose
        # for each strategy index we have a tuple of two experiments:
        # 'olsrd2_vanilla' and 'prince'
        self.strategy_exps_dict = {}
        # Map node names to corresponding IDs used by olsrd2
        self.nodes_names_to_id_dict = {}
        self.killed_nodes_olsrd2_vanilla_dict = {}
        self.killed_nodes_prince_dict = {}
        self.desync_idx0_olsrd2_vanilla_dict = {}
        self.desync_idx0_prince_dict = {}
        self.olsrd2_vanilla_routes_results_summary_dict = {}
        self.prince_routes_results_summary_dict = {}

        # strategy: (start_graph, graph_idx0, graph_idx_last)
        self.master_start_end_graphs_olsrd2_vanilla_dict = {}
        self.master_start_end_graphs_prince_dict = {}

    def initialize(self):
        # find the names of all the nodes involved in the experiment
        self.nodes_name_list = self.get_name_all_nodes()
        self.nodes_names_to_id_dict = self.compute_node_name_to_id_dict()
        print('Nodes involved in the experiment:')
        for node_name in self.nodes_name_list:
            print(node_name, self.nodes_names_to_id_dict[node_name])

        # find the name of the master node
        self.master_node_name = self.find_master_node()
        print('Master node name: %s' % (self.master_node_name,))

        # find highest result index
        self.highest_res_index = self.find_highest_result_file_index()
        print('Highest results index: %d' % (self.highest_res_index,))

        # find the strategies directories names (0, 1, 2,...)
        self.strategies_dir_names_list = self.get_strategies_dir_names()
        print('#Kill strategies: %d' % (len(self.strategies_dir_names_list),))

        # Load experiment data for each strategy directory
        for strategy in self.strategies_dir_names_list:
            olsrd2_vanilla_exp = OlsrPrinceExp(self.exp_name,
                                               self.exp_base_dir_name_str,
                                               strategy,
                                               self.nodes_name_list,
                                               self.master_node_name,
                                               self.highest_res_index,
                                               'olsrd2_vanilla')
            olsrd2_vanilla_exp.load_experiment_data()
            olsrd2_vanilla_exp.compute_desynchronization_rt_at_idx0()
            self.desync_idx0_olsrd2_vanilla_dict[strategy] =\
                olsrd2_vanilla_exp.get_desynchronization_rt_at_idx0()

            print('Routing tables desynchronization at idx 0 for '
                  'olsrd2_vanilla : %fs' %
                  (self.desync_idx0_olsrd2_vanilla_dict[strategy]))

            prince_exp = OlsrPrinceExp(self.exp_name,
                                       self.exp_base_dir_name_str,
                                       strategy,
                                       self.nodes_name_list,
                                       self.master_node_name,
                                       self.highest_res_index,
                                       'prince')
            prince_exp.load_experiment_data()
            prince_exp.compute_desynchronization_rt_at_idx0()
            self.desync_idx0_prince_dict[strategy] =\
                prince_exp.get_desynchronization_rt_at_idx0()

            print('Routing tables desynchronization at idx 0 for ' +
                  'prince : %fs' %
                  (self.desync_idx0_prince_dict[strategy]))

            self.strategy_exps_dict[strategy] = (olsrd2_vanilla_exp,
                                                 prince_exp)

            self.killed_nodes_olsrd2_vanilla_dict[strategy] =\
                self.strategy_exps_dict[
                    strategy][0].get_killed_nodes_and_times()
            print("Killed nodes for olsrd2_vanilla (idx, ts):")
            for node_name\
                    in self.killed_nodes_olsrd2_vanilla_dict[strategy].keys():
                node_killed_ts =\
                    self.killed_nodes_olsrd2_vanilla_dict[strategy][node_name]
                print("%s: %d %f" % (node_name,
                                     node_killed_ts[0],
                                     node_killed_ts[1]))

            self.killed_nodes_prince_dict[strategy] = self.strategy_exps_dict[
                strategy][1].get_killed_nodes_and_times()
            print("Killed nodes for prince (idx, ts):")
            for node_name in self.killed_nodes_prince_dict[strategy].keys():
                node_killed_ts =\
                    self.killed_nodes_prince_dict[strategy][node_name]
                print("%s: %d %f" % (node_name,
                                     node_killed_ts[0],
                                     node_killed_ts[1]))

            self.load_master_start_end_graphs(strategy,
                                              olsrd2_vanilla_exp,
                                              prince_exp)

        # For each strategy navigate the routing table and compute the broken
        # routes and the loops (both for olsrd2_vanilla and prince)
        for strategy in self.strategies_dir_names_list:
            # olsrd2_vanilla
            print("Navigating routing tables for olsrd2_vanilla (strategy %s)"
                  % (strategy,))
            self.strategy_exps_dict[
                strategy][
                0].navigate_routing_tables(
                    self.nodes_names_to_id_dict,
                    self.killed_nodes_olsrd2_vanilla_dict[strategy])

            self.olsrd2_vanilla_routes_results_summary_dict[strategy] =\
                self.strategy_exps_dict[strategy][
                    0].get_routes_results_summary()

            # prince
            print("Navigating routing tables for prince (strategy %s)"
                  % (strategy,))
            self.strategy_exps_dict[strategy][
                    1].navigate_routing_tables(
                        self.nodes_names_to_id_dict,
                        self.killed_nodes_prince_dict[strategy])

            self.prince_routes_results_summary_dict[strategy] =\
                self.strategy_exps_dict[strategy][
                    1].get_routes_results_summary()

    def get_lcost_float(self, lcost_str):
        if lcost_str.startswith('0x'):
            return float(int(lcost_str, 16))
        else:
            if lcost_str.endswith('k'):
                return float(lcost_str.replace('k', '')) * 1000
            else:
                return float(lcost_str)

    def load_master_start_end_graphs(self, strategy,
                                     olsrd2_vanilla_exp,
                                     prince_exp):
        '''
        return a tuple of three elements: (start_graph, graph_idx0,
        graph_last_idx)
        '''
        master_dir = self.exp_base_dir_name_str + '/' +\
            self.master_node_name + '_' + self.exp_name +\
            '/' + strategy
        olsrd2_vanilla_dir = master_dir + '/olsrd2_vanilla'
        prince_dir = master_dir + '/prince'

        olsrd2_vanilla_start_graph = nx.read_graphml(olsrd2_vanilla_dir +
                                                     '/start_graph.graphml')
        prince_start_graph = nx.read_graphml(prince_dir +
                                             '/start_graph.graphml')

        olsrd2_vanilla_master_topos =\
            olsrd2_vanilla_exp.get_node_topologies(self.master_node_name)
        prince_master_topos =\
            prince_exp.get_node_topologies(self.master_node_name)

        olsrd2_vanilla_graph_idx0 =\
            olsrd2_vanilla_master_topos[0].get_topo_g()
        olsrd2_vanilla_graph_idxend =\
            olsrd2_vanilla_master_topos[-1].get_topo_g()

        prince_graph_idx0 =\
            prince_master_topos[0].get_topo_g()
        prince_graph_idxend =\
            prince_master_topos[-1].get_topo_g()

        self.master_start_end_graphs_olsrd2_vanilla_dict[strategy] =\
            (olsrd2_vanilla_start_graph,
             olsrd2_vanilla_graph_idx0,
             olsrd2_vanilla_graph_idxend)

        self.master_start_end_graphs_prince_dict[strategy] =\
            (prince_start_graph,
             prince_graph_idx0,
             prince_graph_idxend)

    def compute_node_name_to_id_dict(self):
        # Use the etchost file to create a dictionary that maps the nodes names
        # to the corresponding ids
        node_names_to_id_dict = {}
        with open('etchosts', 'r') as hosts_file:
            for line in hosts_file.readlines():
                node_name = line.split(' ')[1].replace('pop-', '').rstrip()
                node_id = line.split(' ')[0]
                node_names_to_id_dict[node_name] = node_id

        return node_names_to_id_dict

    def get_name_all_nodes(self):
        '''Return a list with the names of all the nodes involved in the
        experiment'''
        nodes_name_list = []
        for d in os.listdir(self.exp_base_dir_name_str):
            if os.path.isdir(self.exp_base_dir_name_str + '/' + d):
                nodes_name_list.append(d.split('_')[0])

        return nodes_name_list

    def find_master_node(self):
        '''
        Look for the master node: we suppose that a node is the master node
        if the file ${nodedir}/0/olsrd2_vanilla/start_graph.graphml exists.

        Return None if the method fails in finding the master node
        '''
        if not self.nodes_name_list:
            return None

        for node_name in self.nodes_name_list:
            file_path_name = self.exp_base_dir_name_str + '/' +\
                             node_name + '_' + self.exp_name +\
                             '/0/olsrd2_vanilla/start_graph.graphml'
            if os.path.exists(file_path_name):
                return node_name

        return None

    def find_highest_result_file_index(self):
        '''
        Parses the name of all the results files for finding the highest
        result index. Results files have the following format:
        <exp_name>_<node_name>_<index>_<s>_<ms>.{int,topo.route}

        Return -1 if self.nodes_name_list is None or the highest result index
        otherwise
        '''

        if not self.nodes_name_list:
            return -1

        highest_index = -1

        for root, dirs, files in os.walk(self.exp_base_dir_name_str):
            for file in files:
                if file.endswith(('.int', '.topo', '.route')):
                    # extract index from file name
                    index = int(file.split(self.exp_name)[1].split('_')[2])
                    if index > highest_index:
                        highest_index = index

        return highest_index

    def get_strategies_dir_names(self):
        '''
        Returns the list of strategies directories names. We use the master
        node result directory for finding the strategies directories
        '''

        if not self.master_node_name:
            return None

        strategies_dir_names_list = []
        master_node_dir_name = self.exp_base_dir_name_str +\
            '/' + self.master_node_name + '_' + self.exp_name

        for d in os.listdir(master_node_dir_name):
            if os.path.isdir(master_node_dir_name + '/' + d):
                strategies_dir_names_list.append(d)

        return strategies_dir_names_list

    def save_routes_summary(self):
        for strategy in self.strategies_dir_names_list:
            strategy_dir = self.summary_dir + '/' + strategy
            olsrd2_vanilla_dir = strategy_dir + '/olsrd2_vanilla'
            prince_dir = strategy_dir + '/prince'

            with open(olsrd2_vanilla_dir + '/routes_summary', 'w') as of:
                summary_list =\
                    self.olsrd2_vanilla_routes_results_summary_dict[strategy]
                for tot, brk, loop in summary_list:
                    of.write('%d %d %d\n' % (tot, brk, loop))

            with open(prince_dir + '/routes_summary', 'w') as of:
                summary_list =\
                    self.prince_routes_results_summary_dict[strategy]
                for tot, brk, loop in summary_list:
                    of.write('%d %d %d\n' % (tot, brk, loop))

    def save_killed_nodes_and_times(self):
        for strategy in self.strategies_dir_names_list:
            strategy_dir = self.summary_dir + '/' + strategy
            olsrd2_vanilla_dir = strategy_dir + '/olsrd2_vanilla'
            prince_dir = strategy_dir + '/prince'

            with open(olsrd2_vanilla_dir +
                      '/killed_nodes_and_times', 'w') as of:
                killed_nodes_dict =\
                    self.killed_nodes_olsrd2_vanilla_dict[strategy]
                for node_name in killed_nodes_dict.keys():
                    idx, ts = killed_nodes_dict[node_name]
                    of.write('%s,%d,%.3f\n' % (node_name, idx, ts))

            with open(prince_dir +
                      '/killed_nodes_and_times', 'w') as of:
                killed_nodes_dict =\
                    self.killed_nodes_prince_dict[strategy]
                for node_name in killed_nodes_dict.keys():
                    idx, ts = killed_nodes_dict[node_name]
                    of.write('%s,%d,%.3f\n' % (node_name, idx, ts))

    def save_desync_idx0(self):
        for strategy in self.strategies_dir_names_list:
            strategy_dir = self.summary_dir + '/' + strategy
            olsrd2_vanilla_dir = strategy_dir + '/olsrd2_vanilla'
            prince_dir = strategy_dir + '/prince'

            with open(olsrd2_vanilla_dir + '/desync_idx0', 'w') as of:
                desync_s = self.desync_idx0_olsrd2_vanilla_dict[strategy]
                of.write('%.4fs' % (desync_s,))

            with open(prince_dir + '/desync_idx0', 'w') as of:
                desync_s = self.desync_idx0_prince_dict[strategy]
                of.write('%.4fs' % (desync_s,))

    def save_graphs(self):
        for strategy in self.strategies_dir_names_list:
            strategy_dir = self.summary_dir + '/' + strategy
            olsrd2_vanilla_dir = strategy_dir + '/olsrd2_vanilla'
            prince_dir = strategy_dir + '/prince'

            nx.write_graphml(self.master_start_end_graphs_olsrd2_vanilla_dict[
                             strategy][0],
                             olsrd2_vanilla_dir + '/start_graph.graphml')
            nx.write_graphml(self.master_start_end_graphs_olsrd2_vanilla_dict[
                             strategy][1],
                             olsrd2_vanilla_dir + '/graph_idx0.graphml')
            nx.write_graphml(self.master_start_end_graphs_olsrd2_vanilla_dict[
                             strategy][2],
                             olsrd2_vanilla_dir + '/graph_idxend.graphml')

            nx.write_graphml(self.master_start_end_graphs_prince_dict[
                             strategy][0],
                             prince_dir + '/start_graph.graphml')
            nx.write_graphml(self.master_start_end_graphs_prince_dict[
                             strategy][1],
                             prince_dir + '/graph_idx0.graphml')
            nx.write_graphml(self.master_start_end_graphs_prince_dict[
                             strategy][2],
                             prince_dir + '/graph_idxend.graphml')

    def save_paths(self):
        for strategy in self.strategies_dir_names_list:
            strategy_dir = self.summary_dir + '/' + strategy
            olsrd2_vanilla_dir = strategy_dir + '/olsrd2_vanilla'
            prince_dir = strategy_dir + '/prince'
            olsrd2_vanilla_paths_list =\
                self.strategy_exps_dict[strategy][0].get_paths_list()
            prince_paths_list =\
                self.strategy_exps_dict[strategy][1].get_paths_list()

            with open(olsrd2_vanilla_dir + '/paths_idx0', 'w') as of:
                paths_idx0 = olsrd2_vanilla_paths_list[0]
                for path_id in paths_idx0.keys():
                    of.write('%s:' % (path_id,))
                    for i, hop in enumerate(paths_idx0[path_id]):
                        of.write('%s' % (hop,))
                        if i == (len(paths_idx0[path_id]) - 1):
                            of.write('\n')
                        else:
                            of.write(',')

            with open(olsrd2_vanilla_dir + '/paths_idxend', 'w') as of:
                paths_idxend = olsrd2_vanilla_paths_list[-1]
                for path_id in paths_idxend.keys():
                    of.write('%s:' % (path_id,))
                    for i, hop in enumerate(paths_idxend[path_id]):
                        of.write('%s' % (hop,))
                        if i == (len(paths_idxend[path_id]) - 1):
                            of.write('\n')
                        else:
                            of.write(',')

            with open(prince_dir + '/paths_idx0', 'w') as of:
                paths_idx0 = prince_paths_list[0]
                for path_id in paths_idx0.keys():
                    of.write('%s:' % (path_id,))
                    for i, hop in enumerate(paths_idx0[path_id]):
                        of.write('%s' % (hop,))
                        if i == (len(paths_idx0[path_id]) - 1):
                            of.write('\n')
                        else:
                            of.write(',')

            with open(prince_dir + '/paths_idxend', 'w') as of:
                paths_idxend = prince_paths_list[-1]
                for path_id in paths_idxend.keys():
                    of.write('%s:' % (path_id,))
                    for i, hop in enumerate(paths_idxend[path_id]):
                        of.write('%s' % (hop,))
                        if i == (len(paths_idxend[path_id]) - 1):
                            of.write('\n')
                        else:
                            of.write(',')

    def save_results_summary(self):
        if os.path.isdir(self.summary_dir):
            shutil.rmtree(self.summary_dir)

        os.mkdir(self.summary_dir)
        print('Saving results in %s' % (self.summary_dir,))

        for strategy in self.strategies_dir_names_list:
            strategy_dir = self.summary_dir + '/' + strategy
            olsrd2_vanilla_dir = strategy_dir + '/olsrd2_vanilla'
            prince_dir = strategy_dir + '/prince'

            os.mkdir(strategy_dir)
            os.mkdir(olsrd2_vanilla_dir)
            os.mkdir(prince_dir)

        self.save_routes_summary()
        self.save_killed_nodes_and_times()
        self.save_desync_idx0()
        self.save_graphs()
        self.save_paths()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--expname', dest='expname', type=str,
                        help='''Name of the experiment. This parameter is used
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
                        '_' character). Inside the directory of a node there
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
    expdir = resultsbdir + '/' + expname + '_results'
    summarydir = resultsbdir + '/' + expname + '_summary'

    # Check if expriment directoy exists
    if not os.path.isdir(expdir):
        print('ERROR: directory %s does not exist' % (expdir))
        sys.exit(-1)

    print('Analysing experiment %s' % (expname,))
    print('Experiment directory: %s' % (expdir,))

    exp_analyzer = OlsrPrinceAnalyzer(expname, expdir,
                                      summarydir, verbose=verbose)
    exp_analyzer.initialize()
    exp_analyzer.save_results_summary()
