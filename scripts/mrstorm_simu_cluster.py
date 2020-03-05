from argparse import ArgumentParser
from enum import Enum
import json

import logging

import numpy as np
from os import makedirs, environ, remove, rmdir
from os.path import exists, join, basename
from shutil import rmtree, copyfile
import tarfile

from mpi4py import MPI

from scripts.geometries_mrstorm import generate_clusters, generate_geometries
from scripts.simulations_mrstorm import generate_simulation

import config

logger = logging.getLogger(__name__.split(".")[0])

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
        "generate", description=DESCRIPTION
    )

    main_parser.add_argument(
        "resolution", type=int, nargs=3, metavar=("Nx", "Ny", "Nz"),
        help="Wanted resolution for the output images"
    )
    main_parser.add_argument(
        "spacing", type=int, nargs=3, metavar=("Sx", "Sy", "Sz"),
        help="Size of voxels of the output images"
    )

    main_parser.add_argument(
        '-g', "--geojson", required=True, metavar="<geo.json>",
        help="Json file for geometry (see geo_json parser to generate)"
    )
    main_parser.add_argument(
        '-s', "--simjson", required=True, metavar="<sim.json>",
        help="Json file for simulation (see sim_json parser to generate)"
    )

    pg = main_parser.add_argument_group("Parallelism")
    pg.add_argument(
        '-wg', "--n-workers-geo", type=int, default=-1, metavar="W_geo",
        help="Number of workers processing the geometries (Default : %(default)s)"
    )
    pg.add_argument(
        '-ws', "--n-workers-sim", type=int, default=-1, metavar="W_sim",
        help="Number of workers processing the simulations (Default : %(default)s)"
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
        '-sf', "--sim-pre", default="file", metavar="<prefix>",
        help="Prefix for the file names in the simulation output"
    )

    geo_parser = subparser.add_parser(
        "geo-json", description=GEO_DESCRIPTION
    )
    geo_parser.add_argument(
        "anchors", nargs="+", metavar="<x,y,z>", dest="anchors",
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
        '-pv', "-pert-var", type=float,
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
    simu_parser.add_argument(
        "-n", "--n-sim", type=int, help="Number of simulations to run (Default : 100)"
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
    gg.add_argument("-b0v", "--b0-var", type=int, help="Variance for the number of b0 distribution (Default : 0)")
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


def rename_parameters(in_dict, replacements):
    for in_k, out_k in replacements.items():
        in_dict[out_k] = in_dict.pop(in_k, None)

    return dict(filter(lambda kv: kv[1], in_dict))


def convert_arange(in_dict, conversions):
    for key, n_samples in conversions.items():
        if key in in_dict:
            in_dict[key] = np.arange(*in_dict[key], n_samples)

    return in_dict


def gather_hash_dicts(hash_dict, comm, rank):
    hash_dicts = comm.gather(hash_dict, root=0)

    if rank == 0:
        for hd in hash_dicts[1:]:
            for k, infos in hd.items():
                if k in hash_dict:
                    rmtree(infos["data_path"])
                else:
                    hash_dict[k] = infos

        hash_dict = list(hash_dict.values())
        logger.debug("Final number of unique datasets {}".format(len(hash_dict)))

    return comm.bcast(hash_dict, root=0)


def generate_datasets(args):
    # Get basic MPI variables
    comm = MPI.COMM_WORLD
    world_size = comm.Get_size()
    assert world_size > 1
    rank = comm.Get_rank()

    # Initialize per computing logging
    logger = logging.getLogger("{} | PROC {} / {}".format(__name__.split(".")[0], rank, world_size))
    logger.info("Setting up for dataset generation on node {}".format(rank))

    # Get base directories on node
    logger.debug("Setting up paths")
    node_root = environ["SLURM_TMPDIR"]
    geometry_cfg = join(node_root, "geo_cnf.json")
    simulation_cfg = join(node_root, "sim_cnf.json")
    params_root = join(node_root, "params")
    geo_params = join(params_root, "geo")
    sim_params = join(params_root, "sim")

    makedirs(params_root, exist_ok=True)
    makedirs(geo_params, exist_ok=True)
    makedirs(sim_params, exist_ok=True)

    # Copy config files on node
    logger.debug("Copying config files on node")
    copyfile(args["geojson"], geometry_cfg)
    copyfile(args["simjson"], simulation_cfg)

    # Get singularity to run the code
    logger.info("Copying singularity")
    conf = config.get_config()
    singularity_path = join(node_root, conf["singularity_name"])

    logger.debug("  -> Source      : {}".format(join(conf["singularity_path"], conf["singularity_name"])))
    logger.debug("  -> Destination : {}".format(singularity_path))

    if not exists(singularity_path):
        copyfile(
            join(conf["singularity_path"], conf["singularity_name"]),
            singularity_path
        )
    conf["singularity_path"] = node_root
    config.override_config(config)

    # Fetch image parameters from parser
    resolution = args["resolution"]
    spacing = args["spacing"]

    logger.debug("Output images parameters")
    logger.debug("  -> Resolution : {}, {}, {}".format(*resolution))
    logger.debug("  -> Spacing : {}, {}, {}".format(*spacing))

    # Fetch parameters and outputs from parser
    geometry_json = json.load(open(geometry_cfg))
    simulation_json = json.load(open(simulation_cfg))
    geo_fmt = args["geo-fmt"]
    base_output = args["out"]
    global_geo_output = join(base_output, args["geoout"])
    global_sim_output = join(base_output, args["simout"])
    node_geo_output = join(node_root, args["geoout"])
    node_sim_output = join(node_root, args["simout"])

    logger.debug("Configuration files")
    logger.debug("  -> Geometry : {}".format(geometry_json))
    logger.debug("  -> Simulation : {}".format(simulation_json))
    logger.debug("Output for datasets : {}".format(base_output))

    # Format geometry_json file depending on which node
    # is on to have the right number of samples at the end
    remainder = 0
    if rank == 0:
        logger.info("Creating geometry and simulation output folders")
        makedirs(global_geo_output, exist_ok=True)
        makedirs(global_sim_output, exist_ok=True)

        remainder = 0
        if "n_output" in geometry_json:
            remainder = geometry_json["n_output"] % world_size
            geometry_json["n_output"] = int(geometry_json["n_output"] / world_size)
            logger.debug(
                "A batch of geometries will have size {} with remainder {}".format(geometry_json["n_output"], remainder)
            )

        logger.debug("Sending geometry configuration to slave nodes")
        for i in range(1, world_size):
            req = comm.isend(geometry_json, dest=i, tag=11)
            req.wait()

        if "n_output" in geometry_json:
            geometry_json["n_output"] += remainder
    else:
        logger.debug("Receiving geometry configuration from master node")
        req = comm.irecv(source=0, tag=11)
        geometry_json = req.wait()

    # Generate the geometries by batch
    logger.info("Generating clusters from configuration")
    clusters = generate_clusters(**geometry_json)
    logger.debug("Number of clusters generated {}".format(len(clusters)))
    logger.info("Generating geometries")
    geometries_infos = generate_geometries(
        clusters, resolution, spacing, geo_fmt, geo_params, node_geo_output, rank * geometry_json["n_output"] + (rank > 0) * remainder
    )
    logger.debug("Number of geometries generated {}".format(len(geometries_infos)))

    # Taking only unique realisations of geometries
    hash_dict = {}
    descriptions = json.load(join(node_geo_output, "description.json"))
    d_out = []
    for infos, description in zip(geometries_infos, descriptions):
        geo_hash = infos.pop("hash")
        if geo_hash in hash_dict:
            rmdir(infos["data_package"])
        else:
            hash_dict[geo_hash] = infos
            d_out.append(description)

    json.dump(d_out, open(join(node_geo_output, "description.json"), "w+"))

    hash_dict = gather_hash_dicts(hash_dict, comm, rank)

    logger.info("Generating simulations on datasets")
    # Generate simulations on remaining geometries
    step = int(len(hash_dict) / world_size)
    remainder = len(hash_dict) % world_size if rank == (world_size - 1) else 0
    for infos in list(hash_dict.values())[rank * step:(rank + 1) * step + remainder]:
        sim_pre = infos.get_base_file_name().split(".")[0].rstrip("_base")
        # Copy data locally
        data_package = infos["data_package"]
        data_name = basename(data_package)
        copyfile(data_package, join(node_root, data_name))
        with tarfile.open(join(node_root, data_name), "r") as archive:
            archive.extractall("data", join(node_root, "tmp_data"))
        remove(join(node_root, data_name))
        infos["data_path"] = join(node_root, "tmp_data")
        infos.generate_new_key("processing_node", rank)

        handler = infos.pop("handler")
        generate_simulation(handler, infos, sim_pre, sim_params, node_sim_output, **simulation_json)

    logger.info("Packing and copying data to storage")

    if rank == 0:
        geo_archive = join(node_root, "data.tar.gz")
        with tarfile.open(geo_archive, "w") as archive:
            for infos in hash_dict.values():
                data_package = infos.pop("data_package")
                node_rank = infos.pop("processing_node")
                data_name = basename(data_package)
                archive.add(data_package, arcname="{}_node{}".format(data_name, node_rank))

        copyfile(geo_archive, join(global_geo_output, "data.tar.gz"))
        remove(geo_archive)

    sim_archive = join(node_root, "data_node{}.tar.gz".format(rank))
    with tarfile.open(sim_archive, "w") as archive:
        archive.add(sim_params, arcname="params")
        archive.add(node_sim_output, arcname="simulation")

    copyfile(sim_archive, join(global_sim_output, "data_node{}.tar.gz".format(rank)))


def generate_simulation_json(args):
    logging.info("Generating simulation parameters json file")
    parameters = {k.replace("-", "_"): v for k, v in vars(args).items()}
    parameters = rename_parameters(parameters, {
        "randomize": "randomize_bvecs",
        "b0_mean": "n_b0_mean",
        "b0_var": "n_b0_var",
        "echo_range": "echo_time_range",
        "rep_range": "rep_time_range",
        "n_sim": "n_simulations"
    })

    artifacts = parameters.pop("artifacts", None)
    if artifacts:
        model = json.load(open(artifacts))
        parameters["artifacts_model"] = model

    logging.debug("Parameters as parsed and renamed for function call")
    logging.debug(json.dumps(parameters, indent=4))

    logging.debug("Performing conversion to numpy.arange where required")
    parameters = convert_arange(parameters, {
        "fib_adiff_range": 100,
        "fib_rdiff_range": 100,
        "fib_t1_range": 100,
        "fib_t2_range": 100,
        "iso_diff_range": 100,
        "iso_t1_range": 100,
        "iso_t2_range": 100,
        "echo_time_range": 200,
        "rep_time_range": 200
    })

    output = parameters.pop("output")
    logging.info("Saving function parameters to {}".format(output))
    json.dump(parameters, open(output, "w+"))


def generate_geometry_json(args):
    logging.info("Generating geometry parameters json file")
    parameters = {k.replace("-", "_"): v for k, v in vars(args).items()}
    parameters = rename_parameters(parameters, {
        "anchors": "base_anchors",
        "bun_max": "max_bundles",
        "bun_var": "n_bundles_var",
        "fib_mean": "n_fibers_mean",
        "fib_var": "n_fibers_var",
        "pert_center": "perturbate_center",
        "pert_var": "perturbation_var"
    })
    parameters["limits"] = np.array(parameters["limits"]).reshape((3, 2))

    logging.debug("Parameters as parsed and ready for function call")
    logging.debug(json.dumps(parameters, indent=4))

    logging.debug("Performing conversion to numpy.arange where required")
    if "rad_range" in parameters:
        parameters["rad_range"] = np.arange(*parameters["rad_range"], 20)

    output = parameters.pop("output")
    logging.info("Saving function parameters to {}".format(output))
    json.dump(parameters, open(output, "w+"))


class Parsers(Enum):
    generate = generate_datasets
    simjson = generate_simulation_json
    geojson = generate_geometry_json


if __name__ == "__main__":
    parser = get_parser()
    args = vars(parser.parse_args())
    logger.debug("Arguments parsed")
    step = args.pop("step")
    logger.debug("Loading parser for {}".format(step))
    Parsers[step](args)
    logger.info("{} ended with success".format(step.capitalize()))
