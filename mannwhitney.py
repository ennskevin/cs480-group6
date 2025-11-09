from scipy.stats import mannwhitneyu
import json
import math

# use field to choose what feature to run the test on
field = "user_review_comments"
projects = {
    "curl": "curl",
    "zephyrproject-rtos": "zephyr",
    "vuejs": "core",
    "facebook":"react",
    "ohmyzsh": "ohmyzsh",
    "twbs": "bootstrap"
}

def read_json_file(filename):
    with open(filename, "r") as f:
        data = json.load(f)
        return data
   
def u_test(data, field):
    def is_valid(x):
        return x is not None and not (isinstance(x, float) and math.isnan(x))

    unmerged = [pr[field] for pr in data if not pr["merged"] and is_valid(pr[field])]
    merged = [pr[field] for pr in data if pr["merged"] and is_valid(pr[field])]
    
    u_stat, p_value = mannwhitneyu(unmerged, merged, alternative="two-sided")
    n1n2 = len(unmerged) * len(merged)
    halfn1n2 = n1n2 / 2
    cliffs_delta = ((2 * u_stat) / (n1n2)) - 1
    print(f"n1 * n2 = {n1n2}")
    print(f"(n1 * n2) / 2 = {halfn1n2}")
    print(f"u-statistic: {u_stat}")
    print(f"p_value: {p_value}")
    print(f"cliff's delta: {cliffs_delta}")
    print()


# for owner in projects:
#     repo = projects[owner]
#     field = "changed_files"
#     all_strata = read_json_file(f"longest_50_stratified/stratified_{owner}_{repo}.json")
#     s50_60 = all_strata["50-60"]
#     s60_70 = all_strata["60-70"]
#     s70_80 = all_strata["70-80"]
#     s80_90 = all_strata["80-90"]
#     s90_100 = all_strata["90-100"]
#     print()
#     print(f"FOR {repo}:")
#     print("50-60 strata:")
#     u_test(s50_60, field)
#     print("60-70 strata:")
#     u_test(s60_70, field)
#     print("70-80 strata:")
#     u_test(s70_80, field)
#     print("80-90 strata:")
#     u_test(s80_90, field)
#     print("90-100 strata:")
#     u_test(s90_100, field)
#     print()

for owner in projects:
    repo = projects[owner]
    data = read_json_file(f"longest_15/longlived_{owner}_{repo}.json")
    print()
    print(f"FOR {repo}:")
    u_test(data, field)

    
   


