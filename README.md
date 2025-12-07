# cs480-group6

mine.py consists of three workflows, each of which can be found at the bottom of the script.

#MINING
is for gathering the data from the GitHub API. This requires the user to set the 'token' variable to a valid Github token with repository access. The user must also set the 'owner' and 'repo' variables. We use the "zephyrproject-rtos" and "zephyr" as the owner:repo pair.

#HISTOGRAMS
is for creating histograms for visualizing the data.

#ANALYSIS
is for calculating metric factors and for performing the negative binomial regression across each metric.
