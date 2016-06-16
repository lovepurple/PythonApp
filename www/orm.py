# -*- coding: utf-8 -*-

'''

global x 变量是全局的

关于函数的参数 
	*argv 表示的是Tuple （1,2,3,4）形式的
	**agrv 表示的是一个Dictionary (a=1,b=2,c=3) 形式

'''

import asyncio,logging

#mysql 的连接驱动
import aiomysql	

#数据库连接池
@asyncio.coroutine
def create_pool(loop,**kw):
	logging.info("create database connection pool ....")

	#__pool 是全局的
	global __pool

	#协程
	__pool = yield from aiomysql.create_pool(
			#kw是一个dictionary, get(key,defaultValue)
			
			#配置连接mysql
			host = kw.get('host','localhost')
			port = kw.get('port',3306)
			user = kw.get('user')
			password = kw.get('password')
			db = kw.get('db_pythonapp')
			charset = kw.get('charset','utf8')
			autocommit = kw.get('autocommit',True)
			maxsize = kw.get('maxsize',10)
			minsize = kw.get('minsize',1)
			loop = loop
		)


@asyncio.coroutine
def select(sql,args,size=None):
	logging.info(sql,args)

	#使用上方定义的pool
	global __pool

	#with 自动释放资源,连接属于资源
	#yield from 是协程操作，使用yield from 都是异步的操作，比如sql 的查询
	with (yield from __pool) as conn:
		cur = yield from conn.cursor(aiomysql.DictCursor)
		yield from cur.execute(sql.replace('?',"%s"),args or ())

		if size:
			rs = yield from cur.fetchmany(size)
		else:
			rs = yield from cur.fetchall()
		logging.info("rows returned: %s"%len(rs))
		return rs

@asyncio.coroutine
def execute(sql,args):
	logging.info(sql,args)
	with (yield from __pool) as conn:
		try:
			cur = yield from conn.cursor()
			yield from cur.execute(sql.replace('?','%s'),args)
			affectedrows = cur.rowcount
		except BaseException as e:
			raise
		return affectedrows


#orm的field，Model支持

class Model(dict,metaclass=ModelMetaclass):

	def __init__(self,**kw):
		super(Model,self).__init__(**kw)

	def __getattr__(self,key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError("Model object has no attribute '%s'" %key)

	def __setattr__(self,key,value):
		self[key] = value

	def getValue(self,key):
		return getattr(self,key,None)

	def getValueOrDefault(self,key):
		value = getattr(self,key,None)
		if value is None:
			field = self.__mappings__[key]
			if field.default is not None:
				#callable 判断是否可调用 (field.default 是不是一个方法)
				#下面的写法 跟 ? : 三目运算符一致 Python 里没有三目运算符
				value = field.default() if callable(field.defau) else field.default
				logging.info("using default value for %s:%s"%(key,str(value)))

		return value;
				
				
#各种Field

#Field基类
class Field(object):

	def __init__(self,name,colum_type,primary_key,default):
		self.name = name
		self.colum_type = colum_type
		self.primary_key = primary_key
		self.default = default

	#__str__作用相当于(ToString, 打印类的信息)
	def __str__(self):
		return "<%s,%s,%s>"%(self.__class__.__name__,self.colum_type,self.name)

class StringField(Field):

	def __init__(self,name=None,primary_key = False,default=None,dll='varchar(100)'):
		super().__init__(name,dll,primary_key,default)

class ModelMetaclass(type):

	def __new__(cls,name,bases,attrs):

		if name =='Model':
			return type.__new__(cls,name,bases,attrs)

		tableName = attrs.get("__table__",None) or name

		mappings = dict()
		fields = []
		primaryKey = None

		#attrs 是type的属性 相当于PropertyInfos
		for k,v in attrs.items():
			if isinstance(v,Field):
				mappings[k] = v
				if v.primary_key:
					#主键重复
					if primaryKey:
						raise RuntimeError('Duplicate primary key for field:%s'%k)
					primaryKey = k;
				else:
					fields.append(k)

		if not primaryKey:
			raise RuntimeError("Primary Key not found")

		for k in mappings.keys():
			attrs.pop(k)

		escaped_fields=list(map(lambda f:"%s"%f,fields))

		attrs['__mappings__'] = mappings
		attrs['__table__']=tablename
		


