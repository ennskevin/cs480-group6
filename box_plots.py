import matplotlib.pyplot as plt
import json

def plot(data, field, name):
    merged, unmerged = stratify_merge_status(data)
    A = [pr[field] for pr in unmerged]
    B = [pr[field] for pr in merged]

    plt.figure(figsize=(8, 6))
    plt.boxplot(
        [A, B],
        labels=["Unmerged", "Merged"],
        showmeans=True,
        showfliers=False,
        notch=True
    )
    plt.title(f"Distributions of {name}")
    plt.ylabel(name)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(f"{field}.png")

def stratify_merge_status(data):
    merged = []
    unmerged = []
    for pr in data:
        status = pr["merged"]
        if status == True:
            merged.append(pr)
        else:
            unmerged.append(pr)
    return merged, unmerged

def read_json_file(filename):
    with open(filename, "r") as f:
        data = json.load(f)
        return data

dependent_variables = {
    "commits": "Commits",
    "additions": "Additions",
    "deletions": "Deletions",
    "changed_files": "Changed Files",
    "user_review_comments": "Review Comments",
    "user_conversation_comments": "Conversation Comments",
    "total_user_comments": "All Comments",
    "unique_user_commenters": "Unique Commenters"
}

data = read_json_file("longest_15/longlived_zephyrproject-rtos_zephyr.json")
for field in dependent_variables:
    plot(data, field, dependent_variables[field])