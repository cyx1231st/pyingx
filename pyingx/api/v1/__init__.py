import stevedore

from pyingx.api import wsgi


class Extension(object):
    name = None
    alias = None
    collection_actions = {}
    member_actions = {}
    def __init__(self, extension_info):
        self._extension_info = extension_info
        self._set_alias()

    def is_valid(self):
        return True

    @classmethod
    def _set_alias(cls):
        pass

class RouterV1(wsgi.Router):
    def __init__(self):
        super(RouterV1, self).__init__()
        self._extension_info = {}

        def _register_extension(ext):
            ext = ext.obj
            if not ext.is_valid():
                return False
            if ext.name in self._extension_info:
                raise RuntimeError("Duplicated extension name: %s!" % ext.name)
            self._extension_info[ext.name] = ext
            return True

        self._api_extension_manager = stevedore.enabled.EnabledExtensionManager(
                namespace='pyingx.api.v1',
                check_func=_register_extension,
                invoke_on_load=True,
                invoke_kwds={'extension_info': self._extension_info})

        def _map_extension(ext):
            ext = ext.obj
            self.map.resource(ext.alias, ext.alias,
                              controller=ext,
                              collection=ext.collection_actions,
                              member=ext.member_actions)

        self._api_extension_manager.map(_map_extension)
