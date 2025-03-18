import os
import logging
import lzma
from binascii import hexlify
from io import BytesIO
from uuid import UUID
from .object import ObjectInfo, ObjectPointer, FFOrderedDict
from .type import TypeMetadata
from .utils import BinaryReader, BinaryWriter


class Asset:
	@classmethod
	def from_bundle(cls, bundle, buf):
		ret = cls()
		ret.bundle = bundle
		ret.environment = bundle.environment
		offset = buf.tell()
		ret._buf = BinaryReader(buf, endian=">")

		if bundle.is_unityfs:
			ret._buf_ofs = buf.tell()
			return ret

		if not bundle.compressed:
			ret.name = buf.read_string()
			header_size = buf.read_uint()
			buf.read_uint()  # size

		# FIXME: this offset needs to be explored more
		ofs = buf.tell()
		if bundle.compressed:
			dec = lzma.LZMADecompressor()
			data = dec.decompress(buf.read())

			assert len(data) == bundle.uncompressed_bundle_size

			# parse header
			header = BinaryReader(BytesIO(data), endian=">")
			file_count = header.read_uint()

			if file_count != 1:
				print('WARNING: Bundle contains {} files. Reading only the first.'.format(file_count))

			ret.name = header.read_string()
			file_offset = header.read_uint()
			size = header.read_uint()

			# assign asset body
			ret._buf = BinaryReader(BytesIO(data[file_offset:file_offset+size]), endian=">")
			ret._buf_ofs = 0
			buf.seek(ofs)
		else:
			ret._buf_ofs = offset + header_size - 4
			if ret.is_resource:
				ret._buf_ofs -= len(ret.name)

		return ret

	@classmethod
	def from_file(cls, file, environment=None):
		ret = cls()
		ret.name = file.name
		ret._buf_ofs = file.tell()
		ret._buf = BinaryReader(file)
		base_path = os.path.abspath(os.path.dirname(file.name))
		if environment is None:
			from .environment import UnityEnvironment
			environment = UnityEnvironment(base_path=base_path)
		ret.environment = environment
		return ret

	def get_asset(self, path):
		if ":" in path:
			return self.environment.get_asset(path)
		return self.environment.get_asset_by_filename(path)

	def __init__(self):
		self._buf_ofs = None
		self._objects = {}
		self.adds = []
		self.asset_refs = [self]
		self.types = {}
		self.typenames = {}
		self.bundle = None
		self.name = ""
		self.long_object_ids = False
		self.tree = TypeMetadata(self)
		self.loaded = False

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.name)

	@property
	def objects(self):
		if not self.loaded:
			self.load()
		return self._objects

	@property
	def is_resource(self):
		return self.name.endswith(".resource")

	def load(self):
		if self.is_resource:
			self.loaded = True
			return

		buf = self._buf
		buf.seek(self._buf_ofs)
		buf.endian = ">"

		self.metadata_size = buf.read_uint()
		self.file_size = buf.read_uint()
		self.format = buf.read_uint()
		self.data_offset = buf.read_uint()

		if self.format >= 9:
			self.endianness = buf.read_uint()
			if self.endianness == 0:
				buf.endian = "<"
		elif self.format == 6 or self.format == 7:
			buf.endian = "<"

		self.tree.load(buf)

		if 7 <= self.format <= 13:
			self.long_object_ids = bool(buf.read_uint())

		num_objects = buf.read_uint()
		for i in range(num_objects):
			if self.format >= 14:
				buf.align()
			obj = ObjectInfo(self)
			obj.load(buf)
			self.register_object(obj)

		if self.format >= 11:
			num_adds = buf.read_uint()
			for i in range(num_adds):
				if self.format >= 14:
					buf.align()
				id = self.read_id(buf)
				self.adds.append((id, buf.read_int()))

		if self.format >= 6:
			num_refs = buf.read_uint()
			for i in range(num_refs):
				ref = AssetRef(self)
				ref.load(buf)
				self.asset_refs.append(ref)

		unk_string = buf.read_string()
		assert not unk_string, repr(unk_string)
		self.loaded = True

	def read_id(self, buf):
		if self.format >= 14:
			return buf.read_int64()
		else:
			return buf.read_int()

	def register_object(self, obj):
		if obj.type_id in self.tree.type_trees:
			self.types[obj.type_id] = self.tree.type_trees[obj.type_id]
		elif obj.type_id not in self.types:
			trees = TypeMetadata.default(self).type_trees
			if obj.class_id in trees:
				self.types[obj.type_id] = trees[obj.class_id]
			else:
				logging.warning("%r absent from structs.dat", obj.class_id)
				self.types[obj.type_id] = None

		if obj.epath_id in self._objects:
			raise ValueError("Duplicate asset object: %r (path_id=%r)" % (obj, obj.path_id))

		self._objects[obj.epath_id] = obj

	def pretty(self):
		ret = []
		for id, tree in self.tree.type_trees.items():
			ret.append("%i:" % (id))
			for child in tree.children:
				ret.append("\t" + repr(child))
		return "\n".join(ret)

	def save(self, f):
		buf = BinaryWriter(f, endian="<")

		# skip first four int fields for now
		buf.seek(16, os.SEEK_CUR)

		# write object data
		for obj in self.objects.values(): # will load() if necessary
			buf.align()
			obj.save_data(buf)

		# start of metadata
		metadata_offset = buf.tell()

		# extra byte so there's room for the metadata_offset+1 to
		# seek to when reading
		buf.write_byte(0)
		self.tree.save(buf)

		if self.format == 7:
			buf.write_int(self.long_object_ids)

		# write object metadata
		buf.write_uint(len(self.objects))
		for obj in self.objects.values():
			obj.save_metadata(buf)

		buf.write_uint(len(self.asset_refs) - 1)
		for ref in self.asset_refs[1:]: # skip self
			ref.save(buf)

		# null terminator for empty unk_string at the end
		buf.write_byte(0)

		# recalculate sizes
		self.file_size = buf.tell()
		self.metadata_size = self.file_size - metadata_offset

		# go back to the start, write the header
		buf.seek(0)
		buf.endian = ">"

		buf.write_uint(self.metadata_size)
		buf.write_uint(self.file_size)
		buf.write_uint(self.format)
		buf.write_uint(self.data_offset) # appears to always be 0

		f.flush()

	def next_path_id(self):
		if self.format == 7: # TODO
			raise NotImplementedError('generating path_ids for format 7 is not yet understood')
		else:
			return max(self.objects.keys()) + 1

	def add_object(self, type_id):
		if not self.loaded:
			self.load()

		obj = ObjectInfo(self)

		obj.path_id = self.next_path_id()
		obj.type_id = type_id
		obj.class_id = type_id if type_id >= 0 else 114
		obj.is_destroyed = False

		# populate all fields with their respective null values
		obj.init()

		self._objects[obj.path_id] = obj

		return obj

	def add2ab(self, path, path_id, file_id=0, preloads=None):
		"Add a path -> ObjectPointer connection into the AssetBundle object"

		if self.objects[1].type != 'AssetBundle':
			raise ValueError('AssetBundle object not found. Is this a Scene bundle?')

		ab = self.objects[1].contents
		preload_index = len(ab['m_PreloadTable'])

		ptr = ObjectPointer(None, self) # type argument is unused
		ptr.file_id = file_id
		ptr.path_id = path_id

		if preloads is None:
			# assume that this is a single object preload, and add it to the table
			# TODO: maybe we could also auto collect dependencies for gameobjects, etc.?
			preload_size = 1
			ab['m_PreloadTable'].append(ptr)
		else:
			preload_size = len(preloads)
			ab['m_PreloadTable'] = ab['m_PreloadTable'] + preloads

		abdata = FFOrderedDict()
		abdata['preloadIndex'] = preload_index
		abdata['preloadSize'] = preload_size
		abdata['asset'] = ptr

		ret = (path, abdata)
		ab['m_Container'].append(ret)

		return ret


class AssetRef:
	def __init__(self, source):
		self.source = source

	def __repr__(self):
		return "<%s (asset_path=%r, guid=%r, type=%r, file_path=%r)>" % (
			self.__class__.__name__, self.asset_path, self.guid, self.type, self.file_path
		)

	def load(self, buf):
		self.asset_path = buf.read_string()
		self.guid = UUID(hexlify(buf.read(16)).decode("utf-8"))
		self.type = buf.read_int()
		self.file_path = buf.read_string()
		self.asset = None

	def save(self, buf):
		buf.write_string(self.asset_path)
		buf.seek(16, os.SEEK_CUR) # UUIDs are unused in FF (except for in the client bundle)
		buf.write_int(self.type)
		buf.write_string(self.file_path)

	def resolve(self):
		return self.source.get_asset(self.file_path)
