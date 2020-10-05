#!/usr/bin/env python3

from unitypack.asset import Asset
from PIL import Image
import struct

MAX_HEIGHT = 20000
REPLACE_OFFSET = 0x70335c + 4

img = Image.open('/tmp/DongResources_12_09.png')
print('loaded image.')

pixels = img.tobytes()

#int16s = []
buf = bytes()
for i in range(len(pixels)):
    p = pixels[i]
    buf += struct.pack('<H', p)

#print('length is', len(int16s))

#buf = b''
#for height in int16s:
#    buf += (struct.pack('<h', height))

#buf = bytes(buf)
print('pixels:', len(pixels))
print('length is', len(buf))
with open('/tmp/DongResources_12_09.resourceFile_unpacked/patched_CustomAssetBundle-51ff75b52842e40e9b4c0dd6da9d91f1', 'r+b') as f:
    f.seek(REPLACE_OFFSET)
    f.write(buf)
print('done.')
