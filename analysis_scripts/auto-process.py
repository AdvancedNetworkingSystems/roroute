import argparse
from os import listdir
from os.path import isdir, join, isfile
from subprocess import call


def summary_processed(resultsbdir, expname):
    summary_folder = join(resultsbdir, "%s_summary" % expname)
    if not isdir(summary_folder):
        return False


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
        if f.endswith(".tar.bz"):
            extracted = f.replace(".tar.bz2", "")
            if isdir(join(folder, extracted)):
                continue
            if verbose:
                print("Extracting %s" % join(folder, f))
            call(["tar", "xf", join(folder, f), "--directory", folder])


def remove_extracted_folders(folder, verbose=False):
    for f in listdir(folder):
        if f.endswith(".tar.bz"):
            extracted = f.replace(".tar.bz2", "")
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
        if isdir(full_path) and full_path.startswith("t") and \
                full_path.endswith("_results"):
            expname = d.split("_")[0]

            extracted = False
            if not summary_processed(resultsbdir, expname):
                untar(full_path, verbose)
                extracted = True
                call(["python", "analyse_routing_tables.py", "--resultsbdir",
                      resultsbdir, "--expname", expname])

            if not average_processed(resultsbdir, extracted):
                call(["Rscript", "average-experiment.R",
                      join(resultsbdir, "%s_summary" % expname)])

            if not intervals_processed(resultsbdir, extracted):
                if not extracted:
                    untar(full_path, verbose)
                    extracted = True
                call(["python", "process-intervals.py", "--resultsbdir",
                      resultsbdir, "--expname", expname, "--masteridx",
                      masteridx])

            remove_extracted_folders(full_path, verbose)
