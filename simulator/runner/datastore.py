from os.path import basename, exists, join
import pathlib
from shutil import copyfile
from tempfile import TemporaryDirectory

import nibabel as nib
import numpy as np

from simulator.factory import SimulationFactory


class Datastore:
    def __init__(
        self,
        simulation_path,
        fibers,
        compartment_ids,
        inter_axonal_fraction=None,
    ):
        self.fibers = fibers
        self.compartments = []
        self.ids = compartment_ids
        self.stage_path = simulation_path
        self.iaf = inter_axonal_fraction
        self._temp = TemporaryDirectory()

    def unload(self):
        self.compartments = []
        self._temp.cleanup()

    def get_bind_paths(self, bind_compartments=True):
        return [self.fibers] + (
            self.compartments if bind_compartments else list()
        )

    def load_compartments(self, input_folder, run_name, use_nifti=True):
        extension = "nii.gz" if use_nifti else "nrrd"
        fiber_fraction = join(
            input_folder,
            "{}_phantom_mergedBundlesMaps.{}".format(run_name, extension),
        )

        inter_id = SimulationFactory.CompartmentType.INTER_AXONAL.value
        extra1_id = SimulationFactory.CompartmentType.EXTRA_AXONAL_1.value
        extra2_id = SimulationFactory.CompartmentType.EXTRA_AXONAL_2.value

        if inter_id in self.ids:
            assert self.iaf is not None
            self.generate_inter_axonal_fraction(run_name, fiber_fraction)
        else:
            self.add_compartment(fiber_fraction)

        if extra1_id in self.ids or extra2_id in self.ids:
            ellipses = join(
                input_folder,
                "{}_mergedEllipsesMaps.{}".format(run_name, extension),
            )
            if exists(ellipses):
                self.add_compartment(ellipses)
                if extra1_id in self.ids and extra2_id in self.ids:
                    self.add_compartment("generate")
            else:
                self.add_compartment("generate")

            assert (
                len(list(filter(lambda c: c == "generate", self.compartments)))
                <= 1
            )

            if "generate" in self.compartments:
                self.generate_extra_axonal_fraction(run_name)

    def add_compartment(self, filepath):
        self.compartments.append(filepath)

    def stage_compartments(self, run_name):
        extension = ".".join(basename(self.compartments[0]).split(".")[1:])
        for m, cmp_id in zip(self.compartments, self.ids):
            copyfile(
                m,
                join(
                    self.stage_path,
                    "{}_simulation.ffp_VOLUME{}.{}".format(
                        run_name, cmp_id, extension
                    ),
                ),
            )

    def generate_inter_axonal_fraction(self, run_name, fiber_fraction):
        img = nib.load(fiber_fraction)
        fraction = img.get_fdata()
        inter_fraction = self.iaf * fraction
        intra_fraction = fraction - inter_fraction

        nib.save(
            nib.Nifti1Image(inter_fraction, img.affine, img.header),
            join(self._get_temp(), "{}_inter.nii.gz".format(run_name)),
        )
        nib.save(
            nib.Nifti1Image(intra_fraction, img.affine, img.header),
            join(self._get_temp(), "{}_intra.nii.gz".format(run_name)),
        )

        self.add_compartment(
            join(self._get_temp_path(), "{}_intra.nii.gz".format(run_name))
        )
        self.add_compartment(
            join(self._get_temp_path(), "{}_inter.nii.gz".format(run_name))
        )

    def generate_extra_axonal_fraction(self, run_name):
        other_fractions = list(
            filter(lambda c: c != "generate", self.compartments)
        )

        ref = nib.load(other_fractions[0])
        data = np.concatenate(
            [ref[..., None]]
            + [nib.load(f).get_fdata()[..., None] for f in other_fractions[1:]],
            axis=-1,
        )
        extra = np.ones(ref.shape) - np.sum(data, axis=-1)

        nib.save(
            nib.Nifti1Image(extra, ref.affine, ref.header),
            join(self._get_temp_path(), "{}_extra.nii.gz".format(run_name)),
        )

        self.add_compartment(
            join(self._get_temp_path(), "{}_extra.nii.gz".format(run_name))
        )

    def _get_temp(self):
        assert self._temp is not None
        return self._temp

    def _get_temp_path(self) -> pathlib.Path:
        return pathlib.Path(self._get_temp().name)