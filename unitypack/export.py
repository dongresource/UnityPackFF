from io import BytesIO
from .utils import BinaryReader


class OBJVector2:
	def __init__(self, x=0, y=0):
		self.x = x
		self.y = y

	def read(self, buf):
		self.x = buf.read_float()
		self.y = buf.read_float()
		return self

	def __str__(self):
		return "%s %s" % (self.x, 1 - self.y)


class OBJVector3(OBJVector2):
	def __init__(self, x=0, y=0, z=0):
		super().__init__(x, y)
		self.z = z

	def read(self, buf):
		super().read(buf)
		self.z = buf.read_float()
		return self

	def __str__(self):
		return "%s %s %s" % (-self.x, self.y, self.z)


class OBJVector4(OBJVector3):
	def __init__(self, x=0, y=0, z=0, w=0):
		super().__init__(x, y, z)
		self.w = w

	def read(self, buf):
		super().read(buf)
		self.w = buf.read_float()
		return self

	def read_color(self, buf):
		self.x = buf.read_ubyte()
		self.y = buf.read_ubyte()
		self.z = buf.read_ubyte()
		self.w = buf.read_ubyte()
		return self

	def __str__(self):
		return "%s %s %s %s" % (self.x, self.y, self.z, self.w)


def handle_strip_topology(mesh):
	tris = []

	for i in range(len(mesh.indices[0])):
		tris.append(mesh.indices[0][i])

		if len(tris) < 3:
			continue

		t1 = tris[0]
		t2 = tris[1]
		t3 = tris[2]

		del tris[0]

		if t1 == t2 or t1 == t3 or t2 == t3:
			continue

		if i % 2 == 0:
			mesh.triangles[0].append(t1)
			mesh.triangles[0].append(t2)
			mesh.triangles[0].append(t3)
		else:
			mesh.triangles[0].append(t3)
			mesh.triangles[0].append(t2)
			mesh.triangles[0].append(t1)


class MeshData:
	def __init__(self, mesh):
		self.mesh = mesh
		self.indices = []
		self.triangles = []
		self.vertices = []
		self.normals = []
		self.colors = []
		self.uv1 = []
		self.uv2 = []
		self.uv3 = []
		self.uv4 = []
		self.tangents = []

		self.extract_indices()
		self.simple_extract_vertices()

		if len(self.mesh._obj['m_SubMeshes']) > 0:
			if self.mesh._obj['m_SubMeshes'][0]._obj['isTriStrip'] > 0:
				handle_strip_topology(self)

		#if mesh.asset.format == 6:
		#	self.simple_extract_vertices()
		#else:
		#	self.extract_vertices()

	def simple_extract_vertices(self):
		for v in self.mesh._obj['m_Vertices']:
			self.vertices.append(OBJVector3(v['x'], v['y'], v['z']))

		for v in self.mesh._obj['m_Normals']:
			self.normals.append(OBJVector3(v['x'], v['y'], v['z']))

		for v in self.mesh._obj['m_UV']:
			self.uv1.append(OBJVector2(v['x'], 1-v['y']))

	def extract_indices(self):
		for sub in self.mesh.submeshes:
			sub_indices = []
			sub_triangles = []
			buf = BinaryReader(BytesIO(self.mesh.index_buffer))
			buf.seek(sub.first_byte)

			for i in range(0, sub.index_count):
				sub_indices.append(buf.read_uint16())

			if sub._obj['isTriStrip'] == 0:
				sub_triangles.extend(sub_indices)

			self.indices.append(sub_indices)
			self.triangles.append(sub_triangles)

	def extract_vertices(self):
		# unity 5+ has 8 channels (6 otherwise)
		v5_channel_count = 8
		buf = BinaryReader(BytesIO(self.mesh.vertex_data.data))
		channels = self.mesh.vertex_data.channels
		# actual streams attribute 'm_Streams' may only exist in unity 4,
		# use of channel data alone seems to be sufficient
		stream_count = self.get_num_streams(channels)
		channel_count = len(channels)

		for s in range(0, stream_count):
			for i in range(0, self.mesh.vertex_data.vertex_count):
				for j in range(0, channel_count):
					ch = None
					if channel_count > 0:
						ch = channels[j]
						# format == 1, use half-floats (16 bit)
						if ch["format"] == 1:
							raise NotImplementedError("(%r) 16 bit floats are not supported" % (self.mesh))
					# read the appropriate vertex value into the correct list
					if ch and ch["dimension"] > 0 and ch["stream"] == s:
						if j == 0:
							self.vertices.append(OBJVector3().read(buf))
						elif j == 1:
							self.normals.append(OBJVector3().read(buf))
						elif j == 2:
							self.colors.append(OBJVector4().read_color(buf))
						elif j == 3:
							self.uv1.append(OBJVector2().read(buf))
						elif j == 4:
							self.uv2.append(OBJVector2().read(buf))
						elif j == 5:
							if channel_count == v5_channel_count:
								self.uv3.append(OBJVector2().read(buf))
							else:
								self.tangents.append(OBJVector4().read(buf))
						elif j == 6:  # for unity 5+
							self.uv4.append(OBJVector2().read(buf))
						elif j == 7:  # for unity 5+
							self.tangents.append(OBJVector4().read(buf))
			# TODO investigate possible alignment here, after each stream

	def get_num_streams(self, channels):
		streams = []
		# scan the channel's stream value for distinct entries
		for c in channels:
			if c["stream"] not in streams:
				streams.append(c["stream"])

		return len(streams)

