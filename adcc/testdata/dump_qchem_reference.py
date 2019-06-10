#!/usr/bin/env python3
## vi: tabstop=4 shiftwidth=4 softtabstop=4 expandtab
## ---------------------------------------------------------------------
##
## Copyright (C) 2018 by the adcc authors
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

# TODO:
# this file will only exist as long as we don't have proper
# reference data from adcman.
# However, this could come in handy for also comparing exciton properties
# at some point.

import os
import tempfile

from cclib.parser import QChem

from adcc.testdata.geometry import xyz
from adcc import hdf5io

_qchem_template = """
$rem
method                   {method}
basis                    {basis}
mem_total                {memory}
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
$end

$molecule
{charge} {multiplicity}
{xyz}
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


def generate_qchem_input_file(fname, method, basis, coords, charge=0,
                              multiplicity=1, memory=3000, singlet_states=5,
                              triplet_states=0, bohr=True, maxiter=60,
                              conv_tol=6, n_core_orbitals=0):
    nguess_singles = 2 * max(singlet_states, triplet_states)
    max_ss = 5 * nguess_singles
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
        xyz=clean_xyz(coords)
    )
    qc_file = open(fname, "w")
    qc_file.write(qci)
    qc_file.close()


def dump_qc_h2o(basename, method, basis, n_core_orbitals=0):
    with tempfile.TemporaryDirectory() as tmpdir:
        infile = os.path.join(tmpdir, basename + ".in")
        outfile = os.path.join(tmpdir, basename + ".out")
        ret = {
            "method": method,
            "basis": basis,
        }
        generate_qchem_input_file(
            infile, method, basis, xyz["h2o"].strip(), conv_tol=10,
            n_core_orbitals=n_core_orbitals
        )
        # only works with my (ms) fork of cclib
        # github.com/maxscheurer/cclib
        os.system("qchem -nt 4 {} {}".format(infile, outfile))
        res = QChem(outfile).parse()
        ret["oscillator_strengths"] = res.etoscs
        ret["exc_dipole_moments [D]"] = res.etdipmoms
        hdf5io.save(fname="{}_qc.hdf5".format(basename),
                    dictionary=ret)
        bla = hdf5io.load(fname="{}_qc.hdf5".format(basename))
        print(bla)


def dump_qc_cn(basename, method, basis, n_core_orbitals=0):
    with tempfile.TemporaryDirectory() as tmpdir:
        infile = os.path.join(tmpdir, basename + ".in")
        outfile = os.path.join(tmpdir, basename + ".out")
        ret = {
            "method": method,
            "basis": basis,
        }
        generate_qchem_input_file(
            infile, method, basis, xyz["cn"].strip(), conv_tol=10,
            n_core_orbitals=n_core_orbitals, multiplicity=2
        )
        # only works with my (ms) fork of cclib
        # github.com/maxscheurer/cclib
        os.system("qchem -nt 4 {} {}".format(infile, outfile))
        res = QChem(outfile).parse()
        ret["oscillator_strengths"] = res.etoscs
        ret["exc_dipole_moments [D]"] = res.etdipmoms
        hdf5io.save(fname="{}_qc.hdf5".format(basename),
                    dictionary=ret)
        bla = hdf5io.load(fname="{}_qc.hdf5".format(basename))
        print(bla)


def main():
    # for basis in ["def2tzvp", "sto3g", "ccpvdz"]:
    #     for method in ['adc1', 'adc2', 'adc2x', 'adc3']:
    #         basename = "h2o_{}_{}".format(basis, method)
    #         dump_qc_h2o(basename, method, basis)
    #         basename = "h2o_{}_cvs_{}".format(basis, method)
    #         dump_qc_h2o(
    #             basename, "cvs-{}".format(method), basis, n_core_orbitals=1
    #         )
    for basis in ["sto3g", "ccpvdz"]:
        for method in ['adc1', 'adc2', 'adc2x', 'adc3']:
            basename = "cn_{}_{}".format(basis, method)
            dump_qc_cn(basename, method, basis)
            basename = "cn_{}_cvs_{}".format(basis, method)
            dump_qc_cn(
                basename, "cvs-{}".format(method), basis, n_core_orbitals=1
            )


if __name__ == "__main__":
    main()