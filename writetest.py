#!/usr/bin/env python3

import unitypack
from unitypack.asset import Asset

#f = open('../tabledata104', 'rb')
#outf = open('/tmp/tabledata_new', 'wb')
f = open('../LobbyMusic.resourceFile', 'rb')
outf = open('/tmp/lobbymusic', 'wb')

asset = unitypack.load(f).assets[0]
#asset = Asset.from_file(f)
asset.load()

#xdttable = asset.objects[7].contents

#xdttable['m_pNanoTable']['m_pNanoStringData'][1]['m_strName'] = 'Jade'
#xdttable['m_pNanoTable']['m_pNanoStringData'][2]['m_strName'] = 'Sane'
#xdttable['m_pNanoTable']['m_pNanoStringData'][3]['m_strName'] = 'Cake'

music = asset.objects[2].contents
f1 = open('/tmp/track02.ogg', 'rb')
music.audio_data = f1.read()
music.size = len(music.audio_data)
music.length = 308.60
# music.frequency is probably ususally the same (44100Hz), but it's good to check

asset.save(outf)

print('done.')

f.close()
outf.close()
