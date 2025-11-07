import csv
import os
import requests
import json
from datetime import datetime
from statistics import median
import matplotlib.pyplot as plt
import numpy as np
import time
# import matplotlib


def get_github_pull_requests(owner, repo, token, page=1, number=None):
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        if number:
            url += f"/{number}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        params = {
            "state": "closed",
            "page": page,
            "per_page": 100
        }
        response = requests.get(url, headers=headers, params=params)
        response_headers = response.headers
        if response_headers["x-ratelimit-remaining"] == 0:
            time.sleep(response_headers["x-ratelimit-reset"])
        return response.json()
    except requests.RequestException:
        return get_github_pull_requests(owner, repo, token, page, number)


def get_all_pages(owner, repo, token):
   all_prs = []
   page = 1
   while True:
       prs = get_github_pull_requests(owner, repo, token, page)
       print(page)
       if not prs:
           break
       all_prs.extend(prs)
       page += 1
   return all_prs


def write_to_json_file(data, filename):
   with open(filename, 'w') as f:
       f.write(json.dumps(data, indent=4))


def get_useful_info(pr):
   return {
       "number": pr.get("number"),
       "title": pr["title"],
       "created_at": pr["created_at"],
       "closed_at": pr["closed_at"],
       "merged_at": pr.get("merged_at"),
   }

def get_useful_pr_info_csv(pr, items):
    csv_list = []
    for item in items:
        csv_list.append(pr.get(item))
    return csv_list


def get_useful_pr_info_json(pr, items):
    json_format = {}
    for item in items:
        json_format[item] = pr.get(item)
    return json_format
   

def move_through_prs(prs):
   useful_prs = [get_useful_info(pr) for pr in prs]
   return useful_prs


def collect_and_write(token):
   files_names = {
       # "curl": "curl",
       "zephyrproject-rtos": "zephyr",
       "JabRef": "jabref",
   }
   for name in files_names.keys():
       data = get_all_pages(name, files_names[name], token)
       print(len(data))
       useful_data = move_through_prs(data)
       file_name = name + ".json"
       write_to_json_file(useful_data, file_name)


def read_json_file(filename):
   with open(filename, "r") as f:
       data = json.load(f)
       return data


def calculate_time_delta(created_at, closed_at):
   format = '%Y-%m-%dT%H:%M:%SZ'
   created_at_datetime = datetime.strptime(created_at, format)
   closed_at_datetime = datetime.strptime(closed_at, format)
   time_difference = closed_at_datetime - created_at_datetime
   return time_difference.total_seconds() / 60


def get_median_time_delta(data):
   time_delta = []
   for pr in data:
       created_at = pr["created_at"]
       closed_at = pr["closed_at"]
       delta = calculate_time_delta(created_at, closed_at)
       time_delta.append(delta)
   return median(time_delta)

def get_percentile_time_delta(data, percentile):
   time_delta = []
   for pr in data:
       if pr["created_at"] is None or pr["closed_at"] is None:
           continue
       created_at = pr["created_at"]
       closed_at = pr["closed_at"]
       delta = calculate_time_delta(created_at, closed_at)
       time_delta.append(delta)
   return np.percentile(time_delta, percentile)


def get_long_lived_prs(data, median_time_delta):
   merged_pr_numbers = []
   closed_pr_numbers = []
   for pr in data:
       created_at = pr["created_at"]
       closed_at = pr["closed_at"]
       delta = calculate_time_delta(created_at, closed_at)
       number = pr["number"]
       is_merged = pr["merged_at"] is not None
       if delta > median_time_delta:
           if is_merged:
               merged_pr_numbers.append(number)
           else:
               closed_pr_numbers.append(number)


   return closed_pr_numbers, merged_pr_numbers

def get_long_lived_prs_without_separating(data, percentile_value):
   long_lived_prs = []
   for pr in data:
      created_at = pr["created_at"]
      closed_at = pr["closed_at"]
      delta = calculate_time_delta(created_at, closed_at)
      if delta > percentile_value:
         pr["lifespan_minutes"] = delta
         long_lived_prs.append(pr)
   return long_lived_prs


def make_histogram(data, median_time_delta):
   return None


def write_header_to_csv(items, filename):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write the header row
        writer.writerow(items)


def append_to_csv(data, filename):
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write data row
        writer.writerow(data)


