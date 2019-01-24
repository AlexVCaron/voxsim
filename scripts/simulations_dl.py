from functools import reduce
from math import pi, sqrt
from os import path, listdir, remove, mkdir
from random import randint, uniform
from shutil import copyfile

from numpy import linspace, mgrid, s_, prod, identity
from numpy.core.multiarray import array

from ORM.ConfigBuilder import ConfigBuilder
from ORM.StructureBuilder import StructureBuilder
from ORM.utils.Plane import Plane
from config import *
from utils.Rotation import Rotation, rotate_fiber

if path.exists(path.join(output_path, out_dir_name)) and path.isdir(path.join(output_path, out_dir_name)) and not len(listdir(path.join(
        output_path, out_dir_name))) is 0:
    raise Exception("Output path for voxsim is not empty")

if path.exists(path.join(output_path, voxsim_command_file)) and path.isfile(path.join(output_path, voxsim_command_file)):
    print("voxsim command file written to old")
    copyfile(path.join(output_path, voxsim_command_file), path.join(output_path, voxsim_command_file + "_old"))
    remove(path.join(output_path, voxsim_command_file))

NEX_nb = 5

meta_dimension = 3
meta_center = [0, 0, 0]
meta_limits = "[0,1].[0,1].[0,1]"
meta_density = 2000
meta_sampling = 1

sampling = 30
radius = 2
symmetry = 1

resolution = [10, 10, 10]

base_anchors = [
    [0.5, 0, 0.5],
    [0.5, 0.1, 0.5],
    [0.5, 0.2, 0.5],
    [0.5, 0.3, 0.5],
    [0.5, 0.4, 0.5],
    [0.5, 0.5, 0.5],
    [0.5, 0.6, 0.5],
    [0.5, 0.7, 0.5],
    [0.5, 0.8, 0.5],
    [0.5, 0.9, 0.5],
    [0.5, 1.0, 0.5]
]

no_sphere_intervals = [[3.5, 6.5], [0, 10], [3.5, 6.5]]

spheres_scaling = 1
spheres_radius = 1
spheres_intervals = [
    ([0, 10], [0, 10], [0, 10])
]
decal_sph = array([5, 5, 5])

limits_spheres = [
    ConfigBuilder.create_sphere_object(spheres_radius, [0, 0, 0], spheres_scaling, "yellow"),
    ConfigBuilder.create_sphere_object(spheres_radius, [0, 10, 0], spheres_scaling, "green"),
    ConfigBuilder.create_sphere_object(spheres_radius, [0, 0, 10], spheres_scaling, "red"),
    ConfigBuilder.create_sphere_object(spheres_radius, [10, 0, 0], spheres_scaling, "purple")
]

init_angles = [(None, None), (pi / 2., Plane.XY), (pi / 2., Plane.YZ)]
decal = array([0.5, 0.5, 0.5])

# 0, 10, 20, 30, 40, 50, 60
angles = [pi / 2., pi / 3., pi / 4., pi / 6.]
planes = [None, Plane.XY, Plane.YZ]


def in_interval(pt, center):
    return (pt[0] - center[0]) ** 2 + (pt[1] - center[1]) ** 2 + (pt[2] - center[2]) ** 2 < spheres_radius ** 2


RAND_NUMBER = 3


def get_spheres():
    spheres = []
    for intervals in spheres_intervals:
        for i in linspace(intervals[0][0], intervals[0][1],
                          (intervals[0][1] - intervals[0][0]) / (2. * spheres_radius)):
            for j in linspace(intervals[1][0], intervals[1][1],
                              (intervals[1][1] - intervals[1][0]) / (2. * spheres_radius)):
                for k in linspace(intervals[2][0], intervals[2][1],
                                  (intervals[2][1] - intervals[2][0]) / (2. * spheres_radius)):
                    color = "blue"
                    sphere = ConfigBuilder.create_sphere_object(spheres_radius, [i, j, k], spheres_scaling,
                                                                color)
                    spheres.append(sphere)

    return spheres


def get_fibers(anchors, number):
    return [
        StructureBuilder.create_fiber(
            radius,
            symmetry,
            sampling,
            [[i for i in anchor] for anchor in anchors]
        ) for i in range(number)
    ]


def get_bounding_boxes():
    grid_fibers = array([
        mgrid[[s_[v[0][0]:v[0][1]:float((v[0][1] - v[0][0])) / float(v[1])] for v in
               zip(no_sphere_intervals, resolution)]]
        for i in range(3)
        ])
    return grid_fibers.reshape(len(no_sphere_intervals), 3, prod(grid_fibers.shape[2:])).swapaxes(1, 2)


def rotate_spheres(spheres, rotation, decal):
    o_spheres = []
    for sphere in spheres:
        o_sphere = sphere.copy()
        o_sphere.set_center(((rotation @ (array(sphere.get_center()) - decal)) + decal).tolist())
        o_spheres.append(o_sphere)

    return o_spheres


