import logging
import glob
import pathlib
import tempfile
import tarfile
import json

from argparse import ArgumentParser
from copy import deepcopy
from enum import Enum
from os import makedirs, environ, remove, walk, listdir
from os.path import exists, join, basename, isdir, dirname
from shutil import rmtree, copyfile, move, copy, copytree
from itertools import cycle

import numpy as np

from mpi4py import MPI
from scipy import stats

import config

from scripts.geometries_mrstorm import generate_clusters, generate_geometries
from scripts.simulations_mrstorm import generate_simulation

logger = logging.getLogger(basename(__file__).split(".")[0])

DESCRIPTION = """
This program contains all the utilities needed to generate geometries
and simulations based on probabilistic parameters. It contains 3 
utilities used to generate configurations and batch process them
afterwards on a computing cluster.
"""

GEN_DESCRIPTION = """
This utility generates a group of geometries based on a
range of parameters distributions (see the arguments). It
then simulates the signal based on another group of parameters
distributions. The whole process is distributed on the number
of nodes wanted.
"""

GEO_DESCRIPTION = """
This utility is used before the cluster generator to create the
json configuration file required to parametrize the distributions
of the geometry construction step.
"""

SIM_DESCRIPTION = """
This utility is used before the cluster generator to create the
json configuration file required to parametrize the simulation
step.
"""


class ClusterConfig:
    def __init__(self, n_nodes, base_output):
        self._n_nodes = n_nodes
        self._output = base_output


