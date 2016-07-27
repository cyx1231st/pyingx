from pyingx.api import wsgi


class Versions(wsgi.Resource):
    def index(self, req, body=None):
        return {'version': '1.0', 'author': 'cyx'}
