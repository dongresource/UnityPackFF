#!/usr/bin/env python3

import os
import sys
import colorsys
from collections import OrderedDict

from unitypack.asset import Asset
from unitypack.object import ObjectPointer
from unitypack.engine.component import Transform
from unitypack.engine.object import GameObject
from unitypack.export import OBJMesh

# the GraphViz source file the script will generate
OUTPUT = 'graph.dot'

seen = []
meshes = []
textures = 0
materials = 0

def getcolor(t):
	val = float(hash(t) % 255)

	h,s,l = 50.0, val, 120.0
	r,g,b = [int(256*i) % 255 for i in colorsys.hls_to_rgb(h,l,s)]

	return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def find_pointers(d, oldkey):
	# SubMeshes get their own class, so might as well handle those sitations
	if hasattr(d, "_obj"):
		d = d._obj

	if isinstance(d, ObjectPointer):
		return [(oldkey, d)]

	# halt recursion if not a collection
	if not isinstance(d, OrderedDict) and not isinstance(d, list) and not isinstance(d, tuple):
		return []

	ret = []
	if isinstance(d, dict):
		keys = d.keys()
		d = d.values()

		for key, ent in zip(keys, d):
			ret.extend(find_pointers(ent, key))
	else:
		for n, ent in enumerate(d):
			key = f'{oldkey}[{n}]'
			ret.extend(find_pointers(ent, key))

	return ret

def handle_objbody(objbody, depth, parent_qid):
	global meshes, textures, materials

	d = objbody
	if hasattr(d, "_obj"):
		d = d._obj

	pointers = find_pointers(d, '')

	for key, ptr in pointers:
		try:
			info = ptr.object
			body = ptr.resolve()
		except:
			print('could not resolve {}, skipping...'.format(ptr), file=sys.stderr)
			continue

		# globally unique identifier
		qid = f'{ptr.asset.name}#{ptr.path_id}'

		# connect
		print(f'\t"{parent_qid}" -> "{qid}" [label="{key}"];', file=outf)

		if qid in seen:
			continue
		seen.append(qid)

		# identify
		name = ''
		if hasattr(body, 'name'):
			name = body.name
		print(f'\t"{qid}" [label="{info.type} {ptr.file_id} {ptr.path_id}\n{name}", color="{getcolor(info.type)}"];', file=outf)

		handle_objbody(body, depth + 1, qid)

		if info.type == 'Mesh':
			meshes.append(body)
		elif info.type == 'Texture2D':
			textures += 1
		elif info.type == 'Material':
			materials += 1


def main(f, name, base=None):
	asset = Asset.from_file(f)
	if base is not None:
		asset.environment.base_path = base

	print('''digraph {
	graph [fontname=Arial, nodesep=0.125, ranksep=0.25];
	node [fontcolor=white, fontname=Arial, height=0, shape=box, style=filled, width=0];
	edge [fontname=Arial];
	''', file=outf)

	depth = 0
	container = asset.objects[1].read()['m_Container']
	for path, mtdt in container:
		if path == name:
			gameobject = mtdt['asset'].object

			body = gameobject.read()
			qid = f'{asset.name}#{gameobject.path_id}'
			seen.append(qid)
			print(f'\t"{qid}" [label="{gameobject.type} {0} {gameobject.path_id} {body.name}", color="{getcolor(gameobject.type)}"];', file=outf)

			handle_objbody(body, 1, qid)

                        # uncomment (and change path if on Windows) to auto-extract all encountered meshes
			#i = 0
			#for mesh in meshes:
			#	with open('/tmp/mesh{}.obj'.format(i), 'w') as f:
			#		f.write(OBJMesh(mesh).export())
			#	i += 1

			print('}', file=outf)
			print('\n{} meshes\n{} texutres\n{} materials'.format(meshes, textures, materials), file=sys.stderr)
			return

	print("didn't find", name, file=sys.stderr)

if __name__ == '__main__':
	with open(sys.argv[1], 'rb') as f:
            with open(OUTPUT, 'w') as outf:
                    if len(sys.argv) == 3:
                            main(f, sys.argv[2])
                    elif len(sys.argv) > 3:
                            main(f, sys.argv[2], sys.argv[3])
                    else:
                            sys.exit('usage: show_gameobject.py assetbundle gameobject [assets]')
