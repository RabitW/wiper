#!/usr/bin/env python
#-*- coding: UTF-8 -*-

'''
Wiper, an assistant tool for web penetration test.
Copyright (c) 2014-2015 alpha1e0
See the file COPYING for copying detail
'''

import re
import json
import threading

from dbmanage import DBManage, SQLExec, SQLQuery, escapeString
from config import RTD, WIPError, Dict


class FieldError(WIPError):
	def __init__(self, reason):
		self.errMsg = "FieldError. " + ("reason: "+reason if reason else "")

	def __str__(self):
		return self.errMsg


class ModelError(WIPError):
	def __init__(self, reason):
		self.errMsg = "ModelError. " + ("reason: "+reason if reason else "")

	def __str__(self):
		return self.errMsg


class Field(object):
	'''
	The base class of field.
	The filed attribute includes:
		name: the name of the Field 
		primarykey: True | False; the primarykey
		notnull: True | False; it means the 
		vrange: m-n; for string it means the length range, for integer it means the value range
		ddl: varchar(255)
		default: the default value
	'''
	def __init__(self, **kwargs):
		self.name = kwargs.get("name", None)
		self.primarykey = kwargs.get("primarykey", False)
		self.notnull = kwargs.get("notnull", False)
		self.default = kwargs.get("default", None)
		self.ddl = kwargs.get("ddl", None)
		self.vrange = kwargs.get("vrange", None)

		vrange = kwargs.get("vrange", None)
		if vrange:
			try:
				vrange = [int(n) for n in vrange.split("-")]
			except ValueError:
				raise FieldError("attribute {0} define error".format(vrange))
			if vrange[0] > vrange[1]:
				raise FieldError("attribute {0} define error".format(vrange))
			else:
				self.vrange = vrange

	def inputCheck(self, strValue):
		return True

	def inputFormat(self, strValue):
		'''
		The input data is a string, here format the input date to specified type.
			for example, the IntegerField().format("123") will format the string "123" to integer 123
		If failed, raise FieldError.
		'''
		return strValue


class IntegerField(Field):
	def __init__(self, **kwargs):
		super(IntegerField, self).__init__(**kwargs)

	def inputFormat(self, strValue):
		if not strValue:
			if self.default: 
				strValue = self.default
			if self.notnull: 
				raise FieldError("the integer field '{0}' must not null".format(self.name))
			else:
				return strValue

		try:
			ret = int(strValue)
		except ValueError:
			raise FieldError("the integer field value '{0}' format error".format(strValue))
		if self.vrange:
			if ret<self.vrange[0] or ret>self.vrange[1]:
				raise FieldError("the integer field value '{0}' out of range".format(strValue))
			else:
				return str(ret)
		else:
			return str(ret)


class FloatField(Field):
	def __init__(self, **kwargs):
		super(FloatField, self).__init__(**kwargs)

class BooleanField(Field):
	def __init__(self, **kwargs):
		super(BooleanField, self).__init__(**kwargs)


class StringField(Field):
	def __init__(self, **kwargs):
		super(StringField, self).__init__(**kwargs)

	def inputFormat(self, strValue):
		if not strValue:
			if self.default:
				strValue = self.default
			if self.notnull:
				raise FieldError("the string field '{0}' must not null".format(self.name))
			else:
				return strValue

		ret = escapeString(strValue)
		if self.vrange:
			retLen = len(ret)
			if retLen<self.vrange[0] or retLen>self.vrange[1]:
				raise FieldError("the length of the string field value '{0}' out of range".format(strValue))
			else:
				return ret
		else:
			return ret


class TextField(Field):
	def __init__(self, **kwargs):
		super(TextField, self).__init__(**kwargs)


class UrlField(StringField):
	def __init__(self, **kwargs):
		super(UrlField, self).__init__(**kwargs)

	def inputFormat(self, strValue):
		if not strValue:
			if self.default:
				strValue = self.default
			if self.notnull:
				raise FieldError("the url field '{0}' must not null".format(self.name))
			else:
				return strValue

		urlPattern = re.compile(r"^(?:http(?:s)?\://)?((?:[-0-9a-zA-Z_]+\.)+(?:[-0-9a-zA-Z_]+)(?:\:\d+)?.*)")
		match = urlPattern.match(strValue)
		if not match:
			raise FieldError("the url field value '{0}' format error".format(strValue))
		else:
			return match.groups()[0]


class IPField(StringField):
	def __init__(self, **kwargs):
		super(IPField, self).__init__(**kwargs)

	def inputFormat(self, strValue):
		if not strValue:
			if self.default:
				strValue = self.default
			if self.notnull:
				raise FieldError("the IP field '{0}' must not null".format(self.name))
			else:
				return strValue

		ipPattern = re.compile(r"^((?:(?:(?:2[0-4]\d)|(?:25[0-5])|(?:[01]?\d\d?))\.){3}(?:(?:2[0-4]\d)|(?:25[0-5])|(?:[01]?\d\d?))(?:\:\d+)?)$")
		match = ipPattern.match(strValue)
		if not match:
			raise FieldError("the IP field value '{0}' format error".format(strValue))
		else:
			return match.groups()[0]


