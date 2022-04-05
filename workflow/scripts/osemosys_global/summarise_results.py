import pandas as pd
import itertools
import os
import sys
import yaml
from OPG_configuration import ConfigFile, ConfigPaths
pd.set_option('mode.chained_assignment', None)


def main():
    '''Creates system level and country level graphs. '''

    config_paths = ConfigPaths()
    config = ConfigFile('config')
    scenario_results_dir = '/home/abhi/osemosys_global/results/osemosys-global/results'
    
    print(os.getcwd())

    # SUMMARISE RESULTS
    headline_metrics()


def renewables_filter(df):
    '''Function to filter and keep only renewable
    technologies'''
    renewables = ['BIO', 'CSP', 'GEO', 'HYD', 'SPV', 'WON', 'WOF']
    df = df.loc[(df.TECHNOLOGY.str.startswith('PWR')) &
                (df.TECHNOLOGY.str[3:6].isin(renewables))
                ]
    return df


def fossil_filter(df):
    '''Function to filter and keep only fossil fuel
    technologies'''
    fossil_fuels = ['BIO', 'CSP', 'HYD', 'SPV', 'WON', 'WOF']
    df = df.loc[(df.TECHNOLOGY.str.startswith('PWR')) &
                (df.TECHNOLOGY.str[3:6].isin(fossil_fuels))
                ]
    return df


def headline_metrics():
    '''Function to summarise metrics for:
       1. Total emissions
       2. Average RE share
       3. Average cost of electricity generation
       4. Total system cost
       5. Average fossil fuel share'''

    # CONFIGURATION PARAMETERS
    config_paths = ConfigPaths()
    scenario_results_dir = '/home/abhi/osemosys_global/results/osemosys-global/results'
    
    # GET RESULTS

    metrics = {}
    # Total Emissions
    df_emissions = pd.read_csv(os.path.join(scenario_results_dir,
                                            'AnnualEmissions.csv'
                                            )
                               )
    emissions_total = df_emissions.VALUE.sum()
    metrics['Emissions'] = emissions_total.round(0)

    # RE Share
    df_re_share = pd.read_csv(os.path.join(scenario_results_dir,
                                           'ProductionByTechnologyAnnual.csv'
                                           )
                              )
    gen_total = df_re_share.loc[df_re_share.TECHNOLOGY.str.startswith('PWR'),
                                'VALUE'].sum()
    df_re_share = renewables_filter(df_re_share)
    re_total = df_re_share.VALUE.sum()
    re_share = re_total / gen_total
    metrics['RE Share'] = (re_share*100).round(0)

    # Total System Cost
    df_system_cost = pd.read_csv(os.path.join(scenario_results_dir,
                                              'TotalDiscountedCost.csv'
                                              )
                                 )
    system_cost_total = df_system_cost.VALUE.sum()

    return print(metrics)


if __name__ == '__main__':
    main()
