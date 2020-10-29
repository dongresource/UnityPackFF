#!/usr/bin/env python3

import sys
import unitypack
from unitypack.asset import Asset

def isinterpreted():
    try:
        __file__
        return False
    except:
        return True

def isipython():
    try:
        return __IPYTHON__
    except:
        return False

class Mesh:
    def __init__(self):
        self.vertices = []
        self.normals = []
        self.uv1 = []
        self.uv2 = []
        self.colors = []
        self.indices = []
        self.triangles = []

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


def read_bits(pbv):
    if pbv['m_NumItems'] == 0 or pbv['m_BitSize'] == 0:
        return []

    reader = BitReader(pbv['m_Data'], pbv['m_BitSize'])

    ret = []
    for i in range(pbv['m_NumItems']):
        ret.append(reader.read())

    return ret

def read_floats(pbv):
    if pbv['m_NumItems'] == 0 or pbv['m_BitSize'] == 0:
        return []

    items = read_bits(pbv)
    maxvalue = (1 << pbv['m_BitSize']) - 1
    _range = pbv['m_Range'] / maxvalue

    floats = []
    for i in range(len(items)):
        floats.append(float(items[i] * _range + pbv['m_Start']))

    return floats

def read_normals(normals, normal_signs):
    items = read_bits(normals)
    signs = read_bits(normal_signs)

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

def handleStripTopology(ret, data):
    #print('handling strip topology')
    #print('faces before strip:', len(ret.triangles))

    tris = []
    degen = 0
    added = 0
    for i in range(len(ret.indices)):
        if i > data._obj['m_SubMeshes'][0]._obj['indexCount']:
            break

        tris.append(ret.indices[i])

        if len(tris) < 3:
            continue

        t1 = tris[0]
        t2 = tris[1]
        t3 = tris[2]

        del tris[0]

        if t1 == t2 or t1 == t3 or t2 == t3:
            degen += 1
            continue

        added += 1
        if i % 2 == 0:
            ret.triangles.append(t1)
            ret.triangles.append(t2)
            ret.triangles.append(t3)
        else:
            ret.triangles.append(t3)
            ret.triangles.append(t2)
            ret.triangles.append(t1)

    #print('faces after strip:', len(ret.triangles))
    #print('{} degenerate triangles'.format(degen))
    #print('{} triangles added'.format(added))

def extract_obj(data):
    ret = Mesh()
    cmesh = data._obj['m_CompressedMesh']

    vertex_floats = read_floats(cmesh['m_Vertices'])
    for i in range(0, len(vertex_floats), 3):
        ret.vertices.append((vertex_floats[i], vertex_floats[i+1], vertex_floats[i+2]))

    normal_floats = read_normals(cmesh['m_Normals'], cmesh['m_NormalSigns'])
    for i in range(0, len(normal_floats), 3):
        ret.normals.append((normal_floats[i], normal_floats[i+1], normal_floats[i+2]))

    uv_floats = read_floats(cmesh['m_UV'])
    for i in range(0, len(uv_floats), 2):
        if i < len(vertex_floats) // 3:
            ret.uv1.append((uv_floats[i], uv_floats[i+1]))
        else:
            ret.uv2.append((uv_floats[i], uv_floats[i+1]))

    # colors skipped

    triangle_ints = read_bits(cmesh['m_Triangles'])
#    for submesh in data._obj['m_SubMeshes']:
#        offset = submesh

    # TODO: is grouping triangles into submeshes strictly neccessary?
    #print('remainder was:', len(triangle_ints)%3)
    #triangle_ints = triangle_ints[:-(len(triangle_ints) % 3)]
    if len(triangle_ints) % 3 == 2:
        print('had 2 extra indices')
        #triangle_ints = triangle_ints[:-2]
        triangle_ints.append(triangle_ints[-1])
    elif len(triangle_ints) % 3 == 1:
        print('had 1 extra indice')
        triangle_ints.append(triangle_ints[-1])
        triangle_ints.append(triangle_ints[-2])
        #triangle_ints = triangle_ints[:-1]
    #print('remainder is:', len(triangle_ints)%3)

    ret.triangles.extend(triangle_ints)
    ret.indices.extend(triangle_ints)

    # TODO: fully implement submeshes
    if len(data._obj['m_SubMeshes']) > 0 and data._obj['m_SubMeshes'][0]._obj['isTriStrip'] > 0:
        handleStripTopology(ret, data)

    return ret

def write_obj(data, mesh, outf):
    vts = mesh.uv1
    if len(mesh.uv1) == 0:
        vts = mesh.uv2

    for v in mesh.vertices:
        print('v {} {} {}'.format(v[0], v[1], v[2]), file=outf)
    for n in mesh.normals:
        print('vn {} {} {}'.format(n[0], n[1], n[2]), file=outf)
    for vt in mesh.uv1:
        print('vt {} {}'.format(vt[0], vt[1]), file=outf)
    for vt in mesh.uv2:
        print('vt {} {}'.format(vt[0], vt[1]), file=outf)

    print('\ng {}'.format(data.name), file=outf)
    print('s 1', file=outf)

    for i in range(0, len(mesh.triangles), 3):
        if len(mesh.triangles) - i < 3:
            print("i is", i)
            print(len(mesh.triangles) - i, "STRAY FACES EXIST")
            break
        indices = [mesh.triangles[i+2], mesh.triangles[i+1], mesh.triangles[i]]
        print('f ', end='', file=outf)

        for index in indices:
            index += 1
            print(index, end='', file=outf)

            if len(vts) != 0 and index < len(mesh.uv1) + len(mesh.uv2) or len(mesh.normals) != 0 and index < len(mesh.normals):
                print('/', end='', file=outf)
                if len(vts) != 0 and index < len(mesh.uv1) + len(mesh.uv2):
                    print(index, end='', file=outf)
                if len(mesh.normals) != 0 and index < len(mesh.normals):
                    print('/', end='', file=outf)
                    print(index, end='', file=outf)

            print(' ', end='', file=outf)

        print('', file=outf)

    print('', file=outf)

def main(f):
    asset = Asset.from_file(f)
    wasmesh = False
    for id, obj in asset.objects.items():
        data = obj.read()
        if obj.type != 'Mesh':
            if wasmesh:
                break
            print('skipping', obj.type)
            continue
        wasmesh = True
        print('processing', id, data.name)

        mesh = extract_obj(data)
        with open("/tmp/out/" + data.name + ".obj", "w") as outf:
            write_obj(data, mesh, outf)

def altmain(f):
    asset = Asset.from_file(f)

    ids = [int(x) for x in sys.argv[2:]]
    for id in ids:
        obj = asset.objects[id]
        data = obj.read()
        print('processing', id, data.name)

        mesh = extract_obj(data)
        print("# of triangles:", len(mesh.triangles))
        print("# of vertices:", len(mesh.vertices))
        #print("last vertex:", max(mesh.triangles))
        print("# of normals:", len(mesh.normals))
        print("# of uv1s:", len(mesh.uv1))
        print("# of uv2s:", len(mesh.uv2))

        with open("/tmp/" + data.name + ".obj", "w") as outf:
            write_obj(data, mesh, outf)

if __name__ == '__main__' and not isinterpreted() and not isipython():
    with open(sys.argv[1], "rb") as f:
        if len(sys.argv) > 2:
            altmain(f)
        else:
            main(f)
