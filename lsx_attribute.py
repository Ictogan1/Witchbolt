from lxml import etree

class DataType:
    """
    Base class for all actual LSX data types
    
    All inherting classes shall have the following class members:

    NAME : str - e.g. "int64"
    PYTHON_TYPE : type - e.g. int
    tostring(self) - convert the object to a string (e.g. 32 to "32")
    fromstring(self) - try to initialize a new object from the string
    self.value - an object holding the python value of the type
    """
    def __init__(self, value = None):
        self.value = value
        if self.value is not None:
            if not isinstance(self.value, self.PYTHON_TYPE):
                raise TypeError(f"LSX DataType {NAME} initialized with incorrect type({type(self.value)})")
    @classmethod
    def getname(cls):
        return cls.NAME
#TODO: use python's abc library to have proper abstract classes

class DataTypeInt(DataType):
    """
    Base class for all types implementing int DataTypes.

    All inheriting classes must have the following memebers:

    NAME : str - name of the type
    NUM_BITS : int - number of bits in the integer
    SIGNED : bool - whether the integer is signed
    """
    PYTHON_TYPE = int

    @classmethod
    def fromstring(cls, string):
        self = cls()
        try:
            self.value = int(string)
        except:
            raise ValueException(f"invalid argument for initialization of DT_Int{string}")
        if not cls.check_bounds(self.value):
            raise ValueException(f"Value is too large for {cls.__name__}(value={self.value})")
        return self

    def tostring(self):
        if not self.check_bounds(self.value):
            raise ValueException(f"Value is too large for {cls.__name__}(value={self.value})")
        return str(self.value)
    @classmethod
    def check_bounds(cls, value):
        if cls.SIGNED:
            min_value = -(1<<(cls.NUM_BITS-1))
            max_value = (1<<(cls.NUM_BITS-1))-1
        else:
            min_value = 0
            max_value = (1<<cls.NUM_BITS)-1
        return min_value <= value <= max_value

class DT_Int8(DataTypeInt):
    NAME = "int8"
    NUM_BITS = 8
    SIGNED = True
class DT_UInt8(DataTypeInt):
    NAME = "int8"
    NUM_BITS = 8
    SIGNED = False
class DT_Int16(DataTypeInt):
    NAME = "int16"
    NUM_BITS = 16
    SIGNED = True
class DT_UInt16(DataTypeInt):
    NAME = "int16"
    NUM_BITS = 16
    SIGNED = False
class DT_Int32(DataTypeInt):
    NAME = "int32"
    NUM_BITS = 32
    SIGNED = True
class DT_UInt32(DataTypeInt):
    NAME = "int32"
    NUM_BITS = 32
    SIGNED = False
class DT_Int64(DataTypeInt):
    NAME = "int64"
    NUM_BITS = 64
    SIGNED = True
class DT_UInt64(DataTypeInt):
    NAME = "int64"
    NUM_BITS = 64
    SIGNED = False

class DT_LSString(DataType):
    NAME = "LSString"
    PYTHON_TYPE = str

    @classmethod
    def fromstring(cls,string):
        self = cls(string)
        return self
    def tostring(self):
        return self.value

class DT_FixedString(DT_LSString): # I don't understand the difference between this and LSString, so I just treat them the same for now
    NAME = "FixedString"

def Unknown_DataType(name : str):
    class DT_Unknown(DataType):
        NAME = name
        PYTHON_TYPE = str
        def fromstring(string):
            self = DT_Unknown(string)
            return self
        def tostring(self):
            return self.value
    return DT_Unknown

DATA_TYPE_LOOKUP_TABLE = {
        cls.NAME : cls for cls in [
            DT_Int8,
            DT_UInt8,
            DT_Int16,
            DT_UInt16,
            DT_Int32,
            DT_UInt32,
            DT_Int64,
            DT_UInt64,
            DT_LSString,
            DT_FixedString
        ]
    }

def lookup_type(type_name):
    return DATA_TYPE_LOOKUP_TABLE.get(type_name) or Unknown_DataType(type_name)

class LsxAttribute:
    def __init__(self, attr_id : str=None, value : DataType = None):
        self.id = attr_id
        self.value = value

    def from_etree_element(e : etree.Element):
        self = LsxAttribute()
        self.id = e.get('id')
        type_name = e.get('type')
        value_string = e.get('value')
        data_type = lookup_type(type_name)
        self.value = data_type.fromstring(value_string)
        return self

    def to_etree_element(self):
        return etree.Element("attribute", id=self.id, type=self.value.NAME, value = self.value.tostring())
