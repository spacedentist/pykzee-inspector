import asyncio
import functools
import inspect
import json
import logging
import os
import pkg_resources
import traceback

import aiohttp.web
from pyimmutable import ImmutableDict, ImmutableList

from pykzee.core.Plugin import Plugin
from pykzee.core.common import makePath, pathElementToString, call_soon

resources_path = pkg_resources.resource_filename(__name__, "resources")


class InspectorPlugin(Plugin):
    def init(self, config):
        self.__port = config.get("port", 8000)
        self.__host = config.get("host")
        self.__shutdownEvent = asyncio.Event()
        self.__count = 0
        self.updateCount(0)
        call_soon(self.__taskImpl)

    def shutdown(self):
        self.__shutdownEvent.set()

    async def __taskImpl(self):
        self.app = makeApp(self)
        self.app_runner = aiohttp.web.AppRunner(self.app)
        await self.app_runner.setup()
        self.site = aiohttp.web.TCPSite(
            self.app_runner,
            host=self.__host,
            port=self.__port,
            shutdown_timeout=0,
        )
        try:
            await self.site.start()
            await self.__shutdownEvent.wait()
        finally:
            await self.app.shutdown()
            await self.site.stop()
            await self.app_runner.cleanup()

    async def stateHandler(self, request):
        ws = aiohttp.web.WebSocketResponse()
        conn = InspectorConnection(ws.send_str, self)
        await ws.prepare(request)

        self.updateCount(1)

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        await conn.process_message(msg.json())
                    except Exception as ex:
                        logging.error("EXCEPTION {0!r}".format(ex))
                        traceback.print_exc()
                        await ws.close()
                        break
                else:
                    if msg.type == aiohttp.WSMsgType.ERROR:
                        logging.info(
                            "ws connection closed with exception {}".format(
                                ws.exception()
                            )
                        )
                    else:
                        logging.warn(
                            "ws received msg type {0!r}".format(msg.type)
                        )
                    await ws.close()
                    break

            return ws
        finally:
            self.updateCount(-1)

    def updateCount(self, x):
        self.__count += x
        self.set((), ImmutableDict(connectionCount=self.__count))


def makeApp(plugin):
    app = aiohttp.web.Application()
    app.router.add_get("/", staticFileHandler("index.html"))
    app.router.add_static("/static/", os.path.join(resources_path, "static"))
    app.router.add_get("/state", plugin.stateHandler)
    return app


class InspectorConnection:
    def __init__(self, sendmsg, plugin):
        self.sendmsg = sendmsg
        self.plugin = plugin
        self.subscriptions = {}
        self.sendQueue = asyncio.Queue()
        self.sendTask = asyncio.create_task(self.sendTaskImpl())

    def subscribe(self, pathstr):
        if pathstr in self.subscriptions:
            return
        path = makePath(pathstr)
        unsubscribe = self.plugin.subscribe(
            functools.partial(self.update, pathstr),
            path,
            ("core", "commands", pathstr),
        )
        self.subscriptions[pathstr] = Subscription(unsubscribe)

    def unsubscribe(self, pathstr):
        sub = self.subscriptions.pop(pathstr, None)
        if sub:
            sub.unsubscribe()

    def update(self, pathstr, new_state, commands):
        if type(new_state) not in (ImmutableDict, ImmutableList):
            return self.unsubscribe(pathstr)
        sub = self.subscriptions.get(pathstr)
        if not sub:
            return

        summary = summarize(pathstr, new_state, commands)
        if sub.state == summary:
            return
        sub.state = summary
        self.sendQueue.put_nowait(
            f'{{"subscription":{ json.dumps(pathstr) },"state":{ summary}}}'
        )

    async def process_message(self, msg):
        subscribe = msg.get("subscribe")
        if subscribe:
            self.subscribe(subscribe)
        unsubscribe = msg.get("unsubscribe")
        if unsubscribe:
            self.unsubscribe(unsubscribe)
        command = msg.get("command")
        if command:
            id = int(msg["id"])

            def send_response(key, value, more=""):
                self.sendQueue.put_nowait(
                    f'{{"id":{id},"{key}":{value}{more}}}'
                )

            try:
                path = makePath(str(msg["path"]))
                args = msg.get("args", ())
                kwargs = msg.get("kwargs", {})
                func = self.plugin.command(path, command)
            except Exception:
                traceback.print_exc()
                return send_response("error", '"Invalid path/command"')
            try:
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
            except Exception as ex:
                return send_response("error", json.dumps(repr(ex)))

            async def makeCall():
                try:
                    result = func(*bound.args, **bound.kwargs)
                    if inspect.isawaitable(result):
                        result = await result
                except Exception as ex:
                    return send_response(
                        "error",
                        json.dumps(repr(ex)),
                        f',"tb":{ json.dumps(traceback.format_exc()) }',
                    )
                try:
                    result = json.dumps(result)
                except Exception as ex:
                    return send_response("error", json.dumps(repr(ex)))
                else:
                    return send_response("result", result)

            asyncio.create_task(makeCall())

    async def sendTaskImpl(self):
        while True:
            msg = await self.sendQueue.get()
            await self.sendmsg(msg)


def summarize(pathstr, state, commands):
    if type(state) is ImmutableDict:
        items = (
            ({"key": key}, value)
            for key, value in sorted(state.items(), key=lambda x: x[0])
        )
    else:
        items = (({}, value) for value in state)
    result = []
    if commands:
        for name, info in sorted(commands.items(), key=lambda x: x[0]):
            result.append(dict(info, command=name))
    for idx, (d, item) in enumerate(items):
        if type(item) in (ImmutableDict, ImmutableList):
            if type(state) is ImmutableDict:
                d["path"] = (
                    f"{ pathstr.rstrip('/') }/"
                    f"{ pathElementToString(d['key']) }"
                )
            else:
                d["path"] = f"{ pathstr.rstrip('/') }/[{ idx }]"
            if type(item) is ImmutableDict:
                d["symbols"] = "{", "}"
            else:
                d["symbols"] = "[", "]"
            d["items"] = len(item)
        else:
            d["value"] = item
        result.append(d)
    return json.dumps(result, sort_keys=True)


class Subscription:
    __slots__ = "unsubscribe", "state"

    def __init__(self, unsubscribe):
        self.unsubscribe = unsubscribe
        self.state = None


def staticFileHandler(filename):
    path = os.path.join(resources_path, filename)

    async def handler(request):
        return aiohttp.web.FileResponse(path)

    return handler