def collect_and_write_each_pr(owner, repro, token, closed_pr_numbers, merged_pr_numbers):
    items = [
        "author_association",
        "active_lock_reason",
        "merged",
        "mergeable",
        "rebaseable",
        "mergeable_state",
        "comments",
        "review_comments",
        "commits",
        "additions",
        "deletions",
        "changed_files",
        "number",
        "title",
        "created_at",
        "closed_at",
        "merged_at"
    ]
    closed_prs = []
    merged_prs = []
    count = 0
    print("Getting closed prs")
    write_header_to_csv(items, f"{owner}_{repro}_closed_prs.csv")
    for closed_pr_number in closed_pr_numbers:
        closed_pr = get_github_pull_requests(owner, repro, token, 1, closed_pr_number)
        useful_pr_info = get_useful_pr_info_csv(closed_pr, items)
        append_to_csv(useful_pr_info, f"{owner}_{repro}_closed_prs.csv")
        closed_prs.append(get_useful_pr_info_json(closed_pr, items))
        print(count)
        count += 1
    count = 0
    print("Getting merged prs")
    write_header_to_csv(items, f"{owner}_{repro}_merged_prs.csv")
    for merged_pr_number in merged_pr_numbers:
        merged_pr = get_github_pull_requests(owner, repro, token, 1, merged_pr_number)
        useful_pr_info = get_useful_pr_info_csv(merged_pr, items)
        append_to_csv(useful_pr_info, f"{owner}_{repro}_merged_prs.csv")
        merged_prs.append(get_useful_pr_info_json(merged_pr, items))
        print(count)
        count += 1
    print("Writting output to JSON")
    write_to_json_file(closed_prs, f"{owner}_{repro}_closed_prs.json")
    write_to_json_file(merged_prs, f"{owner}_{repro}_merged_prs.json")


