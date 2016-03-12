CS262 Assignment 2. Willy Xiao and Tomas Reimers
===

To follow along with our design decisions and our experiments, look in labnotebooks/notebook.txt. Otherwise, there are two files in src:

1. answer.py - this is the python program used to run the logical clock experiment. Use this by the command `python answer.py [SECONDS_TO_RUN_FOR] > OUTPUT`. By default this will run for 80 seconds.
2. parse.py - this reads in a log file produced by answer.py and prints a set of summary statistics with the clock speeds, final LC values, biggest gap in any LC stream, and greatest number of messages in the queue at any given time. Run it like: `python parse.py LOGS_FROM_ANSWER.PY`