# Script to calculate the quantities of interest using spekpy
import numpy as np
from spekpy import Spek
import pandas as pd

# User defined variables

# Anode angle
th = 20
# X-ray qualities and their corresponding peak kV and filtration
qualities = {
    'N15': {'kvp': 15, 'filters': [['Be', 1], ['Al', 0.5], ['Air', 1000]]},
    'N20': {'kvp': 20, 'filters': [['Be', 1], ['Al', 1], ['Air', 1000]]},
    'N30': {'kvp': 30, 'filters': [['Be', 1], ['Al', 4], ['Air', 1000]]},
    'N40': {'kvp': 40, 'filters': [['Al', 4], ['Cu', 0.21], ['Air', 1000]]},
    'N60': {'kvp': 60, 'filters': [['Al', 4], ['Cu', 0.6], ['Air', 1000]]},
    'N250': {'kvp': 250, 'filters': [['Al', 4], ['Pb', 3], ['Sn', 2], ['Air', 1000]]},
    'H60': {'kvp': 60, 'filters': [['Be', 1], ['Al', 3.9], ['Air', 1000]]},
    'H200': {'kvp': 200, 'filters': [['Al', 4], ['Cu', 1], ['Air', 1000]]}
}
# Output folder path
folder = f'output/spekpy'

# Calculate and store the results

# Define empty dictionary to store results
results = {}
for k, v in qualities.items():
    # Generate a spectrum
    s = Spek(kvp=v['kvp'], th=th)
    # Mutli-filter the spectrum
    s.multi_filter(v['filters'])
    # Get quantities of interest
    d = {
        'Mean energy (keV)': s.get_emean(),
        'Air kerma (uGy)': s.get_kerma(),
        'HVL1 Al (mm)': s.get_hvl1(),
        'HVL2 Al (mm)': s.get_hvl2(),
        'HVL1 Cu (mm)': s.get_hvl1(matl='Cu'),
        'HVL2 Cu (mm)': s.get_hvl2(matl='Cu'),
    }
    # Store results in dictionary
    results[k] = d
    # Get spectrum
    spectrum = s.get_spectrum(diff=False)
    # Create DataFrame with spectrum
    df = pd.DataFrame(np.transpose(spectrum), columns=['E (keV)', 'F (1/cm2)'])
    # Save spectrum to CSV file
    df.to_csv(f'{folder}/{k}.csv', index=False)
# Save quantities of interest as CSV file
df = pd.DataFrame(results)
df.to_csv(f'{folder}/quantities.csv')

