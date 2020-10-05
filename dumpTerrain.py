#!/usr/bin/env python3

import sys
from unitypack.asset import Asset
from PIL import Image

MAX_HEIGHT = 20000

def main(filename, outpath):
    f = open(filename, 'rb')
    tabledata = Asset.from_file(f)

    # find the terrain height map
    indx = 0
    for k, v in tabledata.objects.items():
        if v.type == 'TerrainData':
            indx = k
            break

    terrainData = tabledata.objects[indx].read()
    ofs = terrainData['m_Heightmap'].getmemboffset('m_Heights')
    print('TerrainData object index is {}, offset in binary is {}'.format(indx, hex(ofs)))

    pixels = []
    for height in terrainData['m_Heightmap']['m_Heights']:
        pix = int((height * 255) / MAX_HEIGHT)
        pixels.append((pix, pix, pix))

    img = Image.new("RGB", (terrainData['m_Heightmap']['m_Width'], terrainData['m_Heightmap']['m_Height']))
    img.putdata(pixels)
    img.save(outpath)

    print('done.')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('usage: dumpTerrain.py assetbundle out.png')
    main(sys.argv[1], sys.argv[2])