def get_parser():
    parser = ArgumentParser(
        description=DESCRIPTION
    )

    subparser = parser.add_subparsers(help="Usable parsers", dest="step")

    main_parser = subparser.add_parser(
        "generate", description=GEN_DESCRIPTION
    )

    main_parser.add_argument(
        "-r", "--resolution", required=True, nargs=3, type=int, metavar=("Nx", "Ny", "Nz"),
        help="Wanted resolution for the output images"
    )
    main_parser.add_argument(
        "-s", "--spacing", required=True, nargs=3, type=float, metavar=("Sx", "Sy", "Sz"),
        help="Size of voxels of the output images"
    )
    main_parser.add_argument(
        "-fp", "--float_precision", default=10, type=int, metavar="fp",
        help="Precision for lossy float conversion (ex: conversion to string)"
    )

    main_parser.add_argument(
        '-gj', "--geojson", required=True, metavar="<geo.json>",
        help="Json file for geometry (see geo_json parser to generate)"
    )
    main_parser.add_argument(
        '-sj', "--simjson", required=True, metavar="<sim.json>",
        help="Json file for simulation (see sim_json parser to generate)"
    )
    main_parser.add_argument(
        '-v', "--verbose", action="store_true",
        help="Enables debug messages output"
    )

    pg = main_parser.add_argument_group("Parallelism")
    pg.add_argument(
        '-c', "--collect", default=-1, type=int, metavar="c",
        help="Number of threads collecting data from thread nodes. If -1, the "
             "main thread will do the collecting when its part of the job is done. (Default : %(default)s)"
    )
    pg.add_argument(
        '-ngc', "--n-geo-collect", default=10, type=int, metavar="ngc",
        help="Number of geometries to generate per node before archiving and calling collect. (Default : %(default)s)"
    )
    pg.add_argument(
        '-nsc', "--n-sim-collect", default=5, type=int, metavar="nsc",
        help="Number of simulations to generate per node before archiving and calling collect. (Default : %(default)s)"
    )
    pg.add_argument(
        '-nbv', "--n-collect-bf-valid", default=-1, type=int, metavar="nbv",
        help="Number of processes to collect before starting slaves collectors data validation. This number will "
             "be capped by the number of available slaves. (Default : %(default)s)"
    )

    og = main_parser.add_argument_group("Outputs")
    og.add_argument(
        '-o', "--out", required=True, metavar="<.../out>",
        help="Base output for the data"
    )
    og.add_argument(
        '-so', "--simout", default="simulation", metavar="<simulation>",
        help="Output folder under the base output for simulation data (Default : %(default)s)"
    )
    og.add_argument(
        '-go', "--geoout", default="geometry", metavar="<geometry>",
        help="Output folder under the base output for geometry data (Default : %(default)s)"
    )
    og.add_argument(
        '-gf', "--geo-fmt", default="geo_{}", metavar="<fmt>",
        help="Format for the file names in the geometry output"
    )
    og.add_argument(
        "-t", "--timings-file", default=None, metavar="<times.json>",
        help="Outputs statistics about execution times in the simulator ("
             "e.g. : time it took to generate geometry a geometry, mean time"
             " of simulation generation, ...)"
    )

    geo_parser = subparser.add_parser(
        "geo-json", description=GEO_DESCRIPTION
    )
    geo_parser.add_argument(
        "anchors", nargs="+", metavar="<x,y,z>",
        help="Base anchors for the fibers generated. Format : x.x,y.y,z.z"
    )
    geo_parser.add_argument(
        '-l', "--limits", required=True, nargs=6, type=float,
        metavar=("x_min", "x_max", "y_min", "y_max", "z_min", "z_max"),
        help="Limits for the base bundle space (Default : [[0,1], [0,1], [0,1]])"
    )
    geo_parser.add_argument(
        '-n', "--n-output", required=True, type=int, metavar="N", help="Number of geometries to generate"
    )
    geo_parser.add_argument("-o", "--output", required=True, help="Output json file path and name")

    cg = geo_parser.add_argument_group("Clusters definition configuration")
    cg.add_argument(
        '-rd', "--rad-dist",
        help="Scipy distribution used for radius determination (Default : norm)"
    )
    cg.add_argument(
        '-rr', "--rad-range", nargs=2, type=float, metavar=("r_min", "r_max"),
        help="Possible range of radii (Default : [0, 5])"
    )
    cg.add_argument(
        '-bm', "--bun-max", type=int,
        help="Maximum number of bundles possible in a cluster (Default : 3)"
    )
    cg.add_argument(
        '-bv', "--bun-var", type=float,
        help="Variance for the distribution on number of bundles (Default : 0.4)"
    )
    cg.add_argument(
        '-fm', "--fib-mean", type=int,
        help="Mean number of fibers in a bundle (Default : 6000)"
    )
    cg.add_argument(
        '-fv', "--fib-var", type=float,
        help="Variance for the distribution on number of fibers (Default : 1000)"
    )

    tg = geo_parser.add_argument_group("Random transformations configuration")
    tg.add_argument(
        '-rm', "--rot-max", type=float,
        help="Maximum rotation possible for bundles (Default : 0.5 * Pi)"
    )
    tg.add_argument(
        '-rp', "--rot-prob", type=float,
        help="Probability of a random rotation (Default : 0.7)"
    )
    tg.add_argument(
        '-td', "--trans-dist",
        help="Scipy distribution used for translation determination (Default : norm)"
    )
    tg.add_argument(
        '-tm', "--trans-max", nargs=3, type=float, metavar=("Tx_max", "Ty_max", "Tz_max"),
        help="Maximum translation possible on each axis (Default : [0.5, 0.5, 0.5])"
    )
    tg.add_argument(
        '-tp', "--trans-prob", type=float,
        help="Probability of a random translation (Default : 0.6)"
    )
    cg.add_argument(
        '-pc', "--pert-center", action='store_true',
        help="Enables perturbation of the center of a bundle after random transformation"
    )
    cg.add_argument(
        '-pv', "--pert-var", type=float,
        help="Variance on the pertubation of the center of bundles after transformation (Default : 0.4)"
    )

    simu_parser = subparser.add_parser(
        "sim-json", description=SIM_DESCRIPTION
    )

    simu_parser.add_argument("n_simulations", type=int, help="Number of simulations to run on geometry")
    simu_parser.add_argument("-a", "--artifacts", help="Path to json file containing the artifact model")
    simu_parser.add_argument(
        "-nf", "--noiseless", action="store_true",
        help="Enables the generation of a noiseless dataset before the one with the artifacts"
    )
    simu_parser.add_argument("-o", "--output", required=True, help="Output json file name and path")

    gg = simu_parser.add_argument_group("Acquisition profile")
    gg.add_argument("bvalues", nargs="+", type=int, metavar="<bval>", help="B-values used for DWI generation")
    gg.add_argument(
        "-s", "--shells", nargs="+", type=int, metavar=("<N_1>", "<N_2>"),
        help="Number of b-vectors per bvalue"
    )
    gg.add_argument(
        "-r", "--randomize", action="store_true",
        help="Enables randomization of gradient shells between simulations"
    )
    gg.add_argument("-b0m", "--b0-mean", type=int, help="Mean number of b0 to generate (Default : 1)")
    gg.add_argument("-b0v", "--b0-var", type=float, help="Variance for the number of b0 distribution (Default : 0)")
    gg.add_argument(
        "-b0d", "--b0-dir", nargs=3, type=float, metavar=("<b0_x>", "<b0_y>", "<b0_z>"),
        help="Gradient direction for b0 volumes (Default : [0, 0, 0])"
    )
    gg.add_argument(
        "-er", "--echo-range", nargs=2, type=int, metavar=("TE_min", "TE_max"),
        help="Possible range of echo time (Default : [70, 190])"
    )
    gg.add_argument(
        "-rr", "--rep-range", nargs=2, type=int, metavar=("TR_min", "TR_max"),
        help="Possible range of repetition time (Default : [600, 1600])"
    )
    gg.add_argument("-nc", "--n-coils", type=int, help="Number of coils to simulate")

    fcg = simu_parser.add_argument_group("Fiber compartment configuration")
    fcg.add_argument(
        "-fadr", "--fib-adiff-range", nargs=2, type=float, metavar=("fAD_min", "fAD_max"),
        help="Possible range of axial diffusivity for fibers (Default : [1.4e-3, 1.8e-3])"
    )
    fcg.add_argument(
        "-frdr", "--fib-rdiff-range", nargs=2, type=float, metavar=("fRD_min", "fRD_max"),
        help="Possible range of radial diffusivity for fibers (Default : [6e-4, 8e-4])"
    )
    fcg.add_argument(
        "-ft1r", "--fib-t1-range", nargs=2, type=int, metavar=("fT1_min", "fT1_max"),
        help="Possible range of T1 for fibers (Default : [700, 1200])"
    )
    fcg.add_argument(
        "-ft2r", "--fib-t2-range", nargs=2, type=int, metavar=("fT2_min", "fT2_max"),
        help="Possible range of T2 for fibers (Default : [70, 110])"
    )

    icg = simu_parser.add_argument_group("Isotropic compartment configuration")
    icg.add_argument(
        "-idr", "--iso-diff-range", nargs=2, type=float, metavar=("isoD_min", "isoD_max"),
        help="Possible range of diffusivity for isotropic compartment (Default : [2e-3, 3e-3])"
    )
    icg.add_argument(
        "-it1r", "--iso-t1-range", nargs=2, type=int, metavar=("isoT1_min", "isoT1_max"),
        help="Possible range of T1 for isotropic compartment (Default : [700, 1200])"
    )
    icg.add_argument(
        "-it2r", "--iso-t2-range", nargs=2, type=int, metavar=("isoT2_min", "isoT2_max"),
        help="Possible range of T2 for isotropic compartment (Default : [70, 110])"
    )

    return parser


class MrstormCOMM(Enum):
    GENERAL = 0
    COLLECT = 1
    PROCESS = 2
    REGROUP = 3
    COLLECT_INTER = 4
    ALL_COLLECT = 5

    @classmethod
    def isend(cls, *args, tag=None, **kwargs):
        tag = tag if tag else MrstormCOMM.GENERAL
        MPI.COMM_WORLD.isend(*args, tag=tag.value, **kwargs).wait()

    @classmethod
    def irecv(cls, *args, tag=None, **kwargs):
        tag = tag if tag else MrstormCOMM.GENERAL
        return MPI.COMM_WORLD.irecv(*args, tag=tag.value, **kwargs).wait()

    @classmethod
    def block_all(cls):
        MPI.COMM_WORLD.Barrier()

    @classmethod
    def gather(cls, *args, **kwargs):
        return MPI.COMM_WORLD.gather(*args, **kwargs)

    @classmethod
    def size(cls):
        return MPI.COMM_WORLD.Get_size()

    @classmethod
    def rank(cls):
        return MPI.COMM_WORLD.Get_rank()


