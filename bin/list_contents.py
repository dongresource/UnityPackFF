#!/usr/bin/env python3

import sys
from unitypack.asset import Asset

def main(f):
    asset = Asset.from_file(f)

    for id, obj in asset.objects.items():
        name = ''
        if hasattr(obj.read(), 'name'):
            name = obj.read().name
        print('{}\t{}\t{}\t{}'.format(id, obj.type_id, obj.type, name))

if __name__ == '__main__':
    with open(sys.argv[1], 'rb') as f:
        main(f)
