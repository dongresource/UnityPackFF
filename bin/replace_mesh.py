#!/usr/bin/env python3

import sys
import unitypack
from unitypack.asset import Asset
from unitypack.object import FFOrderedDict
from io import BytesIO
from unitypack.utils import BinaryWriter

# CharacterSelection asset bundle
f = open('CustomAssetBundle-ce09c4c9be8a046ca92e0044f22d1b99', 'rb')
outf = open('CustomAssetBundle-ce09c4c9be8a046ca92e0044f22d1b99_new', 'wb')

#asset = unitypack.load(f).assets[0]
asset = Asset.from_file(f)

# input object (don't forget to triangulate the mesh!)
f1 = open('nano_davestrider.obj')
lines = [line for line in f1.read().split('\n') if line != '']
lines = [line.split(' ') for line in lines]
f1.close()

_vertices = []
_normals = []
_uvs = []
vertices = []
normals = []
uvs = []
idxdict = dict()

indices = []
idxbuf = BytesIO()
buf = BinaryWriter(idxbuf)

nextidx = 0
for line in lines:
	if line[0] == 'v':
		vert = FFOrderedDict(0)
		vert['x'] = float(line[1])
		vert['y'] = float(line[2])
		vert['z'] = float(line[3])
		_vertices.append(vert)
	elif line[0] == 'vn':
		norm = FFOrderedDict(0)
		norm['x'] = float(line[1])
		norm['y'] = float(line[2])
		norm['z'] = float(line[3])
		_normals.append(norm)
	elif line[0] == 'vt':
		uv = FFOrderedDict(0)
		uv['x'] = float(line[1])
		uv['y'] = float(line[2])
		_uvs.append(uv)
	elif line[0] == 'f':
		# make sure the model is fully triangulated
		assert len(line) == 4

		for col in line[1:]:
			tmp = col.split('/')
			v = int(tmp[0]) - 1
			t = int(tmp[1]) - 1
			n = int(tmp[2]) - 1

			if (v, t, n) in idxdict.keys():
				idx = idxdict[(v, t, n)]
			else:
				idx = nextidx
				nextidx += 1
				idxdict[(v, t, n)] = idx

				vertices.append(_vertices[v])
				normals.append(_normals[n])
				uvs.append(_uvs[t])

			indices.append(idx)

for i in indices:
	buf.write_uint16(i)

print(f'{len(vertices)} vertices, {len(normals)} normals, {len(uvs)} UVs, {len(indices)} indices, {len(indices)/3} triangles')

#mesh = asset.objects[17].contents # Eddy Nano in FutureNano
mesh = asset.objects[12316].contents # Fish Backpack in CharacterSelecion
#mesh = asset.objects[711].contents # Terrafuser engine 01 in Tutorial

mesh.mesh_compression = 0

mesh._obj['m_Vertices'] = vertices
mesh._obj['m_Normals'] = normals
mesh._obj['m_UV'] = uvs
mesh._obj['m_IndexBuffer'] = idxbuf.getvalue()

mesh._obj['m_SubMeshes'][0]._obj['firstByte'] = 0
mesh._obj['m_SubMeshes'][0]._obj['indexCount'] = len(indices)
mesh._obj['m_SubMeshes'][0]._obj['isTriStrip'] = 0
mesh._obj['m_SubMeshes'][0]._obj['triangleCount'] = len(indices) // 3

asset.save(outf)

print('done.')

f.close()
outf.close()
