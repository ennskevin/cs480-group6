import csv
import requests
import json
from datetime import datetime
from statistics import median
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
    
    

owner = "zephyrproject-rtos"
repro = "zephyr"
token = "GH_token"
# collect_and_write(token)
data = read_json_file("zephyrproject-rtos.json")
median_time_delta = get_median_time_delta(data)
# make_histogram(data, median_time_delta)
closed_pr_numbers, merged_pr_numbers = get_long_lived_prs(data, median_time_delta)
collect_and_write_each_pr(owner, repro, token, closed_pr_numbers, merged_pr_numbers)
# print(len(closed_pr_numbers))
# print(len(merged_pr_numbers))
# print(merged_pr_numbers[44])
