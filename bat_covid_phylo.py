from Bio.Phylo.TreeConstruction import DistanceMatrix
from Bio.Phylo.TreeConstruction import DistanceTreeConstructor
from Bio import Phylo
import pandas as pd
import numpy as np

%matplotlib qt

df_bat = pd.read_csv("https://raw.githubusercontent.com/bfkwong/data/master/_bats_distance_mtrx.csv", index_col="host")
df_bat.head()

matrix = np.tril(df_bat.values).tolist()
for i in range(len(matrix)):
    matrix[i] = matrix[i][:i+1]
dm = DistanceMatrix(list(df_bat.index), matrix)

constructor = DistanceTreeConstructor()
tree = constructor.nj(dm)

tree.ladderize()   # Flip branches so deeper clades are displayed at top
Phylo.draw(tree)