def remove_spheres(spheres, bbox):
    o_spheres = []
    for sphere in spheres:
        for point in bbox:
            if in_interval(point, sphere.get_center()):
                break
        else:
            o_spheres.append(ConfigBuilder.create_sphere_object(
                    sphere.get_radius(),
                    sphere.get_center(),
                    sphere.get_scaling(),
                    sphere.get_color()
                )
            )

    return o_spheres


def write(meta, fibers, spheres, NEX, k, angle, generate_spheres):
    with open(path.join(output_path, voxsim_command_file), "a+") as f_voxsim_commands:
        structures = [ConfigBuilder.create_bundle_object(
            "",
            [
                vspl_fname_fmt.format(
                    NEX,
                    k,
                    int(angle / pi * 180.) if angle else 0
                )
            ],
            [1],
            [0, 0, 0]
        )]

        if generate_spheres:
            structures += spheres

        world = ConfigBuilder.create_world(3, [10, 10, 10])

        with open(output_path + "/" + bundle_fname_fmt.format(
                              NEX,
                              k,
                              int(angle / pi * 180.) if angle else 0,
                              "_sph" if generate_spheres else ""
                          ), "a+") as f:
            f.write(
                "{\n" +
                "    \"world\": " + world.serialize(indent=6) + ",\n" +
                "    \"path\": \"{0}\"".format(output_path) + ",\n" +
                "    \"structures\": [\n" + "      " + ",\n".join(
                    [structure.serialize(indent=8) for structure in structures]) + "\n    ]\n" +
                "}"
            )

        vxm_out = output_path + "\\\\vxmout\\\\{}".format(
            bundle_fname_fmt.format(
                NEX,
                k,
                int(angle / pi * 180.) if angle else 0,
                "_sph" if generate_spheres else "")
        )

        mkdir(vxm_out)

        f_voxsim_commands.write(
            "I:/vxm2/bld/Voxsim-build/bin/VoxsimDrawCmdApp_release.bat -f " +
            output_path + "\\\\{}".format(
                bundle_fname_fmt.format(
                    NEX,
                    k,
                    int(angle / pi * 180.) if angle else 0,
                    "_sph" if generate_spheres else "")) +
            " -r {0}".format(",".join([str(i) for i in resolution])) +
            " -s 2,2,2 --quiet --comp-map -o " +
            vxm_out + "\\\\mdmd" + "\n"
        )

        bundle = StructureBuilder.create_bundle(meta, fibers)
        with open(output_path + "/" + vspl_fname_fmt.format(
                              NEX,
                              k,
                              int(angle / pi * 180.) if angle else 0
                          ), "a+") as f:

            f.write(bundle.serialize())


def generate_simulations():
    bundle_meta = StructureBuilder.create_bundle_meta(meta_dimension, meta_density, meta_sampling, meta_center,
                                                      meta_limits)

    spheres = get_spheres()
    fibers = get_fibers(base_anchors, 3)
    bounding_boxes = get_bounding_boxes()

    random_planes_possibility = planes + [Plane.ZX]
    get_random_plane = lambda: random_planes_possibility[randint(0, RAND_NUMBER)]
    get_random_angle = lambda: uniform(-pi, pi)

    for angle in angles:

        R = [
            array(Rotation(Plane.YZ).generate(-angle / 2.)),
            array(Rotation(Plane.YZ).generate(angle / 2.)),
            array(Rotation(Plane.ZX).generate(pi / 2.)),
            array(Rotation(Plane.XY).generate(sqrt(3.) / 2. * angle))
        ]
        Rf = [R[0], R[1], R[3] @ R[2]]

        for i in range(NEX_nb):
            r_plane = get_random_plane()
            Rrand = reduce(lambda a, b: a @ b if b is not None else a, [
                array(Rotation(r_plane).generate(get_random_angle())) if r_plane else None for i in range(0, 3)
                ])

            if Rrand is not None:
                spheres = rotate_spheres(spheres, Rrand, decal_sph)
            else:
                Rrand = identity(3)

            w_fibers = []

            w_spheres = [sph.copy() for sph in spheres]

            for R, fiber, bbox in zip(Rf, fibers, bounding_boxes):

                generate_spheres = False
                if randint(0, 1):
                    generate_spheres = True

                if R is not None:
                    bb, f = rotate_fiber(fiber, bbox, Rrand @ R, decal, decal_sph)
                    w_fibers.append(f)
                else:
                    bb, f = rotate_fiber(fiber, bbox, Rrand, decal, decal_sph)
                    w_fibers.append(f)

                if generate_spheres:
                    w_spheres = remove_spheres(w_spheres, bb)

                write(bundle_meta, w_fibers, w_spheres, i, len(w_fibers), angle, generate_spheres)


if __name__ == "__main__":
    generate_simulations()
