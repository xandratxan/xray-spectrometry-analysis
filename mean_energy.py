# Script to compare mean energies obtained from measurements and spekpy
import pandas as pd

# User defined variables

# Mean energies from measured spectra
qualities = ['N15', 'N20', 'N30', 'N40', 'N60', 'N250', 'H60', 'H200']
measurements_path = f'data/measurements'
filter = False
lower = [0]*8
upper = [15, 20, 30, 40, 60, 250, 60, 200]
# Mean energies from spekpy
spekpy_path = 'data/spekpy/quantities.csv'
# Mean energies from ISO 4037-1 Table 1
iso = {'N15': 12.4, 'N20': 16.3, 'N30': 24.6, 'N40': 33.3, 'N60': 47.9, 'N250': 207, 'H60': 38.0, 'H200': 99.3}
# Output file
output_path = 'data/comparison/mean_energy_max_kvp_filter.csv'

# Calculate and store the results

# Mean energies from measured spectra
measurements_csv = [f'{measurements_path}/{q}.csv' for q in qualities]
measurements_dfs = {q: pd.read_csv(f) for q, f in zip(qualities, measurements_csv)}
measurements = {}
for i, q in enumerate(qualities):
    df = measurements_dfs[q]
    if filter:
        max_energy = upper[i]
        min_energy = lower[i]
        df = df[df['Energy[keV]'] < max_energy]
        df = df[df['Energy[keV]'] > min_energy]
    energies = df['Energy[keV]']
    fluences = df['Fluence_rate [cm^-2s^-1]']
    e_mean = sum(fluences * energies) / fluences.sum()
    measurements[q] = e_mean
measurements = pd.Series(measurements)

# Mean energies from spekpy
spekpy = pd.read_csv(spekpy_path)
spekpy = spekpy.set_index('Unnamed: 0')
spekpy = spekpy.transpose()
spekpy = spekpy['Mean energy (keV)']

# Mean energies from ISO 4037-1 Table 1
iso = pd.Series(iso)

# Results DataFrame
df = pd.DataFrame({'Measurements': measurements, 'SpekPy': spekpy, 'ISO': iso})
df['Measurements vs. ISO'] = (1 - df['Measurements']/df['ISO'])*100
df['Measurements vs. SpekPy'] = (1 - df['Measurements']/df['SpekPy'])*100
df['SpekPy vs. ISO'] = (1 - df['SpekPy']/df['ISO'])*100

df.to_csv(output_path)
markdown_df = df.round(3).to_markdown()
print(markdown_df)