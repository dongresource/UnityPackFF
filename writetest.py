#!/usr/bin/env python3

import unitypack
from unitypack.asset import Asset

f = open('../tabledata104', 'rb')
outf = open('/tmp/tabledata_new', 'wb')

asset = Asset.from_file(f)
asset.load()

asset.save(outf)

print('done.')

f.close()
outf.close()
