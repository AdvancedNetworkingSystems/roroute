#!/usr/bin/env python
import xml.etree.ElementTree as ET
from StringIO import StringIO
from subprocess import check_output
from argparse import ArgumentParser


def matches(name, filters, nodes):
    if len(nodes) > 0:
        return name in nodes
    if len(filters) == 0:
        return True
    for f in filters:
        if name.startswith(f):
            return True
    return False


parser = ArgumentParser()
parser.add_argument("-t", "--testbed", dest="testbed",
                    default="twist", action="store", metavar="TESTBED",
                    help="Testbed to use [default: %(default)s]")
parser.add_argument("-f", "--filter", dest="filter",
                    default="", action="store", metavar="List of filters",
                    help="Comma separated list of node prefixes [default: %("
                         "default)s]")
parser.add_argument("-n", "--nodes", dest="nodes",
                    default="", action="store", metavar="List of nodes",
                    help="Comma separated list of nodes [default: %("
                         "default)s] This argument has precedence over "
                         "--filter")
parser.add_argument("-d", "--dump", dest="dump",
                    default="", action="store", metavar="FILENAME",
                    help="Output file where to store the list of available "
                         "nodes. If not specified, no file will be written")
args = parser.parse_args()

testbed = args.testbed
if args.filter:
    filters = args.filter.split(",")
else:
    filters = []

if args.nodes:
    nodes = args.nodes.split(",")
else:
    nodes = []

dump_file = args.dump

omni = ["omni", "-V3", "listresources", "-a", testbed, "--error", "--tostdout"]

xml = check_output(omni)

# parse the xml file removing the namespaces from tag names
xml_file = StringIO(xml)
it = ET.iterparse(xml_file)
for _, el in it:
    el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
e = it.root


t = __import__('%stemplates' % testbed, globals(), locals(),
               ['node_template', 'header_template', 'footer_template'])

h = 40
w = 120
xs = 100
ys = 100

if dump_file != "":
    df = open(dump_file, "w")

n = 0
print(t.header_template)
for node in e.findall('node'):
    name = node.get('component_name')
    available = node.find('available').get('now').lower() == "true"
    has_position = 'x' in node.find('location').attrib
    component_id = node.get('component_id')
    if has_position:
        x = float(node.find('location').get('x'))
        y = float(node.find('location').get('y'))
        z = float(node.find('location').get('z'))
    else:
        x = 0
        y = 0
        z = 0
    row = (n - 1) / 8
    col = (n - 1) % 8
    if available and matches(name, filters, nodes):
        print(t.node_template %
              (name, component_id, xs + col * w, ys + row * h))
        if dump_file != "":
            df.write("%s\n" % name)
        n += 1
    # sys.stdout.write("Node: %s (%savailable) (%s)" %
    #                  (name, "" if available else "not", component_id))
    # if has_position:
    #     sys.stdout.write(" Position x=%f, y=%f, z=%f" % (x, y, z))
    # sys.stdout.write("\n")
print(t.footer_template)

if dump_file != "":
    df.close()