class EmailField(StringField):
	def __init__(self, **kwargs):
		super(EmailField, self).__init__(**kwargs)

	def inputFormat(self, strValue):
		if not strValue:
			if self.default:
				strValue = self.default
			if self.notnull:
				raise FieldError("the email field '{0}' must not null".format(self.name))
			else:
				return strValue

		emailPattern = re.compile(r"^((?:[-0-9a-zA-Z_!=:.%+])+@(?:[-0-9a-zA-Z_!=:]+\.)+(?:[-0-9a-zA-Z_!=:]+))$")
		match = emailPattern.match(strValue)
		if not match:
			raise FieldError("the email field value '{0}' format error".format(strValue))
		else:
			return match.groups()[0]


class ModelMetaClass(type):
	'''
	The Metaclass will scan the attributes of the class and get some useful information.
	'''
	def __new__(cls, name, bases, attrs):
		if name == "Model" or name == "Database":
			return type.__new__(cls, name, bases, attrs)

		if "_table" not in attrs:
			raise ModelError("model {0} error, attribute '_table' not specified".format(name))

		mapping = dict()
		primaryKey = False
		notnulls = dict()
		for key,value in attrs.iteritems():		
			if isinstance(value, Field):
				if not value.name:
					value.name = key
				if value.primarykey:
					if not primaryKey:
						primaryKey = value
					else:
						raise ModelError("model {0} error, duplicate primary key".format(name))
				mapping[key] = value
		if not primaryKey:
			raise ModelError("model {0} error, primary key not found.".format(name))
			
		for key in mapping:
			attrs.pop(key)

		attrs['_mapping'] = mapping
		attrs['_primaryKey'] = primaryKey

		return type.__new__(cls, name, bases, attrs)


