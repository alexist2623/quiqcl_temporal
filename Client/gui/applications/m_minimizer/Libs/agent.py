# -*- coding: utf-8 -*-
"""
@author: LKM
"""

import torch, pickle
import torch.nn.functional as F 
from torch import optim
import numpy as np
from Network import ValueNetwork, ActorNetwork
from datetime import datetime

class Agent:

    def __init__(self, config):
        self.basic_params(config)
        # State space = 8 values of two DC electrode (UL/UR/ML/MR/DL/DR/IL/IR)
        self.state_space = 3
        # Action space = UP/DOWN for one set of DC electrode (2 for each = 16)
        self.action_space = 6
        self.gamma = 0.01
        
        self.episode_hist = {}
        self.episode_hist['actions'], self.episode_hist['states'], self.episode_hist['rewards'], self.episode_hist['returns'] = [],[],[],[]
        
        self.value_network = ValueNetwork(self.state_space, 15, 1)
        self.actor_network = ActorNetwork(self.state_space, 15, self.action_space)
        
        self.value_network_optimizer = optim.Adam(self.value_network.parameters(), lr=0.01)
        self.actor_network_optimizer = optim.Adam(self.actor_network.parameters(), lr=0.01)
        
        self.values, self.actions, self.dones, self.rewards, self.states  = [], [], [], [], []
        
    def basic_params(self,config):
        self.detun = config['detuning']
        self.secular_high = config['secular freq high rf']
        self.secular_low = config['secular freq low rf']        
        self.gamma = config['gamma']
        self.sigma = config['sigma']
        self.n_avg = config['average count']
        self.k = 2*np.pi/(369.5e-9)
        
        self.ccd_lim = 6.45e-6 / 8.6
        self.vis_lim = self.sigma / (self.k*8*np.sqrt(2)*self.secular_high*self.detun) * np.sqrt((self.gamma**2 + 4*self.detun**2)**3 / (2*self.gamma**2*self.n_avg))

    def _returns_advantages(self):
        rewards = np.array(self.rewards)
        dones = np.array(self.dones)
        values = np.array(self.values)
        returns = np.append(np.zeros_like(rewards), [0], axis=0)
        
        for t in reversed(range(rewards.shape[0])):
            returns[t] = rewards[t] + self.gamma * returns[t + 1] * (1 - dones[t])
            
        returns = returns[:-1]
        advantages = returns - values
        return returns, advantages
    
    def done_episode(self, returns):
        self.episode_hist['actions'].append(self.actions)
        self.episode_hist['states'].append(self.states) 
        self.episode_hist['rewards'].append(self.rewards)
        self.episode_hist['returns'].append(returns)
        self.values, self.actions, self.dones, self.rewards, self.states  = [], [], [], [], []
        
    def step(self, obs_state):
        value = self.value_network(torch.tensor(obs_state, dtype=torch.float)).detach().numpy()
        policy = self.actor_network(torch.tensor(obs_state, dtype=torch.float))
        action = torch.multinomial(policy, 1).detach().numpy() # Sample action
        self.states.append(obs_state)
        self.values.append(value)
        self.actions.append(action)
        return action        
        
    def observe(self, obs_env):
        ccd_delta, visbility, next_state, done = obs_env
        reward = self.get_reward(ccd_delta, visbility, done)
        self.dones.append(done)
        self.rewards.append(reward)
        if done:
            # self.states.append(next_state)
            returns, advantages = self._returns_advantages()
            self.optimize_model(returns, advantages)
            self.done_episode(returns)
            
    def get_reward(self, ccd_delta, visibility, done):
        secular_diff = np.abs(self.secular_high**2 - self.secular_low**2)
        ccd_dis = self.secular_low**2 / secular_diff * ccd_delta
        vis_dis = (self.gamma**2 + 4*self.detun**2) / (np.sqrt(128) * self.detun * self.k * self.secular_high**2) * visibility
        
        if ccd_dis >= self.ccd_lim:
            reward = 1/ccd_dis * 1e6
        elif ccd_dis <= self.ccd_lim and vis_dis >= self.vis_lim:
            reward = 1/vis_dis * 1e6
        elif vis_dis < self.vis_lim:
            reward = 1/self.vis_lim * 1e6
        
        if done:
            reward *= 10
        
        return reward

    def optimize_model(self, returns, advantages):        
        actions = F.one_hot(torch.tensor(self.actions), self.action_space)
        states = torch.tensor(self.states, dtype=torch.float)
        returns = torch.tensor(returns, dtype=torch.float)
        advantages = torch.tensor(advantages, dtype=torch.float)

        # MSE for the values
        self.value_network_optimizer.zero_grad()
        values = self.value_network(states)
        loss_value = 1 * F.mse_loss(values, returns)
        loss_value.backward()
        self.value_network_optimizer.step()

        # Actor loss
        self.actor_network_optimizer.zero_grad()
        policies = self.actor_network(states)
        loss_policy = ((actions.float() * policies.log()).sum(-1) * advantages).mean()
        loss_entropy = - (policies * policies.log()).sum(-1).mean()
        loss_actor = - loss_policy - 0.001 * loss_entropy
        loss_actor.backward()
        self.actor_network_optimizer.step()
        
        return loss_value, loss_actor    
    
    def save_model(self, path):
        current_time = datetime.now().strftime("%m%d_%Hh%Mm%Ss")
        torch.save(self.value_network, path + '/' + current_time + '_value_network.pt')
        torch.save(self.actor_network, path + '/' + current_time + '_actor_network.pt')
        
    def save_episode_hist(self,path):
        current_time = datetime.now().strftime("%m%d_%Hh%Mm%Ss")
        with open('episode_hist_' + current_time + '.pkl', 'wb') as f:
            pickle.dump(self.episode_hist, f)
            
    def load_model(self, path, current_time):
        self.value_network = torch.load(path + '/' + current_time + '_value_network.pt')
        self.actor_network = torch.load(path + '/' + current_time + '_actor_network.pt')