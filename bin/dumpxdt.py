#!/usr/bin/env python3

import json
from unitypack.asset import Asset

INPUT = 'CustomAssetBundle-1dca92eecee4742d985b799d8226666d'
OUTPUT = 'xdt.json'
XDTINDEX = 7

def main(tabledata):
    xdtdata = tabledata.objects[XDTINDEX].read()

    out = {}
    for tname, table in xdtdata.items():
        out[tname] = {}
        try:
            for dname, data in table.items():
                out[tname][dname] = data
        except:
            out[tname] = '<err>'

    with open(OUTPUT, 'w') as f:
        json.dump(out, f, indent=4)


with open(INPUT, 'rb') as f:
    tabledata = Asset.from_file(f)
    main(tabledata)