class Message:
    def __init__(self, data=None, end_flag=False, meta=None):
        self.data = data
        self.end_flag = end_flag
        self.metadata = meta
        self._multipart = False

    def multipart(self):
        self._multipart = True
        return self

    def last(self):
        self._multipart = False
        return self

    def has_next(self):
        return self._multipart

    def __getstate__(self):
        return deepcopy(self.__dict__)

    def __setstate__(self, state):
        self.__dict__.update(state)


class WorkersConfiguration:
    def __init__(
        self, master_node, process_nodes,
        collect_master=None, collect_slaves=()
    ):
        self._master = master_node
        self._workers = process_nodes
        self._collectors = (collect_master,) + collect_slaves

    @property
    def master(self):
        return self._master

    @property
    def workforce(self):
        return (self._master,) + self._workers

    @property
    def workers(self):
        return self._workers

    @property
    def master_collector(self):
        return self._collectors[0]

    @property
    def slaves_collectors(self):
        return self._collectors[1:]

    @property
    def collectors(self):
        return self._collectors


def rename_parameters(in_dict, replacements):
    for in_k, out_k in replacements.items():
        in_dict[out_k] = in_dict.pop(in_k, None)

    return dict(filter(lambda kv: kv[1], in_dict.items()))


def convert_arange(in_dict, conversions):
    for key, n_samples in conversions.items():
        if key in in_dict:
            in_dict[key] = np.arange(
                *in_dict[key],
                (in_dict[key][1] - in_dict[key][0]) / float(n_samples)
            ).astype(type(n_samples)).tolist()

    return in_dict


# def gather_hash_dicts(hash_dict, comm, rank, data_root):
#     hash_dicts = comm.gather(hash_dict, root=MrstormCOMM.REGROUP)
#
#     if rank == 0:
#         hash_dict = hash_dicts[0]
#
#         for hd in hash_dicts[1:]:
#             for k, infos in hd.items():
#                 if k in hash_dict:
#                     logger.debug("Data package {} already present in the dataset {}".format(
#                         infos["data_package"], hash_dict[k]["data_package"])
#                     )
#                     rmtree(join(data_root, infos["data_package"]))
#                 else:
#                     infos.generate_new_key("data_path", join(data_root, infos["data_package"]))
#                     hash_dict[k] = infos
#
#         hash_dict = list(hash_dict.values())
#         logger.debug("Final number of unique datasets {}".format(len(hash_dict)))
#
#     return comm.bcast(hash_dict, root=MrstormCOMM.REGROUP)


# From https://lukelogbook.tech/2018/01/25/merging-two-folders-in-python/
def fuse_directories_and_overwrite_files(root_src_dir, root_dst_dir):
    for src_dir, dirs, files in walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not exists(dst_dir):
            makedirs(dst_dir)
        for file_ in files:
            src_file = join(src_dir, file_)
            dst_file = join(dst_dir, file_)
            if exists(dst_file):
                remove(dst_file)
            copy(src_file, dst_dir)


def get_stat_dist(name):
    return [
        getattr(stats, d) for d in dir(stats)
        if isinstance(getattr(stats, d), stats.rv_continuous) and d == name
    ][0]


def import_parameters_dists(params, keys):
    return {
        k: get_stat_dist(v) if k in keys else v for k, v in params.items()
    }


