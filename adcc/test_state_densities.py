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
import unittest

from .misc import expand_test_templates

from pytest import approx

from adcc.state_densities import attach_state_densities
from adcc.testdata.cache import cache

# The methods to test
basemethods = ["adc0", "adc1", "adc2", "adc2x", "adc3"]
methods = [m for bm in basemethods for m in [bm, "cvs_" + bm]]
methods.remove("cvs_adc3")  # Not implemented yet


@expand_test_templates(methods)
class Runners():
    def base_test(self, *args, **kwargs):
        raise NotImplementedError

    def template_h2o_sto3g_singlet(self, method):
        kwargs = {}
        if method == "adc3":
            kwargs = {"propmethod": "adc2"}
        self.base_test("h2o_sto3g", method, "singlet", **kwargs)

    def template_h2o_def2tzvp_singlet(self, method):
        kwargs = {}
        if method == "adc3":
            kwargs = {"propmethod": "adc2"}
        self.base_test("h2o_def2tzvp", method, "singlet", **kwargs)

    def template_h2o_sto3g_triplet(self, method):
        kwargs = {}
        if method == "adc3":
            kwargs = {"propmethod": "adc2"}
        self.base_test("h2o_sto3g", method, "triplet", **kwargs)

    def template_h2o_def2tzvp_triplet(self, method):
        kwargs = {}
        if method == "adc3":
            kwargs = {"propmethod": "adc2"}
        self.base_test("h2o_def2tzvp", method, "triplet", **kwargs)

    def template_cn_sto3g(self, method):
        kwargs = {}
        if method == "adc3":
            kwargs = {"propmethod": "adc2"}
        self.base_test("cn_sto3g", method, "state", **kwargs)

    def template_cn_ccpvdz(self, method):
        kwargs = {}
        if method == "adc3":
            kwargs = {"propmethod": "adc2"}
        self.base_test("cn_ccpvdz", method, "state", **kwargs)

    def template_hf3_631g_spin_flip(self, method):
        kwargs = {}
        if method == "adc3":
            kwargs = {"propmethod": "adc2"}
        self.base_test("hf3_631g", method, "spin_flip", **kwargs)


# Return combinations not tested so far:
#     The rationale is that cvs-spin-flip as a method do not make
#     that much sense and probably the routines are anyway covered
#     by the other testing we do.
delattr(Runners, "test_hf3_631g_spin_flip_cvs_adc0")
delattr(Runners, "test_hf3_631g_spin_flip_cvs_adc1")
delattr(Runners, "test_hf3_631g_spin_flip_cvs_adc2")
delattr(Runners, "test_hf3_631g_spin_flip_cvs_adc2x")
# delattr(Runners, "test_hf3_631g_spin_flip_cvs_adc3")


class TestStateDiffDm(unittest.TestCase, Runners):
    def base_test(self, system, method, kind, propmethod=None):
        if propmethod is None:
            propmethod = method
        method = method.replace("_", "-")
        propmethod = propmethod.replace("_", "-")

        refdata = cache.reference_data[system]
        state = cache.adc_states[system][method][kind]
        state = attach_state_densities(state, method=propmethod,
                                       state_diffdm=True,
                                       ground_to_excited_tdm=False,
                                       state_to_state_tdm=False)

        refdens_a = refdata[method][kind]["state_diffdm_bb_a"]
        refdens_b = refdata[method][kind]["state_diffdm_bb_b"]
        refevals = refdata[method][kind]["eigenvalues"]
        for i in range(len(state.eigenvectors)):
            # Check that we are talking about the same state when
            # comparing reference and computed
            assert state.eigenvalues[i] == refevals[i]

            dm_ao_a, dm_ao_b = state.state_diffdms[i].transform_to_ao_basis(
                state.reference_state
            )
            dm_ao_a = dm_ao_a.to_ndarray()
            dm_ao_b = dm_ao_b.to_ndarray()
            assert dm_ao_a == approx(refdens_a[i])
            assert dm_ao_b == approx(refdens_b[i])


class TestStateGroundToExcitedTdm(unittest.TestCase, Runners):
    def base_test(self, system, method, kind, propmethod=None):
        if propmethod is None:
            propmethod = method
        method = method.replace("_", "-")
        propmethod = propmethod.replace("_", "-")

        refdata = cache.reference_data[system]
        state = cache.adc_states[system][method][kind]
        state = attach_state_densities(state, method=propmethod,
                                       state_diffdm=False,
                                       ground_to_excited_tdm=True,
                                       state_to_state_tdm=False)

        refdens_a = refdata[method][kind]["ground_to_excited_tdm_bb_a"]
        refdens_b = refdata[method][kind]["ground_to_excited_tdm_bb_b"]
        refevals = refdata[method][kind]["eigenvalues"]
        for i in range(len(state.eigenvectors)):
            # Check that we are talking about the same state when
            # comparing reference and computed
            assert state.eigenvalues[i] == refevals[i]

            tdms = state.ground_to_excited_tdms[i].transform_to_ao_basis(
                state.ground_state.reference_state
            )
            dm_ao_a, dm_ao_b = tdms
            dm_ao_a = dm_ao_a.to_ndarray()
            dm_ao_b = dm_ao_b.to_ndarray()
            assert dm_ao_a == approx(refdens_a[i])
            assert dm_ao_b == approx(refdens_b[i])
