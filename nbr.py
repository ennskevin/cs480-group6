import json
import statsmodels.api as sm
import pandas as pd
import numpy as np
import warnings

def read_json_file(filename):
   with open(filename, "r") as f:
       data = json.load(f)
       return data
   
def get_field(data, field):
    returned = [[],[]]
    for pr in data:
        returned[0].append(pr["merged"])
        returned[1].append(pr[field])
    return returned
   
def get_field_n_rows(data, field, n):
    returned = [[],[]]
    for i in range(n):
        returned[0].append(data[i]["merged"])
        returned[1].append(data[i][field])
    return returned

def nbr(data, field):
    print(f"{field}: NEGATIVE BINOMIAL REGRESSION")
    a_and_b = get_field(data, field)
    A = a_and_b[0]
    B = a_and_b[1]

    df = pd.DataFrame({"A": A, "B": B})
    df["A"] = df["A"].astype(int)
    X = sm.add_constant(df["A"])
    model = sm.GLM(df["B"], X, family=sm.families.NegativeBinomial())
    result = model.fit()
    print(result.summary())

    effect_size = np.exp(result.params["A"])
    print("Rate ratio =", effect_size)

dependent_variables = [
    "commits",
    "additions",
    "deletions",
    "changed_files",
    "user_review_comments",
    "user_conversation_comments",
    "total_user_comments",
    "unique_user_commenters"
]

warnings.filterwarnings("ignore", category=UserWarning)
data = read_json_file("longest_15/longlived_zephyrproject-rtos_zephyr.json")
for field in dependent_variables:
    print()
    nbr(data, field)
    print()

num_merged = 0
num_unmerged = 0
for pr in data:
    if pr["merged"] == True:
        num_merged += 1
    else:
        num_unmerged += 1

print(num_merged)
print(num_unmerged)