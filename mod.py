import io, os
#from defusedxml import ElementTree
from xml.etree import ElementTree
import pak
import copy
from abc import ABC

        

class ModMetaLsx:
    REQUIRED_ATTRIBUTES = ["Folder", "Name", "UUID"]
    def __init__(self, xml_string):
        self.root : ElementTree
        self.info : ElementTree.Element
        try:
            self.root = ElementTree.fromstring(meta_file.read())
        except:
            raise Exception(f"meta.lsx is not a valid xml file")
        self.info = self.root.find("./region[@id='Config']/node[@id='root']/children/node[@id='ModuleInfo']")
        if self.info is None:
            raise Exception(f"meta.lsx does not contain module info")
    def get_required_attributes(self):
        return [e for e in self.info.iter(tag='attribute') if e.get('id') in self.REQUIRED_ATTRIBUTES]

class ModSettingsLsx:
    def __init__(self, file):
        self.tree : ElementTree = None
        self.root : Element = None
        self.mods : Element = None

        try:
            self.tree = ElementTree.parse(file)
        except:
            raise Exception(f"modsettings.lsx is not a valid xml file")
        self.root = self.tree.getroot()
        self.mods = self.root.find("./region[@id='ModuleSettings']/node[@id='root']/children/node[@id='Mods']/children")
    def insert_mod(self, meta_lsx):
        

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create modsetting entry for mod')
    parser.add_argument('modsettings', type=argparse.FileType('r'))
    parser.add_argument('modfile', type=argparse.FileType('rb'))
    args = parser.parse_args()
    modfile = args.modfile
    modsettings = args.modsettings
    print(modsettings.name)
    settings = ModSettingsLsx(modsettings)
    print(settings.mods)

    print(modfile.name)
    package = pak.PackageReader(modfile)

    meta_files = [f for f in package.files if f.info.name.endswith("/meta.lsx")]
    print(meta_files)
    for meta_file in meta_files:
        print(meta_file.info.name)
        meta = ModMetaLsx(meta_file.read())
        ElementTree.indent(meta.root, space='    ', level=0)
        print(ElementTree.tostring(meta.info).decode())
        print([ElementTree.tostring(a) for a in meta.get_required_attributes()])


"""
        for i, f in enumerate(files):
            path = f[0].decode().split('\0',1)[0]
            if path.endswith('meta.lsx'):
    #            print(f)
     #           print(path)
                meta_file = f
        if meta_file:
            meta_file_offset = meta_file[1]+(meta_file[2]<<32)
            meta_file_archive_part = meta_file[3]
            meta_file_flags = meta_file[4]
            meta_file_size_on_disk=meta_file[5]
            meta_file_uncompressed_size=meta_file[6]
            file.seek(meta_file_offset, 0)
            compressed_data = file.read(meta_file_size_on_disk)
            if (meta_file_flags&0xF) == 0:
                uncompressed_data = compressed_data
            if (meta_file_flags&0xF) == 1:
                raise Exception("Zlib compression not supported")
            if(meta_file_flags&0xF) == 2:
                uncompressed_data = lz4.block.decompress(compressed_data, uncompressed_size = meta_file_uncompressed_size)
       #     print(meta_file_data)
            self.decode_xml(uncompressed_data.decode())
        else:
            print(f"could not find meta file for {file.name}")
"""
