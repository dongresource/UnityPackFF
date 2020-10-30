import os
from urllib.parse import urlparse
from .asset import Asset
from .assetbundle import AssetBundle


class UnityEnvironment:
	def __init__(self, base_path=""):
		self.bundles = {}
		self.assets = {}
		self.base_path = base_path
		self.files = []

	def __del__(self):
		for f in self.files:
			f.close()

	def __repr__(self):
		return "%s(base_path=%r)" % (self.__class__.__name__, self.base_path)

	def load(self, file):
		for bundle in self.bundles.values():
			if os.path.abspath(file.name) == os.path.abspath(bundle.path):
				return bundle
		ret = AssetBundle(self)
		ret.load(file)
		self.bundles[ret.name.lower()] = ret
		for asset in ret.assets:
			self.assets[asset.name.lower()] = asset
		return ret

	def discover(self, name):
		for bundle in list(self.bundles.values()):
			dirname = os.path.dirname(os.path.abspath(bundle.path))
			for filename in os.listdir(dirname):
				basename = os.path.splitext(os.path.basename(filename))[0]
				if name.lower() == "cab-" + basename.lower():
					f = open(os.path.join(dirname, filename), "rb")
					self.files.append(f)
					self.load(f)

	def get_asset_by_filename(self, name):
		short = os.path.basename(name).lower()
		if short in self.assets:
			return self.assets[short]

		path = os.path.join(self.base_path, name)
		if os.path.exists(path):
			f = open(path, "rb")
			self.files.append(f)
			self.assets[short] = Asset.from_file(f, environment=self)
			return self.assets[short]

		# recurse one directory deep and search in there
		for d in os.listdir(self.base_path):
			if not os.path.isdir(os.path.join(self.base_path, d)):
				continue

			for ent in os.listdir(os.path.join(self.base_path, d)):
				if ent.lower() == name.lower():
					f = open(os.path.join(self.base_path, d, ent), "rb")
					self.files.append(f)
					self.assets[short] = Asset.from_file(f, environment=self)
					return self.assets[short]

		self.discover(name)
		self.populate_assets()
		if short in self.assets:
			return self.assets[short]

		raise KeyError("No such asset: %r" % (name))
		#print('WARNING: failed to open asset: %r' % (name))

	def populate_assets(self):
		for bundle in self.bundles.values():
			for asset in bundle.assets:
				asset_name = asset.name.lower()
				if asset_name not in self.assets:
					self.assets[asset_name] = asset

	def get_asset(self, url):
		if not url:
			return None

		u = urlparse(url)
		if u.scheme == "archive":
			archive, name = os.path.split(u.path.lstrip("/").lower())
		else:
			raise NotImplementedError("Unsupported scheme: %r" % (u.scheme))

		if archive not in self.bundles:
			self.discover(archive)

			# Still didn't find it? Give up...
			if archive not in self.bundles:
				raise NotImplementedError("Cannot find %r in %r" % (archive, self.bundles))

		bundle = self.bundles[archive]

		for asset in bundle.assets:
			if asset.name.lower() == name:
				return asset
		raise KeyError("No such asset: %r" % (name))
		#print('WARNING: failed to open asset: %r' % (name))