def execute_computing_node(rank, args, mpi_conf, is_master_collect=False):
    # Get base directories on node
    logger.info("Setting up local paths")

    base_output = args["out"]
    global_sim_output = join(base_output, args["simout"])
    global_geo_output = join(base_output, args["geoout"])

    node_root = join(environ["SLURM_TMPDIR"], "node{}_root".format(rank))
    node_geo_output = join(node_root, args["geoout"])
    node_sim_output = join(node_root, args["simout"])
    params_root = join(node_root, "params")
    geo_params = join(params_root, "geo")
    sim_params = join(params_root, "sim")

    makedirs(node_root, exist_ok=True)
    makedirs(params_root, exist_ok=True)
    makedirs(geo_params, exist_ok=True)
    makedirs(sim_params, exist_ok=True)

    logger.debug("  -> Node root   : {}".format(node_root))
    logger.debug("  -> Params root : {}".format(params_root))
    logger.debug("  -> Outputs     :")
    logger.debug("      -> Geometry   : {}".format(node_geo_output))
    logger.debug("      -> Simulation : {}".format(node_sim_output))

    # Copy config files on node
    logger.info("Copying config files on node")

    geometry_cfg = join(node_root, "geo_cnf.json")
    simulation_cfg = join(node_root, "sim_cnf.json")
    copyfile(args["geojson"], geometry_cfg)
    copyfile(args["simjson"], simulation_cfg)

    logger.debug("  -> Source      : {}".format(args["geojson"]))
    logger.debug("  -> Destination : {}".format(geometry_cfg))
    logger.debug("  -> Source      : {}".format(args["simjson"]))
    logger.debug("  -> Destination : {}".format(simulation_cfg))

    # Get singularity to run the code
    logger.info("Copying singularity on the node")

    conf = config.get_config()
    singularity_path = join(node_root, conf["singularity_name"])

    logger.debug("  -> Source      : {}".format(
        join(conf["singularity_path"], conf["singularity_name"])
    ))
    logger.debug("  -> Destination : {}".format(singularity_path))

    if not exists(singularity_path):
        copyfile(
            join(conf["singularity_path"], conf["singularity_name"]),
            singularity_path
        )
    conf["singularity_path"] = node_root

    # Fetch remaining parameters from parser
    resolution = args["resolution"]
    spacing = args["spacing"]
    geo_fmt = args["geo_fmt"]

    logger.debug("Output images parameters")
    logger.debug("  -> Resolution : {}, {}, {}".format(*resolution))
    logger.debug("  -> Spacing    : {:.2}, {:.2}, {:.2}".format(*spacing))

    logger.debug("Format for output geometry files : {}".format(geo_fmt))

    # Fetch geometry and simulation configurations
    logger.info("Opening configuration files for generation")

    geo_json = json.load(open(geometry_cfg))
    simulation_json = json.load(open(simulation_cfg))

    logger.debug("  -> Geometry :\n{}".format(json.dumps(geo_json, indent=4)))
    logger.debug(
        "  -> Simulation :\n{}".format(json.dumps(simulation_json, indent=4))
    )

    # Format geo_json file depending on which node
    # is on to have the right number of samples at the end
    world_size = MrstormCOMM.size()
    processing_size = len(mpi_conf.workforce)

    remainder = 0
    if "n_output" in geo_json:
        remainder = geo_json["n_output"] % processing_size

    if rank == mpi_conf.master:
        if "n_output" in geo_json:
            geo_json["n_output"] = int(geo_json["n_output"] / processing_size)
            logger.debug(
                "A batch of geometries will have size {} "
                "with remainder {}".format(geo_json["n_output"], remainder)
            )

        logger.debug("Sending geometry configuration to slave nodes")
        slaves = mpi_conf.workers

        # Calculate bundle to world transformation
        limits = [l[1] - l[0] for l in geo_json['limits']]
        res = args['resolution']
        geo_json['world_scale'] = np.diag(np.array(res) / limits).tolist()

        for i in range(len(slaves)):
            geo_conf = deepcopy(geo_json)
            if "n_output" in geo_conf and i < (remainder - 1):
                geo_conf["n_output"] += 1
            MrstormCOMM.isend(
                geo_conf, dest=slaves[i], tag=MrstormCOMM.PROCESS
            )

        if "n_output" in geo_json:
            geo_json["n_output"] += int(remainder > 0)
    else:
        logger.debug("Receiving geometry configuration from master node")
        geo_json = MrstormCOMM.irecv(
            source=mpi_conf.master, tag=MrstormCOMM.PROCESS
        )

    geo_json = import_parameters_dists(geo_json, ['rad_dist', 'trans_dist'])

    # Define the collection callback
    if is_master_collect:
        f_collect = None
        args['n_geo_collect'] = -1
    else:
        def _collect_callback(data_infos, idx, end=False, **kwargs):
            arc = join(node_root, "geo_iter{}_node{}.tar.gz".format(
                idx, rank
            ))

            with tarfile.open(arc, "w") as archive:
                for data in data_infos:
                    # data.pop("handler")
                    archive.add(
                        data['data_package'],
                        arcname=basename(data['data_package'])
                    )
                    remove(data['data_package'])
                    data['data_package'] = basename(data['data_package'])

            out_arc = join(global_geo_output, "geo_iter{}_node{}.tar.gz".format(
                idx, rank
            ))

            copyfile(arc, out_arc)
            remove(arc)

            meta = {"archive": out_arc}
            if "time_exec" in args and "extra" in kwargs:
                if "timings" in kwargs["extra"]:
                    meta["timings"] = kwargs["extra"]["timings"]

            logger.debug("Node {} sending out infos. Ended {}".format(rank, end))

            MrstormCOMM.isend(
                Message(data_infos, end, meta=meta),
                dest=mpi_conf.master_collector,
                tag=MrstormCOMM.ALL_COLLECT
            )
            return True

        f_collect = _collect_callback

    # Generate the geometries by batch
    logger.info("Generating clusters from configuration")
    if "n_output" not in geo_json or geo_json["n_output"] > 0:
        clusters = generate_clusters(**geo_json)

        logger.debug("Number of clusters generated {}".format(len(clusters)))

        logger.info("Generating geometries")

        geo_infos = generate_geometries(
            clusters, resolution, spacing, geo_fmt, geo_params, node_geo_output,
            rank * geo_json["n_output"] + (0 if rank < remainder else remainder),
            singularity_conf=conf, dump_infos=True, geo_ready_callback=f_collect,
            callback_stride=args['n_geo_collect'], get_timings=args["time_exec"]
        )

        logger.debug("Number of geometries generated {}".format(len(geo_infos)))
    else:
        MrstormCOMM.isend(
            Message(end_flag=True),
            dest=mpi_conf.master_collector,
            tag=MrstormCOMM.ALL_COLLECT
        )

    if not is_master_collect \
       and len(mpi_conf.workforce) < len(mpi_conf.slaves_collectors):
        if rank == mpi_conf.master:
            for i in range(
                    len(mpi_conf.slaves_collectors) - len(mpi_conf.workforce)
            ):
                MrstormCOMM.isend(
                    Message(end_flag=True),
                    dest=mpi_conf.master_collector,
                    tag=MrstormCOMM.ALL_COLLECT
                )

    logger.info("Node {} finished computing geometries".format(rank))

    if is_master_collect:
        package_path, geo_infos = collect_geometries_offline(
            rank, args, geo_infos, mpi_conf
        )
    else:
        package_path, geo_infos = MrstormCOMM.irecv(
            source=mpi_conf.master_collector, tag=MrstormCOMM.COLLECT
        )

    arc = join(node_geo_output, basename(package_path))

    rmtree(node_geo_output)
    makedirs(node_geo_output, exist_ok=True)
    copyfile(package_path, arc)

    with tarfile.open(arc, 'r') as archive:
        archive.extractall(node_geo_output)

    logger.info("Generating simulations on datasets")

    if is_master_collect:
        f_sim_collect = None
        args['n_geo_collect'] = -1
        sim_archive = join(node_root, "data_node{}.tar.gz".format(rank))
        pathlib.Path(sim_archive).touch()
    else:
        sim_archive = None

        def f_sim_collect(paths=None, infos=None, idx=None, end=False, **kwargs):
            archive_path = None
            if paths:
                archive_path = join(
                    global_sim_output, "sim_iter{}_node{}.tar.gz".format(idx, rank)
                )
                tmpf = tempfile.mkdtemp(prefix=node_root)
                json.dump(
                    serialize_floats(
                        deepcopy(infos), dec=args['float_precision']
                    ),
                    open(join(tmpf, "description.json"), 'w+')
                )
                node_archive_path = join(
                    tmpf, "sim_iter{}_node{}.tar.gz".format(idx, rank)
                )
                with tarfile.open(node_archive_path, 'w') as archive:
                    for path_group in paths:
                        for path in path_group:
                            folder = dirname(path)
                            search_tag = basename(path).split(".")[0]
                            sim_path = join(folder, "simulation_outputs")
                            for item in glob.glob1(
                                sim_path, "{}*".format(search_tag)
                            ):
                                archive.addfile(
                                    tarfile.TarInfo(item),
                                    open(join(sim_path, item))
                                )

                copyfile(node_archive_path, archive_path)
                remove(node_archive_path)
                rmtree(tmpf)

            meta = None

            if args["time_exec"] and "extra" in kwargs:
                if "timings" in kwargs["extra"]:
                    meta = {"timings": kwargs["extra"]["timings"]}

            MrstormCOMM.isend(
                Message(archive_path, end, meta=meta),
                dest=mpi_conf.master_collector,
                tag=MrstormCOMM.COLLECT
            )

    # Generate simulations on remaining geometries
    step = int(len(geo_infos) / len(mpi_conf.workforce))
    remainder = len(geo_infos) % len(mpi_conf.workforce)
    # sim_archive = join(node_root, "data_node{}.tar.gz".format(rank))
    # with tarfile.open(sim_archive, "w:gz") as archive:
    i0 = rank * step + (rank if rank < remainder else remainder)
    i1 = (rank + 1) * step + (
        (rank + 1) if (rank + 1) < remainder else remainder
    )
    for infos in list(geo_infos.values())[i0:i1]:
        sim_pre = infos.get_base_file_name().split(".")[0].rstrip("_base")
        infos["file_path"] = node_geo_output
        infos.generate_new_key("processing_node", rank)

        handler = infos.pop("handler")
        generate_simulation(
            handler, infos, sim_pre, sim_params, node_sim_output,
            singularity_conf=conf, sim_ready_callback=f_sim_collect,
            callback_stride=args['n_sim_collect'],
            get_timings=args["time_exec"], **simulation_json
        )

        if is_master_collect:
            with tarfile.open(sim_archive, 'a') as archive:
                description_filename = join(node_sim_output, "{}_description.json".format(sim_pre))
                description = json.load(open(description_filename))

                for i in range(len(description["paths"])):
                    description["paths"][str(i)] = [join(global_sim_output, "simulation_outputs", basename(sim)) for sim in description["paths"][str(i)]]

                json.dump(description, open(description_filename, "w+"))
                archive.addfile(tarfile.TarInfo("{}_description.json".format(sim_pre)), open(description_filename))

    if is_master_collect:
        with tarfile.open(sim_archive, 'a') as archive:
            archive.add(join(node_sim_output, "simulation_outputs"), arcname="simulation_outputs")

        copyfile(
            sim_archive,
            join(global_sim_output, "data_node{}.tar.gz".format(rank))
        )

        with tarfile.open(
            join(global_sim_output, "data_node{}.tar.gz".format(rank)),
            "r:gz"
        ) as archive:
            archive.extractall(join(global_sim_output))
    else:
        MrstormCOMM.isend(
            Message(end_flag=True),
            dest=mpi_conf.master_collector,
            tag=MrstormCOMM.COLLECT
        )


