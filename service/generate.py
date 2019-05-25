import sys
import collections

infile = sys.argv[1]

d = collections.defaultdict(list)

for line in open(infile):
    prefix = line[:5]
    suffix = line[5:]
    d[prefix].append(suffix)
for prefix, suffices in d.items():
    with open(prefix, "w") as f:
        f.writelines(suffices)
