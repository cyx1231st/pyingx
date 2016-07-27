from pyingx.api.v1 import Extension
from pyingx.api import wsgi


class Test(Extension, wsgi.Resource):
    name = "test"
    alias = "test"
    def index(self, req):
        return {'version': '1.0', 'author': 'cyx'}
