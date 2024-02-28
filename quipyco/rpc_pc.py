# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 16:45:23 2024

@author: alexi
"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

@app.post("/items/")
async def create_item(item: Item):
    return item

class Client:
    def __init__(self):
        self.__valid_methods = ['i']
        print('hello')
    
    def __getattr__(self, name):
        if name not in self.__valid_methods:
            raise AttributeError

        def proxy(*args, **kwargs):
            return self.__do_rpc(name, args, kwargs)
        return proxy
    def select_rpc_target(self, target_name):
        """Selects a RPC target by name. This function should be called
        exactly once if the object was created with ``target_name=None``."""
        target_name = _validate_target_name(target_name, self.__target_names)
        self.__socket.sendall((target_name + "\n").encode())
        self.__selected_target = target_name
        self.__valid_methods = self.__recv()

    def get_selected_target(self):
        """Returns the selected target, or ``None`` if no target has been
        selected yet."""
        return self.__selected_target

    def get_rpc_id(self):
        """Returns a tuple (target_names, description) containing the
        identification information of the server."""
        return (self.__target_names, self.__description)

    def get_local_host(self):
        """Returns the address of the local end of the connection."""
        return self.__socket.getsockname()[0]

    def close_rpc(self):
        """Closes the connection to the RPC server.

        No further method calls should be done after this method is called.
        """
        self.__socket.close()

    def __send(self, obj):
        line = pyon.encode(obj) + "\n"
        self.__socket.sendall(line.encode())

    def __recv(self):
        line = _socket_readline(self.__socket)
        return pyon.decode(line)
    
    def __do_action(self, action):
        self.__send(action)

        obj = self.__recv()
        if obj["status"] == "ok":
            return obj["ret"]
        elif obj["status"] == "failed":
            raise_packed_exc(obj["exception"])
        else:
            raise ValueError
        pass

    def __do_rpc(self, name, args, kwargs):
        obj = {"action": "call", "name": name, "args": args, "kwargs": kwargs}
        return self.__do_action(obj)

def _validate_target_name(target_name, target_names):
    if target_name is AutoTarget:
        if len(target_names) > 1:
            raise ValueError("Server has multiple targets: " +
                             " ".join(sorted(target_names)))
        else:
            target_name = target_names[0]
    elif target_name not in target_names:
        raise IncompatibleServer(
            "valid target name(s): " + " ".join(sorted(target_names)))
    return target_name


def _socket_readline(socket, bufsize=4096):
    buf = socket.recv(bufsize).decode()
    offset = 0
    while buf.find("\n", offset) == -1:
        more = socket.recv(bufsize)
        if not more:
            break
        buf += more.decode()
        offset += len(more)

    return buf