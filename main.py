import numpy as np
import pandas as pd
from scipy.interpolate import Akima1DInterpolator
from scipy.optimize import minimize_scalar
from spekpy import Spek


# Spekpy
def get_characteristics_from_spekpy(th, qualities, save=False, folder=None):
    spectra, results = {}, {}
    for k, v in qualities.items():
        s = Spek(kvp=v['kvp'], th=th)
        s.multi_filter(v['filters'])
        d = {
            'Mean energy (keV)': s.get_emean(),
            'HVL1 (mm)': s.get_hvl1() if k in ['N15', 'N20', 'N30', 'N40', 'H60'] else s.get_hvl1(matl='Cu'),
            'HVL2 (mm)': s.get_hvl2() if k in ['N15', 'N20', 'N30', 'N40', 'H60'] else s.get_hvl2(matl='Cu')
        }
        results[k] = d
        spectrum = s.get_spectrum(diff=False)
        df = pd.DataFrame(np.transpose(spectrum), columns=['Energy (keV)', 'Fluence (1/cm2)'])
        spectra[k] = df
        if save:
            df.to_csv(f'{folder}/{k}.csv', index=False)
    characteristics = pd.DataFrame(results)
    characteristics = characteristics.transpose()
    characteristics = characteristics.reset_index()
    characteristics.rename(columns={'index': 'Quality'}, inplace=True)
    if save:
        characteristics.to_csv(f'{folder}/characteristics.csv', index=False)
    return spectra, characteristics


# Experimental spectra
def get_mean_energy(csv_path, columns, filter_energy=None):
    df = pd.read_csv(csv_path)
    df = df[columns]
    df.columns = ['energy', 'fluence']

    if filter_energy is not None:
        min_energy = filter_energy[0]
        max_energy = filter_energy[1]
        df = df[df['energy'] > min_energy]
        df = df[df['energy'] < max_energy]

    energies = df['energy']
    fluences = df['fluence']

    mean_energy = sum(fluences * energies) / fluences.sum()
    return mean_energy


def get_mean_conversion_coefficient(spectrum_path, spectrum_columns, mu_tr_rho_path, mu_tr_rho_columns, hk_path,
                                    hk_columns, filter_energy=None):
    spectrum = pd.read_csv(spectrum_path)
    spectrum = spectrum[spectrum_columns]
    spectrum.columns = ['energy', 'fluence']

    mu_tr_rho = pd.read_csv(mu_tr_rho_path)
    mu_tr_rho = mu_tr_rho[mu_tr_rho_columns]
    mu_tr_rho.columns = ['energy', 'mu_tr_rho']

    hk = pd.read_csv(hk_path)
    hk = hk[hk_columns]
    hk.columns = ['energy', 'hk']

    mu_tr_rho_interpolator = Akima1DInterpolator(x=np.log(mu_tr_rho['energy']), y=np.log(mu_tr_rho['mu_tr_rho']))
    hk_interpolator = Akima1DInterpolator(x=np.log(hk['energy']), y=np.log(hk['mu_tr_rho']))

    df = pd.DataFrame({
        'energy': spectrum['energy'],
        'fluence': spectrum['fluence'],
        'mu_tr_rho': np.exp(mu_tr_rho_interpolator(x=np.log(spectrum['energy']))),
        'hk': np.exp(hk_interpolator(x=np.log(hk['energy']))),
    })

    if filter_energy is not None:
        min_energy = filter_energy[0]
        max_energy = filter_energy[1]
        df = df[df['energy'] > min_energy]
        df = df[df['energy'] < max_energy]

    energy = df['energy']
    fluence = df['fluence']
    mu_tr_rho = df['mu_tr_rho']
    hk = df['hk']

    return sum(fluence * energy * mu_tr_rho * hk) / sum(fluence * energy * mu_tr_rho)


