# -*- coding: utf-8 -*-

"""Http服务器入口
    使用的是asyncio

    使用# -*- coding: utf-8 -*-  中文问题

    aiohttp:
    	1.基于协程的异步模式，不能调用普通同步IO操作,所有用户都是由一个线程服务
    	2.耗时的IO不能在协程中以同步的方式调用
    	3.使用异步，每一层操作必须都是异步
"""

__author__="guangze song"

import logging
logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time
from datetime import datetime

from aiohttp import web

def index(request):
	return web.Response(body=b'<h1>Awesome</h1>')

@asyncio.coroutine
def init(loop):
	app = web.Application(loop=loop)

	#接受get请求，处理方法是上方定义的index
	app.router.add_route('GET','/',index)
	srv = yield from loop.create_server(app.make_handler(),"127.0.0.1",65530)
	logging.info("server started.... at port :65530")
	return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()