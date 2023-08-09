import io, os
from lxml import etree
import pak
import lsx_attribute
from copy import deepcopy
import re

xmlparser = etree.XMLParser(remove_blank_text = True)

class ModInfo:
    META_ATTRIBUTES = ["Folder", "Name", "UUID", "MD5", "Version", "Version64"]
    def __init__(self, module_info_element : etree.Element):
        self.element = module_info_element
        self.attributes : Dist[str, lsx_attribute.LsxAttribute] = {}
        for e in self.element.findall('./attribute'):
            attr = lsx_attribute.LsxAttribute.from_etree_element(e)
            self.attributes[attr.id] = attr

    def to_meta_element(self):
        meta_element = etree.Element("node", id="ModuleShortDesc")
        for attr in self.META_ATTRIBUTES:
            a = self.attributes.get(attr)
            if a is not None:
                meta_element.append(a.to_etree_element())
        return meta_element


class ModMetaLsx:
    def __init__(self, xml_string):
        self.root : ElementTree = None
        self.info : List[etree.Element] = None
        self.mods : List[ModInfo] = []

        try:
            self.root = etree.fromstring(meta_file.read(), parser = xmlparser)
        except:
            raise Exception(f"meta.lsx is not a valid xml file")
        self.info = self.root.findall("./region[@id='Config']/node[@id='root']/children/node[@id='ModuleInfo']")
        if not self.info:
            raise Exception(f"meta.lsx does not contain module info")
        for info_elem in self.info:
            self.mods.append(ModInfo(info_elem))


class ModSettingsLsx:
    def __init__(self, file : io.IOBase):
        self.file = file
        self.tree : etree = None
        self.root : Element = None
        self.mod_elems : Element = None
        self.mods : List[ModInfo] = []

        try:
            self.tree = etree.parse(file, parser = xmlparser)
        except:
            raise Exception(f"modsettings.lsx is not a valid xml file")
        self.root = self.tree.getroot()
        self.mod_elems = self.root.find("./region[@id='ModuleSettings']/node[@id='root']/children/node[@id='Mods']/children")
        for e in self.mod_elems.findall('./node[@id="ModuleShortDesc"]'):
            self.mods.append(ModInfo(e))

    def add_mod(self, mod : ModInfo):
        self.mod_elems.append(mod.to_meta_element())

    def remove_mod(self, mod : ModInfo):
        for m in self.mods:
            if mod.attributes["UUID"] == m.attributes["UUID"]:
                self.mod_elems.remove(m.element)
                self.mods.remove(m)

    def remove_all_mods(self):
        for mod in self.mods:
            if mod.attributes['UUID'].value.value != "28ac9ce2-2aba-8cda-b3b5-6e922f71b6b8":
                self.remove_mod(mod)

    def save_file(self):
        etree.indent(self.tree, space='    ')
        self.file.seek(0)
        self.file.truncate()
        self.tree.write(self.file, pretty_print=True, xml_declaration=True, encoding='utf-8')
#        print(etree.tostring(self.mod_elems, pretty_print=True).decode())
 #       print(etree.tostring(mod.to_meta_element(), pretty_print=True).decode())
#    def remove_mod(self, mod : ModInfo):
#        for m in self.mods:
#            if m.attribute

        

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create modsetting entry for mod')
    parser.add_argument('modsettings', type=argparse.FileType('rb+'))
    parser.add_argument('modfile', type=argparse.FileType('rb'), nargs='+')
    args = parser.parse_args()
    modfiles = args.modfile
    modsettings = args.modsettings
    settings = ModSettingsLsx(modsettings)

    print('removing all mods')
    settings.remove_all_mods()

    for modfile in modfiles:
        print(f'Reading {modfile.name}')
        package = pak.PackageReader(modfile)

        meta_files = [f for f in package.files if re.fullmatch("Mods/([^/]+)/meta.lsx", f.info.name)]
        #print(meta_files)
        for meta_file in meta_files:
            print(f"Reading meta file {meta_file.info.name}")
         #   print(meta_file.info.name)
            meta = ModMetaLsx(meta_file.read())
            etree.indent(meta.root, space='    ')
          #  print(etree.tostring(meta.root, pretty_print=True).decode())
            for e in meta.info:
                modinfo = ModInfo(e)
                print(f"enabling mod {modinfo.attributes['Name'].value.value}")
                settings.add_mod(modinfo)


    print(etree.tostring(settings.root, pretty_print=True).decode())
    settings.save_file()

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
