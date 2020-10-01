#!/usr/bin/env python3

from unitypack.asset import Asset
from PIL import Image
import glob

#for filename in glob.glob("Dong*/*"):
for filename in glob.glob('/tmp/DongResources_12_09.resourceFile_unpacked/CustomAssetBundle-*'):
    f = open(filename, 'rb')
    tabledata = Asset.from_file(f)
    MAX_HEIGHT = 20000

    indx = 0

    # find the terrain height map
    for k, v in tabledata.objects.items():
        if v.type == 'TerrainData':
            indx = k
            break

    terrainData = tabledata.objects[indx].read()
    print('terrainData index is {}, offset is {}'.format(indx, terrainData.offset))
    pixles = []
    #k = 0
    for height in terrainData['m_Heightmap']['m_Heights']:
        #x = k % terrainData['m_Heightmap']['m_Width']
        #y = k // terrainData['m_Heightmap']['m_Width']
        #intensity = height / MAX_HEIGHT
        #pix = int(intensity * 255)
        pix = int((height * 255) / MAX_HEIGHT)
        pixles.append((pix, pix, pix))

    img = Image.new("RGB", (terrainData['m_Heightmap']['m_Width'], terrainData['m_Heightmap']['m_Height']))
    img.putdata(pixles)
    #img = img.resize((512,512))
    print(filename.split('.')[0])
    img.save(filename.split('.')[0] + ".tga")
