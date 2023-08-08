"""
This file provides an interface for Larian Studios' .pak files, which are used for mods. Loosely based on https://github.com/Norbyte/lslib
"""


import io, os
import lz4.block
import lz4.frame
import zlib
import enum
from ctypes import *
from typing import List

class CompressionMethod(enum.Enum):
    NONE = 0
    ZLIB = 1
    LZ4  = 2

class Flags(enum.IntEnum):
    ALLOW_MEMORY_MAPPING = 0x2
    SOLID = 0x4
    PRELOAD = 0x8


class LSPKHeader15(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
            ("version", c_uint32),
            ("file_list_offset", c_uint64),
            ("file_list_size", c_uint32),
            ("flags", c_byte),
            ("priority", c_byte),
            ("md5", c_byte*16)
        ]
class FileEntry15(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
            ("name", c_char*256),
            ("offset_in_file", c_uint64),
            ("size_on_disk", c_uint64),
            ("uncompressed_size", c_uint64),
            ("archive_part", c_uint32),
            ("flags", c_uint32),
            ("crc", c_uint32),
            ("unknown2", c_uint32)
        ]
class LSPKHeader16(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
            ("version", c_uint32),
            ("file_list_offset", c_uint64),
            ("file_list_size", c_uint32),
            ("flags", c_byte),
            ("priority", c_byte),
            ("md5", c_byte*16),
            ("num_parts", c_uint16)
        ]
class FileEntry18(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
            ("name", c_char*256),
            ("offset_in_file_1", c_uint32),
            ("offset_in_file_2", c_uint16),
            ("archive_part", c_uint8),
            ("flags", c_uint8),
            ("size_on_disk", c_uint32),
            ("uncompressed_size", c_uint32),
        ]

class PackagedFileInfo:
    """Describes a file inside a .pak file"""
    def __init__(self):
        selfname: str
        self.archive_part : int
        self.crc : None | int
        self.flags : int
        self.offset_in_file : int
        self.size_on_disk : int
        self.uncompressed_size : int
        # TODO: support solid file entries(as far as I understand, this means that all files are compressed at once rather than individually - only seems to be done for V13)

    def get_compression_method(self):
        compression_flag = self.flags & 0xF
        try:
            return CompressionMethod(compression_flag)
        except TypeError:
            raise ValueError(f"Unsupported compression method(flags=0x{compression_flag:x})")

    def from_file_entry_15(buf : bytes):
        self = PackagedFileInfo()
        entry = FileEntry15.from_buffer_copy(buf)
        self.name = c_char_p(entry.name).value
        self.offset_in_file = entry.offset_in_file
        self.size_on_disk = entry.size_on_disk
        self.uncompressed_size = entry.uncompressed_size
        self.archive_part = entry.archive_part
        self.flags = entry.flags
        self.crc = entry.crc
        return self

    def from_file_entry_18(buf : bytes):
        self = PackagedFileInfo()
        entry = FileEntry18.from_buffer_copy(buf)
        self.name = c_char_p(entry.name).value
        self.offset_in_file = entry.offset_in_file_1 + (entry.offset_in_file_2 << 32)
        self.size_on_disk = entry.size_on_disk
        self.uncompressed_size = entry.uncompressed_size
        self.archive_part = entry.archive_part
        self.flags = entry.flags
        self.crc = 0
        return self


class FileReader:
    def __init__(self, file_info : PackagedFileInfo, pak_file : io.IOBase):
        self.info : PackedFileInfo = file_info
        self.pak_file : io.IOBase = pak_file

    def read(self):
        off = self.pak_file.seek(self.info.offset_in_file)
        if off != self.info.offset_in_file:
            raise EOFError()
        compressed_data = self.pak_file.read(self.info.size_on_disk)
        if len(compressed_data) != self.info.size_on_disk:
            raise EOFError()

        compression_method = self.info.get_compression_method()

        match compression_method:
            case CompressionMethod.NONE:
                uncompressed_data = compressed_data
            case CompressionMethod.ZLIB:
                uncompressed_data = self.decompress_zlib(compressed_data)
            case CompressionMethod.LZ4:
                uncompressed_data = self.decompress_lz4(compressed_data)
        if (compression_method != CompressionMethod.NONE) and (len(uncompressed_data) != self.info.uncompressed_size):
            raise Exception(f"Uncompressed file length does not match expected value({len(uncompressed_data)} instead of {self.info.uncompressed_size})")
        return uncompressed_data
    
    def decompress_zlib(self, compressed_data):
        data = zlib.decompress(compressed_data)
        return data
        
    def decompress_lz4(self, compressed_data, chunked = False):
        if chunked:
            return lz4.frame.decompress(compressed_data)
        else:
            return lz4.block.decompress(compressed_data, uncompressed_size = self.info.uncompressed_size)




