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
				value = field.default()

				#callable 判断是否可调用
				
