#!/usr/bin/env python3
## vi: tabstop=4 shiftwidth=4 softtabstop=4 expandtab
import adcc

from import_data import import_data
from adcc.solver.adcman import jacobi_davidson

# Gather preliminary data and import it into an HfData object
data = import_data()

# Initialise the memory (256 MiB)
adcc.memory_pool.initialise(max_memory=256 * 1024 * 1024)

# Setup the matrix
refstate = adcc.tmp_build_reference_state(data)
matrix = adcc.AdcMatrix("adc2", adcc.LazyMp(refstate))

# Solve for 3 singlets and 3 triplets with some default output
states = jacobi_davidson(matrix, print_level=100, n_singlets=3, n_triplets=3)
print(states[0].describe())
print(states[1].describe())
