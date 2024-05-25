from io import BytesIO
from wand.image import Image

from .utils import BinaryWriter
from .object import FFOrderedDict
from .engine.object import Object
from .engine.mesh import SubMesh


def import_audio(obj, audiopath, length, name=None, freq=44100):
	if not isinstance(obj, Object):
		raise ValueError('Invalid target object')
	if not audiopath.endswith(".ogg"):
		raise ValueError('Only OGG Vorbis is supported')

	with open(audiopath, 'rb') as f:
		obj.audio_data = f.read()
	obj.length = length # in seconds; float
	obj.frequency = freq

	obj._obj['m_Format'] = 5
	obj._obj['m_DecompressOnLoad'] = True
	obj._obj['m_Size'] = len(obj.audio_data)

	if name is not None:
		obj.name = name


def import_texture(obj, imgpath, name=None, fmt='dxt1'):
	if not isinstance(obj, Object):
		raise ValueError('Invalid target object')

	img = Image(filename=imgpath)

	if name is not None:
		obj.name = name
	obj.height = img.height
	obj.width = img.width
	# DXT1 or DXT5
	obj.format = 12 if fmt == 'dxt5' else 10
	obj.image_count = 1

	img.flip()

	# HACK: ImageMagick apparently thinks it knows better than you and will
	# give you a DXT1 if there's no transparency *even if you ask for DXT5*
	buf = img.make_blob(fmt)
	if chr(buf[87]) == '1':
		obj.format = 10 # DXT1

	# load image as DDS, stripping 128-byte header
	obj.data = buf[128:]
	obj.complete_image_size = len(obj.data)

	# these are all the same across all Texture2Ds in CharTexture and Icons
	# but only m_TextureDimension = 2 seems to be mandatory
	obj._obj['m_Limit'] = -1
	obj._obj['m_TextureDimension'] = 2
	obj._obj['m_TextureSettings']['m_FilterMode'] = 1
	obj._obj['m_TextureSettings']['m_Aniso'] = 1
	obj._obj['m_TextureSettings']['m_MipBias'] = 0.0
	obj._obj['m_TextureSettings']['m_WrapMode'] = 0

def import_mesh(obj, meshpath, name=None):
	if not isinstance(obj, Object):
		raise ValueError('Invalid target object')

	# read obj file
	with open(meshpath) as f:
		lines = [line for line in f.read().split('\n') if line != '']
		lines = [line.split(' ') for line in lines]

	_vertices = []
	_normals = []
	_uvs = []

	vertices = []
	normals = []
	uvs = []
	indices = []
	idxdict = dict()

	idxbuf = BytesIO()
	buf = BinaryWriter(idxbuf)

	# parse obj file
	nextidx = 0
	for line in lines:
		if line[0] == 'v':
			vert = FFOrderedDict()
			vert['x'] = -float(line[1])
			vert['y'] = float(line[2])
			vert['z'] = float(line[3])
			_vertices.append(vert)
		elif line[0] == 'vn':
			norm = FFOrderedDict()
			norm['x'] = -float(line[1])
			norm['y'] = float(line[2])
			norm['z'] = float(line[3])
			_normals.append(norm)
		elif line[0] == 'vt':
			uv = FFOrderedDict()
			uv['x'] = float(line[1])
			uv['y'] = float(line[2])
			_uvs.append(uv)
		elif line[0] == 'f':
			if len(line) != 4:
				raise ValueError('Mesh is not triangulated')

			_indices = []
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

				_indices.append(idx)

			# reorder vertices to flip faces
			indices.extend(_indices[::-1])

	for i in indices:
		buf.write_uint16(i)

	# assign to mesh object
	if name is not None:
		obj.name = name

	obj.mesh_compression = 0
	obj.use_16bit_indices = 1

	obj.vertices = vertices
	obj.normals = normals
	obj.uvs = uvs
	obj.index_buffer = idxbuf.getvalue()

	if len(obj.submeshes) == 0:
		obj.submeshes.append(SubMesh(FFOrderedDict()))

	obj.submeshes[0].first_byte = 0
	obj.submeshes[0].index_count = len(indices)
	obj.submeshes[0].is_tri_strip = 0
	obj.submeshes[0].triangle_count = len(indices) // 3
