# cs480-group6
This package provides the dataset used, as well as the script to replicate both datamining and data analysis

## DATASETS
/all_prs.json -- basic descriptors of all closed pull requests from the zephyrproject-rtos/zephyr Github repository. All prs are fetched so as to be able to calculate lifespan statistics
/longlived_prs.json -- this is the final dataset used in analysis. This is a subset of all_prs, specifically every pull request above the 85th percentile lifespan. This data has also been enriched.

## REPLICATION
mine.py consists of three workflows, each of which can be found at the bottom of the script.

### MINE
is for gathering the data from the GitHub API. This requires the user to set the 'token' variable to a valid Github token with repository access. The user must also set the 'owner' and 'repo' variables. We use the "zephyrproject-rtos" and "zephyr" as the owner:repo pair.

### PLOT
is for creating histograms for visualizing the data.

### ANALYZE
is for calculating metric factors and for performing the negative binomial regression across each metric.
