import pandas as pd 
import sys
import matplotlib.pyplot as plt 


input_data = pd.read_csv(sys.argv[1])
#print(input_data)
input_data[input_data.columns[1]] = input_data[input_data.columns[1]].astype(str)
input_data.plot(kind='line', x=input_data.columns[1],y=input_data.columns[2],color='blue')
fig = plt.gcf()
fig.set_size_inches(18.5, 10.5)
fig.savefig(sys.argv[2])
    

#plt.show()