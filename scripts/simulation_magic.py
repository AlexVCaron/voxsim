from math import pi

from os import path, mkdir
from numpy import array

from ORM.ConfigBuilder import ConfigBuilder
from ORM.StructureBuilder import StructureBuilder
from ORM.utils.Plane import Plane
from utils.Rotation import rotate_fiber, Rotation

from config import *
from utils.Translation import translate_fiber

meta_dimension = 3
meta_center = [0, 0, 0]
meta_limits = "[0,1].[0,1].[0,1]"
meta_density = 160000
meta_sampling = 1

resolution = [10, 10, 10]

sampling = 30

spheres_center = [
    [-2, 7, 10],
    [2, -1, 11]
]
sphere_radius = 5

base_anchors = [
    [0.5, -0.3, 0.5],
    [0.5, -0.2, 0.5],
    [0.5, -0.1, 0.5],
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
    [0.5, 1.1, 0.5],
    [0.5, 1.2, 0.5],
    [0.5, 1.3, 0.5],
    [0.5, 1.4, 0.5]
]


init_angles = [(pi / 2., Plane.XY), (pi / 4., Plane.YZ)]


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


def generate():
    bundles_meta = StructureBuilder.create_bundle_meta(meta_dimension, meta_density, meta_sampling, meta_center,
                                                       meta_limits)

    bundles = [
        StructureBuilder.create_fiber(6, 1, sampling, base_anchors),
        StructureBuilder.create_fiber(7, 1, sampling, base_anchors),
        StructureBuilder.create_fiber(8, 1, sampling, base_anchors)
    ]

    spheres = [
        ConfigBuilder.create_sphere_object(sphere_radius, spheres_center[0]),
        ConfigBuilder.create_sphere_object(sphere_radius, spheres_center[1])
    ]

    R1, R2 = Rotation(init_angles[0][1]).generate(init_angles[0][0]), Rotation(init_angles[1][1]).generate(
        init_angles[1][0])

    _, bundles[0] = translate_fiber(bundles[0], [], [0, 0, -.2])
    _, bundles[1] = rotate_fiber(bundles[1], [], R1, array([0.5, 0.5, 0.5]), [])
    _, bundles[1] = translate_fiber(bundles[1], [], [0, -.2, -.2])
    _, bundles[2] = rotate_fiber(bundles[2], [], R2, array([0.5, 0.5, 0.5]), [])
    _, bundles[2] = translate_fiber(bundles[2], [], [.2, 0, 0])

    write(bundles_meta, bundles, spheres, 1, 1, 0, True)

if __name__ == "__main__":
    generate()
