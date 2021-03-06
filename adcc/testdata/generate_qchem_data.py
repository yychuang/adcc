#!/usr/bin/env python3
## vi: tabstop=4 shiftwidth=4 softtabstop=4 expandtab
## ---------------------------------------------------------------------
##
## Copyright (C) 2020 by the adcc authors
##
## This file is part of adcc.
##
## adcc is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published
## by the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## adcc is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with adcc. If not, see <http://www.gnu.org/licenses/>.
##
## ---------------------------------------------------------------------
import os
import sh
import tempfile
import yaml

from cclib.parser import QChem
import numpy as np

from static_data import xyz
from static_data import pe_potentials

from scipy import constants

eV = constants.value("Hartree energy in eV")

_qchem_template = """
$rem
method                   {method}
basis                    {basis}
mem_total                {memory}
pe                       {pe}
ee_singlets              {singlet_states}
ee_triplets              {triplet_states}
input_bohr               {bohr}
sym_ignore               true
adc_davidson_maxiter     {maxiter}
adc_davidson_conv        {conv_tol}
adc_nguess_singles       {n_guesses}
adc_davidson_maxsubspace {max_ss}
adc_prop_es              true
cc_rest_occ              {cc_rest_occ}

! scf stuff
use_libqints             true
gen_scfman               true
$end

$molecule
{charge} {multiplicity}
{xyz}
$end
"""

_pe_template = """
$pe
potfile {potfile}
$end
"""

_method_dict = {
    "adc0": "adc(0)",
    "adc1": "adc(1)",
    "adc2": "adc(2)",
    "adc2x": "adc(2)-x",
    "adc3": "adc(3)",
    "cvs-adc0": "cvs-adc(0)",
    "cvs-adc1": "cvs-adc(1)",
    "cvs-adc2": "cvs-adc(2)",
    "cvs-adc2x": "cvs-adc(2)-x",
    "cvs-adc3": "cvs-adc(3)",
}

basis_remap = {
    "sto3g": "sto-3g",
    "def2tzvp": "def2-tzvp",
    "ccpvdz": "cc-pvdz",
}


def clean_xyz(xyz):
    return "\n".join(x.strip() for x in xyz.splitlines())


def generate_qchem_input_file(fname, method, basis, coords, potfile=None,
                              charge=0, multiplicity=1, memory=8000,
                              singlet_states=5, triplet_states=0, bohr=True,
                              maxiter=160, conv_tol=10, n_core_orbitals=0):
    nguess_singles = 2 * max(singlet_states, triplet_states)
    max_ss = 5 * nguess_singles
    pe = potfile is not None
    qci = _qchem_template.format(
        method=_method_dict[method],
        basis=basis_remap[basis],
        memory=memory,
        singlet_states=singlet_states,
        triplet_states=triplet_states,
        n_guesses=nguess_singles,
        bohr=bohr,
        maxiter=maxiter,
        conv_tol=conv_tol,
        max_ss=max_ss,
        charge=charge,
        multiplicity=multiplicity,
        cc_rest_occ=n_core_orbitals,
        xyz=clean_xyz(coords),
        pe=pe
    )
    if pe:
        qci += _pe_template.format(potfile=potfile)
    qc_file = open(fname, "w")
    qc_file.write(qci)
    qc_file.close()


def dump_qchem(molecule, method, basis, **kwargs):
    with tempfile.TemporaryDirectory() as tmpdir:
        pe = kwargs.get("potfile", None) is not None
        if pe:
            basename = f"{molecule}_{basis}_pe_{method}"
        else:
            basename = f"{molecule}_{basis}_{method}"
        infile = os.path.join(tmpdir, basename + ".in")
        outfile = os.path.join(tmpdir, basename + ".out")
        geom = xyz[molecule].strip()
        ret = {
            "molecule": molecule,
            "method": method,
            "basis": basis,
            "pe": pe,
            "geometry": geom
        }
        generate_qchem_input_file(infile, method, basis,
                                  geom, **kwargs)
        # only works with my (ms) fork of cclib
        # github.com/maxscheurer/cclib, branch dev-qchem
        sh.qchem(infile, outfile)
        res = QChem(outfile).parse()
        ret["oscillator_strength"] = res.etoscs
        ret["excitation_energy"] = res.etenergies / eV
        if pe:
            ret["pe_ptss_correction"] = np.array(res.peenergies["ptSS"]) / eV
            ret["pe_ptlr_correction"] = np.array(res.peenergies["ptLR"]) / eV
        for key in ret:
            if isinstance(ret[key], np.ndarray):
                ret[key] = ret[key].tolist()
        return basename, ret


def main():
    basissets = ["sto3g", "ccpvdz"]
    methods = ["adc1", "adc2", "adc3"]
    qchem_results = {}
    for method in methods:
        for basis in basissets:
            key, ret = dump_qchem("formaldehyde", method, basis,
                                  potfile=pe_potentials["fa_6w"])
            qchem_results[key] = ret
            print(f"Dumped {key}.")
    with open("qchem_dump.yml", "w") as yamlout:
        yaml.safe_dump(qchem_results, yamlout)


if __name__ == "__main__":
    main()