def serialize_floats(obj, dec=10):
    def serialize_dict(ob, p):
        return {k: serialize_floats(o, p) for k, o in ob.items()}

    return serialize_dict(obj, dec) \
        if isinstance(obj, dict) else [serialize_floats(o, dec) for o in obj] \
        if isinstance(obj, list) else ("{:" + str(dec) + "f}").format(obj) \
        if isinstance(obj, float) else str(obj)


def collect_geometries_offline(rank, args, geo_infos, mpi_conf):
    base_output = args["out"]
    global_geo_output = join(base_output, args["geoout"])
    node_root = join(environ["SLURM_TMPDIR"], "node{}_root".format(rank))
    arc = join(node_root, "geo_package_node{}.tar.gz".format(rank))

    with tarfile.open(arc, "w") as archive:
        for info in geo_infos:
            archive.add(
                info['data_package'], arcname=basename(info['data_package'])
            )
            remove(info['data_package'])

    move_package_to(arc, global_geo_output, True, True)

    infos = MrstormCOMM.gather(geo_infos, root=mpi_conf.master)

    if rank == mpi_conf.master:
        unique_geos = {}

        for info in infos:
            if not info['hash'] in unique_geos.keys():
                unique_geos[info['hash']] = info
            else:
                remove(join(global_geo_output, basename(info['data_package'])))

        package_path = create_geometry_archive(
            global_geo_output, unique_geos, base_output
        )

        for i in mpi_conf.workers:
            MrstormCOMM.isend(
                (package_path, unique_geos),
                dest=i,
                tag=MrstormCOMM.PROCESS
            )
    else:
        package_path, unique_geos = MrstormCOMM.irecv(
            source=mpi_conf.master, tag=MrstormCOMM.PROCESS
        )

    return package_path, unique_geos


def validate_slaves(collective_hash_dict, collect_slaves):
    for i in deepcopy(collect_slaves):
        while True:
            message = MrstormCOMM.irecv(
                source=i, tag=MrstormCOMM.COLLECT_INTER
            )
            if message.end_flag:
                collect_slaves = tuple(
                    filter(lambda k: not (k == i), collect_slaves)
                )
            if message.data:
                data_hash = message.data["hash"]
                if data_hash in collective_hash_dict.keys():
                    MrstormCOMM.isend(False, i, tag=MrstormCOMM.COLLECT_INTER)
                else:
                    collective_hash_dict[data_hash] = message.data
                    MrstormCOMM.isend(True, i, tag=MrstormCOMM.COLLECT_INTER)

            if not message.has_next():
                break

    return collective_hash_dict, collect_slaves


