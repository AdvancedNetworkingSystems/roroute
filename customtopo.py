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


def line_diamond_graph(n):
    """
    Generate a line diamond graph with n nodes, i.e., with the following
    topology:
                _ 7 _
               /     \
    0 -- 1 -- 2      4 -- 5 -- 6
               \_ 3 _/
    :param n: number of nodes
    :return: a networkx graph with the given topology
    """
    # create an empty undirected graph with n nodes
    g = nx.empty_graph(n, create_using=nx.Graph())
    for i in range(n-2):
        g.add_edge(i, i+1)
    g.add_edge(n/2, n-1)
    g.add_edge(n/2-2, n-1)
    return g


def ring_graph(n):
    """
    Generate a ring graph with n nodes
    :param n: number of nodes
    :return: a networkx graph with the given topology
    """
    # create an empty undirected graph with n nodes
    g = nx.empty_graph(n, create_using=nx.Graph())
    for i in range(n-1):
        g.add_edge(i, i+1)
    g.add_edge(0, n-1)
    return g


def shortcut_graph(n, l_odd, l_even):
    """
    Generate a graph with two chains are connected together in this way:
    0 -- 1 -- 2 ------ 3 ------ 4 -- 5 -- 6
              |                 |
              6 --- 7 --- 8 --- 9
    In the example, the function is called with:
    - n = 10
    - l_odd = 1 (node number 3)
    - l_even = 4 (nodes 6, 7, 8, and 9)
    :param n: total number of nodes
    :param l_odd: number of nodes in the odd chain (minimum 1)
    :param l_even: number of nodes in the even chain (minimum 2)
    :return: a networkx graph with the given topology
    """
    assert(l_odd % 2 == 1 and l_odd >= 1)
    assert(l_even % 2 == 0 and l_even >= 2)
    assert(n - l_even - l_odd >= 4)
    g = nx.empty_graph(n, create_using=nx.Graph())
    # create upper chain
    for i in range(n - l_even - 1):
        g.add_edge(i, i+1)
    # create lower chain
    for i in range(n - l_even, n - 1):
        g.add_edge(i, i+1)
    # connect the two chains together
    g.add_edge((n-l_odd-l_even)/2-1, n-l_even)
    g.add_edge((n-l_odd-l_even)/2+l_odd, n-1)
    return g
