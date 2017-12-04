#!/usr/bin/env python
import time
import datetime as dt
from argparse import ArgumentParser
from subprocess import Popen, PIPE
from os.path import isfile


class ProcessOutput():
    def __init__(self, out, err):
        self.stdout = out
        self.stderr = err


def local(command):
    proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = proc.communicate()
    return ProcessOutput(stdout, stderr)


def reserve(testbed, exp_name, duration, rspec):
    args = "-V3 -a {}".format(testbed)
    end = dt.datetime.utcnow() + dt.timedelta(hours=int(duration))
    end = end.strftime("%Y%m%dT%H:%M:%S%Z")
    checkcmd = "omni -c ./omni_config status {} {}".format(args, exp_name)
    cmd_result = local(checkcmd)
    if cmd_result.stderr.find("geni_ready") != -1:
        print("Slice already reserved. Resources ready")
        return True

    # Reserve and start
    print("Creating slice and allocating experiment")
    local("omni -c ./omni_config createslice {}".format(exp_name))
    local("omni -c ./omni_config renewslice {} {}".format(exp_name, end))
    alloc = local("omni -c ./omni_config allocate {} {} {}".
                  format(args, exp_name, rspec))

    if alloc.stderr.find("Error") != -1:
        print(alloc.stderr)
        print("Resources are not available")
        return False

    local("omni -c ./omni_config provision {} {}".format(args, exp_name))
    local("omni -c ./omni_config performoperationalaction {} {} geni_start"
          .format(args, exp_name))

    # Wait till reserved
    tic = time.time()
    n = 1
    cmd_result = local(checkcmd)
    while cmd_result.stderr.find("geni_ready") == -1:
        if cmd_result.stderr.find("geni_failed") != -1:
            print("One node failed to boot. Output:")
            print(cmd_result.stderr)
            return False
        print("Waiting for nodes to perform boot... Attempt {}".format(n))
        n += 1
        time.sleep(10)
        cmd_result = local(checkcmd)
    toc = time.time() - tic
    print("Resources ready." + " Took: {}".format(toc))
    return True


def release(testbed, exp_name):
    args = "-V3 -a {}".format(testbed)
    checkcmd = "omni -c ./omni_config status {} {}".format(args, exp_name)
    if local(checkcmd).stderr.find("geni_ready") == -1 and \
       local(checkcmd).stderr.find("geni_provisioned") == -1:
        print("Experiment %s not found" % exp_name)
        return False

    # release the slice
    print("Releasing resources")
    local("omni -c ./omni_config delete {} {}".format(args, exp_name))
    return True


def main():
    parser = ArgumentParser()
    parser.add_argument("-t", "--testbed", dest="testbed",
                        default="twist", action="store", metavar="TESTBED",
                        help="Testbed to use [default: %(default)s]")
    parser.add_argument("-d", "--duration", dest="duration", type=int,
                        default=3, action="store", metavar="DURATION",
                        help="Duration in hours [default: %(default)s]")
    parser.add_argument("-n", "--name", dest="name", default="experiment",
                        action="store", metavar="SLICENAME",
                        help="Name of the slice [default: %(default)s]")
    parser.add_argument("-f", "--rspec", dest="rspec", default="test.rspec",
                        action="store", metavar="FILENAME",
                        help=".rspec file to use [default: %(default)s]")
    parser.add_argument("-r", "--release", dest="delete", action="store_true",
                        help="Deletes an existing experiment. If not set, "
                             "the application creates a new experiment",
                        default=False)

    args = parser.parse_args()
    testbed = args.testbed
    duration = args.duration
    name = args.name
    rspec = args.rspec
    delete = args.delete

    if not isfile(rspec):
        print("File %s not found" % rspec)
        return False

    if not delete:
        return reserve(testbed, name, duration, rspec)
    else:
        return release(testbed, name)

if __name__ == "__main__":
    main()