def move_package_to(package, dest, unload=False, delete_dest_pkg=False):
    if not dest == dirname(package):
        copyfile(package, join(dest, basename(package)))
    if unload:
        with tarfile.open(join(dest, basename(package)), "r") as archive:
            archive.extractall(dest)
        if delete_dest_pkg:
            remove(join(dest, basename(package)))


def unpack_geometry_output(geo_path, empty_path=True):
    tmp = tempfile.mkdtemp()
    for item in listdir(geo_path):
        if not isdir(join(geo_path, item)):
            if tarfile.is_tarfile(join(geo_path, item)):
                logger.debug("Unpacking {} to {}".format(
                    join(geo_path, item), tmp
                ))

                tmp_arc = tempfile.mkdtemp()
                with tarfile.open(join(geo_path, item), "r") as archive:
                    archive.extractall(tmp_arc)

                fuse_directories_and_overwrite_files(tmp_arc, tmp)
                rmtree(tmp_arc)


    if empty_path:
        rmtree(geo_path)
        makedirs(geo_path, exist_ok=True)

    fuse_directories_and_overwrite_files(tmp, geo_path)
    rmtree(tmp)


def execute_collecting_node(rank, args, mpi_conf):
    extra = None

    base_output = args["out"]
    global_geo_output = join(base_output, args["geoout"])
    global_sim_output = join(base_output, args["simout"])

    if args['n_collect_bf_valid'] == -1:
        args['n_collect_bf_valid'] = len(mpi_conf.slaves_collectors)

    # Execute collection for geometry generation
    tmp_arc_dir = tempfile.mkdtemp(prefix=global_geo_output)
    if rank == mpi_conf.master_collector:
        if args["time_exec"]:
            extra = {
                "timings": {
                    "geo": {"start": [], "end": [], "duration": []},
                    "sim": {"values": []}
                }
            }

        collective_hash_dict = {}
        collect_slaves = deepcopy(mpi_conf.slaves_collectors)

        def geo_unpacker(geo_info, **kwargs):
            data_hash = geo_info['hash']
            if data_hash not in collective_hash_dict.keys():
                collective_hash_dict[data_hash] = geo_info
                move_package_to(
                    geo_info["data_package"],
                    global_geo_output
                )
                return True
            return False

        active_wks = len(mpi_conf.workforce)
        while True:
            cycle_slaves = cycle(collect_slaves)
            idle_slaves, working_slaves = (), ()

            logger.debug("Available slaves {}".format(collect_slaves))

            for i in range(
                args['n_collect_bf_valid']
                if args['n_collect_bf_valid'] < len(collect_slaves)
                else len(collect_slaves)
            ):
                message = MrstormCOMM.irecv(tag=MrstormCOMM.ALL_COLLECT)

                if message.end_flag:
                    active_wks -= 1
                    logger.debug("Workforce reduced to {}".format(active_wks))

                if message.data:
                    working_slaves += (next(cycle_slaves),)

                    MrstormCOMM.isend(
                        Message(
                            data=message.data,
                            end_flag=((active_wks < len(mpi_conf.slaves_collectors)) and message.end_flag),
                            meta=message.metadata
                        ),
                        dest=working_slaves[-1],
                        tag=MrstormCOMM.COLLECT_INTER
                    )

                if args["time_exec"]:
                    if message.metadata and "timings" in message.metadata:
                        extra["timings"]["geo"]["start"].extend(
                            message.metadata["timings"]["start"]
                        )

                        extra["timings"]["geo"]["end"].extend(
                            message.metadata["timings"]["end"]
                        )

                        extra["timings"]["geo"]["duration"].extend(
                            message.metadata["timings"]["duration"]
                        )

                if active_wks == 0:
                    break

            for i in range(len(collect_slaves) - len(working_slaves)):
                idle_slaves += (next(cycle_slaves),)

            if len(working_slaves) > 0:
                collective_hash_dict, working_slaves = validate_slaves(
                    collective_hash_dict, working_slaves
                )

            collect_slaves = idle_slaves + working_slaves

            if len(collect_slaves) == 0 or active_wks == 0:
                break

        logger.debug("Master collector has finished its geometry overseeing")

        logger.debug("Dequeueing slaves {}".format(collect_slaves))
        logger.debug("Dequeueing active workers {}".format(active_wks))

        for slave in collect_slaves:
            MrstormCOMM.isend(
                Message(end_flag=True),
                dest=slave,
                tag=MrstormCOMM.COLLECT_INTER
            )

        while active_wks > 0:
            message = MrstormCOMM.irecv(tag=MrstormCOMM.ALL_COLLECT)
            if message.data:
                unpack_geo_data(message, tmp_arc_dir, geo_unpacker)
            if message.end_flag:
                active_wks -= 1
                logger.debug("Workforce reduced to {}".format(active_wks))

        # if len(mpi_conf.workers) > len(mpi_conf.slaves_collectors):
        #     i = len(mpi_conf.workers) - len(mpi_conf.slaves_collectors)
        #     while i > 0:
        #         message = MrstormCOMM.irecv(tag=MrstormCOMM.ALL_COLLECT)
        #         if message.data:
        #             unpack_geo_data(message, tmp_arc_dir, geo_unpacker)
        #         if message.end_flag:
        #             i -= 1

        rmtree(tmp_arc_dir)
        package_path = create_geometry_archive(
            global_geo_output, collective_hash_dict, base_output
        )

        logger.debug("Master collector sending geometry config to workers")

        for i in mpi_conf.workforce:
            MrstormCOMM.isend(
                (package_path, collective_hash_dict),
                dest=i,
                tag=MrstormCOMM.COLLECT
            )

    else:
        def geo_unpacker_slave(info, end=False, is_multipart=False):
            MrstormCOMM.isend(
                Message(info, end_flag=end).multipart()
                if is_multipart else Message(info, end_flag=end),
                mpi_conf.master_collector, tag=MrstormCOMM.COLLECT_INTER
            )

            if MrstormCOMM.irecv(
                source=mpi_conf.master_collector,
                tag=MrstormCOMM.COLLECT_INTER
            ):
                move_package_to(
                    info["data_package"],
                    global_geo_output
                )
                return True

            return False

        while True:
            message = MrstormCOMM.irecv(
                source=mpi_conf.master_collector, tag=MrstormCOMM.COLLECT_INTER
            )
            if message.data:
                logger.debug("Node {} received a geometry message".format(rank))
                unpack_geo_data(message, tmp_arc_dir, geo_unpacker_slave)

            if message.end_flag:
                logger.debug("Node {} called to end geometry collecting")
                break

        rmtree(tmp_arc_dir)
        logger.info("Node {} finished collecting geometries".format(rank))

    if rank == mpi_conf.master_collector:
        n_workers = len(mpi_conf.workforce)
        collectors = mpi_conf.slaves_collectors
        collect_iter = cycle(collectors)

        while True:
            message = MrstormCOMM.irecv(tag=MrstormCOMM.COLLECT)

            if message.end_flag:
                n_workers -= 1

            if message.data:
                collector = next(collect_iter)
                if n_workers < len(mpi_conf.slaves_collectors) and message.end_flag:
                    collectors = list(
                        filter(lambda c: not c == collector, collectors)
                    )
                    collect_iter = cycle(collectors)

                MrstormCOMM.isend(
                    Message(
                        data=message.data,
                        end_flag=n_workers < len(mpi_conf.slaves_collectors) and message.end_flag,
                        meta=message.metadata
                    ),
                    dest=collector,
                    tag=MrstormCOMM.COLLECT_INTER
                )

            if args["time_exec"]:
                if message.metadata and "timings" in message.metadata:
                    for item in message.metadata["timings"].values():
                        extra["timings"]["sim"]["values"].extend(item)

            if len(collectors) == 0 or n_workers == 0:
                break

        if len(collectors) > 0:
            for i in collectors:
                MrstormCOMM.isend(
                    Message(end_flag=True),
                    dest=i,
                    tag=MrstormCOMM.COLLECT_INTER
                )

        while n_workers > 0:
            message = MrstormCOMM.irecv(tag=MrstormCOMM.COLLECT)
            if message.data:
                unpack_sim_data(message, global_sim_output)
            if message.end_flag:
                n_workers -= 1

        # if len(mpi_conf.workers) > len(mpi_conf.slaves_collectors):
        #     remainder = len(mpi_conf.workers) - len(mpi_conf.slaves_collectors)
        #     while remainder > 0:
        #         message = MrstormCOMM.irecv(tag=MrstormCOMM.COLLECT)
        #         if message.data:
        #             unpack_sim_data(message, global_sim_output)
        #         if message.end_flag:
        #             remainder -= 1

        if args["time_exec"]:
            extra["timings"]["geo"]["mean"] = np.mean(extra["timings"]["geo"]["duration"])
            extra["timings"]["sim"]["mean"] = np.mean(extra["timings"]["sim"]["values"])
            extra["timings"]["geo"]["var"] = np.var(extra["timings"]["geo"]["duration"])
            extra["timings"]["sim"]["var"] = np.var(extra["timings"]["sim"]["values"])

            logger.debug("Timings statistics")
            logger.debug("  -> Geometry : {} samples | mean : {} s | var : {} s".format(
                len(extra["timings"]["geo"]["duration"]),
                extra["timings"]["geo"]["mean"], extra["timings"]["geo"]["var"]
            ))
            logger.debug("  -> Simulation : {} samples | mean : {} s | var : {} s".format(
                len(extra["timings"]["sim"]["values"]),
                extra["timings"]["sim"]["mean"], extra["timings"]["sim"]["var"]
            ))

            json.dump(extra["timings"], open(args["timings_file"], "w+"))

    else:
        while True:
            message = MrstormCOMM.irecv(
                source=mpi_conf.master_collector, tag=MrstormCOMM.COLLECT_INTER
            )
            if message.data:
                unpack_sim_data(message, global_sim_output)
            if message.end_flag:
                break


