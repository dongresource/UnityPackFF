#!/usr/bin/env python3

import sys
from io import BytesIO

import unitypack
from unitypack.asset import Asset
from unitypack.object import FFOrderedDict
from unitypack.utils import BinaryWriter
from unitypack.modding import import_mesh

# CharacterSelection asset bundle
f = open('CustomAssetBundle-ce09c4c9be8a046ca92e0044f22d1b99', 'rb')
outf = open('CustomAssetBundle-ce09c4c9be8a046ca92e0044f22d1b99_new', 'wb')

#asset = unitypack.load(f).assets[0]
asset = Asset.from_file(f)

#mesh = asset.objects[17].contents # Eddy Nano in FutureNano (doesn't work yet)
mesh = asset.objects[12316].contents # Fish Backpack in CharacterSelecion
#mesh = asset.objects[711].contents # Terrafuser engine 01 in Tutorial

import_mesh(mesh, 'nano_davestrider8.obj')

print(f'{len(mesh.vertices)} vertices, {len(mesh.normals)} normals, {len(mesh.uvs)} UVs, {len(mesh.index_buffer)//2} indices, {len(mesh.index_buffer)/6} triangles')

asset.save(outf)

print('done.')

f.close()
outf.close()
