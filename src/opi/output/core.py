"""
This module contains the main class for output handling.
It's mostly based on the ORCA's two JSONs files.
"""

import json
from pathlib import Path
from typing import Any, Callable, cast
from warnings import warn

import numpy as np
import numpy.typing as npt
from pydantic import StrictInt, StrictStr

from opi.execution.core import Runner
from opi.input.structures import Atom, Coordinates, Structure
from opi.output.cube import CubeOutput
from opi.output.gbw_suffix import GbwSuffix
from opi.output.grepper.recipes import (
    get_float_from_line,
    has_geometry_optimization_converged,
    has_scf_converged,
    has_terminated_normally,
)
from opi.output.hftyp import Hftyp
from opi.output.mo_data import MOData
from opi.output.models.base.strict_types import (
    StrictFiniteFloat,
    StrictNonNegativeInt,
    StrictPositiveFloat,
    StrictPositiveInt,
)
from opi.output.models.json.gbw.gbw_results import GbwResults
from opi.output.models.json.gbw.properties.mo import MO
from opi.output.models.json.property.properties.dipole_moment import DipoleMoment
from opi.output.models.json.property.properties.energy import Energy
from opi.output.models.json.property.properties.energy_list import EnergyList
from opi.output.models.json.property.properties.hirshfeld_population_analysis import (
    HirshfeldPopulationAnalysis,
)
from opi.output.models.json.property.properties.mayer_population_analysis import (
    MayerPopulationAnalysis,
)
from opi.output.models.json.property.properties.mbis_population_analysis import (
    MbisPopulationAnalysis,
)
from opi.output.models.json.property.properties.polarizability import Polarizability
from opi.output.models.json.property.properties.population_analysis import (
    ChelpgPopulationAnalysis,
    LoewdinPopulationAnalysis,
    MullikenPopulationAnalysis,
)
from opi.output.models.json.property.properties.quadrupole_moment import QuadrupoleMoment
from opi.output.models.json.property.property_results import (
    PropertyResults,
)
from opi.utils.misc import check_minimal_version, lowercase
from opi.utils.orca_version import OrcaVersion
from opi.utils.units import AU_TO_ANGST, AU_TO_EV