def create_geometry_archive(geo_root, infos_dict, output):
    unpack_geometry_output(geo_root)

    data_root = join(geo_root, "data")
    logs_root = join(geo_root, "logs")
    outputs_root = join(data_root, "geometry_outputs")

    makedirs(logs_root)
    for log_file in glob.glob1(data_root, "*.log"):
        move(join(data_root, log_file), join(logs_root, log_file))

    move(
        outputs_root,
        join(geo_root, "geometry_outputs"),
        copy_function=copytree
    )
    rmtree(data_root)

    serializable_infos = {}
    for k, info in infos_dict.items():
        info_copy = deepcopy(info)
        info_copy.pop('data_package')
        info_copy.pop('handler')
        info_copy['file_path'] = geo_root
        serializable_infos[k] = info_copy.as_dict()

    json.dump(serializable_infos, open(
        join(geo_root, "description.json"), "w+"
    ))

    with tarfile.open(
            join(output, "geo_package.tar.gz"), "w:gz"
    ) as archive:
        for item in listdir(geo_root):
            archive.add(join(geo_root, item), arcname=item)

    return join(output, "geo_package.tar.gz")


def unpack_sim_data(message, output_dir):
    package = message.data
    move_package_to(
        package, output_dir, unload=True, delete_dest_pkg=True
    )


def unpack_geo_data(
        message, output_dir, valid_data_fn=lambda *args, **kwargs: True
):
    archive = message.metadata["archive"]
    move_package_to(
        archive, output_dir, unload=True, delete_dest_pkg=True
    )
    for i in range(len(message.data)):
        message.data[i]["data_package"] = join(
            output_dir, message.data[i]["data_package"]
        )

        if not valid_data_fn(
            message.data[i], end=message.end_flag, is_multipart=(i < (len(message.data) - 1))
        ):
            remove(message.data[i]["data_package"])


