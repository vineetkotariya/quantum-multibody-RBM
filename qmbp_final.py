# -*- coding: utf-8 -*-
"""QMBP_final.ipynb
Author: Vineet Kotariya
Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/19Sc5l-N2FFXLIEQHu3J2yxpt3Q58LdNC
"""

import numpy as np
#import cupy as np
import random
import math

#TODO: See if Thetas is needed!
class wavefunct(object):
    def __init__(self, n_hidden, n_visible, w0, a=None, b=None, w = None):
        if a:
            self.a = np.array(a)  # If weights are provided
            self.b = np.array(b)
            self.w = np.array(w)
        else:
            self.a = w0 * (np.random.rand(n_visible, 1) - 0.5)  # Random weights at start from w0*[-0.5,0.5]
            self.b = w0 * (np.random.rand(n_hidden, 1) - 0.5)
            self.w = w0 * (np.random.rand(n_visible, n_hidden) - 0.5)

        self.a = self.a.astype(dtype=complex)  # Typecasting all to complex
        self.b = self.b.astype(dtype=complex)
        self.w = self.w.astype(dtype=complex)
        self.n_hidden = n_hidden
        self.n_visible = n_visible
        self.thetas = b

    def derivative(self, state):
        # wrt to a:
        d_da = np.array(state).reshape((self.n_visible, 1))
        theta = self.b + np.matmul(self.w.T, state.reshape(self.n_visible, 1))
        # for i in range (0,self.n_visible):#    theta = theta + self.w[i] * state[i]

        d_db = np.tanh(theta)
        d_dw = np.matmul(d_da.reshape((self.n_visible, 1)), d_db.reshape((1, self.n_hidden)))
        return d_da, d_db, d_dw

    def theta_calc(self, state):
        return self.b + np.matmul(self.w.T, state.reshape(self.n_visible, 1))

    def ln_psi(self, state):
        return np.matmul(self.a.T, state) + np.sum(np.log(2 * np.cosh(self.theta_calc(state))))
    def ln_ratio_of_psi(self, state, flip_positions):
        #ratio ln(psi(s')/psi(s)) = ln(psi(s')) - ln(psi(s))
        if(len(flip_positions) == 0):
            return 0.0
        '''
        # sum(a(i)*s'(i)) + sum(ln(2*cosh(theta(s'(i))))) - sum(a(i)*s(i)) - sum(ln(2*cosh(theta(s(i)))))
        # Alt: sum(a(i)*s'(i)) - sum(a(i)*s(i)) = 2*(product at flip positions) + diff of sum(ln(cosh))
        temp = state
        for i in flip_positions:
            temp[i] = -1*state[i]
        return self.ln_psi(temp) - self.ln_psi(state)
        '''
        v = np.zeros((self.n_visible, 1))
        for flip_loc in flip_positions:
            v[flip_loc] = 2 * state[flip_loc]

        logpop = - np.dot(self.a.T, v) + np.sum(np.log(np.cosh(self.thetas - np.dot(self.w.T, v))) - np.log(np.cosh(self.thetas)))

        return logpop

    def init_lookup_tables(self, state):
        s = np.array(state, dtype=float).reshape((self.n_visible, 1))
        self.thetas = self.b + np.dot(self.w.T, s)   

    def update_lookup_tables(self, state, flips_to_new_state):
        if len(flips_to_new_state) == 0:
            return
        v = np.zeros((self.n_visible, 1))
        for flip_loc in flips_to_new_state:
            v[flip_loc] = 2 * state[flip_loc]

        self.thetas -= np.dot(self.w.T, v) 
        
    def update_params(self, update_vals):
      da = update_vals[:self.n_visible]
      db = update_vals[self.n_visible:self.n_visible+self.n_hidden]
      dw = update_vals[self.n_visible+self.n_hidden:]
      dw = dw.reshape((self.n_visible, self.n_hidden))
      self.a -= da
      self.b -= db
      self.w -= dw
      #self.thetas = self.b

class ising1D(object):
    """
    Class represents the Hamiltonian of the 1D ising model with
    transverse field h_x and exchange J_z=1
    """
    def __init__(self, n_spins, h_x, periodic):
        self.min_flip = 1
        self.n_spins = n_spins
        self.h_x = h_x
        self.periodic = periodic
        self.matrix_elements = np.zeros((n_spins + 1)) - self.h_x
        self.spin_flip_transitions = [[]] + [[i] for i in range(self.n_spins)]

    def min_flips(self):
        return self.min_flip

    def num_spins(self):
        return self.n_spins

    def field(self):
        return self.h_x

    def is_periodic(self):
        return self.periodic

    def find_matrix_elements(self, state):
        """
        inputs
            state: list of integers, with each corresponding to quantum number
        returns:
            transitions: list of states s such that <s|H|state> is nonzero.
                s are represented as a list of integers corresponding to which
                quantum variables got swapped
            matrix_elements: complex list <s|H|state> for each s in transitions
        """
        matrix_elements = self.matrix_elements

        # computing interaction part Sz*Sz
        matrix_elements[0] = 0.0
        for i in range(self.n_spins - 1):
            matrix_elements[0] -= state[i] * state[i + 1]
        if self.periodic:
            matrix_elements[0] -= state[self.n_spins - 1] * state[0]

        return matrix_elements, self.spin_flip_transitions

