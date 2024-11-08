import numpy as np
from scipy.interpolate import Akima1DInterpolator
from scipy.optimize import minimize_scalar
import pandas as pd
import matplotlib.pyplot as plt

# Read CSV files
spectrum = pd.read_csv('../data/measurements/N30.csv')
mu_tr_rho = pd.read_csv('../data/coefficients/mutr.txt')
mu_al = pd.read_csv('../data/coefficients/muAl.txt', skiprows=2)

# Conversions
mu_al['Energy (keV)'] = mu_al['Energy (MeV)'] * 1000  # Energy in keV
rho_al = 2.699  # g/cm3
mu_al['μ (cm-1)'] = mu_al['μ/ρ (cm2/g)'] * rho_al  # mu_al in 1/cm

# Interpolation to spectrum energies
# Create interpolators
mu_tr_rho_interpolator = Akima1DInterpolator(x=np.log(mu_tr_rho['Energy (keV)']), y=np.log(mu_tr_rho['μtr/ρ (cm2/g)']))
mu_al_interpolator = Akima1DInterpolator(x=np.log(mu_al['Energy (keV)']), y=np.log(mu_al['μ (cm-1)']))
# Data from interpolation
df = pd.DataFrame({
    'Energy (keV)': spectrum['Energy[keV]'],
    'Fluence (cm-2s-1)': spectrum['Fluence_rate [cm^-2s^-1]'],
    'μtr/ρ (cm2/g)': np.exp(mu_tr_rho_interpolator(x=np.log(spectrum['Energy[keV]']))),
    'μ (cm-1)': np.exp(mu_al_interpolator(x=np.log(spectrum['Energy[keV]'])))
})

# Plot to check the data
fig, axs = plt.subplots(2, 2, figsize=(6.4*2, 4.8*2))
# plt.tight_layout()
axs = axs.flatten()
# Spectrum
axs[0].plot(spectrum['Energy[keV]'], spectrum['Fluence_rate [cm^-2s^-1]'], 'o', markersize=3, label='N30')
axs[0].set_xlabel('E (keV)')
axs[0].set_ylabel(r'$\mathrm{\phi\ (cm^2s^{-1})}$')
axs[0].set_xscale('log')
# axs[0].set_yscale('log')
axs[0].legend()
# μtr/ρ (cm2/g)
axs[1].plot(mu_tr_rho['Energy (keV)'], mu_tr_rho['μtr/ρ (cm2/g)'], 'o', markersize=3, label='Air (1 m) data')
axs[1].plot(df['Energy (keV)'], df['μtr/ρ (cm2/g)'], label='Air (1 m) interpolation')
axs[1].set_xlabel('E (keV)')
axs[1].set_ylabel(r'$\mathrm{\mu_{tr}/\rho\ (cm^2/g)}$')
axs[1].set_xscale('log')
axs[1].set_yscale('log')
axs[1].legend()
# μ/ρ (cm2/g)
axs[2].plot(mu_al['Energy (keV)'], mu_al['μ/ρ (cm2/g)'], 'o', markersize=3, label='Al')
axs[2].set_xlabel('E (keV)')
axs[2].set_ylabel(r'$\mathrm{\mu/\rho\ (cm^2/g)}$')
axs[2].set_xscale('log')
axs[2].set_yscale('log')
axs[2].legend()
# μ (cm-1)
axs[3].plot(mu_al['Energy (keV)'], mu_al['μ (cm-1)'], 'o', markersize=3, label='Al data')
axs[3].plot(df['Energy (keV)'], df['μ (cm-1)'], label='Al interpolation')
axs[3].set_xlabel('E (keV)')
axs[3].set_ylabel(r'$\mathrm{\mu\ (cm^{-1})}$')
axs[3].set_xscale('log')
axs[3].set_yscale('log')
axs[3].legend()
# plt.show()

# Filter data
filter = True
max_energy = 30.2
min_energy = 15
filtered_df = df[df['Energy (keV)'] <= max_energy]
filtered_df = filtered_df[filtered_df['Energy (keV)'] > min_energy]
if filter:
    df = filtered_df

# Values for optimization
energy = df['Energy (keV)']
fluence = df['Fluence (cm-2s-1)']
mu_tr_rho = df['μtr/ρ (cm2/g)']
mu = df['μ (cm-1)']

# Compute HVL1

# Define the function hvl(x)
def hvl1(x):
    return sum(fluence*energy*mu_tr_rho*np.exp(-mu*x))/sum(fluence*energy*mu_tr_rho)

# Define the objective function to find x for which H(x) = 0.5
def objective_function_hvl1(x):
    return (hvl1(x) - 0.5)**2

# Use minimize_scalar to find the value of x that minimizes the objective function
result = minimize_scalar(objective_function_hvl1, method='Brent')
hvl1 = result.x  # cm
print(result)

# Compute HVL2

x1 = hvl1
# Define the function hvl(x)
def hvl2(x):
    return sum(fluence*energy*mu_tr_rho*np.exp(-mu*(x1+x)))/sum(fluence*energy*mu_tr_rho)

def objective_function_hvl2(x):
    return (hvl2(x) - 0.25)**2

result = minimize_scalar(objective_function_hvl2, method='Brent')
hvl2 = result.x  # cm

# HVL from spekpy
spekpy = pd.read_csv('../data/spekpy/quantities.csv')
spekpy = spekpy.set_index('Unnamed: 0')
spekpy = spekpy.transpose()
spekpy_hvl1 = spekpy['HVL1 Al (mm)']['N30']
spekpy_hvl2 = spekpy['HVL2 Al (mm)']['N30']

# Comparison
print(f'HVL1 Al:\nMeasurement:{hvl1*10} mm\nSpekPy: {spekpy_hvl1} mm')
print(f'HVL2 Al:\nMeasurement:{hvl2*10} mm\nSpekPy: {spekpy_hvl2} mm')
