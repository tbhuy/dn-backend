import pandas as pd 
import sys


input_data = pd.read_csv(sys.argv[1])

input_data[input_data.columns[1]] = input_data[input_data.columns[1]]/1000000
input_data[input_data.columns[1]] = input_data[input_data.columns[1]].astype(int)
output_data = input_data.groupby([input_data.columns[0], input_data.columns[1]]).mean()
output_data.to_csv(sys.argv[2])