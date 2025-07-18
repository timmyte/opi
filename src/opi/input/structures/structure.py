import re
from os import PathLike
from pathlib import Path
from typing import Any, Iterable, Sequence, cast

import numpy as np
import numpy.typing as npt

# > RDKIT
from rdkit.Chem import Mol as RdkitMol
from rdkit.Chem.rdDistGeom import EmbedMolecule
from rdkit.Chem.rdmolfiles import MolFromSmiles, MolFromXYZBlock  # type: ignore
from rdkit.Chem.rdmolops import AddHs

from opi.input.structures.atom import (
    Atom,
    DummyAtom,
    EmbeddingPotential,
    GhostAtom,
    PointCharge,
)
from opi.input.structures.coordinates import Coordinates
from opi.utils.element import Element

__all__ = ("Structure",)


class Structure:
    """
    Class to model internal structure for ORCA calculations.

    Attributes
    ----------
    atoms: list[Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge]
        Atoms in the molecule
    charge: int
        Charge of structure
    multiplicity: int
        Multiplicity of structure
    origin: Path | str
        Origin of the molecule, usually path to a file or some identifier

    """

    def __init__(
        self,
        atoms: Atom
        | DummyAtom
        | EmbeddingPotential
        | GhostAtom
        | PointCharge
        | Sequence[Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge]
        | Iterable[Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge],
        charge: int = 0,
        multiplicity: int = 1,
        origin: Path | str | None = None,
    ) -> None:
        # // Atoms
        self._atoms: list[Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge] = []
        self.atoms = cast(
            list[Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge], atoms
        )
        # // Charge
        self._charge: int
        self.charge = charge
        # // Multiplicity
        self._multiplicity: int
        self.multiplicity = multiplicity

        # > Origin of the molecule. Typically, the path to the file or some identifier
        self.origin: Any | None = origin

    @property
    def atoms(self) -> list[Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge]:
        return self._atoms

    @atoms.setter
    def atoms(
        self,
        value: Atom
        | DummyAtom
        | EmbeddingPotential
        | GhostAtom
        | PointCharge
        | Sequence[Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge]
        | Iterable[Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge],
    ) -> None:
        """
        Parameters
        ----------
        value : Atom | DummyAtom| EmbeddingPotential | GhostAtom | PointCharge | Sequence[Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge]| Iterable[Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge]
        """
        if not isinstance(value, (Sequence, Iterable)):
            # > Assume a single Atom object
            value = [value]
        self._atoms = list(value)

    @property
    def charge(self) -> int:
        return self._charge

    @charge.setter
    def charge(self, value: int) -> None:
        """
        Parameters
        ----------
        value : int
        """
        if not isinstance(value, int):
            raise TypeError(f"{self.__class__.__name__}.charge: must be an integer")
        self._charge = value

    @property
    def multiplicity(self) -> int:
        return self._multiplicity

    @multiplicity.setter
    def multiplicity(self, value: int) -> None:
        """
        Parameters
        ----------
        value : int
        """
        if not isinstance(value, int):
            raise TypeError(f"{self.__class__.__name__}.multiplicity: must be an integer")
        elif value < 1:
            raise ValueError(f"{self.__class__.__name__}.multiplicity: must be positive")
        self._multiplicity = value

    @classmethod
    def combine_molecules(cls, structure1: "Structure", structure2: "Structure") -> "Structure":
        """
        function to combine two objects of `Molecule` class

        Parameters
        ----------
        structure1: Structure
            Define first structure to be combined
        structure2: Structure
            Define second structure to be combined

        Returns
        -------
        Structure:Combined structure
        """
        # data from structure2 will be concatenated to end of data for structure1
        new_atoms = structure1.atoms + structure2.atoms
        return Structure(atoms=new_atoms)

    def format_orca(self) -> str:
        """
        Returns string representation of Molecule
        Iteratively calls Atom.format_orca() and compiles it all together to create string representation of Molecule

        Returns
        -------
            str:
                String representation of Molecule
        """
        # String representation of Molecule class , mostly used for .xyz file
        text = f"* xyz {self.charge} {self.multiplicity}\n"
        for atom in self.atoms:
            text += f"{atom.format_orca()}\n"
        text += "*"

        return text

    def add_atom(
        self,
        new_atom: Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge,
        position: int | None = None,
    ) -> None:
        """
        Adds Atom object at specified index.
        If index is None, Atom object appended to end of list

        Parameters
        ----------
        new_atom : Atom
            Atom model to be added to self.atoms
        position : int | None, default = None
            position at which Atom is supposed to be added , default value None

        Raises
        ------
        ValueError
          if index is an invalid value
        """
        # adds atom at a specified position
        if position is not None and (position <= 0 or position > len(self.atoms) + 1):
            raise ValueError("Invalid position")
        # In the case that e is a str , it is converted into object from Element
        # New atom added to self.atoms
        if position is None:
            self.atoms.append(new_atom)
        else:
            self.atoms.insert(position, new_atom)

    def delete_atom(self, index: int) -> None:
        """
        Deletes Atom at specified index

        Parameters
        ----------
        index : int
            specifies index of Atom to be deleted

        Raises
        ------
        ValueError
          if index is invalid value
        """
        # deletes atom at specific index
        if 0 <= index < len(self.atoms):
            self.atoms.pop(index)
        else:
            raise ValueError("Invalid index")

    def replace_atom(
        self, new_atom: Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge, index: int
    ) -> None:
        """
        replaces Atom at index with a new Atom object

        Parameters
        ----------
        new_atom : Atom | DummyAtom | EmbeddingPotential | GhostAtom | PointCharge
            new Atom object to replace the old Atom object
        index : int
            index of Atom to be replaced

        Raises
        ------
        ValueError
          if index is invalid value
        """
        # replaces atom at specific index with new_index
        if 0 <= index < len(self.atoms):
            self.atoms[index] = new_atom
        else:
            raise ValueError("Invalid index")

    def extract_substructure(self, indexes: list[int]) -> "Structure":
        """
        returns Molecule object that is a sub-molecule specified by indexes.

        Parameters
        ----------
        indexes : list[int]
            specifies indexes of Atom objects to be extracted

        Returns
        -------
        Molecule: new Molecule object
        """
        return Structure(atoms=[self.atoms[i] for i in indexes])

    def update_coordinates(self, array: npt.NDArray[np.float64]) -> None:
        """
        Validates dimensions of array first
        replace all coordinates of all atoms in Molecule object.
        Calls Atom.update_coordinates() iteratively , replacing the Atom.coordinates with rows from array argument

        Parameters
        ----------
        array : npt.NDArray[np.float64]
            new coordinates

        Raises
        ------
        ValueError
          in the case of wrong dimensions
        """
        # function to replace self.coord_block with another numpy array
        # dimensions checked first before proceeding
        if array.shape != (len(self.atoms), 3):
            raise ValueError(
                f"Invalid dimension ({array.shape}) coordinates. Expected shape: {(len(self.atoms), 3)}"
            )

        for i in range(len(array)):
            self.atoms[i].coordinates = array[i]

    def to_xyz_block(self) -> str:
        """Function to generate XYZ block"""
        # > Comment line will be empty
        xyz_block = f"{len(self)}\n\n"
        for atom in self.atoms:
            xyz_block += atom.format_xyz_line() + "\n"
        return xyz_block + "\n"

    @classmethod
    def from_xyz(
        cls,
        xyzfile: Path | str | PathLike[str],
        /,
        *,
        charge: int = 0,
        multiplicity: int = 1,
    ) -> "Structure":
        """
        Function for reading a xyz file and converting it to a molecular Structure

        Parameters
        ----------
        xyzfile : Path | str | PathLike[str]
            Name or path to xyz file
        charge : int, default: 0
            Charge of the molecule
        multiplicity : int, default: 1
            Electron spin multiplicity of the molecule

        Returns
        --------
        `Structure`:`Structure object extracted from file
        """
        # > converting into Path
        xyzfile = Path(xyzfile)

        # > Check if file exists
        if not xyzfile.exists():
            raise FileNotFoundError(f"XYZ file not found: {xyzfile}")

        # > Try reading the file
        atoms = []
        rgx_frag_id = re.compile(r"(?<=\()\d+(?=\))")
        rgx_atom_symbol_frag_id = re.compile(r"(?P<elem>[A-Za-z]{1,2})(\((?P<frag_id>\d+)\))?")

        with xyzfile.open() as f_xyz:
            # > Fetch number of atoms
            try:
                natoms = int(f_xyz.readline().split()[0])
            except (ValueError, IndexError) as err:
                raise ValueError(
                    f"Could not read number of atoms in line 1 from: {xyzfile}"
                ) from err

            # > Skipping comment line
            f_xyz.readline()

            # > Read atoms
            # >> This is just a helper variable for error reporting. Coordinates start from line 3
            iline = 2
            while line := f_xyz.readline().rstrip():
                iline += 1
                # > Line should have at least 4 columns
                atom_cols = line.split()
                if len(atom_cols) < 4:
                    raise ValueError(
                        f"Line {iline}: Invalidly formatted coordinate line in: {xyzfile}"
                    )

                # > Get atom symbol. > Titlelizing symbol, so the first letter is capitalized, any others are in lowercase.
                # >> First check if we have combination of atom symbol + fragment id
                match_atom_sym_frag_id = rgx_atom_symbol_frag_id.match(line.lstrip())
                if not match_atom_sym_frag_id:
                    raise ValueError(f"Line {iline}: Could not find atom symbol.")

                atom_sym = match_atom_sym_frag_id.group("elem")
                try:
                    element = Element(atom_sym)
                except Exception as err:
                    raise ValueError(f"Line {iline}: Invalid atom symbol: {atom_sym}") from err

                # > Fragment id
                # >> First, let's assume columns 2 through 4 are the coordinates.
                coords_cols = atom_cols[1:4]

                # > Check if the fragment id follows the atom symbol directly or is in a column of its own.
                if not (match_frag_id := match_atom_sym_frag_id.group("frag_id")):
                    if match_frag_id := rgx_frag_id.match(atom_cols[1]):
                        # > Coordinates are in columns 3 through 5
                        coords_cols = atom_cols[2:5]

                # > Convert string fragment id to integer
                frag_id = None
                if match_frag_id:
                    try:
                        frag_id = int(match_frag_id)
                    except ValueError as err:
                        raise ValueError(
                            f"Line {iline}: Invalid fragment id: {match_frag_id}"
                        ) from err

                # > Pass coordinates
                # // X
                try:
                    coord_x = float(coords_cols[0])
                except (ValueError, IndexError):
                    raise ValueError(f"Line {iline}: Invalid X coordinate: {coords_cols[1]}")
                # // Y
                try:
                    coord_y = float(coords_cols[1])
                except (ValueError, IndexError):
                    raise ValueError(f"Line {iline}: Invalid Y coordinate: {coords_cols[2]}")
                # // Z
                try:
                    coord_z = float(coords_cols[2])
                except (ValueError, IndexError) as err:
                    raise ValueError(f"Line {iline}: Invalid Z coordinate: {atom_cols[3]}") from err

                # > Adding atom
                atoms.append(
                    Atom(
                        element=element,
                        coordinates=Coordinates(coordinates=(coord_x, coord_y, coord_z)),
                        fragment_id=frag_id,
                    )
                )
            # << END OF LOOP
        # << END of WITH

        # > Check number of atoms declared in file agrees with apparent number of atoms.
        if natoms != len(atoms):
            raise ValueError(f"{natoms} were expected but {len(atoms)} were found in: {xyzfile}")

        return Structure(
            atoms=atoms,
            origin=xyzfile.expanduser().resolve(),
            charge=charge,
            multiplicity=multiplicity,
        )

    @classmethod
    def from_smiles(
        cls,
        smiles: str,
        /,
        *,
        charge: int | None = None,
        multiplicity: int | None = None,
    ) -> "Structure":
        """
        Function to read SMILES string and convert string to 3D coordinate structure and create Molecule object with it
        to store in self.molecule.

        Parameters
        ----------
        smiles : str
            SMILES string to be converted
        charge : int | None
            Charge of the molecule, will overwrite charge obtained from SMILES string
        multiplicity : int | None
            Electron spin multiplicity of the molecule, will overwrite multiplicity obtained from SMILES
            (which is always 1 by default)

        Returns
        --------
        `Structure`:`Structure object extracted from file

        Raises
        ------
        RuntimeError
            If EmbedMolecule() is unsuccessful
        """
        mol = MolFromSmiles(smiles)
        if not mol:
            raise ValueError(f"Invalid SMILES string: {smiles}")

        mol = AddHs(mol)
        if not mol:
            raise ValueError("Error when running AddHs")

        res = EmbedMolecule(mol)
        if res < 0:
            raise RuntimeError("Failed to embed molecule")

        return cls.from_rdkitmol(mol, charge=charge, multiplicity=multiplicity)

    @classmethod
    def from_rdkitmol(
        cls,
        mol: "RdkitMol",
        /,
        *,
        charge: int | None = None,
        multiplicity: int | None = None,
    ) -> "Structure":
        """
        Function to convert a RDKit Mol object to Structure object

        Parameters
        ----------
        mol : RdkitMol
            RDKit Mol object to be converted
        charge : int | None
            Charge of the molecule, will overwrite charge obtained from RDKit Mol
        multiplicity : int | None
            Electron spin multiplicity of the molecule, will overwrite multiplicity obtained from RDKit Mol

        Returns
        ---------
        `Structure` : Structure object created from information given by RDKit Mol object
        """

        # Compute 3D coordinates if needed
        if not mol.GetConformer().Is3D():  # type: ignore
            res = EmbedMolecule(mol)
            if res < 0:
                raise RuntimeError("Failed to embed molecule")

        conformer = mol.GetConformer()

        # Extract atoms
        atoms = []
        # RDKit saves charges and radical electrons as atomic properties
        # so to obtain the molecular charge and multiplicity we have to sum them
        rd_charge: int = 0
        rd_radical_electrons: int = 0
        for atom in mol.GetAtoms():
            idx = atom.GetIdx()
            element = atom.GetSymbol()  # type: ignore
            rd_charge += atom.GetFormalCharge()  # type: ignore
            rd_radical_electrons += atom.GetNumRadicalElectrons()  # type: ignore
            pos = conformer.GetAtomPosition(idx)  # type: ignore
            atoms.append(Atom(element=Element(element), coordinates=pos))

        # multiplicity is the number of open-shell/radical electrons + 1
        rd_multiplicity = rd_radical_electrons + 1

        # if nothing is enforced, we use the rdkit Mol charge
        if charge is None:
            charge = rd_charge

        # if nothing is enforced, we use the rdkit Mol multiplicity
        if multiplicity is None:
            multiplicity = rd_multiplicity

        return Structure(atoms=atoms, charge=charge, multiplicity=multiplicity)

    def to_rdkitmol(self, structure: "Structure", /) -> "RdkitMol":
        """
        Function to convert Molecule object to RDKit Mol object
        The Structure is converted into XYZ file format, which is then read by RDKit.

        Parameters
        ----------
        structure : `Structure`
            Molecule object to be converted

        Returns
        -------
        RdkitMol : RDKit Mol object generated from `Structure` object
        """

        xyz_block = structure.to_xyz_block()
        return cast(RdkitMol, MolFromXYZBlock(xyz_block))

    def __len__(self) -> int:
        return len(self.atoms)
