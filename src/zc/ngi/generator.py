##############################################################################
#
# Copyright Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################


def handler(func=None, connection_adapter=None):
    if func is None:
        return lambda func: Handler(func, connection_adapter)
    return Handler(func, connection_adapter)

class Handler(object):

    def __init__(self, func, connection_adapter):
        self.func = func
        self.connection_adapter = connection_adapter

    def __call__(self, *args):
        if self.connection_adapter is not None:
            args = args[:-1]+(self.connection_adapter(args[-1]), )
        return ConnectionHandler(self.func(*args), args[-1])

    def __get__(self, inst, class_):
        if inst is None:
            return self

        if self.connection_adapter is not None:
            def connected(connection):
                connection = self.connection_adapter(connection)
                return ConnectionHandler(self.func(inst, connection),
                                         connection)
            return connected

        return (lambda connection:
                ConnectionHandler(self.func(inst, connection), connection)
                )

class ConnectionHandler(object):

    def __init__(self, gen, connection):
        try:
            gen.next()
        except StopIteration:
            return

        self.gen = gen
        connection.setHandler(self)

    def handle_input(self, connection, data):
        try:
            self.gen.send(data)
        except StopIteration:
            connection.close()

    def handle_close(self, connection, reason):
        try:
            self.gen.throw(GeneratorExit, GeneratorExit(reason))
        except (GeneratorExit, StopIteration):
            pass

    def handle_exception(self, connection, exception):
        self.gen.throw(exception.__class__, exception)
