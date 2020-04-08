import logging
import tarfile
import json
import copy

from os import makedirs
from shutil import rmtree
from os.path import join, basename
from time import time

import numpy as np

from scipy.stats import norm, vonmises

from simulator.factory.geometry_factory.geometry_factory import GeometryFactory, Plane
from simulator.runner.simulation_runner import SimulationRunner

logger = logging.getLogger(basename(__file__).split(".")[0])


def generate_clusters(
    base_anchors, limits, n_output,
    rad_dist=norm, rad_range=np.arange(1., 5., 0.2),
    rot_max=np.pi/2., rot_prob=0.7,
    trans_dist=norm, trans_max=(0.5, 0.5, 0.5), trans_prob=0.6,
    n_bundles_var=0.4, max_bundles=3,
    n_fibers_mean=6000, n_fibers_var=1000,
    perturbate_center=True, perturbation_var=0.4,
    world_scale=np.eye(3), initial_translation=np.zeros(3)
):

    clusters = []
    initial_translation = np.array(initial_translation) \
        if isinstance(initial_translation, (list, tuple)) \
        else initial_translation

    rad_rvs = rad_dist.rvs(np.mean(rad_range), np.var(rad_range), size=100)
    rot_rvs = vonmises.rvs(3.99, rot_max / 2., rot_max / 6., size=100)
    trans_rvs = [
        trans_dist.rvs(tmax / 2., tmax / 6., size=100)
        for tmax in trans_max
    ]
    n_rvs = norm.rvs(max_bundles / 2. + 0.5, n_bundles_var, size=100)

    for i in range(n_output):

        n = int(round(np.random.choice(n_rvs)))
        while n < 1:
            n = int(round(np.random.choice(n_rvs)))

        rads = np.abs(np.random.choice(rad_rvs, size=n))
        bundles, centers = [], []

        for b in range(int(n)):
            translation = [
                np.random.choice(trans_rvs[0])
                if np.random.uniform(0, 1) < trans_prob else 0.,
                np.random.choice(trans_rvs[1])
                if np.random.uniform(0, 1) < trans_prob else 0.,
                np.random.choice(trans_rvs[2])
                if np.random.uniform(0, 1) < trans_prob else 0.
            ]
            rotation = np.random.choice(rot_rvs, size=3)
            planes = np.random.choice([Plane.XY, Plane.YZ, Plane.ZX], size=3)

            bundle = GeometryFactory.create_bundle(
                rads[b], 1., 5., base_anchors
            )

            _, bundle = GeometryFactory.translate_bundle(
                bundle, translation
            )

            centers.append(np.mean(bundle.get_anchors(), axis=0))

            for j in range(3):
                if np.random.uniform(0, 1) < rot_prob:

                    _, bundle = GeometryFactory.rotate_bundle(
                        bundle, centers[-1], rotation[j], planes[j]
                    )

            bundles.append(bundle)

        world_center = np.mean(centers, axis=0) + initial_translation

        if perturbate_center:
            world_center *= 1 + norm.rvs(loc=0, scale=perturbation_var, size=1)

        world_center = world_scale @ world_center

        if any(np.isnan(world_center)):
            raise Exception("World center contains nan !")

        n_fibers = norm.rvs(loc=n_fibers_mean, scale=n_fibers_var)

        meta = GeometryFactory.create_cluster_meta(3, n_fibers, 1, world_center.tolist(), limits)
        cluster = GeometryFactory.create_cluster(meta, bundles)
        clusters.append([cluster])

    return clusters


def generate_geometries(
        clusters_groups, resolution, spacing, output_name_fmt, output_params, output_data, init_i=0,
        geo_ready_callback=lambda *args, **kwargs: None, callback_stride=-1, dump_infos=False, singularity_conf=None, get_timings=False
):
    extra_package = {}
    if get_timings:
        extra_package["timings"] = []

    geometries_infos = []
    persistent_infos = []

    for geo_idx, clusters in enumerate(clusters_groups):
        handler = GeometryFactory.get_geometry_handler(resolution, spacing)
        for cluster in clusters:
            handler.add_cluster(cluster)

        hash_table = [cl.serialize() for cl in clusters]
        hash_table.extend(str(resolution + spacing))

        infos = handler.generate_json_configuration_files(output_name_fmt.format(geo_idx + init_i), output_params)
        runner = SimulationRunner(output_name_fmt.format(geo_idx + init_i), infos, singularity_conf=singularity_conf)

        infos.generate_new_key("hash", hash(str(hash_table)))
        infos.generate_new_key("handler", handler)
        geometries_infos.append(infos)

        makedirs(join(output_data, output_name_fmt.format(geo_idx + init_i)), exist_ok=True)

        if get_timings:
            extra_package["timings"].append(time())

        runner.run(join(output_data, output_name_fmt.format(geo_idx + init_i)))

        if get_timings:
            extra_package["timings"][-1] = (
                time() - extra_package["timings"][-1]
            )
            logger.debug("Geometry took {} s".format(
                extra_package["timings"][-1]
            ))

        infos.generate_new_key(
            "data_package",
            join(output_data, "data_package_{}.tar.gz".format(output_name_fmt.format(geo_idx + init_i)))
        )
        with tarfile.open(
                join(output_data, "data_package_{}.tar.gz".format(output_name_fmt.format(geo_idx + init_i))), "w"
        ) as archive:
            archive.add(join(output_data, output_name_fmt.format(geo_idx + init_i)), arcname="data")

        rmtree(join(output_data, output_name_fmt.format(geo_idx + init_i)))

        if callback_stride > 0 and (geo_idx + 1) % callback_stride == 0:
            if geo_ready_callback(
                copy.deepcopy(geometries_infos),
                idx=int((geo_idx + 1) / callback_stride),
                extra=extra_package
            ):
                if dump_infos:
                    persistent_infos.extend(geometries_infos)
                geometries_infos.clear()
                if get_timings:
                    extra_package["timings"].clear()

    if callback_stride > 0 and len(clusters_groups) % callback_stride > 0:
        if geo_ready_callback(
            copy.deepcopy(geometries_infos),
            idx=int(len(clusters_groups) / callback_stride) + 1,
            end=True,
            extra=extra_package
        ):
            if dump_infos:
                persistent_infos.extend(geometries_infos)
            geometries_infos.clear()

    if dump_infos:
        serializable_infos = []
        for info in geometries_infos + persistent_infos:
            cp = copy.deepcopy(info)
            cp.pop("handler")
            serializable_infos.append(cp.as_dict())

        json.dump(serializable_infos, open(join(output_data, "description.json"), "w+"))

    return geometries_infos + persistent_infos
