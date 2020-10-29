#!/usr/bin/env python3

import sys
from collections import OrderedDict
from unitypack.asset import Asset
from unitypack.object import ObjectPointer
from unitypack.engine.component import Transform
from unitypack.engine.object import GameObject
from unitypack.export import OBJMesh

seen = []
meshes = []
textures = 0
materials = 0

#def fun(obj, srch):
#    if isinstance(obj, ObjectPointer) and obj.object not in srch.seen:
#        #if obj.object.type == 'Mesh':
#        #    srch.meshes.append(obj.resolve())
#        if obj.object.type == 'SkinnedMeshRenderer':
#            d = obj.resolve()
#            srch.meshes.append(d['m_Mesh'].resolve())
#            #return
#        elif obj.object.type == 'MeshFilter':
#            d = obj.resolve()._obj
#            srch.meshes.append(d['m_Mesh'].resolve())
#            #return
#
#        srch.seen.add(obj.object)
#        fun(obj.resolve(), srch)
#
#    #if not isinstance(obj, Transform) and not isinstance(obj, GameObject):
#    #    return
#
#    d = obj
#    if not isinstance(d, OrderedDict):
#        try:
#            d = obj._obj
#        except:
#            pass
#    if not isinstance(d, OrderedDict) and not isinstance(d, list) and not isinstance(d, tuple):
#        return
#
#    if type(d) == list:
#        for ent in d:
#            fun(ent, srch)
#    elif type(d) == tuple:
#        for ent in d:
#            fun(ent, srch)
#    else:
#        for k, v in d.items():
#            fun(v, srch)


def fun(obj, depth):
    global meshes, textures, materials
    #print('checking', obj)
    if isinstance(obj, ObjectPointer) and obj.object not in seen:
#        if isinstance(obj.resolve(), Transform):
#            return None

        name = ''
        if obj.object.type == 'Mesh':
            print('found mesh')
            meshes.append(obj.resolve())
        elif obj.object.type == 'Texture2D':
            textures += 1
        elif obj.object.type == 'Material':
            materials += 1
        elif obj.object.type.endswith('MeshRenderer'):
            print('*'*8)
        elif obj.object.type == 'GameObject':
            name = obj.resolve().name

        print(' ' * depth + obj.object.type, obj.file_id, obj.path_id, name)
        seen.append(obj.object)
        fun(obj.resolve(), depth + 1)

    d = obj
    if not isinstance(d, OrderedDict):
        try:
            d = obj._obj
        except:
            pass
    if not isinstance(d, OrderedDict) and not isinstance(d, list) and not isinstance(d, tuple):
        return None

    if type(d) == list:
        for ent in d:
            #print('checking list item', ent)
            fun(ent, depth)
    elif type(d) == tuple:
        for ent in d:
            #print('checking tuple item', ent)
            fun(ent, depth)
    else:
        for k, v in d.items():
            #print('checking dict item', k)
            fun(v, depth)

def main(f, name):
    asset = Asset.from_file(f)

    depth = 0
    container = asset.objects[1].read()['m_Container']
    for path, mtdt in container:
        if path == name:
            gameobject = mtdt['asset'].object
            print(gameobject.type, gameobject.read().name)
            seen.append(gameobject)
            fun(gameobject.read(), 1)

            i = 0
            for mesh in meshes:
                with open('/tmp/mesh{}.obj'.format(i), 'w') as f:
                    f.write(OBJMesh(mesh).export())
                i += 1

            print('\n{} meshes\n{} texutres\n{} materials'.format(meshes, textures, materials))
            return

    print('didn\'t find', name)

if __name__ == '__main__':
    with open(sys.argv[1], 'rb') as f:
        main(f, sys.argv[2])