class PackageReader:
    MAGIC = b"LSPK"

    def __init__(self, package):
        self.package : io.IOBase = package
        self.files : List[FileReader] = []
        self.flags : int = 0
        self.header = None

        # first check for v13 headers, which are always at the end of the file
        package.seek(-4, io.SEEK_END)
        signature = package.read(4)
        if signature == self.MAGIC:
            raise Exception("V13 not supported")
            return
        package.seek(0)
        signature = package.read(4)
        if signature == self.MAGIC:
            version = c_uint32.from_buffer_copy(package.read(4)).value
            match version:
                case 15:
                    self.read_v15()
                    return
                case 16:
                    self.read_v16()
                    return
                case 18:
                    self.read_v18()
                    return
                case _:
                    raise Exception(f"V{version} not supported")
        # TODO: handle V7 and V9
        raise Exception("Version not supported or not a valid pak file")

    def read_file_list_15(self):
        package.seek(self.header.file_list_offset)
        num_files = c_uint32.from_buffer_copy(package.read(4)).value
        compressed_file_list_size = c_uint32.from_buffer_copy(package.read(4)).value
        compressed_file_list = package.read(compressed_file_list_size)
        file_list_size = num_files*sizeof(FileEntry15)
        file_list = lz4.block.decompress(compressed_file_list, uncompressed_size = file_list_size)
        if len(file_list) != file_list_size:
            raise Exception("Incorrect file list length")

        for i in range(0, num_files):
            entry = PackagedFileInfo.from_file_entry_15(file_list[i*sizeof(FileEntry15):(i+1)*sizeof(FileEntry15)])
            self.files.append(FileReader(entry, package))

    def read_file_list_18(self):
        package.seek(self.header.file_list_offset)
        num_files = c_uint32.from_buffer_copy(package.read(4)).value
        compressed_file_list_size = c_uint32.from_buffer_copy(package.read(4)).value
        compressed_file_list = package.read(compressed_file_list_size)
        file_list_size = num_files*sizeof(FileEntry18)
        file_list = lz4.block.decompress(compressed_file_list, uncompressed_size = file_list_size)
        if len(file_list) != file_list_size:
            raise Exception("Incorrect file list length")

        for i in range(0, num_files):
            entry = PackagedFileInfo.from_file_entry_18(file_list[i*sizeof(FileEntry18):(i+1)*sizeof(FileEntry18)])
            self.files.append(FileReader(entry, package))

    def read_v15(self):
        package.seek(4)
        self.header = LSPKHeader15.from_buffer_copy(package.read(sizeof(LSPKHeader15)))
        self.flags = self.header.flags

        self.read_file_list_15()

    def read_v16(self):
        package.seek(4)
        self.header = LSPKHeader16.from_buffer_copy(package.read(sizeof(LSPKHeader16)))
        self.flags = self.header.flags

        self.read_file_list_15()

    def read_v18(self):
        package.seek(4)
        self.header = LSPKHeader16.from_buffer_copy(package.read(sizeof(LSPKHeader16)))
        self.flags = self.header.flags

        self.read_file_list_18()
        """
        num_files = c_uint32.from_buffer_copy(package.read(4)).value
        compressed_file_list_size = c_uint32.from_buffer_copy(package.read(4)).value
        compressed_file_list = package.read(compressed_file_list_size)
        file_list_size = num_files*sizeof(FileEntry18)
        file_list = lz4.block.decompress(compressed_file_list, uncompressed_size = file_list_size)
        if len(file_list) != file_list_size:
            raise Exception("Incorrect file list length")

        for i in range(0, num_files):
            entry = PackagedFileInfo.from_file_entry_18(file_list[i*sizeof(FileEntry18):(i+1)*sizeof(FileEntry18)])
            self.files.append(FileReader(entry, package))
        """

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Create modsetting entry for mod')
    parser.add_argument('package', nargs="+", type=argparse.FileType('rb'))
    args = parser.parse_args()
    packages = args.package

    for package in packages:
        print("\n")
        print(package.name)
        try:
            reader = PackageReader(package)
        except Exception as e:
            print(f"Error while reading file {package.name} : {e}")
            continue
        for file in reader.files:
            print(file.info.name)
            #print(file.read())