def safe_get(url, headers=None, retries=8, backoff=2):
    """Safely perform GET requests with retries and graceful failure."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response_headers = response.headers
            if int(response_headers["X-Ratelimit-Remaining"]) == 0:
                time.sleep(max(int(response_headers["X-Ratelimit-Reset"]) - time.time(), 0))
                continue
            return response
        except requests.exceptions.RequestException as e:
            print(f"Connection error on {url}: {e}")
            if attempt < retries - 1:
                wait_time = backoff * (attempt)
                print(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print("Giving up on this request.")
                # Create a dummy response-like object
                class DummyResponse:
                    status_code = 0
                    def json(self):
                        return {}
                return DummyResponse()
            

# enrich each PR datapoint with PR meta data and PR comments data
def enhance_pr_data(data, owner, repo, token):
   headers = {
      "Accept": "application/vnd.github+json",
      "Authorization": f"token {token}"
   }
   base_repo_url = f"https://api.github.com/repos/{owner}/{repo}"

   desired_fields = [
        "author_association",
        "active_lock_reason",
        "merged",
        "mergeable",
        "rebaseable",
        "mergeable_state",
        "comments",
        "commits",
        "additions",
        "deletions",
        "changed_files",
        "number",
        "title",
        "created_at",
        "closed_at",
        "merged_at"
   ]

   i = 0
   for pr in data:
      pr_number = pr["number"]
      pr_url = f"{base_repo_url}/pulls/{pr_number}"
      pulls_comments_url = f"{base_repo_url}/pulls/{pr_number}/comments"
      issues_comments_url = f"{base_repo_url}/issues/{pr_number}/comments"

      # general pr data
      pr_details_response = safe_get(pr_url, headers)
      if pr_details_response.status_code == 200:
            pr_details = pr_details_response.json()
            for field in desired_fields:
                pr[field] = pr_details.get(field, 0)
      else:
            print(f"Failed to fetch PR details for pr #{pr_number}")
            for field in desired_fields:
                pr[field] = None

      # from pulls/
      pulls_comments_response = safe_get(pulls_comments_url, headers)
      if pulls_comments_response.status_code == 200:
         pulls_comments = pulls_comments_response.json()
      else:
         pulls_comments = []
         print(f"Failed to fetch pull comments for pr #{pr_number}")
      user_pulls_comments = [
         c for c in pulls_comments 
         if c and isinstance(c, dict) and isinstance(c.get("user"), dict) and c.get("user", {}).get("type") == "User"
      ]
      pr["user_review_comments"] = len(user_pulls_comments)

      # from issues/
      issues_comments_response = safe_get(issues_comments_url, headers)
      if issues_comments_response.status_code == 200:
         issues_comments = issues_comments_response.json()
      else:
         issues_comments = []
         print(f"Failed to fetch issue comments for pr #{pr_number}")
      user_conversation_comments = [
         c for c in issues_comments 
         if c and isinstance(c, dict) and isinstance(c.get("user"), dict) and c.get("user", {}).get("type") == "User"
      ]
      pr["user_conversation_comments"] = len(user_conversation_comments)

      all_user_comments = user_pulls_comments + user_conversation_comments
      unique_users = set()
      for c in all_user_comments:
         user = c.get("user", {}).get("login")
         if user:
            unique_users.add(user)
      pr["total_user_comments"] = len(all_user_comments)
      pr["unique_user_commenters"] = len(unique_users)

      
      i += 1
      remaining_prs = len(data) - i
      print(pr)
      print(f"PR #{pr_number} enhanced, {remaining_prs} prs to go...")
    #   time.sleep(1.5)


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

def stratify_lifespans(data, field="lifespan_minutes"):
    strata = {
        "50-60": [],
        "60-70": [],
        "70-80": [],
        "80-90": [],
        "90-100": []
    }
    p20 = get_percentile_time_delta(data, 20)
    p40 = get_percentile_time_delta(data, 40)
    p60 = get_percentile_time_delta(data, 60)
    p80 = get_percentile_time_delta(data, 80)
    for pr in data:
        value = pr[field]
        if value <= p20:
            strata["50-60"].append(pr)
        elif value <= p40:
            strata["60-70"].append(pr)
        elif value <= p60:
            strata["70-80"].append(pr)
        elif value <= p80:
            strata["80-90"].append(pr)
        else:
            strata["90-100"].append(pr)    
    return strata


def get_lifespan_histogram(data):
    delta_times = []
    for pr in data:
       created_at = pr["created_at"]
       closed_at = pr["closed_at"]
       delta = calculate_time_delta(created_at, closed_at)
       delta_times.append(delta)
    raw_values = np.array(delta_times, dtype=float)
    upper = np.percentile(raw_values, 95)
    lower = np.percentile(raw_values, 65)
    values = raw_values[(raw_values <= upper) & (raw_values >= lower)]
    
    # Compute basic stats
    mean = np.mean(values)
    std = np.std(values)

    # # 🧮 Generate a reference normal distribution
    # x = np.linspace(min(values), max(values), 100)
    # normal_curve = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std) ** 2)

    # 📊 Plot histogram and overlay normal curve
    plt.hist(values, bins=30, density=True, alpha=0.6, color='skyblue', edgecolor='black', label="Data")
    # plt.plot(x, normal_curve, 'r--', label="Normal Distribution (same mean/std)")
    plt.title("Distribution of Pull Request Lifespans")
    plt.xlabel("Lifespan (minutes)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.show()

    print(f"Mean: {mean:.3f}, Std Dev: {std:.3f}")  

def get_field_histogram(data, field):
    field_values = []
    for pr in data:
        value = pr[field]
        if value is None:
            continue
        field_values.append(value)
    
    raw_values = np.array(field_values, dtype=float)
    upper = np.percentile(raw_values, 100)
    lower = np.percentile(raw_values, 0)
    values = raw_values[(raw_values <= upper) & (raw_values >= lower)]

    weights = np.ones_like(values) / len(values)

    plt.hist(values, bins=15, weights=weights, alpha=0.6, color='skyblue', edgecolor='black', label="Data")
    plt.title(f"Distribution of Pull Request {field}")
    plt.xlabel(field)
    plt.ylabel("Frequency")
    plt.legend()
    plt.show()
    

def get_field_histogram_by_merge_status(data, field):
    # Split data
    merged, unmerged = stratify_merge_status(data)

    merged_vals = [pr[field] for pr in merged if pr[field] is not None]
    unmerged_vals = [pr[field] for pr in unmerged if pr[field] is not None]

    merged_arr = np.array(merged_vals, dtype=float)
    unmerged_arr = np.array(unmerged_vals, dtype=float)

    upper = np.percentile(np.concatenate([merged_arr, unmerged_arr]), 100)
    lower = np.percentile(np.concatenate([merged_arr, unmerged_arr]), 0)

    merged_arr = merged_arr[(merged_arr >= lower) & (merged_arr <= upper)]
    unmerged_arr = unmerged_arr[(unmerged_arr >= lower) & (unmerged_arr <= upper)]

    merged_weights = np.ones_like(merged_arr) / len(merged_arr) if len(merged_arr) > 0 else None
    unmerged_weights = np.ones_like(unmerged_arr) / len(unmerged_arr) if len(unmerged_arr) > 0 else None

    # Plot
    bins = 15

    plt.hist(
        merged_arr,
        bins=bins,
        weights=merged_weights,
        alpha=0.6,
        color='skyblue',
        edgecolor='black',
        label='Merged'
    )

    plt.hist(
        unmerged_arr,
        bins=bins,
        weights=unmerged_weights,
        alpha=0.4,
        color='salmon',
        edgecolor='black',
        label='Unmerged'
    )

    plt.title(f"Distribution of Pull Request {field}")
    plt.xlabel(field)
    plt.ylabel("Proportion")
    plt.legend()
    plt.show()



def get_first_x_of_data(x, file):
    data = read_json_file(file)
    return  data[:x]

def analyze_data(file):
    data = read_json_file(file)

    merged = [pr for pr in data if pr["merged"]]
    closed = [pr for pr in data if pr["closed_at"] is not None and not pr["merged"]]

    overview = _get_overview(data, merged, closed)

    avg_merged = _compute_avg(merged)
    avg_closed = _compute_avg(closed)

    factors = _get_factors(avg_merged, avg_closed),

    results = {
        "Overview" : overview,
        "Average metrics for merged PRs": avg_merged,
        "Average metrics for closed PRs": avg_closed,
        "Factors (closed -> merged)" : factors
    }

    analysis_file = file.replace(".json", "_analysis.json")

    with open(analysis_file, "w") as out_file:
        json.dump(results, out_file, indent=4)

    print ("writintg to" + analysis_file)

    return results

def _get_overview (data, merged, closed):
    
    merged_count = len(merged)
    closed_count = len(closed)
    total = len(data)

    merged_percent = round((merged_count / total) * 100, 2)
    closed_percent = round((closed_count / total) * 100, 2)
   
    overview = {}
    overview["merged_count"] = merged_count
    overview["closed_count"] = closed_count
    overview["total"] = total
    overview["merged_percent"] = merged_percent
    overview["closed_percent"] = closed_percent

    return overview
    
def _compute_avg(records):
        
    numeric_fields = [
        "commits",
        "additions",
        "deletions",
        "changed_files",
        "user_review_comments",
        "user_conversation_comments",
        "total_user_comments",
        "unique_user_commenters"
    ]

    averages = {}
    for field in numeric_fields:
        values = [r[field] for r in records if field in r]
        averages[field] = round(sum(values) / len(values) if values else 0, 2)
    
    return averages

def _get_factors (avg_merged, avg_closed):

    factors = {}
    for field in avg_merged:
        merged_val = avg_merged[field]
        closed_val = avg_closed[field]

        if merged_val == 0:
            factors[field] = None  
        else:
            factors[field] = round(closed_val / merged_val, 2) # will read as closed has x times more than merged

    return factors


def read_all_repos():
    repo_files = {
        "zephyr": "longlived_zehpyr_analysis.json",
        "curl": "longlived_curl_analysis.json",
        "facebook_react": "longlived_facebook_react_analysis.json",
        "ohmyzhs": "longlived_ohmyzsh_analysis.json",
        "twbs_boostrap": "longlived_twbs_bootstrap_analysis.json",
        "vuejs": "longlived_vuejs_analysis.json"
    }

    repo_analytics = []

    for repo_name, file_name in repo_files.items():
        if not os.path.exists(file_name):
            print(f"Warning: file not found {file_name}")
            continue
         
        data = read_json_file(file_name)

        repo_analytics.append({
            "repo": repo_name,
            "overview": data["Overview"],
            "merged_avg": data["Average metrics for merged PRs"],
            "closed_avg": data["Average metrics for closed PRs"],
            "factors": data["Factors (closed -> merged)"][0]
        })

    return repo_analytics


def write_overview_csv(repo_analytics, filename="overview.csv"):
    metrics = [
        "merged_count",
        "closed_count",
        "total",
        "merged_percent",
        "closed_percent"
    ]

    header = ["metric"] + [repo["repo"] for repo in repo_analytics]

    rows = []

    for metric in metrics:
        row = {"metric": metric}
        for repo in repo_analytics:
            name = repo["repo"]
            row[name] = repo["overview"][metric]
        rows.append(row)
        
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Wrote overview to {filename}")

   
def write_detailed_merged_csv(repo_analytics, filename="detailed_merged.csv"):
    
    metrics = list(repo_analytics[0]["merged_avg"].keys())

    header = ["metric"]
    for repo in repo_analytics:
        name = repo["repo"]
        header.extend([f"{name}"])

    rows = []

    for metric in metrics:
        row = {"metric": metric}
        for repo in repo_analytics:
            name = repo["repo"]
            row[f"{name}"] = repo["merged_avg"][metric]
        rows.append(row)

    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote detailed comparison to {filename}")


def write_detailed_closed_csv(repo_analytics, filename="detailed_closed.csv"):
    
    metrics = list(repo_analytics[0]["closed_avg"].keys())

    header = ["metric"]
    for repo in repo_analytics:
        name = repo["repo"]
        header.extend([f"{name}"])

    rows = []

    for metric in metrics:
        row = {"metric": metric}
        for repo in repo_analytics:
            name = repo["repo"]
            row[f"{name}"] = repo["closed_avg"][metric]
        rows.append(row)

    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote detailed comparison to {filename}")



def write_detailed_factor_csv(repo_analytics, filename="detailed_factors.csv"):
    
    metrics = list(repo_analytics[0]["merged_avg"].keys())

    header = ["metric"]
    for repo in repo_analytics:
        name = repo["repo"]
        header.extend([f"{name}"])

    rows = []

    for metric in metrics:
        row = {"metric": metric}
        for repo in repo_analytics:
            name = repo["repo"]
            row[f"{name}"] = repo["factors"][metric]
        rows.append(row)

    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote detailed comparison to {filename}")



files_names = {
    "curl": "curl",
    "zephyrproject-rtos": "zephyr",
    "vuejs": "core",
    "facebook":"react",
    "ohmyzsh": "ohmyzsh",
    "twbs": "bootstrap"
}

# MINING
# for owner in files_names.keys():
#     token = ""
#     repo = files_names[owner]
#     data = read_json_file(owner + ".json")
#     percentile_value = get_percentile_time_delta(data, 50)
#     data = get_long_lived_prs_without_separating(data, percentile_value)
#     enhance_pr_data(data, owner, repo, token)
#     write_to_json_file(data, "longlived_"+ owner + "_" + repo + ".json")
    
# HISTOGRAMS Individual fields
# for owner in files_names.keys():
#     repo = files_names[owner]
#     folder = "longest_15"
#     longlived_data = read_json_file(f"{folder}/longlived_{owner}_{repo}.json")
#     field = "total_user_comments"
#     get_field_histogram(longlived_data, field)
#     get_field_histogram_by_merge_status(longlived_data, field)

# STRATIFY BY LIFESPAN
# for owner in files_names.keys():
#     repo = files_names[owner]
#     data = read_json_file(f"longest_50/longlived_{owner}_{repo}.json")
#     prs = stratify_lifespans(data)
#     write_to_json_file(prs, f"longest_50_stratified/stratified_{owner}_{repo}.json")


# ANALYSIS
# for owner in files_names.keys():
#     analyze_data("longlived_"+ owner + "_" + repo + ".json")




# collect_and_write(token)
#data = read_json_file("zephyrproject-rtos.json")
#data = get_first_x_of_data(500, owner + ".json")
#median_time_delta = get_median_time_delta(data)
#percentile_value = get_percentile_time_delta(data, 85)
#data = get_long_lived_prs_without_separating(data, percentile_value)
#enhance_pr_data(data, owner, repro, token)
#write_to_json_file(data, "longlived_zehpyr_prs.json")
#analyze_data("longlived_vuejs.json")

# repo_analytics = read_all_repos()
# write_overview_csv(repo_analytics)
#write_detailed_merged_csv(repo_analytics)
#write_detailed_closed_csv(repo_analytics)
#write_detailed_factor_csv(repo_analytics)


# make_histogram(data, median_time_delta)
# closed_pr_numbers, merged_pr_numbers = get_long_lived_prs(data, median_time_delta)

# collect_and_write_each_pr(owner, repro, token, closed_pr_numbers, merged_pr_numbers)
# print(len(closed_pr_numbers))
# print(len(merged_pr_numbers))
# print(merged_pr_numbers[44])