#TODO: See if Thetas is needed!
class Sampler(object):

  def __init__(self, hamiltonian, nqs, zero_magnetization=True, filename=None, initial_state=None, any_total_spin=False):

    self.nqs = nqs
    self.n_visible = nqs.n_visible
    self.outfile = filename
    self.n_acceptances = 0.0
    self.n_moves = 0.0
    self.state_history = []
    self.local_energies = []
    self.current_Hloc = 0
    self.zero_magnetization = zero_magnetization
    self.hamiltonian = hamiltonian
    self.nqs_energy = None
    self.nqs_energy_err = None
    self.any_total_spin = any_total_spin # If False : means total spin can either be 0, +1 or -1 at initialization #TODO: update the flip_position rule to incorporate

    if initial_state is None:
      self.initialize_state()
    else:
      self.curr_state = initial_state
    
  def initialize_state(self):

    # Initializing the spin config.
    self.curr_state = np.zeros(self.n_visible, int)
    if(self.any_total_spin==False):
        if(self.zero_magnetization):  # self.n_visible/2 no. of 1 and -1
            if((self.n_visible % 2) != 0):
                raise SystemExit('No. of spins has to be even for zero total spin')
            for i in range(0, int(self.n_visible / 2)):
                self.curr_state[i] = -1
            for i in range(int(self.n_visible / 2), self.n_visible):
                self.curr_state[i] = 1
        else:  # (self.n_visible/2 - 1) no. of 1 and (self.n_visible/2 - 1) no. of -1 to start with
            for i in range(0, int(self.n_visible / 2)):
                self.curr_state[i] = -1
            for i in range(int(self.n_visible / 2), self.n_visible - 1):
                self.curr_state[i] = 1
            self.curr_state[self.n_visible - 1] = random.choice([-1, 1])
        np.random.shuffle(self.curr_state)
    else:
        self.curr_state = [random.randrange(-1, 2, 2)
                          for _ in range(self.n_visible)]

  def flip_the_spins(self, n_flips):

    first_flip_position = random.randint(0, self.n_visible - 1) # Random spin position is picked
    if(n_flips == 2): 
      second_flip_position = random.randint(0, self.n_visible - 1)
      if(self.zero_magnetization): # We can't filp two same spins
        if (self.curr_state[first_flip_position] == self.curr_state[second_flip_position]): #Both spins are the same
          return []
        else: # Both spins are different
          #TODO: # Is it okay if both positions are the same?
          return [first_flip_position, second_flip_position] 
      else:
        if(first_flip_position == second_flip_position):
          return []
        else:
          return [first_flip_position, second_flip_position] 
    else:
      return [first_flip_position]

  def move(self, n_flips): #Wavefunction (nqs) 

    flip_positions = self.flip_the_spins(n_flips)
    if (len(flip_positions) > 0):
      wavef_ratio = np.exp(self.nqs.ln_ratio_of_psi(self.curr_state, flip_positions)) # e^(ln(psi(s')/psi(s)))
      acceptance_prob = np.square(np.abs(wavef_ratio)) # is np.abs needed?

      if acceptance_prob > random.random(): # Metropolis-Hastings Test
        #TODO: Update lookup table (if implemented)
        self.nqs.update_lookup_tables(self.curr_state, flip_positions)
        self.n_acceptances = self.n_acceptances + 1
        for f in flip_positions:
          self.curr_state[f] = self.curr_state[f] * -1

  def run(self, n_sweeps, therm_factor=0.1, sweep_factor=1, n_flips=None):

    if(n_flips != 1  & n_flips !=2 ):
      raise SystemExit('Invalid value of n_flips')
    if not (0 <= therm_factor <= 1):
      raise SystemExit('Thermalization Factor must be between 0 and 1')
    if(n_sweeps < 50):
      raise SystemExit('No. of sweeps must be greater than 50')

    print('Starting Sampling')
    print('Will perform',n_sweeps,'steps')

    #init_lookup_tables
    #reset_sampler_values()
    self.n_acceptances = 0
    self.n_moves = 0

    self.nqs.init_lookup_tables(self.curr_state)
    if(therm_factor != 0): # This is to ignore the first few iterations as mentioned in the paper 
      print('Starting Thermalization')
      self.n_moves = int(therm_factor * n_sweeps) * int(sweep_factor * self.n_visible)
      for _ in range(self.n_moves):
        self.move(n_flips)
      print('Thermalization completed')

    #self.reset_sampler_values()
    self.n_acceptances = 0
    self.n_moves = 0
    self.state_history = []

    print('Starting Monte Carlo Sampling')
    for i in range(int(n_sweeps)):
      for _ in range(int(sweep_factor * self.n_visible)):
        self.move(n_flips)

      #TODO: Whatever needed here
      self.state_history.append(np.array(self.curr_state))
      self.current_Hloc = self.loc_energy()
      self.local_energies.append(self.current_Hloc)
      
    print('Completed Monte Carlo Sampling')
    return self.wavef_energy()
  
  
  def loc_energy(self):
    # all the state' such that <state'|H|state> = mel(state') != 0
    state = self.curr_state
    (matrix_elements, transitions) = self.hamiltonian.find_matrix_elements(state)

    energy_list = [np.exp(self.nqs.ln_ratio_of_psi(state, transitions[i])) * mel #self.nqs.amplitude_ratio(state, transitions[i]) * mel
                    for (i, mel) in enumerate(matrix_elements)]
    return np.sum(energy_list)

  def wavef_energy(self):
    #Refer to OutputEnergy() function in sampler.cc of Carleo code

    nblocks = 50
    blocksize = int(len(self.local_energies) / nblocks)
    enmean = 0.0
    enmeansq = 0.0
    enmean_unblocked = 0.0
    enmeansq_unblocked = 0.0

    for i in range(nblocks):
      eblock = 0.0
      for j in range(i * blocksize, (i + 1) * blocksize):
        eblock += self.local_energies[j].real
        delta = self.local_energies[j].real - enmean_unblocked
        enmean_unblocked += delta / (j + 1)
        delta2 = self.local_energies[j].real - enmean_unblocked
        enmeansq_unblocked += delta * delta2
      eblock /= blocksize
      delta = eblock - enmean
      enmean += delta / (i + 1)
      delta2 = eblock - enmean
      enmeansq += delta * delta2

    enmeansq /= (nblocks - 1)
    enmeansq_unblocked /= (nblocks * blocksize - 1)
    est_avg = enmean / self.n_visible
    est_error = math.sqrt(enmeansq / nblocks) / self.n_visible

    #Squeeze needed to remove the extra brackets at the end (change from (1,m,n) -> (m,n))
    self.nqs_energy = np.squeeze(est_avg)
    self.nqs_energy_err = np.squeeze(est_error)

    energy_report = 'Estimated average energy per spin: {} +/- {}'
    print(energy_report.format(est_avg, est_error))
    #self.f_aeps.write(aeps.format(est_avg, est_error))
    #f_aeps = open('avg_energy_per_spin.txt', 'w+')
    #f_aeps.write('Avg_energy_per_spin error_estimate')
    with open('avg_energy_per_spin.txt', 'a') as f_aeps:
      f_aeps.write("{} {}\n".format(np.squeeze(est_avg), est_error))

    bin_report = 'Error estimated with binning analysis consisting of ' + '{} bins'
    print(bin_report.format(nblocks))
    print('Block size is', blocksize)
    autocorrelation = 'Estimated autocorrelation time is {}'
    self.correlation_time = 0.5 * blocksize * enmeansq / enmeansq_unblocked
    print(autocorrelation.format(self.correlation_time))
    
    #print(self.local_energies)

  #def write_state(self, file):

