#!/usr/bin/env python3

import sys
import struct

class GUID: # fusionfall doesn't seem to use guids
    def __init__(self, f):
        self.most = struct.unpack(">Q", f.read(8))[0]
        self.least = struct.unpack(">Q", f.read(8))[0]

    def __str__(self):
        return "{:08x}-{:04x}-{:04x}-{:04x}-{:012x}".format((self.most>>4&0xffffffff), (self.most>>2&0xffff),
                self.most&0xffff, (self.least>>6)&0xffff, self.least&0xffffffffffff) # verify that this is actually right

class External:
    def __str__(self):
        return str(self.__dict__)

class ObjectInfo:
    def __str__(self):
        return str(self.__dict__)

class Type:
    def __str__(self):
        return "type with {} children".format(len(self.children))

class BaseClass:
    def __str__(self):
        return str(self.__dict__)

class Assets:
    def __str__(self):
        return "Assets with {} types, {} objects, {} externals".format(self.nbaseclasses, self.nobjects, self.nexternals)

global endian
endian = ">"

def die(s):
    print(s, file=sys.stderr)
    sys.exit(1)

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

def read_int(f):
    return struct.unpack(endian + "I", f.read(4))[0]

def read_short(f):
    return struct.unpack(endian + "H", f.read(2))[0]

def read_string(f):
    ret = []
    c = b''

    while c != b'\0':
        ret.append(c)
        c = f.read(1)

    return b''.join(ret).decode()

def read_type(f, parent):
    parent.type = read_string(f)
    parent.name = read_string(f)
    parent.size = read_int(f)
    parent.index = read_int(f)
    parent.isarray = bool(read_int(f))
    parent.version = read_int(f)
    parent.flags = read_int(f)

    nchildren = read_int(f)
    for i in range(nchildren):
        t = Type()
        t.children = []
        read_type(f, t)
        parent.children.append(t)

def load(f, a):
    # header
    a.metadatasize = read_int(f)
    a.filesize = read_int(f)
    if read_int(f) != 6:
        die("not a fusionfall asset file")
    a.objectdataoffset = read_int(f)

    global endian
    endian = "<"

    # metadata
    f.seek(a.filesize - a.metadatasize + 1)
    a.typemap = dict()
    a.nbaseclasses = read_int(f)
    for i in range(a.nbaseclasses):
        base = BaseClass()
        base.class_id = read_int(f) # should be signed?
        base.root = Type()
        base.root.children = []
        read_type(f, base.root)
        a.typemap[base.class_id] = base

    # objectinfomap
    a.infomap = dict()
    a.nobjects = read_int(f)
    for i in range(a.nobjects):
        path_id = read_int(f)
        info = ObjectInfo()
        info.start = read_int(f)
        info.size = read_int(f)
        info.type_id = read_int(f)
        info.class_id = read_short(f)
        info.isdestroyed = read_short(f)
        a.infomap[path_id] = info

    # externals
    a.nexternals = read_int(f)
    a.externals = []
    for i in range(a.nexternals):
        ext = External()
        ext.assetpath = read_string(f)
        ext.guid = GUID(f)
        ext.type = read_int(f)
        ext.filepath = read_string(f)
        a.externals.append(ext)

    # object data
    for id, info in a.infomap.items():
        off = a.objectdataoffset + info.start
        f.seek(off)
        info.data = f.read(info.size)

if __name__ == '__main__' and not isinterpreted() and not isipython():
    with open(sys.argv[1], "rb") as f:
        a = Assets()
        load(f, a)
        #print(a)
