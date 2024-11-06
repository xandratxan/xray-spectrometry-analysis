# Script to plot spectra obtained from measurements and spekpy (normalized to the maximum value)
import matplotlib.pyplot as plt
import pandas as pd

# Read measured x-ray measurements

# List of x-ray qualities
qualities = ['N15', 'N20', 'N30', 'N40', 'N60', 'N250', 'H60', 'H200']
print(qualities)
# Path to folders with spectrum CSV files
measurements_path = f'data/measurements'
spekpy_path = f'data/spekpy'
# List of CSV file paths
measurements_csv = [f'{measurements_path}/{q}.csv' for q in qualities]
spekpy_csv = [f'{spekpy_path}/{q}.csv' for q in qualities]
# Dictionary of read dataframes from CSV files
measurements_dfs = {q: pd.read_csv(f) for q, f in zip(qualities, measurements_csv)}
spekpy_dfs = {q: pd.read_csv(f) for q, f in zip(qualities, spekpy_csv)}

# Plot measured x-ray measurements

# Create a figure and a set of subplots
fig, axs = plt.subplots(4, 2, figsize=(15, 10))
# Flatten the axs array for easy iteration
axs = axs.flatten()
# Plot each dataframe in a separate subplot using the keys as titles
for i, q in enumerate(qualities):
    axs[i].plot(measurements_dfs[q].iloc[:, 0], measurements_dfs[q].iloc[:, 1] / measurements_dfs[q].iloc[:, 1].max(),
                label='Measurement')
    axs[i].plot(spekpy_dfs[q].iloc[:, 0], spekpy_dfs[q].iloc[:, 1] / spekpy_dfs[q].iloc[:, 1].max(), label='SpekPy')
    axs[i].set_title(q)
    axs[i].set_xlabel('E (keV)')
    axs[i].set_ylabel('\u03A6 (cm\u00B2s\u207B\u00B9)')
    axs[i].legend()
# Adjust layout to prevent overlap
plt.tight_layout()
# Show the plot
plt.show()
