import argparse
from os import listdir
from os.path import isdir, join, isfile
import subprocess


def call(args, verbose=False):
    if verbose:
        print("Running " + " ".join(args))
    ret_code = subprocess.call(args)
    if ret_code != 0:
        raise Exception


def summary_processed(resultsbdir, expname):
    summary_folder = join(resultsbdir, "%s_summary" % expname)
    if not isdir(summary_folder):
        return False
    else:
        return True


def files_exist(folder, files):
    for f in files:
        full_path = join(folder, f)
        if not isfile(full_path):
            return False
    return True


def average_processed(resultsbdir, expname):
    return files_exist(join(resultsbdir, "%s_summary" % expname),
                       ["average.csv", "experiments.csv", "integral.csv",
                        "lr.csv"])


def intervals_processed(resultsbdir, expname):
    return files_exist(join(resultsbdir, "%s_summary" % expname),
                       ["intervals.csv"])


def untar(folder, verbose=False):
    for f in listdir(folder):
        if f.endswith(".tar.gz"):
            extracted = f.replace(".tar.gz", "")
            if isdir(join(folder, extracted)):
                if verbose:
                    print("Skipping %s. Already extracted" % join(folder, f))
                continue
            if verbose:
                print("Extracting %s" % join(folder, f))
            call(["tar", "xf", join(folder, f), "--directory", folder])


def remove_extracted_folders(folder, verbose=False):
    for f in listdir(folder):
        if f.endswith(".tar.gz"):
            extracted = f.replace(".tar.gz", "")
            if not isdir(join(folder, extracted)):
                continue
            if verbose:
                print("Deleting %s" % join(folder, extracted))
            call(["rm", "-rf", join(folder, extracted)])


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--masteridx', dest='masteridx', type=int,
                        help='Master node number')
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
    resultsbdir = args.resultsbdir
    verbose = args.verbose
    masteridx = args.masteridx

    directories = listdir(resultsbdir)

    for d in directories:
        full_path = join(resultsbdir, d)
        if isdir(full_path) and d.startswith("t") and \
                d.endswith("_results"):
            if verbose:
                print("Processing directory %s" % d)
            expname = d.split("_")[0]

            extracted = False
            if not summary_processed(resultsbdir, expname):
                if verbose:
                    print("Analyzing routing tables")
                untar(full_path, verbose)
                extracted = True
                call(["python", "analyse_routing_tables.py", "--resultsbdir",
                      resultsbdir, "--expname", expname], verbose)
            else:
                if verbose:
                    print("Skipping routing tables analysis as already done")

            if not average_processed(resultsbdir, expname):
                if verbose:
                    print("Performing experiment averaging")
                call(["Rscript", "average-experiments.R",
                      join(resultsbdir, "%s_summary" % expname)], verbose)
            else:
                if verbose:
                    print("Skipping experiment averaging as already done")

            if not intervals_processed(resultsbdir, expname):
                if verbose:
                    print("Performing interval processing")
                if not extracted:
                    untar(full_path, verbose)
                    extracted = True
                call(["python", "process-intervals.py", "--resultsbdir",
                      resultsbdir, "--expname", expname, "--masteridx",
                      str(masteridx)], verbose)
            else:
                if verbose:
                    print("Skipping interval processing as already done")

            remove_extracted_folders(full_path, verbose)
