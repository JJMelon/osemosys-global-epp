import pandas as pd
pd.set_option('mode.chained_assignment', None)
import plotly.express as px
import numpy as np
import os
import sys
label_mapping = {
    'BIO': 'Biomass',
    'BAT': 'Battery',
    'CCG': 'Gas - Combined cycle',
    'COA': 'Coal',
    'COG': 'Cogeneration',
    'CSP': 'Concentrated Solar Power',
    'ELC': 'Electricity',
    'GAS': 'Natural gas',
    'GEO': 'Geothermal',
    'HYD': 'Hydroelectric',
    'OCG': 'Gas - Open Cycle',
    'OIL': 'Oil',
    'OTH': 'Other',
    'PET': 'Petroleum',
    'SOL': 'Solar',
    'SPV': 'Solar Photovoltaic',
    'URN': 'Nuclear',
    'WAS': 'Waste',
    'WAV': 'Wave',
    'WOF': 'Wind - Offshore',
    'WON': 'Wind - Onshore',
    'INT': 'International'
}

def get_color_codes() -> dict:
    """Get color naming dictionary.
    
    Return:
        Dictionary with tech and color name map
    """
    input_data_path = os.path.join("resources", "data", "color_codes.csv")
    name_colour_codes = pd.read_csv(input_data_path, encoding='latin-1')

    # Get colour mapping dictionary
    color_dict = dict([(n, c) for n, c
                   in zip(name_colour_codes.tech_id,
                          name_colour_codes.colour)])
    return color_dict


def powerplant_filter(df: pd.DataFrame, country:str = None) -> pd.DataFrame:
    """Filters dataframe by powerplant generator (PWR)
    
    Arguments: 
        df: pd.DataFrame
            Input result dataframe  
        country: str 
            If a country provided, get data at a country level, else get data
            at a system level
    """

    filtered_df = df[~df.TECHNOLOGY.str.contains('TRN')]
    filtered_df = filtered_df.loc[filtered_df.TECHNOLOGY.str[0:3] == 'PWR']
    filtered_df['TYPE'] = filtered_df.TECHNOLOGY.str[3:6]
    filtered_df['COUNTRY'] = filtered_df.TECHNOLOGY.str[6:9]

    if country:
        filtered_df = filtered_df.loc[filtered_df['COUNTRY'] == country]
        filtered_df['LABEL'] = filtered_df['TYPE']
    else:
        filtered_df['LABEL'] = filtered_df['TYPE']
    
    filtered_df.drop(['TECHNOLOGY', 'TYPE', 'COUNTRY'],
            axis=1,
            inplace=True)
    return filtered_df

def plot_total_capacity(input_file: str, output_file: str) -> None:
    """Plots annual total capacity with an area chart 
    """

    df = pd.read_csv(input_file)
    df = powerplant_filter(df)
    df.VALUE = df.VALUE.astype('float64')
    df = df.groupby(['LABEL', 'YEAR'],
                    as_index=False)['VALUE'].sum()
    plot_colors = get_color_codes() 
    
    
    threshold = 25 # Lower Threshold (in GW) to include specific plant legend
    labels_to_include = set()
    
    # Get list of labels whose values are above threshold at some point
    for year, group in df.groupby('YEAR'):
        labels = group.loc[group['VALUE'] > threshold, 'LABEL'].tolist()

        # Append labels to the list
        for label in labels:
            labels_to_include.add(label)


    # Calculate sum of values for each year for labels below the threshold
    sums = df.groupby('YEAR').apply(lambda x: x.loc[x['VALUE'] < threshold, 'VALUE'].sum())

    # Add sums to the 'OTH' label for each year
    for year, sum_value in sums.items():
        df.loc[(df['YEAR'] == year) & (df['LABEL'] == 'OTH'), 'VALUE'] += sum_value

    # Remove rows with labels that were aggregated into 'OTH'
    df = df[df['LABEL'].isin(list(labels_to_include))]


    graph_title = 'USA System Capacity'
    legend_title = 'Powerplant'

    fig = px.area(df,
                 x='YEAR',
                 y='VALUE',
                 color='LABEL',
                 color_discrete_map=plot_colors,
                 template='plotly_white',
                 labels={'YEAR': 'Year',
                         'VALUE': 'Gigawatts (GW)',
                         'LABEL': legend_title},
                 title=graph_title)

    # Update legend labels
    fig.for_each_trace(lambda t: t.update(name=label_mapping.get(t.name, t.name)))
    
    fig.update_layout(
        font_family="Arial",
        font_size=24,
        legend_traceorder="reversed",
        title_x=0.5)
    fig['layout']['title']['font'] = dict(size=24)
    fig.update_traces(marker_line_width=0, opacity=0.8)

    # Adjust the legend position
    fig.update_layout(legend=dict(
        x=1.02,  # Move the legend to the right of the plot
        y=0.5,   # Adjust vertical position
        xanchor='left',  # Anchor the legend to the left
        yanchor='middle' # Anchor the legend to the middle
    ))

    output_file

    return fig.write_html(output_file)

    

if __name__ == "__main__":
    # Check if the correct number of arguments are provided
    if len(sys.argv) != 3:
        print("Usage: python plot_capacity.py <input_file> <output_file>")
        sys.exit(1)

    # Extract input and output file paths from command-line arguments
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    plot_total_capacity(input_file, output_file)