class Output:
    """
    Class that handles of ORCA output, especially the `<basename>.json` `<basename>.property.json`

    Attributes
    ----------
    basename: str
        Basename of the job.
    working_dir: Path
        Optional path to the working directory.
    results_properties: PropertyResults
        Properties parsed from `property.json`.
        Should be preferred over `property_json_data`.
    results_gbw: GbwResults
        Data parsed from `<basename>.json`.
        Should be preferred over `gbw_json_data`.
    property_json_data: dict[str, Any]
        JSON tree read from `<basename>.property.json`.
    gbw_json_data: dict[str, Any]
        JSON tree of read from `<basename>.json`.
    do_redump_jsons: bool, default: False
        Redump JSONs files after parsing. This is mostly meant for debugging.
    """

    def __init__(
        self,
        basename: str,
        *,
        working_dir: Path | None = None,
        version_check: bool = True,
        parse: bool = False,
    ):
        """
        ORCA output parser that is mainly based on the JSON-property and JSON-GBW file.
        It can also read strings from the output file (if present).
        All files are determined based on the job basename given at initialization.

        Arguments
        ---------
        basename: str
            Basename of the job.
        working_dir: Path
            Optional path to the working directory.
        version_check: bool, default: True
            If True, check if the ORCA version stored in JSON-property file is compliant with the minimal supported ORCA version of this interface.
            A warning is printed if the version check is not passed.
            If the version check runs into an error a ValueError is raised.
        parse: bool, default: False
            True: Create (if turned on by `create_gbw_json/create_property_json`) and parse JSONs files at the end of the initialization.
            False: Only return an Output object. In order to use the object to access the JSON data,
                   `Output.parse()` has to be called first.

        Raises
        ----------
        FileExistsError
            If multi-gbw files from different multi-gbw runs exist (e.g., scan and neb).
        """
        self.basename = basename
        self.do_version_check = version_check

        self.working_dir = working_dir.expanduser().resolve() if working_dir else Path.cwd()
        if not self.working_dir.is_dir():
            raise FileNotFoundError(f"Working dir does not exist: {working_dir}")

        # // JSON PATHS
        self.gbw_json_files = self.get_gbw_json_files()
        self.property_json_file = self.get_file(".property.json")

        # > // REDUMP JSON AFTER PARSING
        self.do_redump_jsons: bool = False

        # > // RAW JSON TREES
        self.gbw_json_data: list[dict[str, Any]] | None = None
        self.property_json_data: dict[str, Any] | None = None

        # > // PARSED JSON TREES
        self.results_properties: PropertyResults | None = None
        self.results_gbw: list[GbwResults] | None = None

        # // CREATE AND PARSE JSONS FILES
        if parse:
            self.parse()

    def parse(
        self,
        do_create_property_json: bool | None = None,
        do_create_gbw_json: bool | None = None,
        read_prop_json: bool = True,
        read_gbw_json: bool = True,
    ) -> None:
        """
        Create property- and gbw-JSON file (according to `do_create_property_json` and `do_create_gbw_json`).
        Creates the required files with the default `None` without overwriting any JSON files.

        Parameters
        ----------
        do_create_property_json: bool | None, default: None
            Whether to create the property JSON file. If None, the file is only created if it is missing. If True,
            the existing file will be overwritten. If False, the file will not be created. Default is None.
        do_create_gbw_json: bool | None, default: None
            Whether to create the gbw JSON files. If None, the files are only created if they are missing. If True,
            the existing files will be overwritten. If False, the files will not be created. Default is None.
        read_prop_json: bool, default: True
            Whether to read the property JSON file. If True, the file will be read. If False, the file will not
            be read. If the file should be read but is not present, a FileNotFoundError is raised.
        read_gbw_json: bool, default: True
            Whether to read the gbw JSON files. If True, the base gbw JSON file and any gbw JSON files from multi gbw
            runs (e.g., scan or neb) will be read. If False, none of these files will be read.
            If any of the JSON files that should be read are not present, a FileNotFoundError is raised.

        Raises
        ----------
        FileNotFoundError
            If any JSON file should be read that is not present.
        """
        # // Create JSONs files
        # // GBW JSON files
        if do_create_gbw_json is None:
            self.create_missing_gbw_json()
        elif do_create_gbw_json:
            self.create_gbw_json(force=True)

        # // Property JSON file
        if do_create_property_json is None:
            self.create_missing_property_json()
        elif do_create_property_json:
            self.create_property_json(force=True)

        # // PARSE JSONS
        # // Property JSON
        if read_prop_json:
            self.property_json_data = self._process_json_file(self.property_json_file)
            # > Check in property json whether version fits:
            if self.do_version_check:
                self.check_version()
            self.results_properties = PropertyResults(**self.property_json_data)
        else:
            if self.do_version_check:
                warn("No version check possible.")

        # // GBW JSON file
        if read_gbw_json:
            self.gbw_json_data = [self._process_json_file(file) for file in self.gbw_json_files]
            self.results_gbw = [GbwResults(**data) for data in self.gbw_json_data]

        # > Redump JSON files
        if self.do_redump_jsons:
            self._redump_jsons()

    @property
    def num_gbw_json_files(self) -> int:
        return len(self.gbw_json_files) if self.gbw_json_files else 0

    @property
    def num_gbw_json_data(self) -> int:
        return len(self.gbw_json_data) if self.gbw_json_data else 0

    @property
    def num_results_gbw(self) -> int:
        return len(self.results_gbw) if self.results_gbw else 0

    def _read_json(self, json_file: Path, /) -> dict[str, Any]:
        """
        Read a JSON file and return its JSON tree.

        Parameters
        ---------
        json_file: Path
            Path to the JSON file to be read.

        Returns
        -------
        dict[str, Any]
            The JSON tree.

        Raises
        ------
        FileNotFoundError
            If the Path leads to no file
        """

        if not json_file.is_file():
            raise FileNotFoundError(f"JSON file does not exist: {json_file}")

        with json_file.open() as f_json:
            json_data: dict[str, Any] = json.load(f_json)
            return json_data

    def _process_json_file(self, json_file: Path, /) -> dict[str, Any]:
        """
        Read the JSON file and convert all keys to lowercase.

        Parameters
        ----------
        json_file : Path
            Path to JSON file to be read.
        """

        json_data: dict[str, Any] = self._read_json(json_file)
        # > Convert all keys to lowercase.
        lowercase(json_data)
        return json_data

    def _redump_jsons(self) -> None:
        """Redump both JSON files as read and parse by `PropertyResults` and `GbwResults`."""

        assert self.gbw_json_files
        assert self.results_gbw
        for i, gbw_json_file in enumerate(self.gbw_json_files):
            redumped_gbw_json_file = gbw_json_file.with_suffix(".interface.json")
            self._dump_json(self.results_gbw[i], redumped_gbw_json_file)

        assert self.property_json_file
        assert self.results_properties
        redumped_property_json_file = self.property_json_file.with_suffix(".interface.json")
        self._dump_json(self.results_properties, redumped_property_json_file)

    def _dump_json(self, result: GbwResults | PropertyResults, json_file: Path, /) -> None:
        """
        Dump `GbwResults` or `PropertyResults` to a JSON file.

        Parameters
        ----------
        result : GbwResults | PropertyResults
            Results to be dumped.
        json_file : Path
            Path to JSON file to be written.
        """

        json_string: str = result.model_dump_json(indent=2)
        json_file.write_text(json_string)

    def collect_json_files(
        self,
        pattern: str | Callable[[int], str],
        *,
        start: int = 0,
        end: int = 1_000,
        step: int = 1,
    ) -> list[Path]:
        """
        Searches for available gbw files according to a pattern in `working_dir` and returns a list of corresponding `.json` file paths.

        Parameters
        ----------
        pattern: str | Callable[[int], str]
            Search pattern. If a string is provided, only a single file is checked. If a callable is provided,
            files are searched based on the generated pattern over a specified range.
        start: int, default = 0
            Start of the range. Only used if `pattern` is a callable.
        end: int, default = 1_000
            End of the range. Only used if `pattern` is a callable.
        step: int, default = 1
            Step size of the range. Only used if `pattern` is a callable.

        Returns
        ----------
        list[Path]
            Paths to the `.json` files corresponding to the `.gbw` files found.
        """
        files = []
        if isinstance(pattern, str):
            # > String pattern must not end with ".json"!
            gbw_file = self.get_file(pattern + ".json")
            if gbw_file.is_file():
                files.append(gbw_file)
            return files
        else:
            for i in range(start, end, step):
                gbw_file = self.get_file(pattern(i))
                if gbw_file.is_file():
                    files.append(gbw_file.with_suffix(".json"))
                else:
                    break
        return files

    def get_gbw_json_files(self, suffix: str = ".gbw", /) -> list[Path]:
        """
        Checks if other gbw files with indexes from scans or NEB exist and returns a list with their paths.
        Naming of gbw files from scan and neb is different. There should never be both so we first check for scan
        and then neb.

        Parameters
        ----------
        suffix : str
            Suffix of file. Must include the leading dot.

        Returns
        ----------
        list[Path]
            Returns list of indexed gbw files, e.g., from relaxed surface scan or neb calculation

        Raises
        ----------
        FileExistsError
            If multi-gbw files from scan and neb calculations exist.
        """

        # // Get path to main gbw/json file
        gbw_json_list = [self.get_file(".json")]

        # // Check for scan files
        scan_list = self.collect_json_files(lambda i: f".{i:03}{suffix}", start=1)

        # // Check for neb files
        neb_list = self.collect_json_files(lambda i: f"_im{i}{suffix}")

        if neb_list and scan_list:
            raise FileExistsError(
                "Both Scan and NEB type .gbw files found! Only one type should be present."
            )

        gbw_json_list.extend(scan_list or neb_list)

        return gbw_json_list

    def get_file(self, suffix: str, /, *, basename: str = "") -> Path:
        """
        Get path to file, by specifying file suffix (including the leading dot).
        Fullpath will be inferred from `self.working_dir` and `self.basename`.

        Parameters
        ----------
        suffix : str
            Suffix of file. Must include the leading dot.
        basename : str, default = ""
            Optional alternative basename to use instead of `self.basename`.
        """
        if not basename:
            basename = self.basename
        return self.working_dir / (basename + suffix)

    def _get_version(self) -> "OrcaVersion":
        """Gets the ORCA version from the property-JSON file."""

        # > Path to property JSON needs to be set
        try:
            assert self.property_json_data
            return OrcaVersion.from_json(self.property_json_data)
        except AssertionError:
            raise ValueError(
                "Could not determine ORCA version, as JSON-property file has not been parsed."
            )
        except ValueError:
            raise

    def check_version(self) -> None:
        """
        Check if the version from the property-JSON file fits to minimally support ORCA version of the current OPI version.
        """
        try:
            version = self._get_version()
        except ValueError:
            warn("Could not determine ORCA version from JSON file. Subsequent error might occur.")
        else:
            if not check_minimal_version(version):
                raise RuntimeError(
                    f"JSON property file was created with unsupported ORCA version: {version}"
                )

    def _create_runner(self) -> "Runner":
        """Create a `Runner` object passing on `self.working_dir`."""
        return Runner(working_dir=self.working_dir)

    def create_missing_gbw_json(self, *, config: dict[str, Any] | None = None) -> bool:
        """
        Check if gbw JSON files are available and try to create missing files

        Parameters
        ----------
        config : dict[str | Any] | None, default = None
            Determine contents of gbw-json file.
            For details about the configuration refer to the ORCA manual "9.3.2 Configuration file"

        Returns
        ----------
        was_create : bool
            A boolean indicating if any file was created.
        """
        # // loop over files, check if present and create if missing
        was_created = False
        for index, file in enumerate(self.gbw_json_files):
            if not file.is_file():
                self.create_gbw_json(config=config, gbw_index=index)
                was_created = True
        return was_created

    def create_gbw_json(
        self,
        *,
        force: bool = False,
        config: dict[str, Any] | None = None,
        gbw_index: int | None = None,
    ) -> None:
        """
        Thin-wrapper around `Runner.create_jsons()`.
        Creates all `<basename>.json` file(s).

        Parameters
        ----------
        force : bool, default = False
            Overwrite any existing ORCA GBW JSON file.
        config : dict[str | Any] | None, default = None
            Determine contents of gbw-json file.
            For details about the configuration refer to the ORCA manual "9.3.2 Configuration file"
        gbw_index: int | None, default = None
            Non-negative index of gbw file in `self.gbw_json_files` for which json files will be generated. If it is None, all files
            will be generated. If the index is negative or out of range silently nothing is done.

        """
        files_to_process: list[Path]

        if gbw_index is not None:
            try:
                files_to_process = [self.gbw_json_files[gbw_index]]
            except IndexError:
                return
        else:
            files_to_process = self.gbw_json_files

        for file in files_to_process:
            basename = file.stem
            runner = self._create_runner()
            runner.create_gbw_json(basename, config=config, force=force)

    def create_missing_property_json(self) -> bool:
        """
        Check if the property json file is available and try to create it if it is missing.

        Returns
        ----------
        was_create : bool
            A boolean indicating if the file was created.
        """
        if not self.property_json_file.is_file():
            self.create_property_json()
            return True
        return False

    def create_property_json(self, *, force: bool = False) -> None:
        """
        Thin-wrapper around `Runner.create_property_json()`.
        Create the `<basename>.property.json` file

        Parameters
        ----------
        force : bool, default = None
            Overwrite any existing ORCA property JSON file.
        """
        runner = self._create_runner()
        runner.create_property_json(self.basename, force=force)

    def create_jsons(self, *, force: bool = False) -> None:
        """
        Thin-wrapper around `Runner.create_jsons()`.
        Create the `<basename>.json` and the `<basename>.property.json` file

        Parameters
        ----------
        force : bool, default: None
            Overwrite any existing ORCA property and GBW JSON files.
        """
        runner = self._create_runner()
        runner.create_jsons(self.basename, force=force)

    def get_outfile(self) -> Path:
        """
        The full path to the ".out" file.
        """
        return self.get_file(".out")

    def terminated_normally(self) -> bool:
        """
        Determine if ORCA terminated normally, by looking for "ORCA TERMINATED NORMALLY" in the ".out" file.
        If the ".out" file does not exist, also return False.

        Returns
        -------
        bool
            True if "ORCA TERMINATED NORMALLY" is found in ".out" file else False
        """
        outfile = self.get_outfile()
        try:
            return has_terminated_normally(outfile)
        except FileNotFoundError:
            return False

    def scf_converged(self) -> bool:
        """
        Determine if ORCA SCF converged, by looking for "SUCCESS" in the ".out" file.
        Check only if ORCA SCF was actually requested.
        If the ".out" file does not exist, also return False.

        Returns
        -------
        bool
            True if "SUCCESS" is found in ".out" file else False
        """
        outfile = self.get_outfile()
        try:
            return has_scf_converged(outfile)
        except FileNotFoundError:
            return False

    def geometry_optimization_converged(self) -> bool:
        """
        Determine if ORCA geometry optimization converged, by looking for "HURRAY" in the ".out" file.
        Check only if ORCA geometry optimization was actually requested.
        If the ".out" file does not exist, also return False.

        Returns
        -------
        bool
            True if "HURRAY" is found in ".out" file else False
        """
        outfile = self.get_outfile()
        try:
            return has_geometry_optimization_converged(outfile)
        except FileNotFoundError:
            return False

    def print_graph(self, *, max_length: int = 3, depth: int = -1) -> None:
        """
        Prints a graph of the available properties in the output

        Parameters
        -------
        max_length : int, default = 3
            Maximum length of lists displayed in the graph printout
        depth : int, default = -1
            Maximum depth of the output tree that is printed. With the default -1 everything is printed.

        """
        print("Printing graph of property results:")
        if self.results_properties is not None:
            print(self.results_properties.graph(depth, max_list_length=max_length))
        else:
            print("No property results are available!")

        print("Printing graph of gbw results:")
        if self.results_gbw is not None:
            for i, result_gbw in enumerate(self.results_gbw):
                print(f"gbw results [{i}]:")
                print(result_gbw.graph(depth, max_list_length=max_length))
        else:
            print("No gbw results are available!")

    def run_orca_plot(
        self, stdin_list: list[str], *, gbw_file: Path | None = None, timeout: int = -1
    ) -> None:
        """
        Executes orca_plot and passes it an input list stdin_list that specifies what to plot.

        Parameters
        ----------
        stdin_list : list[str]
            Input list for interactive orca_plot session
        gbw_file : Path | None, default: None
            Gbw file used for plotting, if None is given {basename}.gbw in working_dir will be used.
        timeout : int, default: = -1
            Timeout in seconds to wait for ORCA process.
            If value is smaller than zero, wait indefinitely.

        Raises
        ----------
        ValueError
            If the input string is empty a ValueError is raised.
        FileNotFoundError
            If the gbwfile {basename}{suffix} is not found.
        """
        runner = self._create_runner()
        if gbw_file is None:
            gbw_file = self.get_file(".gbw")

        if not gbw_file.is_file():
            raise FileNotFoundError(f"The requested .gbw file is not available: ({gbw_file})")

        # if no input for orca_plot is given
        if not stdin_list:
            raise ValueError("No input (stdin_list) supplied for orca_plot, but input is required!")

        runner.run_orca_plot(gbw_file, stdin_list, timeout=timeout)

    def plot_mo(
        self,
        index: StrictNonNegativeInt,
        /,
        *,
        operator: StrictNonNegativeInt = 0,
        resolution: StrictNonNegativeInt = 40,
        timeout: int = 300,
        gbw_type: str | GbwSuffix = GbwSuffix.GBW,
        gbw_index: int = 0,
    ) -> CubeOutput | None:
        """
        Generates and returns the cube file for a molecular orbital by running the orca_plot binary.
        **Attention:** will terminate orca_plot after 300 seconds by default. If you plot something large you will have
        to adapt this threshold or set it to -1 for waiting indefinitely!

        Parameters
        ----------
        index: StrictNonNegativeInt
            Index of the MO to plot.
        operator : StrictNonNegativeInt, default = 0
            Operator of the MO, alpha MOs are indicated by 0 and beta MOs by 1.
        resolution: StrictNonNegativeInt, default = 40
            Resolution of the generated cube file. Higher numbers result in smoother plots, but also in longer orca_plot
            run time and a larger cube file.
        timeout: int, default = 300
            Time after which orca_plot will be stopped. 300 seconds should be sufficient for most MOs but when something
            large is plotted set this to a larger value or to -1 for waiting indefinitely long.
        gbw_type: str | GbwSuffix, default = GbwSuffix.GBW
            Type of the gbw file from which orbitals should be plotted.
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` that is used for plotting. Default 0 refers to the main gbw file.

        Returns
        -------
        CubeOutput | None
            Returns the cube output object or returns None if the cube file cannot be retrieved.
        """

        operator_list = ["a", "b"]

        # > Define input string for orca_plot.
        # > If anything goes wrong orca_plot should exit.
        stdin_list = [
            "1",  # Select type of plot
            "1",  # Enter MO plot
            "2",  # Select index of orbital
            str(index),  # Enter index
            "3",  # Select alpha/beta operator
            str(operator),  # Enter alpha/beta (0/1)
            "4",  # Select the resolution (grid size) settings
            str(resolution),  # Enter resolution
            "5",  # Select the output format
            "7",  # Request cube file format
            "11",  # Perform the plotting
            "12",  # Exit the program
        ]

        if isinstance(gbw_type, str):
            gbw_type = GbwSuffix(gbw_type)

        # > determine which gbw file to plot
        suffix = gbw_type.value
        gbw_file = self.gbw_json_files[gbw_index].with_suffix(suffix)

        self.run_orca_plot(stdin_list, timeout=timeout, gbw_file=gbw_file)

        # > get the resulting cube file as string
        cube_file = self.get_file(
            f".mo{index}{operator_list[operator]}.cube",
            basename=self.gbw_json_files[gbw_index].stem,
        )

        if not cube_file.is_file():
            return None

        return CubeOutput(cube_file)

    def plot_density(
        self,
        /,
        *,
        resolution: StrictNonNegativeInt = 40,
        timeout: int = 600,
        suffix: str = ".scfp",
        gbw_index: int = 0,
    ) -> CubeOutput | None:
        """
        Generates and returns the cube file for the density by running the orca_plot binary.
        **Attention:** will terminate orca_plot after 600 seconds by default. If you plot something large you will have
        to adapt this threshold or set it to -1 for waiting indefinitely!

        Parameters
        ----------
        resolution: StrictNonNegativeInt, default=40
            Resolution of the generated cube file. Higher numbers result in smoother plots, but also in longer orca_plot
            run time and a larger cube file.
        timeout: int, default: 600
            Time after which orca_plot will be stopped. 600 seconds should be sufficient for most MOs but when something
            large is plotted set this to a larger value or to -1 for waiting indefinitely long.
        suffix: str, default: ".scfp"
            suffix for selecting different densities, e.g., FOD via ".scfp_fod".
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` that is used for plotting. Default 0 refers to the main gbw file.

        Returns
        -------
        CubeOutput | None
            Returns the cube output object or returns None if the cube file cannot be retrieved.
        """
        gbw_file = self.gbw_json_files[gbw_index].with_suffix(".gbw")

        # > Define input string for orca_plot.
        # > If anything goes wrong orca_plot should exit.
        stdin_list = [
            "1",  # Select type of plot
            "2",  # Enter density plot
            "n",  # Do not use the default density
            f"{self.basename}{suffix}",  # Select density name
            "4",  # Select the resolution (grid size) settings
            str(resolution),  # Enter resolution
            "5",  # Select the output format
            "7",  # Request cube file format
            "11",  # Perform the plotting
            "12",  # Exit the program
        ]
        self.run_orca_plot(stdin_list, timeout=timeout, gbw_file=gbw_file)

        # > get the resulting cube file as string
        cube_file = self.get_file(".eldens.cube", basename=gbw_file.stem)

        if not cube_file.is_file():
            return None

        return CubeOutput(cube_file)

    def plot_spin_density(
        self,
        /,
        *,
        resolution: StrictNonNegativeInt = 40,
        timeout: int = 600,
        suffix: str = ".scfp",
        gbw_index: int = 0,
    ) -> CubeOutput | None:
        """
        Generates and returns the cube file for the spin-density by running the orca_plot binary. Note that for RHF/RKS
        calculations the density will be returned.
        **Attention:** will terminate orca_plot after 600 seconds by default. If you plot something large you will have
        to adapt this threshold or set it to -1 for waiting indefinitely!

        Parameters
        ----------
        resolution: StrictNonNegativeInt, default=40
            Resolution of the generated cube file. Higher numbers result in smoother plots, but also in longer orca_plot
            run time and a larger cube file.
        timeout: int, default = 600
            Time after which orca_plot will be stopped. 600 seconds should be sufficient for most MOs but when something
            large is plotted set this to a larger value or to -1 for waiting indefinitely long.
        suffix: str, default: ".scfp"
            suffix for selecting different densities, e.g., FOD via ".scfp_fod".
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` that is used for plotting. Default 0 refers to the main gbw file.

        Returns
        -------
        CubeOutput | None
            Returns the cube output object or returns None if the cube file cannot be retrieved.
        """
        gbw_file = self.gbw_json_files[gbw_index].with_suffix(".gbw")
        # > Define input string for orca_plot.
        # > If anything goes wrong orca_plot should exit.
        stdin_list = [
            "1",  # Select type of plot
            "3",  # Enter spin density plot
            "n",  # Do not use the default density
            f"{self.basename}{suffix}",  # Select density name
            "4",  # Select the resolution (grid size) settings
            str(resolution),  # Enter resolution
            "5",  # Select the output format
            "7",  # Request cube file format
            "11",  # Perform the plotting
            "12",  # Exit the program
        ]
        self.run_orca_plot(stdin_list, timeout=timeout, gbw_file=gbw_file)

        # > get the resulting cube file as string
        cube_file = self.get_file(".spindens.cube", basename=gbw_file.stem)

        if not cube_file.is_file():
            return None

        return CubeOutput(cube_file)

    def _safe_get(self, *attrs: str | int) -> Any | None:
        """
        Safely access a nested chain of attributes or list indices on the output object.

        This method walks through a sequence of attributes (str) or indices (int),
        returning the nested value if all lookups succeed and none of the intermediate
        objects are None. If any step fails—due to a missing attribute, invalid index,
        or None encountered in the chain—it returns None instead of raising an exception.

        Parameters
        ----------
        *attrs : str | int
            A sequence of strings (attribute names) and/or integers (list or indexable
            container indices) that define the path to follow.

        Returns
        -------
        Any | None
            The resolved value at the end of the access path if all steps succeed;
            otherwise, None. Should be cast into the correct type for usage.

        Examples
        --------
            self._safe_get("results_properties", "geometries", index, "geometry")
            is equivalent to:
            self.results_properties.geometries[index].geometry
            but returns None if any part of the chain is missing or None, in a mypy-friendly way.
        """
        current = self
        for attr in attrs:
            if current is None:
                return None
            try:
                if isinstance(attr, int) and isinstance(current, list):
                    current = current[attr]
                elif isinstance(attr, str):
                    current = getattr(current, attr)
                else:
                    raise TypeError
            except (AttributeError, IndexError, TypeError):
                return None
        return current

    def get_hftype(self, index: int = 0) -> Hftyp | None:
        """
        Get the HFType from GBW json file.

        Parameters
        -------
        index: int, default: 0
            Index of geometry for which the hftype should be retrieved.

        Returns
        -------
        hftype : Hftyp | None
        """
        hftype = self._safe_get("results_gbw", index, "molecule", "hftyp")
        if hftype is not None:
            hftype = cast(str, hftype)
            try:
                hftype = Hftyp(hftype)
                return hftype
            except ValueError:
                return None
        else:
            return None

    def get_charge(self) -> StrictInt | None:
        """
        Get the molecular charge from the json properties file.

        Returns
        -------
        charge : StrictInt | None
        """
        charge = self._safe_get("results_properties", "calculation_info", "charge")

        if charge is not None:
            charge = cast(StrictInt, charge)

        return charge

    def get_mult(self) -> StrictPositiveInt | None:
        """
        Get the molecular electron multiplicity from the json properties file.

        Returns
        -------
        mult : StrictPositiveInt | None
        """
        mult = self._safe_get("results_properties", "calculation_info", "mult")

        if mult is not None:
            mult = cast(StrictPositiveInt, mult)

        return mult

    def get_nelectrons(
        self, *, spin_resolved: bool = False
    ) -> tuple[int, int | None] | tuple[None, None]:
        """
        Get the number of electrons from property results. If requested separated into alpha and beta.

        Parameters
        -------
        spin_resolved: bool, default=False
            If True, the numbers of electrons are returned as alpha and beta electrons separately, if False,
            the total number of electrons is returned.

        Returns
        -------
        nalpha : int | None
            * None: if no electrons could be retrieved, or no multiplicity for spin resolution is available.
            * int:
                * if `spin_resolved == False`, the total number of electrons
                * if `spin_resolved == True`, the number of alpha electrons.
        nbeta : int | None
            * None:
                * if no electrons could be retrieved, or no multiplicity for spin resolution is available.
                * if `spin_resolved == False`
            * int : number of beta electrons (requires `spin_resolved == True`)
        """
        nel = self._safe_get("results_properties", "calculation_info", "numofelectrons")

        if nel is not None:
            nel = cast(int, nel)
        else:
            return None, None

        # > Return total number of electrons
        if not spin_resolved:
            return nel, None

        # > Get the electron spin multiplicity
        mult = self.get_mult()
        if mult is None:
            return None, None

        # > Calculate amount of alpha and beta electrons
        nalpha = nel // 2 + (mult - 1)
        nbeta = nel - nalpha

        # > Return spin resolved number of electrons
        return nalpha, nbeta

    def get_nbf(self) -> StrictNonNegativeInt | None:
        """
        Get the number of basis functions (nbf) from the json properties file.

        Returns
        -------
        nbf : StrictNonNegativeInt | None
        """
        nbf = self._safe_get("results_properties", "calculation_info", "numofbasisfuncts")

        if nbf is not None:
            nbf = cast(StrictNonNegativeInt, nbf)

        return nbf

    def get_final_energy(self, *, index: int = -1) -> StrictFiniteFloat | None:
        """
        Easy access to the final single point energy.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the energy should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        final_energy: StrictFiniteFloat | None
            Returns the final energy of the ORCA calculation or None if there is none in the output for the requested index.
        """

        # > Get the final energy
        final_energy = self._safe_get(
            "results_properties", "geometries", index, "single_point_data", "finalenergy"
        )

        if final_energy is not None:
            final_energy = cast(StrictFiniteFloat, final_energy)

        return final_energy

    def get_energies(self, *, index: int = -1) -> dict[str, Energy] | None:
        """
        Return a dictionary with different energy types for the geometry at a given index.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the energy should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        -------
        energy_dict : dict[str, Energy] | None
            Dictionary where keys identify the energy type. If multiple energies of the same type are present, an index is
            appended after the first one, e.g., SCF, SCF_1, SCF_2, etc. If no energy for the requested index is available None is returned.

        Notes
        -----
        Common keys include:
            - **Unknown**     : No information about the energy is provided.
            - **SCF**         : SCF energy from HF, DFT, or SQM methods.
            - **MDCI(SD)**    : Typically the (DLPNO-)CCSD energy.
            - **MDCI(SD(T))** : Typically the (DLPNO-)CCSD(T) energy.
            - **CASSCF**      : CASSCF energy.
            - **MP2**         : MP2 energy.
            - **TDA/CIS**     : TDA-TD-DFT or CIS energy.
        """

        # > Energy dict to populate & return
        energy_dict: dict[str, Energy] = {}

        # > Get the list of energies to be converted to a dictionary
        energy_list = self._safe_get("results_properties", "geometries", index, "energy")

        if energy_list is not None:
            energy_list = cast(EnergyList, energy_list)
        else:
            return None

        for energy in energy_list:
            if not energy.method:
                key = "Unknown"
            else:
                key = energy.method
            # > Add index at the end if multiple energies of the same type are present
            index = 1
            while key in energy_dict:
                key = f"{key}_{index}"
                index += 1
            energy_dict[key] = energy

        return energy_dict

    def get_gradient(self, *, index: int = -1) -> list[StrictFiniteFloat] | None:
        """
        Easy access to the nuclear gradient

        Parameters
        ----------
        index : int, default: -1
            index of geometry for which the gradient is to be returned. The default -1 refers to the final geometry.
            **Attention:** In a normal geometry optimization ORCA does not calculate the gradient for the final
            geometry, so the default index will return None. You can request the gradient for the structure one step
            before the final one with the index -2. For most intents and purposes, the last and second to last
            geometries, energies and gradients are the same within the given tolerances.

        Returns
        ----------
        list[StrictFiniteFloat] | None
            Returns nuclear gradient (packed in order x1, y1, z1, x2 y2, z2, ... in Eh/Bohr) for the given index
            or None if it cannot be obtained.
        """
        # > Safely get the gradient
        gradient = self._safe_get(
            "results_properties", "geometries", index, "nuclear_gradient", 0, "grad"
        )

        # > Cast them into the correct type
        if gradient is not None:
            gradient = cast(
                list[list[StrictFiniteFloat]],
                gradient,
            )
            flat = [inner[0] for inner in gradient]
            gradient = flat

        return gradient

    def get_structure(self, *, index: int = -1, with_fragments: bool = True) -> Structure | None:
        """
        Returns structure from ORCA job as Structure object (by default the final structure).
        Silently returns None of no structure is available.

        Parameters
        ----------
        index : int, default: -1
            index of geometry to return. The default -1 refers to the final geometry.
        with_fragments : bool, default: True
            whether the fragment IDs should be added as well to the structure (if available)

        Returns
        ----------
        structure: Structure | None
            Returns structure object generated from the output for the given index or None if no structure is available.
        """

        atoms: list[Atom] = []
        # > Get Cartesian coordinates
        cartesians = self._get_cartesians(index)

        if cartesians is None:
            return None

        for line in cartesians:
            elem, x_au, y_au, z_au = line
            # > Get coordinates and convert to angstrom
            x = x_au * AU_TO_ANGST
            y = y_au * AU_TO_ANGST
            z = z_au * AU_TO_ANGST
            # > Generate atom and append to list
            atom = Atom(element=elem, coordinates=Coordinates((x, y, z)))
            atoms.append(atom)

        if with_fragments:
            # > Get fragment IDs
            fragments = self._get_fragments(index)

            if fragments:
                for atom, frag in zip(atoms, fragments):
                    atom.fragment_id = frag[0]

        structure = Structure(atoms)

        # > Add charge data
        charge = self.get_charge()
        if charge is not None:
            structure.charge = charge

        # > Add multiplicity data
        mult = self.get_mult()
        if mult is not None:
            structure.multiplicity = mult
        return structure

    def _get_cartesians(
        self, index: int, /
    ) -> list[tuple[StrictStr, StrictFiniteFloat, StrictFiniteFloat, StrictFiniteFloat]] | None:
        """
        Returns cartesian coordinates from the output object for a specified index.

        Parameters
        ----------
        index : int
            index of geometry to return.

        Returns
        ----------
        cartesians: list[tuple[StrictStr, StrictFiniteFloat, StrictFiniteFloat, StrictFiniteFloat]] | None
            List containing the cartesian coordinates or None.
        """
        # > Safely get the cartesian coordinates
        cartesians = self._safe_get(
            "results_properties", "geometries", index, "geometry", "coordinates", "cartesians"
        )
        # > Cast them into the correct type
        if cartesians is not None:
            cartesians = cast(
                list[tuple[StrictStr, StrictFiniteFloat, StrictFiniteFloat, StrictFiniteFloat]],
                cartesians,
            )

        return cartesians

    def _get_fragments(self, index: int, /) -> list[list[StrictPositiveInt]] | None:
        """
        Returns fragment ids from the output object for a specified geometry index.

        Parameters
        ----------
        index : int
            index of geometry to return.

        Returns
        ----------
        fragments: list[tuple[StrictStr, StrictFiniteFloat, StrictFiniteFloat, StrictFiniteFloat]] | None
            List containing the cartesian coordinates or None.
        """
        # > Safely get the fragment IDs
        fragments = self._safe_get(
            "results_properties", "geometries", index, "geometry", "fragments"
        )
        # > Cast them into the correct type
        if fragments:
            fragments = cast(
                list[list[StrictPositiveInt]],
                fragments,
            )

        return fragments

    def get_mos(self, gbw_index: int = 0) -> dict[str, list[MO]] | None:
        """
        Returns a dictionary with list(s) of molecular orbitals.

        Parameters
        -------
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` for which the mos are returned. Default 0 refers to the main gbw file.

        Returns
        -------
        dict[str, list[MO]] | None
            Dictionary containing the molecular orbitals as lists.

        Notes
        -----
        The keys are:
           - **mo**      : RHF/ROHF orbitals
           - **alpha**   : UHF alpha orbitals
           - **beta**    : UHF beta orbitals
        """
        molecular_orbitals = self._safe_get(
            "results_gbw", gbw_index, "molecule", "molecularorbitals", "mos"
        )
        if molecular_orbitals is not None:
            mos = {}
            cast(list[MO], molecular_orbitals)
            # > Get the hftype (e.g. rhf / uhf)
            hftype = self.get_hftype(gbw_index)
            # > Sort for UHF
            if hftype == Hftyp.UHF:
                offset = len(molecular_orbitals) // 2
                mos["alpha"] = molecular_orbitals[:offset]
                mos["beta"] = molecular_orbitals[offset:]
            else:
                mos["mo"] = molecular_orbitals
            return mos
        else:
            return None

    @staticmethod
    def _find_homo(mo_list: list[MO]) -> int | None:
        """
        Find and return the index of the highest occupied molecular orbital HOMO in energy ordered list of MOs.

        Parameter
        -------
        mo_list: list[MO]

        Returns
        -------
        int | None
            index of HOMO, or None, if the HOMO could not be found.
        """

        # > Search for the index of the LUMO
        index = next((i for i, mo in enumerate(mo_list) if mo.occupancy == 0), None)
        if index is not None and index >= 1:
            # > HOMO is LUMO-1
            index -= 1
            return index

        return None

    def get_homo(self, gbw_index: int = 0) -> MOData | None:
        """
        Returns the highest occupied molecular orbital (HOMO, or SOMO for UHF).

        Parameters
        -------
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` for which the homo is returned. Default 0 refers to the main gbw file.

        Returns
        -------
        MOData | None
            Returns MO data of HOMO/SOMO or None, if the HOMO could not be found.
        """
        homo_id: int | None = None
        homo_type: str | None = None
        homo: MO | None = None
        mos = self.get_mos(gbw_index)

        if mos is not None:
            for channel in mos:
                # > find homo for spin channel
                mo_id = self._find_homo(mos[channel])
                if mo_id is not None:
                    channel_homo = mos[channel][mo_id]
                    if channel_homo.orbitalenergy is not None:
                        # > Check if spin channel homo is the actual homo
                        if homo is None:
                            homo = channel_homo
                            homo_id = mo_id
                            homo_type = channel
                        else:
                            # > Compare energies and pick highest
                            if (
                                homo.orbitalenergy is not None
                                and channel_homo.orbitalenergy > homo.orbitalenergy
                            ):
                                homo = channel_homo
                                homo_id = mo_id
                                homo_type = channel
        if homo_id is not None and homo_type is not None and homo is not None:
            return MOData(homo_id, homo_type, homo)
        else:
            return None

    @staticmethod
    def _find_lumo(mo_list: list[MO]) -> int | None:
        """
        Find and return the index of the lowest unoccupied molecular orbital LUMO in energy ordered list of MOs.

        Parameter
        -------
        mo_list: list[MO]

        Returns
        -------
        int | None
            index of LUMO, or None, if the LUMO could not be found.
        """
        index = next((i for i, mo in enumerate(mo_list) if mo.occupancy == 0), None)
        if index is not None:
            return index

        return None

    def get_lumo(self, gbw_index: int = 0) -> MOData | None:
        """
        Returns the lowest unoccupied molecular orbital (LUMO).

        Parameters
        -------
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` for which the lumo is returned. Default 0 refers to the main gbw file.

        Returns
        -------
        MOData | None
            Returns MO data of LUMO, or None, if the LUMO could not be found.
        """
        lumo_id: int | None = None
        lumo_type: str | None = None
        lumo: MO | None = None
        mos = self.get_mos(gbw_index)

        if mos is not None:
            for channel in mos:
                # > find lumo for spin channel
                mo_id = self._find_lumo(mos[channel])
                if mo_id is not None:
                    channel_lumo = mos[channel][mo_id]
                    if channel_lumo.orbitalenergy is not None:
                        # > Check if spin channel lumo is the actual lumo
                        if lumo is None:
                            lumo_id = mo_id
                            lumo_type = channel
                            lumo = channel_lumo
                        else:
                            # > pick lowest lumo
                            if (
                                lumo.orbitalenergy is not None
                                and channel_lumo.orbitalenergy < lumo.orbitalenergy
                            ):
                                lumo = channel_lumo
                                lumo_id = mo_id
                                lumo_type = channel
        if lumo_id is not None and lumo_type is not None and lumo is not None:
            return MOData(lumo_id, lumo_type, lumo)
        else:
            return None

    def get_hl_gap(self, gbw_index: int = 0) -> float | None:
        """
        Returns the HOMO-LUMO gap in eV

        Parameters
        -------
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` for which the gap is returned. Default 0 refers to the main gbw file.

        Returns
        -------
        float | None
            Returns the HOMO-LUMO gap in eV or None if the gap could not be obtained.
        """
        homo_data = self.get_homo(gbw_index)
        if homo_data is not None:
            homo_energy = homo_data.mo.orbitalenergy
        else:
            homo_energy = None
        lumo_data = self.get_lumo(gbw_index)
        if lumo_data is not None:
            lumo_energy = lumo_data.mo.orbitalenergy
        else:
            lumo_energy = None

        if homo_energy is not None and lumo_energy is not None:
            return (lumo_energy - homo_energy) * AU_TO_EV

        return None

    def get_mulliken(self, *, index: int = -1) -> list[MullikenPopulationAnalysis] | None:
        """
        Easy access to the Mulliken population(s) from the properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the population should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        mulliken : list[PopulationAnalysis] | None
            Returns the population(s) or None if there is none in the output for the requested index.
        """

        # > Get the Mulliken population
        mulliken = self._safe_get(
            "results_properties", "geometries", index, "mulliken_population_analysis"
        )

        if mulliken is not None:
            mulliken = cast(list[MullikenPopulationAnalysis], mulliken)

        return mulliken

    def get_loewdin(self, *, index: int = -1) -> list[LoewdinPopulationAnalysis] | None:
        """
        Easy access to the Loewdin population(s) from the properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the population should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        loewdin : list[PopulationAnalysis] | None
            Returns the population(s) or None if there is none in the output for the requested index.
        """

        # > Get the Loewdin population
        loewdin = self._safe_get(
            "results_properties", "geometries", index, "loewdin_population_analysis"
        )

        if loewdin is not None:
            loewdin = cast(list[LoewdinPopulationAnalysis], loewdin)

        return loewdin

    def get_chelpg(self, *, index: int = -1) -> list[ChelpgPopulationAnalysis] | None:
        """
        Easy access to the CHarges from ELectrostatic Potentials using a Grid-based method (CHELPG) from the properties
        results. Note that the RESP charges are basically CHELPG charges with some restraint and are obtained as well
        with this function.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the population should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        chelpg : list[PopulationAnalysis] | None
            Returns the population(s) or None if there is none in the output for the requested index.
        """

        # > Get the CHELPG population
        chelpg = self._safe_get(
            "results_properties", "geometries", index, "chelpg_population_analysis"
        )

        if chelpg is not None:
            chelpg = cast(list[ChelpgPopulationAnalysis], chelpg)

        return chelpg

    def get_mayer(self, *, index: int = -1) -> list[MayerPopulationAnalysis] | None:
        """
        Easy access to the Mayer population(s) from the properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the population should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        mayer : list[MayerPopulationAnalysis] | None
            Returns the population(s) or None if there is none in the output for the requested index.
        """

        # > Get the Mayer population
        mayer = self._safe_get(
            "results_properties", "geometries", index, "mayer_population_analysis"
        )

        if mayer is not None:
            mayer = cast(list[MayerPopulationAnalysis], mayer)

        return mayer

    def get_hirshfeld(self, *, index: int = -1) -> list[HirshfeldPopulationAnalysis] | None:
        """
        Easy access to the Hirshfeld population(s) from the properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the population should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        mbis : list[HirshfeldPopulationAnalysis] | None
            Returns the population(s) or None if there is none in the output for the requested index.
        """

        # > Get the Hirshfeld population
        hirshfeld = self._safe_get(
            "results_properties", "geometries", index, "hirshfeld_population_analysis"
        )

        if hirshfeld is not None:
            hirshfeld = cast(list[HirshfeldPopulationAnalysis], hirshfeld)

        return hirshfeld

    def get_mbis(self, *, index: int = -1) -> list[MbisPopulationAnalysis] | None:
        """
        Easy access to the MBIS population(s) from the properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the population should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        mbis : list[MbisPopulationAnalysis] | None
            Returns the population(s) or None if there is none in the output for the requested index.
        """

        # > Get the MBIS population
        mbis = self._safe_get("results_properties", "geometries", index, "mbis_population_analysis")

        if mbis is not None:
            mbis = cast(list[MbisPopulationAnalysis], mbis)

        return mbis

    def get_dipole(self, *, index: int = -1) -> list[DipoleMoment] | None:
        """
        Get a list of the dipole moments from property results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the dipole moments should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        dipole : list[DipoleMoment] | None
            Returns the dipole moment(s) or None if there is none in the output for the requested index.
        """

        dipole = self._safe_get("results_properties", "geometries", index, "dipole_moment")

        if dipole is not None:
            dipole = cast(list[DipoleMoment], dipole)

        return dipole

    def get_quadrupole(self, *, index: int = -1) -> list[QuadrupoleMoment] | None:
        """
        Get a list of the quadrupole moments from property results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the quadrupole moments should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        quadrupole : list[QuadrupoleMoment] | None
            Returns the quadrupole moment(s) or None if there is none in the output for the requested index.
        """

        quadrupole = self._safe_get("results_properties", "geometries", index, "quadrupole_moment")

        if quadrupole is not None:
            quadrupole = cast(list[QuadrupoleMoment], quadrupole)

        return quadrupole

    def get_polarizability(self, *, index: int = -1) -> list[Polarizability] | None:
        """
        Get a list of the polarizabilities from property results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the polarizabilies should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        pol : list[Polarizability] | None
            Returns the polarizabilities or None if there is none in the output for the requested index.
        """

        pol = self._safe_get("results_properties", "geometries", index, "polarizability")

        if pol is not None:
            pol = cast(list[Polarizability], pol)

        return pol

    def get_s2(self, *, index: int = -1) -> tuple[StrictFiniteFloat, StrictFiniteFloat] | None:
        """
        Get the S² expectation value and the ideal S² value by grepping them from the output file.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which S² should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None.

        Returns
        ----------
        tuple[StrictFiniteFloat, StrictFiniteFloat] | None
            Return the expectation value and the ideal value or None if nothing is found.
        """
        outfile = self.get_outfile()
        # // String for searching the S² expectation value.
        expec_string = "Expectation value of <S**2>"
        # // String for searching the ideal S² value.
        ideal_string = "Ideal value S*(S+1)"
        expec_s2 = get_float_from_line(outfile, expec_string, index, strict=False)
        ideal_s2 = get_float_from_line(outfile, ideal_string, index, strict=False)
        if expec_s2 is not None and ideal_s2 is not None:
            return expec_s2, ideal_s2
        else:
            return None

    def get_zpe(self, *, index: int = -1) -> StrictPositiveFloat | None:
        """
        Returns the zero-point energy (in a.u.) from the thermochemistry key in properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the zpe should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None. Note that in typical ORCA jobs
            thermochemical properties are only available for the final geometry.

        Returns
        ----------
        zpe : StrictFiniteFloat | None
            Returns the zero-point energy in a.u., or None if nothing is found.
        """
        # > "thermochemistry_energies" contains a list, but there should always be only one index
        zpe = self._safe_get(
            "results_properties", "geometries", index, "thermochemistry_energies", 0, "zpe"
        )

        if zpe is not None:
            zpe = cast(StrictPositiveFloat, zpe)

        return zpe

    def get_inner_energy(self, *, index: int = -1) -> StrictFiniteFloat | None:
        """
        Returns the inner energy (in a.u.) from the thermochemistry key in properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the zpe should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None. Note that in typical ORCA jobs
            thermochemical properties are only available for the final geometry.

        Returns
        ----------
        inner_energy : StrictFiniteFloat | None
            Returns the inner energy (U) in a.u., or None if nothing is found.
        """
        # > "thermochemistry_energies" contains a list, but there should always be only one index
        inner_energy = self._safe_get(
            "results_properties", "geometries", index, "thermochemistry_energies", 0, "innerenergyu"
        )

        if inner_energy is not None:
            inner_energy = cast(StrictFiniteFloat, inner_energy)

        return inner_energy

    def get_enthalpy(self, *, index: int = -1) -> StrictFiniteFloat | None:
        """
        Returns the enthalpy (in a.u.) from the thermochemistry key in properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the zpe should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None. Note that in typical ORCA jobs
            thermochemical properties are only available for the final geometry.

        Returns
        ----------
        enthalpy : StrictFiniteFloat | None
            Returns the enthalpy (H) in a.u., or None if nothing is found.
        """
        # > "thermochemistry_energies" contains a list, but there should always be only one index
        enthalpy = self._safe_get(
            "results_properties", "geometries", index, "thermochemistry_energies", 0, "enthalpyh"
        )

        if enthalpy is not None:
            enthalpy = cast(StrictFiniteFloat, enthalpy)

        return enthalpy

    def get_entropy(self, *, index: int = -1) -> StrictFiniteFloat | None:
        """
        Returns the entropy (in a.u.) from the thermochemistry key in properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the zpe should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None. Note that in typical ORCA jobs
            thermochemical properties are only available for the final geometry.

        Returns
        ----------
        entropy : StrictFiniteFloat | None
            Returns the entropy (S) in a.u., or None if nothing is found.
        """
        # > "thermochemistry_energies" contains a list, but there should always be only one index
        entropy = self._safe_get(
            "results_properties", "geometries", index, "thermochemistry_energies", 0, "entropys"
        )

        if entropy is not None:
            entropy = cast(StrictFiniteFloat, entropy)

        return entropy

    def get_free_energy(self, *, index: int = -1) -> StrictFiniteFloat | None:
        """
        Returns the free energy (in a.u.) from the thermochemistry key in properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the zpe should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None. Note that in typical ORCA jobs
            thermochemical properties are only available for the final geometry.

        Returns
        ----------
        free_energy : StrictFiniteFloat | None
            Returns the free energy (G) in a.u., or None if nothing is found.
        """
        # > "thermochemistry_energies" contains a list, but there should always be only one index
        free_energy = self._safe_get(
            "results_properties", "geometries", index, "thermochemistry_energies", 0, "freeenergyg"
        )

        if free_energy is not None:
            free_energy = cast(StrictFiniteFloat, free_energy)

        return free_energy

    def get_el_energy(self, *, index: int = -1) -> StrictFiniteFloat | None:
        """
        Returns the electronic energy (in a.u.) from the thermochemistry key in properties results.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the zpe should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None. Note that in typical ORCA jobs
            thermochemical properties are only available for the final geometry.

        Returns
        ----------
        el_energy : StrictFiniteFloat | None
            Returns electronic energy in a.u., or None if nothing is found.
        """
        # > "thermochemistry_energies" contains a list, but there should always be only one index
        el_energy = self._safe_get(
            "results_properties", "geometries", index, "thermochemistry_energies", 0, "elenergy"
        )

        if el_energy is not None:
            el_energy = cast(StrictFiniteFloat, el_energy)

        return el_energy

    def get_free_energy_delta(self, *, index: int = -1) -> StrictFiniteFloat | None:
        """
        Returns the thermostatistical contributions to the free energy by subtracting the electronic energy from the
        free energy.

        Parameters
        ----------
        index : int, default: -1
            Index of the geometry for which the zpe should be returned. The default -1 refers to the final geometry.
            Silently ignores if the requested index is not available and returns None. Note that in typical ORCA jobs
            thermochemical properties are only available for the final geometry.

        Returns
        ----------
        free_energy_thermo : StrictFiniteFloat | None
            Free energy contributions from thermostatistical corrections (G_thermo) in a.u., or None if one of the
            components is missing.
        """
        free_energy = self.get_free_energy(index=index)
        el_energy = self.get_el_energy(index=index)
        if free_energy is not None and el_energy is not None:
            return free_energy - el_energy
        else:
            return None

    def recreate_gbw_results(self, config_dict: dict[str, Any], gbw_index: int = 0, /) -> None:
        """
        Function for recreating a specific gbw-JSON file with a config dict. Silently does nothing if `gbw_index` is
        not valid.

        Parameters
        ----------
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` for which the json file should be created. Default 0 refers to the main gbw file.

        """
        self.create_gbw_json(force=True, config=config_dict, gbw_index=gbw_index)
        if self.gbw_json_data is not None and self.gbw_json_files is not None:
            if 0 <= gbw_index < self.num_gbw_json_data and 0 <= gbw_index < self.num_gbw_json_files:
                self.gbw_json_data[gbw_index] = self._process_json_file(
                    self.gbw_json_files[gbw_index]
                )
                if self.results_gbw is not None and 0 <= gbw_index < self.num_results_gbw:
                    self.results_gbw[gbw_index] = GbwResults(**self.gbw_json_data[gbw_index])

    def get_int_overlap(
        self, recreate_json: bool = False, gbw_index: int = 0
    ) -> npt.NDArray[np.float64] | None:
        """
        Returns the overlap integral matrix as numpy array.

        Parameters
        ----------
        recreate_json : bool, default = False
            If True, recreate the gbw json file and request (exclusively) the overlap integrals to be included.
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` for which integrals are requested. Default 0 refers to the main gbw file.
        """

        if recreate_json:
            config_dict = {"1elIntegrals": ["S"]}
            self.recreate_gbw_results(config_dict, gbw_index)

        # > get overlap from gbw json files
        overlap_list = self._safe_get("results_gbw", gbw_index, "molecule", "s_matrix")

        if overlap_list is not None:
            overlap = np.array(overlap_list)
            return overlap
        else:
            return None

    def get_int_hcore(
        self, recreate_json: bool = False, gbw_index: int = 0
    ) -> npt.NDArray[np.float64] | None:
        """
        Returns the core hamiltonian integral matrix as numpy array.

        Parameters
        ----------
        recreate_json : bool, default = False
            If True, recreate the gbw json file and request (exclusively) the hcore integrals to be included.
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` for which integrals are requested. Default 0 refers to the main gbw file.
        """

        if recreate_json:
            config_dict = {"1elIntegrals": ["H"]}
            self.recreate_gbw_results(config_dict, gbw_index)

        # > get hcore from gbw json files
        hcore_list = self._safe_get("results_gbw", gbw_index, "molecule", "h_matrix")

        if hcore_list is not None:
            return np.array(hcore_list)
        else:
            return None

    def get_int_f(
        self, recreate_json: bool = False, gbw_index: int = 0
    ) -> npt.NDArray[np.float64] | None:
        """
        Returns the two-electron interaction matrix F (often termed G).

        Parameters
        ----------
        recreate_json : bool, default = False
            If True, recreate the gbw json file and request (exclusively) the fock correction integrals to be included.
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` for which integrals are requested. Default 0 refers to the main gbw file.
        """

        if recreate_json:
            config_dict = {"FockMatrix": ["F"]}
            self.recreate_gbw_results(config_dict, gbw_index)

        # > get hcore from gbw json files
        fock_list = self._safe_get("results_gbw", gbw_index, "molecule", "f_matrix")

        if fock_list is not None:
            return np.array(fock_list[0])
        else:
            return None

    def get_int_j(
        self, recreate_json: bool = False, gbw_index: int = 0
    ) -> npt.NDArray[np.float64] | None:
        """
        Returns the Coulomb matrix J.

        Parameters
        ----------
        recreate_json : bool, default = False
            If True, recreate the gbw json file and request (exclusively) J to be included.
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` for which integrals are requested. Default 0 refers to the main gbw file.
        """

        if recreate_json:
            config_dict = {"FockMatrix": ["J"]}
            self.recreate_gbw_results(config_dict, gbw_index)

        # > get hcore from gbw json files
        j_list = self._safe_get("results_gbw", gbw_index, "molecule", "j_matrix")

        if j_list is not None:
            return np.array(j_list[0])
        else:
            return None

    def get_int_k(
        self, recreate_json: bool = False, gbw_index: int = 0
    ) -> npt.NDArray[np.float64] | None:
        """
        Returns the Exchange matrix K.

        Parameters
        ----------
        recreate_json : bool, default = False
            If True, recreate the gbw json file and request (exclusively) K to be included.
        gbw_index: int, default = 0
            Non-negative index of gbw file in `self.gbw_json_files` for which integrals are requested. Default 0 refers to the main gbw file.
        """

        if recreate_json:
            config_dict = {"FockMatrix": ["K"]}
            self.recreate_gbw_results(config_dict, gbw_index)

        # > get hcore from gbw json files
        k_list = self._safe_get("results_gbw", gbw_index, "molecule", "k_matrix")

        if k_list is not None:
            return np.array(k_list[0])
        else:
            return None