class Model(Dict):
	'''
	Base class for ORM.
	'''

	__metaclass__ = ModelMetaClass

	_status = threading.local()


	@classmethod
	def sqlexec(cls, sqlCmd):
		'''
		Execute sql command direct.
		'''
		with DBManage() as con:
			return con.sql(sqlCmd)

	@classmethod
	def sqlquery(cls, sqlCmd):
		'''
		Execute select query direct.
		'''
		with DBManage() as con:
			return con.query(sqlCmd)


	@classmethod
	def where(cls, **kwargs):
		'''
		Set the 'where' part of the SQL command. 
		'''
		if not kwargs:
			return cls
		params = cls._paramFormat(kwargs)
		strList = ["{0}='{1}'".format(k,v) for k,v in params.iteritems()]
		cls._status.where = "where " + " and ".join(strList)
		return cls

	@classmethod
	def strWhere(cls):
		try:
			return cls._status.where
		except AttributeError:
			cls._status.where = ""
			return ""

	@classmethod
	def orderby(cls, orderby=1):
		'''
		Set the 'order by' part of the SQL command. 
		'''
		cls._status.orderby = "order by {0}".format(orderby)
		return cls

	@classmethod
	def strOrderby(cls):
		try:
			return cls._status.orderby
		except AttributeError:
			cls._status.orderby = ""
			return ""

	@classmethod
	def _clearStatus(cls):
		cls._status.orderby = ""
		cls._status.where = ""


	@classmethod
	def _paramFormat(cls, params):
		if not params:
			return False

		ret = dict()
		for key,value in params.iteritems():
			try:
				tmpValue = cls._mapping[key].inputFormat(value)
			except KeyError:
				raise ModelError("model {0} error, the model did not have key '{1}'".format(cls.__class__.__name__, key))
			else:
				ret[key] = tmpValue

		return ret


	@classmethod
	def get(cls, pvalue, *args):
		'''
		User primary key to select from database, return a model object.
		'''
		if args:
			columns = ",".join(args)
		else:
			columns = "*"

		pvalue = cls._primaryKey.inputFormat(pvalue)
		sqlCmd = "select * from {table} where {key}={value}".format(table=cls._table,key=cls._primaryKey.name,value=pvalue)
		cls._clearStatus()

		result = cls.sqlquery(sqlCmd)
		if result:
			obj = cls(**result[0])
			return obj


	@classmethod
	def gets(cls, *args):
		'''
		Select from database, return a list of model object
		Example: 
			User.where(name='aa').gets('name','ip','url') will returns: [User(),User()]
			User.gets() will return all the rows
		'''
		if args:
			columns = ",".join(args)
		else:
			columns = "*"

		sqlCmd = "select {col} from {table} {where} {orderby}".format(col=columns,table=cls._table,where=cls.strWhere(),orderby=cls.strOrderby())
		cls._clearStatus()

		result = cls.sqlquery(sqlCmd)
		ret = list()
		for line in result:
			obj = cls(**line)
			ret.append(obj)

		return ret


	@classmethod
	def getraw(cls, pvalue, *args):
		'''
		User primary key to select from database, return a row from the database.
		'''
		if args:
			columns = ",".join(args)
		else:
			columns = "*"

		pvalue = cls._primaryKey.inputFormat(pvalue)
		sqlCmd = "select * from {table} where {key}={value}".format(table=cls._table,key=cls._primaryKey.name,value=pvalue)
		cls._clearStatus()

		result = cls.sqlquery(sqlCmd)
		if result:
			return result[0]


	@classmethod
	def getsraw(cls, *args):
		'''
		Select from database, return a list of rows.
		Example: 
			User.where(name='aa').getsraw('name','ip','url') will returns: [{name:'aa',id=1},{name:'bb',id=2}]
			User.getsraw() will return all the rows
		'''
		if args:
			columns = ",".join(args)
		else:
			columns = "*"

		sqlCmd = "select {col} from {table} {where} {orderby}".format(col=columns,table=cls._table,where=cls.strWhere(),orderby=cls.strOrderby())
		cls._clearStatus()

		return cls.sqlquery(sqlCmd)


	@classmethod
	def insert(cls, **kwargs):
		'''
		Insert a row to the database.
		Example: User.insert(name='aa',ip='1.1.1.1',url='test.com')
		'''
		if not kwargs:
			return False

		params = cls._paramFormat(kwargs)
		keys = ",".join([k for k in params])
		values = ",".join(["'"+str(params[k] if params[k] else "")+"'" for k in params])

		sqlCmd = "insert into {table}({keys}) values({values})".format(table=cls._table,keys=keys,values=values)
		
		return cls.sqlexec(sqlCmd)


	@classmethod
	def inserts(cls, rows):
		'''
		Insert some rows to the database.
		Param:
			rows: a list of dict which contains the data
		Example: User.inserts([{'name':'aa','ip','1.1.1.1','url':'test.com'},{'name':....}])
		'''
		if not rows:
			return False

		sqlCmdList = list()
		for row in rows:
			params = cls._paramFormat(row)
			keys = ",".join([k for k in params])
			values = ",".join(["'"+str(params[k] if params[k] else "")+"'" for k in params])

			sqlCmdList.append("insert into {table}({keys}) values({values})".format(table=cls._table,keys=keys,values=values))

		for sqlCmd in sqlCmdList:
			cls.sqlexec(sqlCmd)


	@classmethod
	def update(cls, **kwargs):
		'''
		Update a row.
		Example: User.where(id=100).update(name='bb',ip='2.2.2.2')
		'''
		if not kwargs:
			return False

		params = cls._paramFormat(kwargs)
		setValue = [k+"='"+str(v if v else "")+"'" for k,v in params.iteritems()]
		setValue = ",".join(setValue)

		sqlCmd = "update {table} set {setvalue} {where}".format(table=cls._table,setvalue=setValue,where=cls.strWhere())
		cls._clearStatus()
		
		return cls.sqlexec(sqlCmd)


	@classmethod
	def delete(cls, pvalue=None):
		'''
		Delete rows from database.
		Example:
			User.delete(10) will delete row where primary key is 10
			User.where(name='aa').delete() while delete rows where name is 'aa'
		'''
		if pvalue:
			pvalue = cls._primaryKey.inputFormat(pvalue)
			sqlCmd = "delete from {table} where {key}={value}".format(table=cls._table,key=cls._primaryKey.name,value=pvalue)
		else:
			sqlCmd = "delete from {table} {where}".format(table=cls._table,where=cls.strWhere())
			cls._clearStatus()

		return cls.sqlexec(sqlCmd)


	def save(self, update=False):
		'''
		Save current object, will insert a row into database.
		Exaple:
			u=User(name='aa')
			u.save()

			u=User.get(10)
			u.name='bb'
			u.save(update=True)
		'''
		if not update:
			params = self._paramFormat(self)
			keys = ",".join([k for k in params])
			values = ",".join(["'"+str(params[k] if params[k] else "")+"'" for k in params])
			sqlCmd = "insert into {table}({keys}) values({values})".format(table=self._table,keys=keys,values=values)
		else:
			params = self._paramFormat(self)
			print "debug",params
			setValue = [k+"='"+str(v if v else "")+"'" for k,v in params.iteritems() if k!=self._primaryKey.name]
			setValue = ",".join(setValue)
			where = "where " + "{key}={value}".format(key=self._primaryKey.name,value=self[self._primaryKey.name])
			sqlCmd = "update {table} set {setvalue} {where}".format(table=self._table,setvalue=setValue,where=where)

		return self.sqlexec(sqlCmd)


	def remove(self):
		'''
		Remove current object, will delete a row from database.
		'''
		sqlCmd = "delete from {table} where {key}={value}".format(table=self._table,key=self._primaryKey.name,value=self[self._primaryKey.name])

		return self.sqlexec(sqlCmd)


	def toJson(self):
		return json.dumps(self)


	def getVal(self, key, default=None):
		'''
		Get value from key, when key is not in model return default. like dict.get()
		'''
		try:
			return self[key]
		except KeyError:
			return default


	@classmethod
	def create(cls):
		'''
		Create table.
		'''
		pass










