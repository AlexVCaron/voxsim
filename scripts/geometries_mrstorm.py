import tarfile
from os import makedirs
from shutil import rmtree
from os.path import join
from scipy.stats import norm, vonmises
import numpy as np
import json
import copy

from simulator.factory.geometry_factory.geometry_factory import GeometryFactory, Plane
from simulator.runner.simulation_runner import SimulationRunner


def generate_clusters(
        base_anchors, limits, n_output, rad_dist=norm, rad_range=np.arange(1., 5., 0.2),
        rot_max=np.pi/2., rot_prob=0.7, trans_dist=norm, trans_max=[0.5, 0.5, 0.5],
        trans_prob=0.6, n_bundles_var=0.4, max_bundles=3, n_fibers_mean=6000,
        n_fibers_var=1000, perturbate_center=True, perturbation_var=0.4
):
    clusters = []

    rad_rvs = rad_dist.rvs(np.mean(rad_range), np.var(rad_range), size=100)
    rot_rvs = vonmises.rvs(3.99, rot_max / 2., rot_max / 6., size=100)
    trans_rvs = [
        trans_dist.rvs(tmax / 2., tmax / 6., size=100)
        for tmax in trans_max
    ]
    n_rvs = norm.rvs(max_bundles / 2. + 0.5, n_bundles_var, size=100)

    for i in range(n_output):
        n = int(round(np.random.choice(n_rvs)))
        rads = np.abs(np.random.choice(rad_rvs, size=n))
        bundles, centers = [], []

        for b in range(int(n)):
            translation = [
                np.random.choice(trans_rvs[0]) if np.random.uniform(0, 1) < trans_prob else 0.,
                np.random.choice(trans_rvs[1]) if np.random.uniform(0, 1) < trans_prob else 0.,
                np.random.choice(trans_rvs[2]) if np.random.uniform(0, 1) < trans_prob else 0.
            ]
            rotation = np.random.choice(rot_rvs, size=3)
            planes = np.random.choice([Plane.XY, Plane.YZ, Plane.ZX], size=3)

            bundle = GeometryFactory.create_bundle(rads[b], 1., 5., base_anchors)

            _, bundle = GeometryFactory.translate_bundle(bundle, translation)

            centers.append(np.mean(bundle.get_anchors(), axis=0))

            for j in range(3):
                if np.random.uniform(0, 1) < rot_prob:

                    _, bundle = GeometryFactory.rotate_bundle(
                        bundle, centers[-1], rotation[j], planes[j]
                    )

            bundles.append(bundle)

        world_center = np.mean(centers, axis=0)

        if perturbate_center:
            world_center *= 1.5 - norm.rvs(loc=0, scale=perturbation_var, size=1)

        if any(np.isnan(world_center)):
            raise Exception("World center contains nan !")

        n_fibers = norm.rvs(loc=n_fibers_mean, scale=n_fibers_var)

        meta = GeometryFactory.create_cluster_meta(3, n_fibers, 1, world_center.tolist(), limits)
        cluster = GeometryFactory.create_cluster(meta, bundles)
        clusters.append([cluster])

    return clusters


def generate_geometries(
        clusters_groups, resolution, spacing, output_name_fmt, output_params, output_data, init_i=0,
        geo_ready_callback=lambda a: None, dump_infos=False, singularity_conf=None
):
    geometries_infos = []

    for i, clusters in enumerate(clusters_groups):
        handler = GeometryFactory.get_geometry_handler(resolution, spacing)
        for cluster in clusters:
            handler.add_cluster(cluster)

        hash_table = [cl.serialize() for cl in clusters]
        hash_table.extend(str(resolution + spacing))

        infos = handler.generate_json_configuration_files(output_name_fmt.format(i + init_i), output_params)
        runner = SimulationRunner(output_name_fmt.format(i + init_i), infos, singularity_conf=singularity_conf)

        infos.generate_new_key("hash", hash(str(hash_table)))
        infos.generate_new_key("handler", handler)
        geometries_infos.append(infos)

        makedirs(join(output_data, output_name_fmt.format(i + init_i)), exist_ok=True)
        runner.run(join(output_data, output_name_fmt.format(i + init_i)))
        infos.generate_new_key(
            "data_package",
            join(output_data, "data_package_{}.tar.gz".format(output_name_fmt.format(i + init_i)))
        )
        with tarfile.open(
                join(output_data, "data_package_{}.tar.gz".format(output_name_fmt.format(i + init_i))), "w"
        ) as archive:
            archive.add(join(output_data, output_name_fmt.format(i + init_i)), arcname="data")

        rmtree(join(output_data, output_name_fmt.format(i + init_i)))

        geo_ready_callback(geometries_infos)

    if dump_infos:
        serializable_infos = []
        for info in geometries_infos:
            cp = copy.deepcopy(info)
            cp.pop("handler")
            serializable_infos.append(cp.as_dict())

        json.dump(serializable_infos, open(join(output_data, "description.json"), "w+"))

    return geometries_infos