def get_first_hvl(spectrum_path, spectrum_columns, mu_tr_rho_path, mu_tr_rho_columns, mu_rho_path, mu_rho_columns,
                  material_density, filter_energy=None):
    spectrum = pd.read_csv(spectrum_path)
    spectrum = spectrum[spectrum_columns]
    spectrum.columns = ['energy', 'fluence']

    mu_tr_rho = pd.read_csv(mu_tr_rho_path)
    mu_tr_rho = mu_tr_rho[mu_tr_rho_columns]
    mu_tr_rho.columns = ['energy', 'mu_tr_rho']

    mu_rho = pd.read_csv(mu_rho_path)
    mu_rho = mu_rho[mu_rho_columns]
    mu_rho.columns = ['energy', 'mu_rho']

    mu_tr_rho_interpolator = Akima1DInterpolator(x=np.log(mu_tr_rho['energy']), y=np.log(mu_tr_rho['mu_tr_rho']))
    mu_rho_interpolator = Akima1DInterpolator(x=np.log(mu_rho['energy'] * 1000), y=np.log(mu_rho['mu_rho']))

    df = pd.DataFrame({
        'energy': spectrum['energy'],
        'fluence': spectrum['fluence'],
        'mu_tr_rho': np.exp(mu_tr_rho_interpolator(x=np.log(spectrum['energy']))),
        'mu': np.exp(mu_rho_interpolator(x=np.log(spectrum['energy']))) * material_density
    })

    if filter_energy is not None:
        min_energy = filter_energy[0]
        max_energy = filter_energy[1]
        df = df[df['energy'] > min_energy]
        df = df[df['energy'] < max_energy]

    energy = df['energy']
    fluence = df['fluence']
    mu_tr_rho = df['mu_tr_rho']
    mu = df['mu']

    def hvl1(x):
        return sum(fluence * energy * mu_tr_rho * np.exp(-mu * x)) / sum(fluence * energy * mu_tr_rho)

    def objective_function(x):
        return (hvl1(x) - 0.5) ** 2

    result = minimize_scalar(objective_function, method='Brent')
    hvl1 = result.x  # cm

    return hvl1


def get_second_hvl(spectrum_path, spectrum_columns, mu_tr_rho_path, mu_tr_rho_columns, mu_rho_path, mu_rho_columns,
                   material_density, hvl1, filter_energy=None):
    spectrum = pd.read_csv(spectrum_path)
    spectrum = spectrum[spectrum_columns]
    spectrum.columns = ['energy', 'fluence']

    mu_tr_rho = pd.read_csv(mu_tr_rho_path)
    mu_tr_rho = mu_tr_rho[mu_tr_rho_columns]
    mu_tr_rho.columns = ['energy', 'mu_tr_rho']

    mu_rho = pd.read_csv(mu_rho_path)
    mu_rho = mu_rho[mu_rho_columns]
    mu_rho.columns = ['energy', 'mu_rho']

    mu_tr_rho_interpolator = Akima1DInterpolator(x=np.log(mu_tr_rho['energy']), y=np.log(mu_tr_rho['mu_tr_rho']))
    mu_rho_interpolator = Akima1DInterpolator(x=np.log(mu_rho['energy'] * 1000), y=np.log(mu_rho['mu_rho']))

    df = pd.DataFrame({
        'energy': spectrum['energy'],
        'fluence': spectrum['fluence'],
        'mu_tr_rho': np.exp(mu_tr_rho_interpolator(x=np.log(spectrum['energy']))),
        'mu': np.exp(mu_rho_interpolator(x=np.log(spectrum['energy']))) * material_density
    })

    if filter_energy is not None:
        min_energy = filter_energy[0]
        max_energy = filter_energy[1]
        df = df[df['energy'] > min_energy]
        df = df[df['energy'] < max_energy]

    energy = df['energy']
    fluence = df['fluence']
    mu_tr_rho = df['mu_tr_rho']
    mu = df['mu']

    def hvl2(x):
        return sum(fluence * energy * mu_tr_rho * np.exp(-mu * (hvl1 + x))) / sum(fluence * energy * mu_tr_rho)

    def objective_function(x):
        return (hvl2(x) - 0.25) ** 2

    result = minimize_scalar(objective_function, method='Brent')
    hvl2 = result.x  # cm

    return hvl2


def get_characteristics_spectrometry(quality, spectrum_path, spectrum_columns, mu_tr_rho_path, mu_tr_rho_columns,
                                     mu_rho_al_path, mu_rho_al_columns, rho_al, mu_rho_cu_path, mu_rho_cu_columns,
                                     rho_cu, hk_path, hk_columns, filter_energy):
    if quality in ['N15', 'N20', 'N30', 'N40', 'H60']:
        mu_rho_path, mu_rho_columns, rho = mu_rho_al_path, mu_rho_al_columns, rho_al
    else:
        mu_rho_path, mu_rho_columns, rho = mu_rho_cu_path, mu_rho_cu_columns, rho_cu

    mean_energy = get_mean_energy(spectrum_path, spectrum_columns, filter_energy=filter_energy)
    hvl1 = get_first_hvl(spectrum_path, spectrum_columns, mu_tr_rho_path, mu_tr_rho_columns,
                         mu_rho_path, mu_rho_columns, rho, filter_energy=filter_energy)
    hvl2 = get_second_hvl(spectrum_path, spectrum_columns, mu_tr_rho_path, mu_tr_rho_columns,
                          mu_rho_path, mu_rho_columns, rho, hvl1, filter_energy=filter_energy)
    hk = get_mean_conversion_coefficient(spectrum_path, spectrum_columns, mu_tr_rho_path, mu_tr_rho_columns, hk_path,
                                         hk_columns, filter_energy=None)
    return mean_energy, hvl1, hvl2, hk