def generate_datasets(args):
    # Get basic MPI variables
    world_size = MrstormCOMM.size()
    assert world_size > 1
    rank = MrstormCOMM.rank()

    # Initialize per computing logging
    logger = logging.getLogger("{} | PROC {} / {}".format(
        basename(__file__).split(".")[0], rank, world_size
    ))
    logger.info("Setting up for dataset generation on node {}".format(rank))

    logger.debug("Arguments from the command line")
    logger.debug(json.dumps(args, indent=4))

    args["time_exec"] = "timings_file" in args

    # Set up global directories
    logger.info("Setting up global paths")

    base_output = args["out"]
    global_geo_output = join(base_output, args["geoout"])
    global_sim_output = join(base_output, args["simout"])

    if rank == 0:
        logger.info("Creating global geometry and simulation output folders")
        makedirs(global_geo_output, exist_ok=True)
        makedirs(global_sim_output, exist_ok=True)

    logger.debug("  -> Global output : {}".format(base_output))
    logger.debug("      -> Geometry output   : {}".format(global_geo_output))
    logger.debug("      -> Simulation output : {}".format(global_sim_output))

    # Job determination for nodes
    class JOB:
        collect = 0
        process = 1
        master_collect = -1

    # Setup nodes configuration
    n_collect = args["collect"]
    mpi_jobs_ranks = (
        0,
        tuple(range(1, world_size - n_collect))
    )
    if n_collect > 0:
        mpi_jobs_ranks += (
            world_size - n_collect,
            tuple(range(world_size - n_collect + 1, world_size))
        )

    mpi_conf = WorkersConfiguration(*mpi_jobs_ranks)

    if rank == 0:
        if n_collect > 0:
            job = JOB.process
            collect_ranks = mpi_conf.collectors
            assert world_size - n_collect > 0 and \
                (world_size - n_collect + len(collect_ranks)) == world_size, \
                ("Bad number of collect nodes ({})"
                 " for MPI world capacity ({})".format(n_collect, world_size))

            for i in range(1, world_size):
                MrstormCOMM.isend(
                    JOB.process if i < world_size - n_collect else JOB.collect,
                    dest=i
                )

        else:
            job = JOB.master_collect
            for i in range(1, world_size):
                MrstormCOMM.isend(JOB.process, dest=i)
    else:
        job = MrstormCOMM.irecv(source=0)

    if job is JOB.collect:
        execute_collecting_node(rank, args, mpi_conf)
    elif job is JOB.process:
        execute_computing_node(rank, args, mpi_conf)
    elif job is JOB.master_collect:
        execute_computing_node(rank, args, mpi_conf, is_master_collect=True)

    logger.info("Worker {} / {} has ended its tasks".format(
        rank + 1, MrstormCOMM.size())
    )


def generate_simulation_json(args):
    logging.info("Generating simulation parameters json file")
    parameters = {k.replace("-", "_"): v for k, v in args.items()}
    parameters = rename_parameters(parameters, {
        "n_simulations": "n_simus",
        "randomize": "randomize_bvecs",
        "b0_mean": "n_b0_mean",
        "b0_var": "n_b0_var",
        "b0_dir": "b0_base_bvec",
        "echo_range": "echo_time_range",
        "rep_range": "rep_time_range",
        "noiseless": "generate_noiseless"
    })

    artifacts = parameters.pop("artifacts", None)
    if artifacts:
        model = json.load(open(artifacts))
        parameters["artifacts_models"] = model

    logging.debug("Parameters as parsed and renamed for function call")
    logging.debug(json.dumps(parameters, indent=4))

    logging.debug("Performing conversion to numpy.arange where required")
    parameters = convert_arange(parameters, {
        "fib_adiff_range": 100.,
        "fib_rdiff_range": 100.,
        "fib_t1_range": 100,
        "fib_t2_range": 100,
        "iso_diff_range": 100.,
        "iso_t1_range": 100,
        "iso_t2_range": 100,
        "echo_time_range": 200,
        "rep_time_range": 200
    })

    output = parameters.pop("output")
    logging.info("Saving function parameters to {}".format(output))
    json.dump(parameters, open(output, "w+"), indent=4)


def generate_geometry_json(args):
    logging.info("Generating geometry parameters json file")
    parameters = {k.replace("-", "_"): v for k, v in args.items()}
    parameters = rename_parameters(parameters, {
        "anchors": "base_anchors",
        "bun_max": "max_bundles",
        "bun_var": "n_bundles_var",
        "fib_mean": "n_fibers_mean",
        "fib_var": "n_fibers_var",
        "pert_center": "perturbate_center",
        "pert_var": "perturbation_var"
    })
    parameters["limits"] = np.array(parameters["limits"]).reshape((3, 2)).tolist()

    logging.debug("Parameters as parsed and ready for function call")
    logging.debug(json.dumps(parameters, indent=4))

    logging.debug("Performing conversion to numpy.arange where required")
    if "rad_range" in parameters:
        parameters["rad_range"] = np.arange(
            *parameters["rad_range"],
            (parameters["rad_range"][1] - parameters["rad_range"][0]) / 20.
        ).tolist()

    parameters["base_anchors"] = np.apply_along_axis(
        lambda s: [float(ss) for ss in s[0].split(",")],
        axis=0,
        arr=np.array(parameters["base_anchors"])[None, :]
    ).T.tolist()

    output = parameters.pop("output")
    logging.info("Saving function parameters to {}".format(output))
    json.dump(parameters, open(output, "w+"), indent=4)


if __name__ == "__main__":
    class Parsers(Enum):
        generate = generate_datasets
        simjson = generate_simulation_json
        geojson = generate_geometry_json

    parser = get_parser()
    args = vars(parser.parse_args())

    if "verbose" in args:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logger.debug("Arguments parsed")
    step = args.pop("step")
    if step is None:
        parser.print_help()
    else:
        logger.debug("Loading parser for {}".format(step))
        Parsers.__dict__[step.replace("-", "")](args)
        logger.info("{} ended with success".format(step.capitalize()))
