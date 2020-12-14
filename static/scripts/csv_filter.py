import pandas as pd 
import sys

input_data = pd.read_csv(sys.argv[1], error_bad_lines=False)
output_data = input_data[input_data[input_data.columns[0]]==int(sys.argv[2])]
output_data.to_csv(sys.argv[3], index=False)