def write_excel(spectrometry, spekpy, iso, measurement, spectrometry_vs_iso, spectrometry_vs_spekpy, spekpy_vs_iso,
                measurement_vs_spectrometry, measurement_vs_iso, measurement_vs_spekpy):
    with pd.ExcelWriter('unfiltered.xlsx', engine='xlsxwriter') as writer:
        sheet_name = 'unfiltered'

        writer.book.add_worksheet(sheet_name)
        worksheet = writer.sheets[sheet_name]
        decimal_format = writer.book.add_format({'num_format': '0.000'})
        worksheet.set_column('A:AA', 15, decimal_format)  # Set the width of column A to 20
        worksheet.conditional_format('B17:AA24', {
            'type': '3_color_scale',
            'min_color': '#63BE7B',  # Green
            'mid_color': '#FFFFFF',  # Yellow
            'max_color': '#F8696B'  # Red
        })

        worksheet.write(1, 1, 'X-ray reference field characteristic values')
        worksheet.write(2, 1, 'From spectrometry')
        spectrometry = spectrometry.reset_index()
        spectrometry.rename(columns={'index': 'Quality'}, inplace=True)
        spectrometry.to_excel(writer, sheet_name=sheet_name, startrow=3, startcol=1, index=False)

        worksheet.write(2, 6, 'From SpekPy')
        spekpy = spekpy.reset_index()
        spekpy.rename(columns={'index': 'Quality'}, inplace=True)
        spekpy.to_excel(writer, sheet_name=sheet_name, startrow=3, startcol=6, index=False)

        worksheet.write(2, 11, 'From ISO')
        iso = iso.reset_index()
        iso.rename(columns={'index': 'Quality'}, inplace=True)
        iso.to_excel(writer, sheet_name=sheet_name, startrow=3, startcol=11, index=False)

        worksheet.write(2, 16, 'From measurement')
        measurement = measurement.reset_index()
        measurement.rename(columns={'index': 'Quality'}, inplace=True)
        measurement.to_excel(writer, sheet_name=sheet_name, startrow=3, startcol=16, index=False)

        worksheet.write(13, 1, 'X-ray reference field characteristic values comparison')
        worksheet.write(14, 1, 'Spectrometry vs. ISO')
        spectrometry_vs_iso = spectrometry_vs_iso.reset_index()
        spectrometry_vs_iso.rename(columns={'index': 'Quality'}, inplace=True)
        spectrometry_vs_iso.to_excel(writer, sheet_name=sheet_name, startrow=15, startcol=1, index=False)

        worksheet.write(14, 6, 'Spectrometry vs. SpekPy')
        spectrometry_vs_spekpy = spectrometry_vs_spekpy.reset_index()
        spectrometry_vs_spekpy.rename(columns={'index': 'Quality'}, inplace=True)
        spectrometry_vs_spekpy.to_excel(writer, sheet_name=sheet_name, startrow=15, startcol=6, index=False)

        worksheet.write(14, 11, 'SpekPy vs. ISO')
        spekpy_vs_iso = spekpy_vs_iso.reset_index()
        spekpy_vs_iso.rename(columns={'index': 'Quality'}, inplace=True)
        spekpy_vs_iso.to_excel(writer, sheet_name=sheet_name, startrow=15, startcol=11, index=False)

        worksheet.write(14, 16, 'Measurement vs. spectrometry')
        measurement_vs_spectrometry = measurement_vs_spectrometry.reset_index()
        measurement_vs_spectrometry.rename(columns={'index': 'Quality'}, inplace=True)
        measurement_vs_spectrometry.to_excel(writer, sheet_name=sheet_name, startrow=15, startcol=16, index=False)

        worksheet.write(14, 20, 'Measurement vs. ISO')
        measurement_vs_iso = measurement_vs_iso.reset_index()
        measurement_vs_iso.rename(columns={'index': 'Quality'}, inplace=True)
        measurement_vs_iso.to_excel(writer, sheet_name=sheet_name, startrow=15, startcol=20, index=False)

        worksheet.write(14, 24, 'Measurement vs. SpekPy')
        measurement_vs_spekpy = measurement_vs_spekpy.reset_index()
        measurement_vs_spekpy.rename(columns={'index': 'Quality'}, inplace=True)
        measurement_vs_spekpy.to_excel(writer, sheet_name=sheet_name, startrow=15, startcol=24, index=False)


