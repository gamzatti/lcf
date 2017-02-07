import pandas as pd
import numpy as np
from pandas import DataFrame, Series

data = pd.read_csv('../code/lcf/data2.csv')
data = data.drop('max_deployment_gen',axis=1)
data.index = pd.Index(name="pk",data=range(1,78))
data.to_json('a.json',orient='index')
