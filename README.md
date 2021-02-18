# UnityPackFF

UnityPackFF is a fork of [UnityPack](https://github.com/HearthSim/UnityPack/) specialized for working with FusionFall assets.
It allows for extraction and limited manipulation of FusionFall assets and might become the basis of a more extensive modding toolkit in the future.

Maintained compatibility with other asset format versions is not guaranteed.

Note: This project is meant to be used by people familiar with the technologies involved, not by end users.
Please do not bother me with questions about Python, FF modding or the nature of binary data.
Please take the time to figure out how to accomplish what you want yourself if you feel you're up to the task of doing so; especially if it's not something that's already been documented as doable.

## Details

This project was forked from commit `d9ce99fa` of UnityPack.
The upstream readme has been renamed to [README.UP.md](README.UP.md).

It currently supports working with all asset bundles from the original game, as well as all asset bundles from FusionFall Retro.

Note that this repository is a loose collection of patches and scripts I had originally written for my own use and have only slightly cleaned up before publishing.
Do read the scripts in `bin` before executing them to make sure you understand what they do.
Tweaking them yourself is to be considered part of standard usage.

I have not tested any of this on Windows myself, though it *should* all work just fine.

Dependencies can be installed using `pip`, as usual:

```
$ sudo pip3 install -r requirements.txt
```

The library itself can also be installed with `setup.py`, like most Python software.
The recommended approach is to install the library in ["Development Mode"](https://setuptools.readthedocs.io/en/latest/userguide/development_mode.html), like so:

```
$ sudo python3 setup.py develop
```

This places only a reference into your system's package directory as opposed to copying the entire library into a directory that isn't user-writable.
This way you can keep modifying the code in your repository directory without having to reinstall the entire thing after every change.
Note that this doesn't seem to work on Windows if Python was installed from the Microsoft Store, and that even with this system, the scripts in `bin/` are still copied whole into the system's Python script directory, so changes to them will still need to be propagated by re-invoking `setup.py` if you wish to use them without specifying their location.
Another option is to just set the `PYTHONPATH` environment variable to this directory.

Current features:

* Extracting models, textures, audio, compiled shaders, terrain data
* Reading/dumping the XDT data from TableData asset bundles in-place
* Looking up offsets in asset bundles to modify data using hex editors or scripts
* Modifying terrain data (albeit imperfectly at the moment)

## Asset structure

Note on terminology: Unity appears to have a lot of overloaded terms for these things, making them difficult to keep track of.
There's three different definitions for what an AssetBundle is, for instance.
I try to be mostly consistent with the terms I use, but when in doubt, consider the context.

As explained in the [OpenFusion readme](https://github.com/OpenFusionProject/OpenFusion/#architecture), the web gateway directs the player's browser to download the main `unity3d` bundle which contains the game's essential assets (`mainData` and `sharedAssets0.asset`) along with all the client's C# DLLs.
Apart from those two assets, all the others will be downloaded in separate bundles from the address in `assetInfo.php` and cached in their extracted forms in `C:\Users\USERNAME\AppData\LocalLow\Unity\Web Player\Cache\FusionFall` (note the space in `Web Player`).

Both the main `unity3d` file and the other assets are transmitted as the same `unity3d` file format, regardless if the file extension is `.unity3d` or `.resourceFile`.
This format is just a trivial LZMA compressed archive containing plain files.
It can be extracted using [quickbms](http://aluigi.altervista.org/quickbms.htm) with the `unity3d_webplayer.bms` script.
The contents of the main bundle were explained in the previous paragraph, the others only contain one asset bundle and one or two metadata files.

Unlike the container format, these asset bundles are not simple file archives.
They store a series of *asset objects*, each of which is a hierarchy of members, some of which are pointers to other objects which are potentially defined in other asset bundles referenced in a table of externals.
Each of these asset objects is structured according to a specific type which is also defined in the asset bundle.
Some of these types are standard (indicated by positive IDs), while others are asset bundle-specific (indicated by negative IDs).

Disunity's wiki has some [notes](https://github.com/ata4/disunity/wiki/Serialized-file-format) on the structure of these asset bundles.
I've also [mirrored](https://github.com/dongresource/UnityPackFF/wiki/Serialized-file-format) them in this repository's wiki for convenience.

Each of these asset bundle files is either a Scene asset bundle or a regular (resource) asset bundle.
Scene asset bundles have a `SceneSettings` object as their first asset object member, the archives they're stored in use the `.unity3d` file extension, and their names are of the format `Map_XX_YY.unity3d`.
The filenames of the asset bundles themselves are of the format `BuildPlayer-Map_XX_YY`, accompanied by another asset bundle with the same name, but ending in `.sharedAssets`.
In FusionFall, each map tile is a scene.
Regular asset bundles have an `AssetBundle` object as their first asset object member and the archives they're stored in use the `.resourceFile` file extension.
For each map tile, there's a `DongResources_XX_YY.resourceFile` that contains the assets that tile makes use of.
All the remaining asset bundles (CharTexture, CharacterCreation, CharacterSelection, TableData, NpcTexture, etc) are also of this type.

This library is meant to operate on the CustomAssetBundles after they've already been extracted from their respective `.unity3d` archives.
You can either copy out your cache directory after having played the game (and gone to the Past zone) or you can extract the asset files from their `.unity3d` archives yourself using a tool like `quickbms`.
This can be automated for every asset bundle with a shell one-liner or any similar means.

## Usage

Depending on what you are trying to achieve, the library can be used either interactively or through one of the provided scripts (or one's own, of course).

### Interactive use

For improved auto-completion I suggest using `ipython` instead of the raw Python interpreter.

Start by importing the `Asset` class from the library, opening an asset (for reading) as a binary file and creating a new `Asset` object:

```python
from unitypack.asset import Asset
f = open('tabledata_2eresourceFile/CustomAssetBundle-1dca92eecee4742d985b799d8226666d', 'rb')
tabledata = Asset.from_file(f)
```

UnityPack also has a `unitypack.load()` function that operates directly on the enclosing `.unity3d` bundle, but that method does not currently set the correct version in the asset bundle, and is therefore unusable.

After you've opened up the `tabledata` asset bundle, you can access its asset objects through its `tabledata.objects` member.
Note that `objects` is a dict with integer keys, not a list. The first member is usually 1 in these.
Most asset bundles have a large number of top-level objects, but TableData only has 9.
Of those, the seventh, `xdtdata`, is the most interesting.
We can read it out into a variable with:

```python
xdtdata = tabledata.objects[7].contents
```

Make sure to read large objects like this one into a variable, as accessing them directly from the asset incurs disk IO every time, which makes browsing the table sluggish.

The way these Unity objects are structured, everything in the `objects` dict is a Python object of type `ObjectInfo`.
The `ObjectInfo` class's `contents` member is the actual asset object, which can be an instance of either one of UnityPack's specialized classes (`Texture2D`, `AudioClip`, `Transform`, etc), or a `FFOrderedDict` object by default.
In case of one of the former, the underlying `FFOrderedDict` can usually be accessed by the specialized class's `_obj` member (like `asset.objects[...].contents._obj`).

You can browse these objects interactively as you would any other Python data structures.
The smaller `FFOrderedDict`s like `Transform`s and `GameObject`s you can print whole, but larger ones (like the aforementioned `xdtdata`) would just overflow your terminal.
You can traverse those by printing them little by little; printing only the keys to `dict`s and checking the lengths of `list`s before indexing them.
`xdtdata` in particular consists of two depths of asset objects (`FFOrderedDict`s) followed by a list of asset objects with only primitive members.
Some of those members are integer indexes into other XDT tables, often the ones in the same subcategory.

So you can traverse the XDT like so:

```python
>>> xdtdata.keys()
odict_keys([..., 'm_pPantsItemTable', 'm_pShirtsItemTable', 'm_pShoesItemTable', 'm_pWeaponItemTable', 'm_pVehicleItemTable', ...])

>>> xdtdata['m_pWeaponItemTable'].keys()
odict_keys(['m_pItemData', 'm_pItemStringData', 'm_pItemIconData', 'm_pItemMeshData', 'm_pItemSoundData'])

>>> len(len(xdtdata['m_pWeaponItemTable']['m_pItemData']))
687

>>> xdtdata['m_pWeaponItemTable']['m_pItemData'][5]
FFOrderedDict([('m_iItemNumber', 5),
               ('m_iItemName', 5),
               ('m_iComment', 5),
               ('m_iTradeAble', 1),
               ('m_iItemPrice', 1090),
               ('m_iItemSellPrice', 273),
               ('m_iSellAble', 1),
               ('m_iStackNumber', 1),
...

>>> xdtdata['m_pWeaponItemTable']['m_pItemStringData'][5]
FFOrderedDict([('m_strName', 'Pewter Apple of Discord'),
               ('m_strComment',
                'Create chaos wherever you go with this powerful thrown weapon.'),
               ('m_strComment1', ' '),
               ('m_strComment2', ''),
               ('m_iExtraNumber', 0)])
```

You can loop over these lists to match index numbers with objects when they aren't obvious.

If you want to modify any of these values, you can get the index of any `FFOrderedDict` from its `index` member, as well as the index of any of its members like so:

```python
xdtdata['m_pWeaponItemTable']['m_pItemData'][5].getmemboffset('m_iItemPrice')
```

You can then open the asset bundle in a hex editor and make whatever change you want at that offset; or write a script for more sophisticated modifications.

Some objects contain `ObjectPointer`s that point to any other object in either the same asset bundle (if `file_id` is 0), or one of the ones linked in `asset.asset_ref`.
`path_id` is the index into the `asset.objects` of the asset bundle `file_id` points to.
If the `base_path` in your asset's `UnityEnvironment` is set up correctly, the `resolve()` method can automatically dereference these asset pointers.

### Scripts

#### `unityextract.py`

---

This is a modified version of the same script from upstream UnityPack.
Like all the other scripts, it has been made robust against exceptions, ie. failure to extract one asset will not halt extraction of the rest.
It rips any supported assets into the current working directory, constructing filenames according to the name fields of each asset object.
Invoke like:

```python
/path/to/unityextract.py --all --as-asset CustomAssetBundle-...
```

It's useful for ripping assets on a smaller scale, and for ripping assets from Scene asset bundles which `ffextract.py` isn't compatible with.

#### `unity2yaml.py`

---

From upstream UnityPack. Mostly irrelevant here.

#### `list_contents.py`, `list_assetbundle.py`, `list_ab_alt.py`

---

These scripts generate textual listings of the asset objects in a given asset bundle.

`list_contents.py` lists the type and name (if any) of every single asset object.
`list_assetbundle.py` lists asset objects according to the asset bundle's `AssetBundle` (first member).
It's only compatible with non-Scene asset bundles, but has the advantage of listing proper asset filenames instead of internal object names.
It also lists the preload indexes of each of those objects, which isn't actually all that useful, so `list_ab_alt.py` is preferred because it instead lists the `path_id` and `file_id` numbers of each entry.

I used these with a few shell one-liners to construct a directory hierarchy that mirrors the layout of the asset cache, but has asset object listings instead of the asset bundles themselves.
This makes it easy to figure out which bundle a given asset is stored in using good ol' `grep`.
In hindsight, I probably should have just written a Python script to do that, instead of enduring the overhead of invoking the Python interpreter to execute these scripts in every loop iteration, but oh well.

#### `show_gameobject.py`

---

This script takes an asset bundle and the full filename of an asset that can be found in the `AssetBundle` member of that asset bundle.
It traverses `ObjectPointer`s from the `GameObject` that the `AssetBundle` points to and draws a tree to standard output with the `path_id`s and names of everything it encounters.
Output puts emphasis on `Mesh` objects.

This is meant to visualize the structure of model-related assets; to aid in writing/modifying `ffextract.py`.
Uninformed graph traversal probably isn't the best way to accomplish this, but there's multiple ways a `GameObject` can connect to a `Mesh`, so this is the lazy way of making sure we hopefully find all of 'em.

The large number of `GameObject`s and `Transform`s in the output are actually bones in the model's armature.
I assume there's a reliable way to avoid traversing the bone tree altogether, but I've yet to find it.

This script takes an optional directory argument that will be used as the `UnityEnvironment`'s `base_path`.
If an asset bundle is being read from within a cache directory (or any other place where the other asset bundles are nearby), passing that directory's path allows the script to follow cross-file `ObjectPointer`s.

#### `ffextract.py`

---

`ffextract.py` is the most significant script as of now.
It extracts all supported asset file formats according to the filenames in each (non-Scene) asset bundle's `AssetBundle` member.
This recreates the directory structure of the game's assets.

File extensions are translated from those of the original formats the developers used to those the library extracts assets into (ex. `.kfm` -> `.obj`, `.mp3` -> `.ogg`, `.psd` -> `.png`).

Because `AssetBundle`s never point to `Mesh` objects directly, and instead point to `GameObject`s that eventually have a `Mesh` in one of their children, we must traverse those children until we find the meshes we want to export to `.obj` files.
`Mesh` objects are usually children of some container object like a `SkinnedMeshRenderer` or a `MeshFilter`.

Because filenames are a property of each `GameObject`, not each mesh, when an object contains multiple meshes, each is extracted as a separate file with a colon followed by a number before the file extension.
An alternative would be to put them all into the same file as submeshes, but this would be a non-trivial task right now.
Quality contributions are welcome.

Currently, only `SkinnedMeshRenderer`s are being ripped from, since most models of interest are in those, and enabling `MeshFilter` extraction causes a lot of garbage to be extracted.
If I recall correctly, some real (non-junk) meshes are actually children of `MeshFilter` objects, so if you wish to rip those anyway, uncomment the `MeshFilter` `if` block in `gameobject_recurse()` along with the mesh limit block.
Be warned that each bone in an object's armature links to a `MeshFilter` with a plain cube, so if `MeshFilter`s are being naively extracted, countless garbage `.obj` files will be generated, wasting tons of disk space and immensely slowing the extraction process.
There is almost certainly a way to skip the armature or the uninformed traversal of the asset object graph entirely, but I haven't had the opportunity to look for one as of yet.

To invoke `ffextract.py`, pass it your asset cache directory (or a similar dir with all the assets) and a (usually empty) output directory.
The input directory will be used as the `UnityEnvironment`'s `base_path`, so `ObjectPointer`s will work properly.
This is important because the `AssetBundle`s often reference asset objects located in files other than their own.
The script will generate an output directory structure that mimics that of the FF developers (according to the filenames in each `AssetBundle` object).
`GameObject` traversal is considerably redundant and not terribly efficient, so the extraction process takes a while. Be patient.

Tip: When importing the resulting `obj` files into Blender, you'll want to select them and "Clear Custom Split Normals Data" either in the "Geometry Data" tab in "Object Data Properties"; or by searching for that option with F3 (or Space, in Blender 2.7x).
This fixes a shading issue. It's possible the normals aren't being ripped correctly.
You'll also want to change the Forward or Up axes in the file selection menu when importing the `obj` file so the models are imported upright without you having to rotate them manually.

#### `dump_terrain.py`, `replace_terrain.py`

---

These are currently imperfect terrain modding scripts.
`dump_terrain.py` was initially written by CPunch.

You supply `dump_terrain.py` with a "dongresources" asset bundle and an output file name and it will print the hexadecimal offset of that map tile's terrain data and extract it as a grayscale PNG file.
Note that the image will be rotated differently than in the game.

This image can be edited in any image editor. Darker shades result in lower, while brighter ones in higher terrain.
You could also use them in Blender in a displacement modifier on a subdivided plane for more natural editing, and then bake it back to an image for export, but getting this to work in a pixel-perfect manner would be tricky.

The modified image can be supplied to `replace_terrain.py` along with the offset that `dump_terrain.py` had printed; as well as the asset bundle to re-inject the terrain data into.
The target asset bundle will be edited in-place, so make sure to make a backup beforehand.

Unfortunately, the terrain data uses 16-bit integers for each pixel and this format doesn't seem to map cleanly to any well-supported pixel format.
Currently, `dump_terrain.py` maps the 16-bit value range to a single byte (and stores it thrice, once for each byte of an RGB pixel), resulting in rounding errors which very clearly mangle the terrain even if no changes were manually introduced.
For that reason, these scripts are only good for testing and goofing around until we can possibly write a custom blender import script to allow terrain modification without messing the entire map tile up.

#### `proto_extract.py`, `proto_mesh_extract.py`

---

These scripts were prototypes I wrote while figuring out the asset bundle and compressed mesh formats, respectively.
Their logic is already in the library as of my first commit to this project (`7ca8bcb5`).
Both were written with reference to the source code of older versions of Disunity.

They might be of use to anyone trying to implement generation of new FF-compatible asset bundles or modification of existing ones.

`proto_extract.py` only loads the asset bundle's type tree so it's browsable interactively if the script is `import`ed or run with `ipython`'s `%run` command.
It does not decode the asset objects themselves.