def main(run_spekpy=False, run_spectrometry=False, run_comparison=False):
    if run_spekpy:
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
        spekpy = get_characteristics_from_spekpy(th=20, qualities=qualities, save=True, folder='data/spekpy')
        spekpy_spectra, spekpy_characteristics = spekpy

    if run_spectrometry:
        qualities = ['N15', 'N20', 'N30', 'N40', 'N60', 'N250', 'H60', 'H200']
        # filters_energy = [(0, 15), (0, 20), (0, 30), (0, 40), (0, 60), (0, 250), (0, 60), (0, 200)]
        filters_energy = [None] * 8

        spectrometry = {'Mean energy (keV)': {}, 'HVL1 (mm)': {}, 'HVL2 (mm)': {}, 'Mean hk (Sv/Gy)': {}}
        for quality, filter_energy in zip(qualities, filters_energy):
            mean_energy, hvl1, hvl2, hk = get_characteristics_spectrometry(
                quality=quality,
                spectrum_path=f'data/measurements/{quality}.csv',
                spectrum_columns=['Energy[keV]', 'Fluence_rate [cm^-2s^-1]'],
                mu_tr_rho_path='data/coefficients/mutr.txt',
                mu_tr_rho_columns=['Energy (keV)', 'μtr/ρ (cm2/g)'],
                mu_rho_al_path='data/coefficients/muAl.txt',
                mu_rho_al_columns=['Energy (MeV)', 'μ/ρ (cm2/g)'],
                rho_al=2.699,
                mu_rho_cu_path='data/coefficients/muCu.txt',
                mu_rho_cu_columns=['Energy (MeV)', 'μ/ρ (cm2/g)'],
                rho_cu=8.96,
                hk_path=None,
                hk_columns=None,
                filter_energy=filter_energy
            )
            spectrometry['Mean energy (keV)'][quality] = mean_energy
            spectrometry['HVL1 (mm)'][quality] = hvl1 * 10
            spectrometry['HVL2 (mm)'][quality] = hvl2 * 10
            spectrometry['Mean hk (Sv/Gy)'][quality] = hk
        spectrometry = pd.DataFrame(spectrometry)

    if run_comparison:
        iso = pd.read_csv('data/iso/characteristics.csv')
        iso = iso.set_index('Quality')
        spekpy = pd.read_csv('data/spekpy/characteristics.csv')
        spekpy = spekpy.set_index('Quality')
        measurement = pd.read_csv('data/measurements/hvl.csv')
        measurement = measurement.set_index('Quality')

        spekpy_vs_iso = np.abs(1 - spekpy / iso) * 100
        spectrometry_vs_iso = np.abs(1 - spectrometry / iso) * 100
        spectrometry_vs_spekpy = np.abs(1 - spectrometry / spekpy) * 100

        measurement_vs_spectrometry = np.abs(1 - measurement / spectrometry) * 100
        measurement_vs_iso = np.abs(1 - measurement / iso) * 100
        measurement_vs_spekpy = np.abs(1 - measurement / spekpy) * 100

        columns = ['HVL1 (mm)', 'HVL2 (mm)']
        measurement_vs_spectrometry = measurement_vs_spectrometry[columns]
        measurement_vs_iso = measurement_vs_iso[columns]
        measurement_vs_spekpy = measurement_vs_spekpy[columns]

        columns_map = {'Mean energy (keV)': 'Mean energy (%)', 'HVL1 (mm)': 'HVL1 (%)', 'HVL2 (mm)': 'HVL2 (%)'}
        spekpy_vs_iso.rename(columns=columns_map, inplace=True)
        spectrometry_vs_iso.rename(columns=columns_map, inplace=True)
        spectrometry_vs_spekpy.rename(columns=columns_map, inplace=True)

        columns_map = {'HVL1 (mm)': 'HVL1 (%)', 'HVL2 (mm)': 'HVL2 (%)'}
        measurement_vs_spectrometry.rename(columns=columns_map, inplace=True)
        measurement_vs_iso.rename(columns=columns_map, inplace=True)
        measurement_vs_spekpy.rename(columns=columns_map, inplace=True)

        write_excel(spectrometry=spectrometry, spekpy=spekpy, iso=iso, measurement=measurement,
                    spectrometry_vs_iso=spectrometry_vs_iso, spectrometry_vs_spekpy=spectrometry_vs_spekpy,
                    spekpy_vs_iso=spekpy_vs_iso, measurement_vs_spectrometry=measurement_vs_spectrometry,
                    measurement_vs_iso=measurement_vs_iso, measurement_vs_spekpy=measurement_vs_spekpy)


if __name__ == "__main__":
    main(run_spekpy=False, run_spectrometry=True, run_comparison=True)