class CompressedMeshData:
	def __init__(self, mesh):
		self.mesh = mesh
		self.indices = []
		self.triangles = []
		self.vertices = []
		self.normals = []
		self.colors = []
		self.uv1 = []
		self.uv2 = []
		self.uv3 = []
		self.uv4 = []
		self.tangents = []

		self.extract_mesh()

	class BitReader:
		def __init__(self, buf, size):
			self.buf = buf
			self.size = size

			self.bitcount = 8
			self.i = 0
			self.byte = self.nextbyte()

		def nextbyte(self):
			if self.i >= len(self.buf):
				return 0
			b = self.buf[self.i]
			self.i += 1
			return b

		def read(self):
			if self.size == 8 and self.bitcount == 0:
				return self.nextbyte()

			while self.bitcount < self.size:
				newbyte = self.nextbyte()
				# XXX: not sure why disunity has a special case for -1 here
				self.byte |= newbyte << self.bitcount
				self.bitcount += 8

			ret = self.byte & ((1 << self.size) - 1)
			self.byte >>= self.size
			self.bitcount -= self.size
			return ret


	def read_bits(self, pbv):
		if pbv['m_NumItems'] == 0 or pbv['m_BitSize'] == 0:
			return []

		reader = self.BitReader(pbv['m_Data'], pbv['m_BitSize'])

		ret = []
		for i in range(pbv['m_NumItems']):
			ret.append(reader.read())

		return ret

	def read_floats(self, pbv):
		if pbv['m_NumItems'] == 0 or pbv['m_BitSize'] == 0:
			return []

		items = self.read_bits(pbv)
		maxvalue = (1 << pbv['m_BitSize']) - 1
		_range = pbv['m_Range'] / maxvalue

		floats = []
		for i in range(len(items)):
			floats.append(float(items[i] * _range + pbv['m_Start']))

		return floats

	def read_normals(self, normals, normal_signs):
		items = self.read_bits(normals)
		signs = self.read_bits(normal_signs)

		if len(items) == 0 or len(signs) == 0:
			return []

		for i in range(len(signs)):
			if signs[i] == 0:
				signs[i] = -1

		maxvalue = (1 << normals['m_BitSize']) - 1
		_range = normals['m_Range'] / maxvalue

		floats = dict()
		for i in range(len(signs)):
			x = items[i * 2] * _range + normals['m_Start']
			y = items[i * 2 + 1] * _range + normals['m_Start']
			z = ((1 - x**2 - y**2) * signs[i])

			floats[i * 3] = x
			floats[i * 3 + 1] = y
			floats[i * 3 + 2] = z

		return list(floats.values())

	def extract_mesh(self):
		cmesh = self.mesh._obj['m_CompressedMesh']

		vertex_floats = self.read_floats(cmesh['m_Vertices'])
		for i in range(0, len(vertex_floats), 3):
			self.vertices.append(OBJVector3(vertex_floats[i], vertex_floats[i+1], vertex_floats[i+2]))

		normal_floats = self.read_normals(cmesh['m_Normals'], cmesh['m_NormalSigns'])
		for i in range(0, len(normal_floats), 3):
			self.normals.append(OBJVector3(normal_floats[i], normal_floats[i+1], normal_floats[i+2]))

		uv_floats = self.read_floats(cmesh['m_UV'])
		for i in range(0, len(uv_floats), 2):
			self.uv1.append(OBJVector2(uv_floats[i], 1-uv_floats[i+1]))

		triangle_ints = self.read_bits(cmesh['m_Triangles'])
		if len(triangle_ints) % 3 == 2:
			triangle_ints.append(triangle_ints[-1])
		elif len(triangle_ints) % 3 == 1:
			triangle_ints.append(triangle_ints[-1])
			triangle_ints.append(triangle_ints[-2])

		self.triangles.append(triangle_ints)
		self.indices.append(triangle_ints)

		if len(self.mesh._obj['m_SubMeshes']) > 0:
			if self.mesh._obj['m_SubMeshes'][0]._obj['isTriStrip'] > 0:
				handle_strip_topology(self)


class OBJMesh:
	def __init__(self, mesh):
		if mesh.mesh_compression:
			self.mesh_data = CompressedMeshData(mesh)
		else:
			self.mesh_data = MeshData(mesh)
		self.mesh = mesh

	@staticmethod
	def face_str(indices, coords, normals):
		ret = ["f "]
		for i in indices[::-1]:
			ret.append(str(i + 1))
			if coords or normals:
				ret.append("/")
				if coords:
					ret.append(str(i + 1))
				if normals:
					ret.append("/")
					ret.append(str(i + 1))
			ret.append(" ")
		ret.append("\n")
		return "".join(ret)

	def export(self):
		ret = []
		verts_per_face = 3
		normals = self.mesh_data.normals
		tex_coords = self.mesh_data.uv1
		if not tex_coords:
			tex_coords = self.mesh_data.uv2

		# for debugging purposes
		if self.mesh.mesh_compression:
			ret.append('# from compressed mesh\n\n')
		else:
			ret.append('# from uncompressed mesh\n\n')

		for v in self.mesh_data.vertices:
			ret.append("v %s\n" % (v))
		for v in normals:
			ret.append("vn %s\n" % (v))
		for v in tex_coords:
			ret.append("vt %s\n" % (v))
		ret.append("\n")

		# write group name and set smoothing to 1
		ret.append("g %s\n" % (self.mesh.name))
		ret.append("s 1\n")

		sub_count = len(self.mesh.submeshes)
		for i in range(0, sub_count):
			if sub_count == 1:
				ret.append("usemtl %s\n" % (self.mesh.name))
			else:
				ret.append("usemtl %s_%d\n" % (self.mesh.name, i))
			face_tri = []
			for t in self.mesh_data.triangles[i]:
				face_tri.append(t)
				if len(face_tri) == verts_per_face:
					ret.append(self.face_str(face_tri, tex_coords, normals))
					face_tri = []
			ret.append("\n")

		return "".join(ret)
