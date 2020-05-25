import multiprocessing
from multiprocessing.pool import ThreadPool
from asyncio import coroutine
from unittest import TestCase, mock
import numpy as np
import sys
import importlib
import tempfile
import copy


class TestMrStormGenerate_datasets(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._open_patches = []
        self._packages = {}
        self._modules = {}
        self._mpi = {"mpi": importlib.import_module("mpi4py.MPI"), "mpi4py": importlib.import_module("mpi4py")}

    def _import_dependencies(self):
        importlib.invalidate_caches()
        self._packages["json"] = importlib.import_module("json")
        self._packages["os"] = importlib.import_module("os")
        self._packages["path"] = importlib.import_module("os.path")
        self._packages["shutil"] = importlib.import_module("shutil")
        self._packages["tarfile"] = importlib.import_module("tarfile")
        self._packages["lxml"] = importlib.import_module("lxml.etree")

    def _import_modules(self):
        self._modules["script"] = importlib.import_module("scripts.mrstorm_simu_cluster")
        self._modules["geo_script"] = importlib.import_module("scripts.geometries_mrstorm")
        self._modules["sim_script"] = importlib.import_module("scripts.simulations_mrstorm")
        self._modules["geo_handler"] = importlib.import_module("simulator.factory.geometry_factory.handlers.geometry_handler")
        self._modules["sim_handler"] = importlib.import_module("simulator.factory.simulation_factory.handlers.simulation_handler")
        self._modules["sim_runner"] = importlib.import_module("simulator.runner.simulation_runner")

    def _reload_modules(self):
        for module in self._modules.values():
            importlib.reload(module)

    def _reload_dependencies(self):
        for package in self._packages.values():
            importlib.reload(package)

    def _create_patch(self, target, *args, **kwargs):
        self._open_patches.append(mock.patch(target, *args, **kwargs))
        self._open_patches[-1].start()
        return self._open_patches[-1]

    def _stop_patches(self, clear=True):
        for patch in self._open_patches:
            patch.stop()

        if clear:
            self._open_patches.clear()

    def _start_patches(self):
        for patch in self._open_patches:
            patch.start()

    def _patch_mpi(self, mpi4py_mock, mpi_mock):
        sys.modules.update([("mpi4py.MPI", mpi_mock)])
        sys.modules.update([("mpi4py", mpi4py_mock)])

    def _unpatch_mpi(self):
        sys.modules.update([("mpi4py.MPI", self._mpi["mpi"])])
        sys.modules.update([("mpi4py", self._mpi["mpi4py"])])

    def mock_imports(self, params, setup_dict={}):
        mpi4py_mock = mock.MagicMock(spec=self._mpi["mpi4py"])
        mpi_mock = mock.MagicMock(spec=self._mpi["mpi"])
        comm_world = mock.MagicMock(spec=self._mpi["mpi"].COMM_WORLD)

        # Setup mocked classes global attributes
        comm_world.Get_size = mock.MagicMock(return_value=3)

        future_mock = mock.MagicMock(spec=self._mpi["mpi"].Request)
        future_mock.wait = mock.MagicMock()
        comm_world.isend = mock.MagicMock(return_value=future_mock)
        comm_world.irecv = mock.Mock(return_value=future_mock)

        import simulator.utils.test_helpers.geometry_helper as gh
        dummy_hash_dict = self.generate_dummy_hash_dict({
            "file_path": "FILEPATH",
            "resolution": params["resolution"],
            "spacing": params["spacing"],
            "n_maps": 2,
            "data_path": "DATAPATH",
            "data_package": "PACKAGE.TAR.GZ",
            "data_path": "DATAPATH",
            "handler": gh.GeometryHelper.get_dummy_geometry_handler()
        }, geo_fmt=params["geo-fmt"])
        comm_world.gather = mock.Mock(return_value=[dummy_hash_dict for i in range(3)])
        comm_world.bcast = mock.Mock(return_value=dummy_hash_dict)

        mpi_mock.COMM_WORLD = comm_world
        mpi4py_mock.MPI = mpi_mock

        modules = {
            "simulation_runner": mock.MagicMock(),
            "mpi4py": mpi4py_mock,
            "mpi": mpi_mock
        }

        modules = {k: setup_dict[k](modules[k]) if k in setup_dict.keys() else modules[k] for k in modules.keys()}

        modules["simulation_runner"] = self._create_patch(
            "simulator.runner.simulation_runner.SimulationRunner",
            modules["simulation_runner"]
        )

        self._patch_mpi(modules["mpi4py"], modules["mpi"])

        return modules

    def mock_vars(self, slurm_tmp="SLURM_TMPDIR"):
        self._packages["os"].environ.update({
            "SLURM_TMPDIR": slurm_tmp
        })
        return {
            "environ": self._create_patch("os.environ", self._packages["os"].environ)
        }

    def _parse_kwargs(self, key, **kwargs):
        print(key)
        return kwargs[key] if key in kwargs else {}

    def _mock_tarfile(self, **kwargs):
        return {
            "tarfile": self._create_patch(
                "tarfile.open", mock.create_autospec(
                    self._packages["tarfile"].open, **self._parse_kwargs("tarfile", **kwargs)
                )) if not isinstance(self._packages["tarfile"].open, mock.Mock) else self._packages["tarfile"].open
        }

    def mock_methods(self, mock_archiving=True, **kwargs):
        dummy_config = {"singularity_path": "SINGULARITY", "singularity_name": "SINGULARITY"}
        d = dict(**{
            "remove": self._create_patch(
                "os.remove", mock.create_autospec(self._packages["os"].remove, **self._parse_kwargs("remove", **kwargs))
            ) if not isinstance(self._packages["os"].remove, mock.MagicMock) else self._packages["os"].remove,
            "exists": self._create_patch(
                "os.path.exists",
                mock.create_autospec(
                    self._packages["path"].exists, return_value=False, **self._parse_kwargs("exists", **kwargs)
                )) if not isinstance(self._packages["path"].exists, mock.MagicMock) else self._packages["path"].exists,
            "rmtree": self._create_patch(
                "shutil.rmtree", mock.create_autospec(
                    self._packages["shutil"].rmtree, **self._parse_kwargs("rmtree", **kwargs)
                )) if not isinstance(self._packages["shutil"].rmtree, mock.MagicMock) else self._packages["shutil"].rmtree,
            "json_load": self._create_patch(
                "json.load", mock.create_autospec(
                    self._packages["json"].load, **self._parse_kwargs("json_load", **kwargs)
                )) if not isinstance(self._packages["json"].load, mock.Mock) else self._packages["json"].load,
            "open": self._create_patch("builtins.open", mock.mock_open(**self._parse_kwargs("open", **kwargs))),
            "get_config": self._create_patch(
                "config.get_config",
                mock.MagicMock(return_value=dummy_config, **self._parse_kwargs("get_config", **kwargs))
            ),
            "override_config": self._create_patch(
                "config.override_config", mock.MagicMock(**self._parse_kwargs("override_config", **kwargs))
            ),
            "copyfile": self._create_patch(
                "shutil.copyfile", mock.create_autospec(
                    self._packages["shutil"].copyfile, **self._parse_kwargs("copyfile", **kwargs)
                )) if not isinstance(self._packages["shutil"].copyfile, mock.MagicMock) else self._packages["shutil"].copyfile
        }, **(self._mock_tarfile(**kwargs) if mock_archiving else {}))

        return d

    def mock_outputs(self, **kwargs):
        return {
            "makedirs": self._create_patch(
                "os.makedirs", mock.create_autospec(
                    self._packages["os"].makedirs, **self._parse_kwargs("makedirs", **kwargs)
                )),
            "json_dump": self._create_patch(
                "json.dump", mock.create_autospec(
                    self._packages["json"].dump, **self._parse_kwargs("json_dump", **kwargs)
                )),
            "lxml": self._create_patch(
                "lxml.etree", mock.create_autospec(self._packages["lxml"], **self._parse_kwargs("lxml", **kwargs))
            )
        }

    def generate_dummy_hash_dict(self, base_dict={}, geo_fmt="{}", n_geo=20):
        from simulator.factory.geometry_factory.handlers.geometry_infos import GeometryInfos
        alphabet = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')

        def make_hashable(np_array):
            np_array.flags.writeable = False
            return np_array.data.tobytes()

        return {
            hash(make_hashable(np.random.randint(0, 100, 100))): GeometryInfos(**{**{
                k: v for k, v in zip(np.random.choice(alphabet, 5), np.random.choice(alphabet, 5))
            }, **base_dict, **{"base_file": "{}_base.json".format(geo_fmt.format(i))}}) for i in range(n_geo)
        }

    def _unwrap(self, tup):
        return [i for l in tup for i in l]

    def setUp(self):
        self._import_dependencies()
        self._import_modules()

    def get_init_args(self, output=None):
        output = output if output else "out"

        geo_args = {
            "base_anchors": [[0, 0, 0], [0.3, 0.3, 0.3], [0.6, 0.6, 0.6], [0.9, 0.9, 0.9]],
            "limits": [[0, 1], [0, 1], [0, 1]],
            "n_output": 30
        }

        simu_args = {
            "bvalues": [1, 2, 3, 4],
            "randomize_bvecs": False,
            "n_simulations": 9
        }

        # Test generation parameters
        args = {
            "geojson": "geojson",
            "simjson": "simjson",
            "resolution": [10, 10, 10],
            "spacing": [2, 2, 2],
            "geo-fmt": "geo{}",
            "out": output,
            "geoout": "geoout",
            "simout": "simout"
        }

        return args, geo_args, simu_args

    def _run_test(
            self, n_instances, args, geo_args, simu_args, output=None,
            create_instance_output=False, mock_archiving=True, import_setup={},
            multithread_pool=None
    ):
        mocks = [{} for i in range(n_instances)]
        # Start generation
        if multithread_pool:
            t_bf_args = (args, create_instance_output, geo_args)
            t_af_args = (import_setup, mock_archiving, n_instances, output, simu_args)
            t_out = multithread_pool.imap_unordered(
                self._run_test_loop, (t_bf_args + (i,) + t_af_args for i in range(n_instances))
            )

            multithread_pool.close()
            multithread_pool.join()

            i = 0
            for out in t_out:
                mocks[i] = out.get()
                i += 1
        else:
            for i in range(n_instances):
                mocks[i] = self._run_test_loop(
                    args, create_instance_output, geo_args,
                    i, import_setup, mock_archiving,
                    n_instances, output, simu_args
                )

        return mocks

    def _run_test_loop(
            self, in_args
    ):

        print(in_args)
        args, create_instance_output, geo_args, n_instance, import_setup, mock_archiving, n_instances, output, simu_args = in_args

        mocks = {}

        mock_methods_dict = {
            "json_load": {"side_effect": [copy.deepcopy(geo_args), copy.deepcopy(simu_args)]}
        }

        if output:
            if create_instance_output:
                output = self._packages["os"].path.join(output, "ins{}_out".format(n_instance))
                self._packages["os"].makedirs(output, exist_ok=True)

            class MockOpenWritable(mock.MagicMock):
                def __call__(self, *args, **kwargs):
                    if "w" in args or "w+" in args or (
                            'mode' in kwargs.keys() and kwargs['mode'] in ["w", "w+", "a"]
                    ):
                        mocks["methods"]["open"].stop()
                        file = open(*args, **kwargs)
                        self.return_value = file
                        mocks["methods"]["open"].start()
                    else:
                        self.return_value = mock.Mock()

                    return super().__call__(*args, **kwargs)

            mock_methods_dict["open"] = {"mock": MockOpenWritable()}

        params = {
            "resolution": args["resolution"],
            "spacing": args["spacing"],
            "geo-fmt": args["geo-fmt"]
        }
        slave_args = copy.deepcopy(geo_args)

        if "n_output" in slave_args.keys():
            slave_args["n_output"] = int(slave_args["n_output"] / n_instances)

        mocked_imports = self.mock_imports(params, import_setup)
        mocked_imports["mpi"].COMM_WORLD.Get_rank = mock.Mock(return_value=n_instance)
        mocked_imports["mpi"].COMM_WORLD.irecv.return_value.wait.return_value = copy.deepcopy(slave_args)
        mocks["imports"] = mocked_imports
        self._reload_dependencies()
        print(mock_archiving)
        print(mock_methods_dict)
        mocks["methods"] = self.mock_methods(mock_archiving, **mock_methods_dict)
        if output is None:
            mocks["outputs"] = self.mock_outputs()

        self._reload_modules()

        root_output = {}
        if output:
            root_output["slurm_tmp"] = output

        mocks["vars"] = self.mock_vars(**root_output)
        self._modules["script"].generate_datasets(args)

        self._stop_patches()
        self._unpatch_mpi()

        return mocks

    def _validate_common(self, mocks, parameters):
        mpi_module = self._mpi["mpi4py"]

        mpi_mock = mocks["imports"]["mpi"]
        self.assertEqual(mpi_mock.__class__, mpi_module.MPI.__class__)
        self.assertFalse(mpi_mock.called)

        comm_mock = mpi_mock.COMM_WORLD
        self.assertEqual(comm_mock.__class__, mpi_module.MPI.COMM_WORLD.__class__)
        self.assertFalse(comm_mock.called)

        comm_mock.Get_size.assert_called_once()
        comm_mock.Get_rank.assert_called_once()
        comm_mock.gather.assert_called_once()
        comm_mock.bcast.assert_called_once()

    def _validate_master(self, mocks, parameters):
        # Validate MPI calls
        self._validate_common(mocks, parameters)

        comm_mock = mocks["imports"]["mpi"].COMM_WORLD

        geo_json = parameters["geo_json"]["input"]
        if "n_output" in geo_json.keys():
            geo_json["n_output"] = int(geo_json["n_output"] / parameters["n_instances"])

        isend_calls = [mock.call(geo_json, dest=i, tag=11) for i in range(1, parameters["n_instances"])]
        comm_mock.isend.assert_called()
        self.assertEqual(comm_mock.isend.call_count, parameters["n_instances"] - 1)
        comm_mock.isend.assert_has_calls(isend_calls)

        req_mock = comm_mock.isend.return_value
        req_mock.wait.assert_called()
        self.assertEqual(req_mock.wait.call_count, parameters["n_instances"] - 1)

    def _validate_slave(self, mocks, parameters):
        # Validate MPI calls
        self._validate_common(mocks, parameters)

        comm_mock = mocks["imports"]["mpi"].COMM_WORLD
        comm_mock.irecv.assert_called_once()
        comm_mock.irecv.assert_called_once_with(source=0, tag=11)

        req_mock = comm_mock.irecv.return_value
        req_mock.wait.assert_called_once()

    def _validate_outputs(self, mock_lists, parameters):
        from os import listdir
        from os.path import isfile, join

        mpi_mock = mock_lists[0]["imports"]["mpi"]

        output_root = join(parameters["args"]["out"], "params")
        n_total_geo = parameters["geo_json"]["input"]["n_output"]
        n_mocked_geo = len(mpi_mock.COMM_WORLD.bcast.return_value.keys())
        n_sim_per_geo = parameters["sim_json"]["input"]["n_simulations"]

        geo_files = list(filter(lambda f: isfile(join(output_root, "geo", f)), listdir(join(output_root, "geo"))))
        sim_files = list(filter(lambda f: isfile(join(output_root, "sim", f)), listdir(join(output_root, "sim"))))

        self.assertEqual(len(geo_files), 2 * n_total_geo)
        self.assertEqual(len(sim_files), n_mocked_geo * n_sim_per_geo + 1)

    def test_outputs(self):
        # Test parameters
        n_instances = 3
        tmp_output = tempfile.mkdtemp()
        args, geo_args, simu_args = self.get_init_args(tmp_output)

        parameters = {
            "n_instances": n_instances,
            "geo_json": {"input": copy.deepcopy(geo_args)},
            "sim_json": {"input": copy.deepcopy(simu_args)},
            "args": args
        }

        # Run tests
        mock_lists = self._run_test(n_instances, args, geo_args, simu_args, tmp_output)

        # Validate mocks
        self._validate_master(mock_lists[0], copy.deepcopy(parameters))
        for i in range(1, len(mock_lists)):
            self._validate_slave(mock_lists[i], copy.deepcopy(parameters))

        self._validate_outputs(mock_lists, copy.deepcopy(parameters))

    def test_intensive(self):
        # Test parameters
        n_instances = 3
        args, geo_args, simu_args = self.get_init_args()

        parameters = {
            "n_instances": n_instances,
            "geo_json": {"input": copy.deepcopy(geo_args)},
            "sim_json": {"input": copy.deepcopy(simu_args)},
            "args": args
        }

        # Run tests
        mock_lists = self._run_test(n_instances, args, geo_args, simu_args)

        # Validate mocks
        self._validate_master(mock_lists[0], parameters)
        for i in range(1, len(mock_lists)):
            self._validate_slave(mock_lists[i], parameters)

    def test_multitalk(self):
        # Test parameters
        n_instances = 3
        tmp_output = tempfile.mkdtemp()
        args, geo_args, simu_args = self.get_init_args(tmp_output)

        parameters = {
            "n_instances": n_instances,
            "geo_json": {"input": copy.deepcopy(geo_args)},
            "sim_json": {"input": copy.deepcopy(simu_args)},
            "args": args
        }

        # Creating the multiprocessing pool that will simulate the multi nodes on the cluster
        pool = ThreadPool(processes=n_instances)
        geo_dicts_queue = multiprocessing.Queue(maxsize=n_instances)
        geo_out_queue = multiprocessing.Queue(maxsize=n_instances - 1)

        # Setup Mock for simulation runner so we stop the processing just at the last time
        sim_runner = self._modules["sim_runner"].SimulationRunner
        patch_stop, patch_start = self._stop_patches, self._start_patches
        os_module = self._packages["os"]

        def configure_runner_mock(mck):
            def create_dummy_output(command, log_file, tag):
                patch_stop(clear=False)

                args = command.rstrip(" -v").split(" ")
                output_position = list(filter(lambda kv: kv[1] == "-o", enumerate(args)))[0][0] + 1
                output = os_module.path.dirname(args[output_position])
                naming = os_module.path.basename(args[output_position])
                for i in range(5):
                    with open(os_module.path.join(output, "{}_{}.tmpf".format(naming, i)),
                              "w+") as f:
                        f.write("I'm the deamon")

                patch_start()

            class MockSimuRunner(sim_runner):
                def __init__(self, base_naming, geometry_infos, simulation_infos=None):
                    super().__init__(base_naming, geometry_infos, simulation_infos)
                    self._launch_command = mock.MagicMock(side_effect=coroutine(create_dummy_output))
                    self._rename_and_copy_compartments_standalone = mock.MagicMock()
                    self._rename_and_copy_compartments = mock.MagicMock()
                    self._generate_background_map = mock.MagicMock()

            return MockSimuRunner

        # Building mock for MPI.COMM_WORLD.gather in order to return infos containing
        # a valid data_package existing in memory
        class MultithreadGatherMock(mock.MagicMock):
            def __call__(self, *args, **kwargs):
                geo_dicts_queue.put(args[0])
                if geo_dicts_queue.full():
                    r_val = []
                    for i in range(geo_dicts_queue.maxsize):
                        r_val += [geo_dicts_queue.get()]
                        geo_dicts_queue.task_done()

                    for i in range(geo_out_queue.maxsize):
                        geo_out_queue.put(r_val)

                    geo_out_queue.join()
                    self.return_value = r_val
                    return super().__call__(*args, **kwargs)

                r_val = geo_out_queue.get()
                geo_out_queue.task_done()
                geo_out_queue.join()

                self.return_value = r_val
                return super().__call__(*args, **kwargs)

        class MultithreadBcastMock(mock.MagicMock):
            def __call__(self, *args, **kwargs):
                geo_dicts_queue.put(args[0])
                if geo_dicts_queue.full():
                    best_idx = 0
                    best_len = 0
                    r_val = []
                    for i in range(geo_dicts_queue.maxsize):
                        r_val += [geo_dicts_queue.get()]
                        if len(r_val[-1].keys()) > best_len:
                            best_len = len(r_val[-1].keys())
                            best_idx = len(r_val) - 1
                        geo_dicts_queue.task_done()

                    for i in range(geo_out_queue.maxsize):
                        geo_out_queue.put(r_val[best_idx])

                    geo_out_queue.join()
                    self.return_value = r_val[best_idx]
                    return super().__call__(*args, **kwargs)

                r_val = geo_out_queue.get()
                geo_out_queue.task_done()
                geo_out_queue.join()
                self.return_value = r_val
                return super().__call__(*args, **kwargs)

        def edit_mpi_comm_mock(mpi_mock):
            mpi_mock.COMM_WORLD.gather = MultithreadGatherMock()
            mpi_mock.COMM_WORLD.bcast = MultithreadBcastMock()
            return mpi_mock

        def edit_mpi4py_mock(mpi_mock):
            mpi_mock.MPI.COMM_WORLD.gather = MultithreadGatherMock()
            mpi_mock.MPI.COMM_WORLD.bcast = MultithreadBcastMock()
            return mpi_mock

        # Run tests
        mock_lists = self._run_test(
            n_instances, args, geo_args, simu_args, tmp_output,
            create_instance_output=True, mock_archiving=False,
            import_setup={
                "simulation_runner": configure_runner_mock,
                "mpi": edit_mpi_comm_mock,
                "mpi4py": edit_mpi4py_mock
            },
            multithread_pool=pool
        )

        # Validate mocks
        self._validate_master(mock_lists[0], parameters)
        for i in range(1, len(mock_lists)):
            self._validate_slave(mock_lists[i], parameters)
