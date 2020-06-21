# quantum-multibody-RBM
Using RBMs to solve certain quantum multi-body problems. Based on work by Carleo Troyer 2017   
### Parameters
n_spins : Number of spins (input states)  
alpha : n_hidden = n_spins * alpha  
h : h_x in the Hamiltonian  
n_sweeps : No. of sweeps per epoch  
sweep_factor : one sweep consists of (n_spins * sweep_factor) steps (flipping each spin an expected number of n_flips times)  
therm_factor : (therm_factor * n_sweeps) no. of markov process steps are discarded (for thermalization)  


