import struct
import io, os
import argparse
import lz4.block
import lz4.frame
import xmltodict
from defusedxml import ElementTree

parser = argparse.ArgumentParser(description='Create modsetting entry for mod')
parser.add_argument('modfile', type=argparse.FileType('rb'))
args = parser.parse_args()
modfile = args.modfile
print(modfile.name)


class Uncompressed : io.RawIOBase:


class CompressionMethod(Enum):


class PackagedFileInfo:
    ArchivePart : int
    Crc : Union[None, int]
    Flags : int
    OffsetInFile : int
    SizeOnDisk : int
    UncompressedSize : int
    #public bool Solid;
    #public UInt32 SolidOffset;
    #public Stream SolidStream;
    #private Stream _uncompressedStream;


        


class PackageReader:
    magic = b"LSPK"

    def decode_xml(self, xml):
        #root = xmltodict.parse(xml)
        root = ElementTree.fromstring(xml)
        print(root)
        info = root.find("./region[@id='Config']/node[@id='root']/children/node[@id='ModuleInfo']")
        print('                        <node id="ModuleShortDesc">')
        print(ElementTree.tostring(info, encoding='unicode'))
        #for att in info:
        #    if att["@id"] in ["Folder", "MD5", "Name", "UUID", "Version"]:
       #         print(att)
        #        print(f"                            <attribute id=\"{att['@id']}\" type=\"{att['@type']}\" value=\"{att['@value']}\"/>")
        print('                        </node>')
    def readV18(self, file):
        file.seek(8, 0)
        file_list_offset = struct.unpack("<Q", file.read(8))[0]
        file_list_size = struct.unpack("<I", file.read(4))[0]
        flags = file.read(1)[0]
        priority = file.read(1)[0]
        md5 = file.read(16)
        num_parts = struct.unpack("<H",file.read(2))[0]
        
        file.seek(file_list_offset, 0)
        num_files = struct.unpack("<I", file.read(4))[0]
        compressed_size = struct.unpack("<I", file.read(4))[0]
#        print(num_files, compressed_size)

        compressed_list = file.read(compressed_size)
 #       print(compressed_list)

        file_entry_size = 256+4+2+1+1+4+4

        uncompressed_list = lz4.block.decompress(compressed_list, uncompressed_size=num_files*(256+4+2+1+1+4+4))
        files = []
        for i in range(0, num_files):
            list_entry = uncompressed_list[(i*file_entry_size):((i+1)*file_entry_size)]
  #          print(len(list_entry))
            files.append(struct.unpack("<256sIHBBII", list_entry))
        self._files = files
   #     print(files)
        
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


    def __init__(self, file):
        # first check for v13 headers, which are always at the end of the file
        file.seek(-8, 2)
        header_size = struct.unpack("<I", file.read(4))[0]
        signature = file.read(4)[0]
      #  print(signature)
        if signature == self.magic:
            raise Exception("V13 not supported")
            return
        file.seek(0, 0)
        signature = file.read(4)
       # print(signature)
        if signature == self.magic:
            version = struct.unpack("<I", file.read(4))[0]
            if version == 18:
                self.readV18(file)
                return 
            else:
                raise Exception(f"V{version} not supported")
        # TODO: handle V7 and V9
        raise Exception("Version not supported or magic not found")



PackageReader(modfile)
