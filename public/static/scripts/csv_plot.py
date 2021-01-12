import pandas as pd 
import sys
import matplotlib.pyplot as plt 


input_data = pd.read_csv(sys.argv[1])
X = int(sys.argv[2])
Y = int(sys.argv[3])
#print(input_data)
input_data[input_data.columns[X]] = input_data[input_data.columns[X]].astype(str)
input_data.plot(kind='line', x=input_data.columns[X],y=input_data.columns[Y],color='blue')
fig = plt.gcf()
fig.set_size_inches(18.5, 10.5)
fig.savefig(sys.argv[4])
    

#plt.show()