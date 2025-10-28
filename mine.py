import csv
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
       response.raise_for_status()  # Raise an exception for bad status codes
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
            return response
        except requests.exceptions.RequestException as e:
            print(f"Connection error on {url}: {e}")
            if attempt < retries - 1:
                wait_time = backoff * (attempt + 1)
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
      time.sleep(1.5)



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


def get_first_x_of_data(x, file):
    data = read_json_file(file)
    return  data[:x]


def analyze_data(file):
    data = read_json_file(file)

    merged = [pr for pr in data if pr["merged"]]
    closed = [pr for pr in data if pr["closed_at"] is not None and not pr["merged"]]

    avg_merged = _compute_avg(merged)
    avg_closed = _compute_avg(closed)

    results = {
        "Average metrics for merged PRs": avg_merged,
        "Average metrics for closed PRs": avg_closed
    }

    # Write results to JSON file
    with open("averages.json", "w") as out_file:
        json.dump(results, out_file, indent=4)

    return results

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
        averages[field] = sum(values) / len(values) if values else 0
    return averages


owner = "zephyrproject-rtos"
repro = "zephyr"
token = ""
# collect_and_write(token)
data = read_json_file("zephyrproject-rtos.json")
# data = get_first_x_of_data(500, owner + ".json")
median_time_delta = get_median_time_delta(data)
percentile_value = get_percentile_time_delta(data, 85)
data = get_long_lived_prs_without_separating(data, percentile_value)
enhance_pr_data(data, owner, repro, token)
write_to_json_file(data, "longlived_zehpyr_prs.json")
analyze_data("longlived_zehpyr_prs.json")
# make_histogram(data, median_time_delta)
# closed_pr_numbers, merged_pr_numbers = get_long_lived_prs(data, median_time_delta)

# collect_and_write_each_pr(owner, repro, token, closed_pr_numbers, merged_pr_numbers)
# print(len(closed_pr_numbers))
# print(len(merged_pr_numbers))
# print(merged_pr_numbers[44])
