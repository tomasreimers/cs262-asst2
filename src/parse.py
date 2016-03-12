import sys
import re

# logical clock value helpers
def get_lc_value(log):
    return int(re.search("lc:(\d+)", log).groups()[0])
def biggest_gap(logs):
    last_lc = get_lc_value(logs[0])
    biggest_gap = 1
    for log in logs[1:]:
        lc = get_lc_value(log)        
        biggest_gap = max(biggest_gap, lc - last_lc)
        last_lc = lc
    return biggest_gap

# longest queue helpers
def get_queue_value(log):
    match = re.search("Message received, Queue still has (\d+) messages", log)
    if match is None:
        return 0
    return int(match.groups()[0])
def longest_queue(logs):
    longest_queue = get_queue_value(logs[0])
    for log in logs[1:]:
        queue = get_queue_value(log)
        longest_queue = max(longest_queue, queue)
    return longest_queue
    
if __name__ == "__main__":
    # python parse.py path/to/experiment_output_file
    f = open(sys.argv[1])

    # the first line gives us the clock speeds    
    lines = f.readlines()
    print lines[0][:-1]

    # sort remaining lines into their own logs
    vm_logs = [[] for i in xrange(3)]
    for line in lines[1:]:
        # each line is "[VM3 | time: 1457727886.48, lc:359] Internal event"
        vm_logs[int(line[3])-1 ].append(line)
    
    print "Number of ticks:" + str([len(logs) for logs in vm_logs])
    print "Final LC Values:" + str([get_lc_value(logs[len(logs) - 1]) for logs in vm_logs])
    print "Biggest gap:" + str([biggest_gap(logs) for logs in vm_logs])
    print "Longest queue:" + str([longest_queue(logs) for logs in vm_logs])