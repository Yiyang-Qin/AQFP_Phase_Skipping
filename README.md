This code contains the algorithmic flow presented in "A Joint Optimization of Buffer and Splitter Insertion for Phase-Skipping Adiabatic Quantum-Flux-Parametron Circuits", Robert S. Aviles and Peter A. Beerel, appearing in ICCD 2024.

Running this code requires a call to IBM CPLEX (https://www.ibm.com/support/pages/installation-ibm-ilog-cplex-optimization-studio-linux-platforms) managed via solve.cpp.  After installation, Make should be called to create the CPLEX executable that is later called by Python. 

Thereafter, the entire flow can be called via python3 AQFP_PhaseSkipping.py > Optimization.log

The Benchmarks being tested and circuit parameter can be modified from the bottom lines in AQFP_PhaseSkipping.py.

The flow uses a created python network and node class to represent the circuit and gates.  Created as a stand-alone enviroment for evaluation of algorithmic results, this implementation was not optimized for performance.  As a result circuit manipulations can take significant time due to numerous calls to large dictionaries and lists.  For the largest Benchmarks expect ~30min of runtime.

For questions or assistance emails can be directed to rsaviles@usc.edu.

