# Compatible with datadef.js

from json import dumps as dict2str, loads as str2dict
from threading import Timer
from os.path import exists
from re import match as regex_match, compile as str2regex

typeof = lambda v : type(v).__name__

class DataDef(list):
  """
    DataDef (extends Python List object)

    DataTypes:

      DataDef.StringType - string data
      DataDef.NumberType - numeric data (int or float)
      DataDef.BooleanType - boolean data
    
    Usage:

      d = DataDef({"name":DataDef.StringType,"age":DataDef.NumberType,"retired":DataDef.BooleanType})
      
  """
  StringType = 'string'
  NumberType = 'number'
  BooleanType = 'boolean'
  
  def __init__(self,fields,data=[]):
    if not self.__validatefields(fields):
      raise Exception(f"Invalid schema definition ({str(fields)})")
    
    self.FIELDS = fields
    
    if len(data) > 0:
      for row in data:
        self.Insert(row)
  
  def AddField(self,fname,ftype):
    """
      # Extend schema by adding type
      d.AddField("town",DataDef.StringType)
    """
    if not self.__validatefields({fname:ftype}):
      raise Exception(f"Invalid schema update ({fname}:{ftype})")
    
    self.FIELDS[fname] = ftype
    for row in self:
      row[fname] = None
  
  def Delete(self,q):
    """
      # Delete records where age is 70-79
      d.Delete([("age","^7[0-9])])

      # Delete records where age is 19
      d.Delete([("age",19)])

      # Delete records where age is 30 and name starts with "J"
      d.Delete([("age",30),("name","^J")])
    """
    r = [i for (i,v) in enumerate(self) if len([b for b in q if regex_match(str2regex(str(b[1])),str(v[b[0]]))]) == len(q)]
    
    for thisidx in r:
      del self[thisidx]
  
  def Update(self,q,updates=[]):
    """
      # Set retired to True where age is 67-69
      d.Update([("age","^6[789]")],[("retired",True)])
    """
    r = [i for (i,v) in enumerate(self) if len([b for b in q if regex_match(str2regex(str(b[1])),str(v[b[0]]))]) == len(q)]
    
    for thisidx in r:
      for thisupdate in updates:
        if not self.__validateupdate(thisupdate):
          raise Exception(f"Invalid update ({str(thisupdate)})")
        
        self[thisidx][thisupdate[0]] = thisupdate[1]          
  
  def Query(self,q):
    """
      # Query for records where age is between 40 and 59
      result = d.Query([("age","^[4-5][0-9]")])
    """
    if not self.__validatequery(q):
      raise Exception(f"Invalid query ({str(q)})")
    
    result = []
    
    r = [i for (i,v) in enumerate(self) if len([b for b in q if regex_match(str2regex(str(b[1])),str(v[b[0]]))]) == len(q)]
    
    for thisidx in r:
      result.append(self[thisidx])
    
    return result
  
  def Insert(self,row):
    """
      # Valid Inserts
      d.insert({"name":"Bob","age":43,"retired":False})
      d.insert({"name":"Jim","age":30,"retired":False})
      d.insert({"name":"Dave","age":71,"retired":True})
      d.insert({"name":"Joe","age":19})

      # Invalid insert will raise an exception (age must be a number)
      d.insert({"name":"Zeke","age":"43","retired":False})
    """
    if not self.__validaterow(row):
      raise Exception(f"Invalid insert ({str(row)})")
    
    self.append(row)
  
  def __jsfieldmap(self,t):
    return { "float" : "number", "int" : "number", "str" : "string", "bool" : "boolean" }[t]
  
  def __validatequery(self,q):
    for thisquery in q:
      if not len(thisquery) == 2:
        return False
      
      if not thisquery[0] in self.FIELDS:
        return False
    
    return True
  
  def __validateupdate(self,fieldupdate):
    if not len(fieldupdate) == 2:
      return False
    
    if not self.__validaterow({fieldupdate[0]:fieldupdate[1]}):
      return False
    
    return True
  
  def __validaterow(self,row):
    fields = list(row.keys())
    
    for thisfield in fields:
      if not thisfield in list(self.FIELDS.keys()):
        return False
      
      if not self.FIELDS[thisfield] == self.__jsfieldmap(typeof(row[thisfield])):
        return False
    
    return True
  
  def __validatefields(self,fields):
    types = [DataDef.StringType,DataDef.NumberType,DataDef.BooleanType]
    
    fieldnames = list(fields.keys())
    
    validfields = [a for a in fieldnames if fields[a] in types]
    
    return True if len(validfields) == len(fields) else False

class DataCache(DataDef):
  """
    DataCache (extends above DataDef object)

    Usage:
    
      # Initialize dataset from JSON file
      # NOTE:  DataCache requiring identical fields on each record to accurately detect schema
      mydata = DataCache({"name":DataDef.StringType,"age":DataDef.NumberType,"retired":DataDef.BooleanType},'/path/to/people.json')
      
      # After first initializing data cache with schema, the schema is cached also.
      # For subsequent executions, the schema can be omitted as follows:
      mydata = DataCache(file='/path/to/people.json')

      # Caching may also be configured to reoccur after a specified number of seconds
      # In this example caching occurs every 30 seconds:
      mydata = DataCache(file='/path/to/people.json',cachetime=30)
  """
  def __init__(self,fields=None,file="",cachetime=0):
    self.FILE = file
    
    if len(file) == 0:
      raise Exception("No cache file provided")
    
    if not exists(file):
      with open(file,'w') as f:
        f.write('[]')
    
    data = str2dict(self.__read_cache())
    
    if not fields:
      if not exists(f"{file}.schema"):
        raise Exception(f"Schema file not found ({file}.schema)")
      
      with open(f"{file}.schema","r") as f:
        fields = str2dict(str("".join(f.readlines())))
    
    if cachetime == 0:
      self.AUTO_CACHE = False
    else:
      self.AUTO_CACHE = True
      self.CACHE_TIME = cachetime
    
    super().__init__(fields,data)
    
    self.__cacheschema()
    
    if not cachetime == 0:
      Timer(self.CACHE_TIME,self.Cache).start()
  
  def AddField(self,fname,ftype):
    super().AddField(fname,ftype)
    self.__cacheschema()
  
  def Insert(self,row={}):
    super().Insert(row)
    if not self.AUTO_CACHE:
      self.Cache()
  
  def Delete(self,q):
    super().Delete(q)
    if not self.AUTO_CACHE:
      self.Cache()
  
  def Update(self,q,updates=[]):
    super().Update(q,updates)
    if not self.AUTO_CACHE:
      self.Cache()
  
  def Cache(self):
    """
      # Manually cache data to JSON file named in the construtor
      mydata.Cache()
      
      # If seconds are provided when DataCache is instantiated this function is called automatically
    """
    filecontent = self.__read_cache()
    datastring = dict2str(self)
    if not filecontent == datastring:
      with open(self.FILE,"w") as f:
        f.write(datastring)
    
    if self.AUTO_CACHE:
      Timer(self.CACHE_TIME,self.Cache).start()
  
  def __cacheschema(self):
    with open(f"{self.FILE}.schema","w") as f:
      f.write(dict2str(self.FIELDS))
  
  def __read_cache(self):
    with open(self.FILE,'r') as f:
      return str(''.join(f.readlines()))