#TODO: See if Thetas is needed!
class stochastic_reconfig(object):
  #Optimize the network
  def __init__(self, nqs, hamiltonian, learning_rate=0.5e-2,n_sweeps=10000, therm_factor=0.1, sweep_factor=1, n_flips=None, zero_magnetization=True):
    self.nqs = nqs
    self.n_sweeps = n_sweeps
    self.therm_factor = therm_factor
    self.sweep_factor = sweep_factor
    self.n_flips = n_flips
    self.eta = learning_rate
    self.err = []
    self.loss = []
    self.zero_magnetization = zero_magnetization
    self.hamiltonian = hamiltonian
    self.learning_rate = learning_rate

    #print('Optimizing the neural network')

  def run(self, n_epochs, init_state=None):

    for e in range(n_epochs):
      print('Epoch:',e)
      sampler = Sampler(hamiltonian=self.hamiltonian, nqs=self.nqs, zero_magnetization=self.zero_magnetization, initial_state=init_state)

      initial_state = sampler.curr_state

      sampler.run(self.n_sweeps, self.therm_factor, self.sweep_factor, self.n_flips)

      update_vals, _ = self.compute_gradients(sampler, e+1)
      print(update_vals.shape)
      self.nqs.update_params(self.learning_rate*update_vals)


  def compute_gradients(self, sampler, e):

    states = sampler.state_history
    Elocs = np.array(sampler.local_energies).reshape((len(sampler.local_energies), 1))

    print('Computing stochastic reconfiguration updates')

    self.loss.append(sampler.nqs_energy)
    self.err.append(sampler.nqs_energy_err)

    B = self.nqs.b
    weight = self.nqs.w


    update, derivs = self.compute_derivs(e, Elocs, B, weight, np.array(states, dtype=complex), self.nqs.n_visible, self.nqs.n_hidden, len(states))

    return update, derivs

  def compute_derivs(self, p, Eloc, b, w, state, n_visible, n_hidden, n_state_history):
    #state = spins (sigma in SM pg 6 eq S9, S10) 
    theta = np.dot(np.transpose(w), np.transpose(state)) + b
    #da = np.transpose(theta)
    da = np.transpose(state)
    #print(da.shape)
    #db = np.transpose(np.tanh(theta))
    db =  np.tanh(theta)
    #print(db.shape)
    dw = ( (np.transpose(state)).reshape((n_visible, 1, n_state_history)) ) * np.tanh(theta.reshape((1, n_hidden, n_state_history)))
    #print(dw.shape)
    #print(n_visible,n_hidden,n_state_history)
    derivs = np.concatenate([da, db, dw.reshape(n_visible * n_hidden, n_state_history)])
    #print(derivs.shape)
    avg_derivs = np.sum(derivs, axis=1, keepdims=True) / n_state_history
    #Use np.mean directly
    avg_derivs_mat = np.conjugate(avg_derivs.reshape(derivs.shape[0], 1))
    avg_derivs_mat = avg_derivs_mat * avg_derivs.reshape(1, derivs.shape[0])

    moment2 = np.einsum('ik,jk->ij', np.conjugate(derivs), derivs) / n_state_history
    # See SM pg2 eq S3 - S5
    S_kk = np.subtract(moment2, avg_derivs_mat)

    F_p = np.sum(Eloc.transpose() * np.conjugate(derivs), axis=1) / n_state_history

    F_p -= np.sum(Eloc.transpose(), axis=1) * np.sum(np.conjugate(derivs), axis=1) / (n_state_history ** 2)
    
    S_kk2 = np.zeros(S_kk.shape, dtype=complex)
    row, col = np.diag_indices(S_kk.shape[0])

    #Lambda regularization parameter for S_kk matrix calculation:
    #Can define a function
    lambda0 = 100
    b_= 0.9
    lambda_min = 1e-4
    lambda_p = max(lambda0 * (b_ ** p), lambda_min)

    S_kk2[row, col] = lambda_p * np.diagonal(S_kk)
    S_reg = S_kk + S_kk2
    update = np.dot(np.linalg.inv(S_reg), F_p).reshape(derivs.shape[0], 1)
    #print(update.shape)

    return update, derivs

