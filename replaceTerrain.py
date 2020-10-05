#!/usr/bin/env python3

import sys
import struct
from unitypack.asset import Asset
from PIL import Image

MAX_HEIGHT = 20000

def main(imgpath, offset, output):
    offset += 4

    img = Image.open(imgpath)
    print('loaded image.')

    pixels = img.tobytes()

    buf = bytes()
    for i in range(0, len(pixels), 3):
        p = pixels[i]
        buf += struct.pack('<H', int((p * MAX_HEIGHT)/255))

    print('buffer length is', len(buf))
    with open(output, 'r+b') as f:
        f.seek(offset)
        f.write(buf)

    print('done.')

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('''usage: replaceTerrain.py input.png offset OutputAssetBundle

NOTE: OutputAssetBundle will be modified in-place, starting from the supplied offset.
It will not check if the offset is correct nor will it make a backup of the asset bundle first.''', file=sys.stderr)
        sys.exit(1)

    main(sys.argv[1], int(sys.argv[2], 0), sys.argv[3])
