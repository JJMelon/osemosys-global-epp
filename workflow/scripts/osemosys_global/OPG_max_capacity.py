
import urllib
import os
import yaml
import pandas as pd

# LOGGING
import logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

# CONFIGURATION

_PY_DIR = os.path.dirname(__file__)
_YAML_FILE = open(os.path.join(_PY_DIR, '../../../config/config.yaml'))
_PARSED_YAML_FILE = yaml.load(_YAML_FILE, Loader=yaml.FullLoader)

def main():
    '''Creates capacity limits on renewable technologies.'''
    
    input_dir = _PARSED_YAML_FILE.get('inputDir')
    output_dir = _PARSED_YAML_FILE.get('outputDir')
    region = _PARSED_YAML_FILE.get('region')
    years = range(
        _PARSED_YAML_FILE.get('startYear'),
        _PARSED_YAML_FILE.get('endYear') + 1)

    ## Checks whether PLEXOS-World/MESSAGEix-GLOBIOM soft-link model data needs to be 
    # retrieved from the PLEXOS-World Harvard Dataverse.
    try:
        Open = pd.read_excel(os.path.join(input_dir,
                                 "data/PLEXOS_World_MESSAGEix_GLOBIOM_Softlink.xlsx"))

    except IOError:
        url = 'https://dvn-cloud.s3.amazonaws.com/10.7910/DVN/O6ICJP/17f2cb5b2ff-174d6e018d76?response-content-disposition=attachment%3B%20filename%2A%3DUTF-8%27%27PLEXOS-World%2520model%2520MESSAGEix%2520-%2520GLOBIOM%2520Soft-Link.xlsx&response-content-type=application%2Fvnd.openxmlformats-officedocument.spreadsheetml.sheet&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20220225T173557Z&X-Amz-SignedHeaders=host&X-Amz-Expires=3600&X-Amz-Credential=AKIAIEJ3NV7UYCSRJC7A%2F20220225%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=b5aee3a0082723fbce0db78512e5cfdae9fc267ac568a46d103842fdf79d1cf2'
        urllib.request.urlretrieve(url, os.path.join(
            input_dir, 'data/PLEXOS_World_MESSAGEix_GLOBIOM_Softlink.xlsx'))

    df_reslimit = pd.read_excel(os.path.join(
        input_dir, "data/PLEXOS_World_MESSAGEix_GLOBIOM_Softlink.xlsx"),
        sheet_name = "Properties")

    # TECHNOLOGY MAPPING FOR PLEXOS -> OSEMOSYS GLOBAL

    dict_reslimit = {'Hydro' : 'HYD',
                     'Solar|CSP' : 'CSP',
                     'Solar|PV' : 'SPV',
                     'Wind|Onshore' : 'WON',
                     'Wind|Offshore' : 'WOF'}

    # GET CAPAPCITY LIMITS FROM PLEXOS WORLD 
    # This is capacity ADDITION limits, not total max capacity limits 

    df_reslimit_units = df_reslimit.loc[(df_reslimit['child_object'].str.contains('|'.join(dict_reslimit.keys()))) & 
                                  (df_reslimit['property'] == 'Max Units Built') &
                                  (df_reslimit['scenario'].str.contains('Base')) &
                                  (df_reslimit['child_class'] == 'Generator')].set_index('child_object')

    df_reslimit_capacity = df_reslimit.loc[(df_reslimit['child_object'].str.contains('|'.join(dict_reslimit.keys()))) & 
                                  (df_reslimit['property'] == 'Max Capacity') &
                                  (df_reslimit['child_class'] == 'Generator')].set_index('child_object')

    df_reslimit_final = pd.DataFrame(df_reslimit_capacity['value'] * df_reslimit_units['value'] / 1000).rename(columns = {'value' : 'VALUE'})
    df_reslimit_final['node'], df_reslimit_final['powerplant']  = df_reslimit_final.index.str.rsplit('|',1).str[1], df_reslimit_final.index.str.rsplit('|',1).str[0]
    df_reslimit_final['powerplant'] = df_reslimit_final['powerplant'].map(dict_reslimit)

    df_reslimit_final.loc[df_reslimit_final['node'].str.len() <= 6, 
                 'node_code'] = (df_reslimit_final['node'].
                                 str.split('-').
                                 str[1:].
                                 str.join("") +
                                 'XX')
    df_reslimit_final.loc[df_reslimit_final['node'].str.len() > 6, 
                 'node_code'] = (df_reslimit_final['node'].
                                 str.split('-').
                                 str[1:].
                                 str.join("")
                                )

    df_reslimit_final['TECHNOLOGY'] = 'PWR' + df_reslimit_final['powerplant'] + df_reslimit_final['node_code'] + '01'
    cap_addition_limit = df_reslimit_final.set_index('TECHNOLOGY').to_dict()['VALUE']

    # GET RESIDUAL CAPACITY VALUES 

    df_res_cap = pd.read_csv(os.path.join(output_dir, 'data/ResidualCapacity.csv'))
    df_res_cap = df_res_cap.loc[
        (df_res_cap['YEAR']==2015) &
        (df_res_cap['TECHNOLOGY'].str[3:6].isin(list(dict_reslimit.values())))]
    df_res_cap['VALUE'] = df_res_cap.loc[:,'VALUE'].round(4)
    res_cap = df_res_cap.set_index('TECHNOLOGY').to_dict()['VALUE']
    
    # CALCULATE AND FORMAT DATA 

    out_data = []
    for tech, residual in res_cap.items():
        try:
            max_capacity = residual + cap_addition_limit[tech]
            for year in years:
                out_data.append([
                    region,
                    tech,
                    year,
                    max_capacity
            ])
        except KeyError:
            logging.warning(f'No max cap set for {tech}')

    df_max_capacity = pd.DataFrame(out_data, columns=[
        'REGION',
        'TECHNOLOGY',
        'YEAR',
        'VALUE'
    ])
    df_max_capacity.to_csv(os.path.join(
        output_dir, "data/TotalAnnualMaxCapacity.csv"), index = None)

if __name__ == '__main__':
    main()