if __name__ == "__main__":
  #Ising 1D
  n_spins = 40
  alpha = 2
  n_vis = n_spins
  n_hid = n_spins*alpha
  h = 2
  ham = ising1D(n_spins,h,True)
  nqs = wavefunct(n_visible=n_vis,n_hidden=n_hid,w0=0.001)
  optimizer = stochastic_reconfig(nqs=nqs, hamiltonian=ham, learning_rate=0.5e-2,n_sweeps=10000, 
                                  therm_factor=0.1, sweep_factor=1, n_flips=1, zero_magnetization=True)
  optimizer.run(200)

  np.savetxt('a.csv', np.squeeze(nqs.a.view(dtype=np.float64)), delimiter=',')
  np.savetxt('b.csv', np.squeeze(nqs.b.view(dtype=np.float64)), delimiter=',')
  np.savetxt('w.csv', np.squeeze(nqs.w.view(dtype=np.float64)).reshape((1600, 2)), delimiter=',')

np.savetxt('a.csv', np.squeeze(nqs.a.view(dtype=np.float64)), delimiter=',')
  np.savetxt('b.csv', np.squeeze(nqs.b.view(dtype=np.float64)), delimiter=',')
  np.savetxt('w.csv', np.squeeze(nqs.w.view(dtype=np.float64)).reshape((1600, 2)), delimiter=',')
  """
  #with open('avg_energy_per_spin.txt', 'w') as f_aeps:
  f_aeps = open('avg_energy_per_spin.txt', 'w')
  print('Avg_energy_per_spin error_estimate' )
  print(est_avg, est_err, file=f_aeps)  # Python 3.x
  f_aeps.close()
  """
  #Print weights
  a = np.squeeze(nqs.a.view(dtype=np.float64))
  print(nqs.a.shape)
  print(nqs.w.shape)
