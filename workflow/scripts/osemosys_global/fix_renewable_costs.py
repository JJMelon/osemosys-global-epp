import pandas as pd
import sys

# Sets the power plant fixed costs to the level at year 2020

PROJECTION_YEARS = 26
def modify_csv(file_path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        # Check if row is first in 25 year series 
        if row['YEAR'] == 2025:
            # Get the value to replace with
            replace_value = row['VALUE']
            # Update the next 29 rows' VALUE column with the replace_value
            for i in range(index + 1, min(index + PROJECTION_YEARS, len(df))):
                df.at[i, 'VALUE'] = replace_value

    # Write the modified DataFrame back to the CSV file
    df.to_csv(file_path, index=False)

if __name__ == "__main__":
    # Check if the filename argument is provided
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_name>")
        sys.exit(1)

    file_name = sys.argv[1]
    try:
        modify_csv(file_name)
        print("File modified successfully.")
    except Exception as e:
        print("An error occurred:", e)
