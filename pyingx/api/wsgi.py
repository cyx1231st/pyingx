import routes
import routes.middleware
import webob.dec

from oslo_serialization import jsonutils


class Application(object):
    @classmethod
    def factory(cls, global_config, **local_config):
        return cls(**local_config)

    @webob.dec.wsgify
    def __call__(self, req):
        # Without webob: __call__(self, environ, start_response):
        raise NotImplementedError(_('You must implement __call__'))

class APIMapper(routes.Mapper):
    def routematch(self, url=None, environ=None):
        #if url == "":
            #result = self._match("", environ)
            #return result[0], result[1]
        return routes.Mapper.routematch(self, url, environ)

    def connect(self, *args, **kargs):
        # NOTE(vish): Default the format part of a route to only accept json
        #             and xml so it doesn't eat all characters after a '.'
        #             in the url.
        #kargs.setdefault('requirements', {})
        #if not kargs['requirements'].get('format'):
            #kargs['requirements']['format'] = 'json|xml'
        return routes.Mapper.connect(self, *args, **kargs)

class Router(Application):
    def __init__(self):
        self.map = APIMapper()
        self._router = routes.middleware.RoutesMiddleware(self._dispatch,
                                                          self.map)
    @staticmethod
    @webob.dec.wsgify
    def _dispatch(req):
        match = req.environ['wsgiorg.routing_args'][1]
        if not match:
            return webob.exc.HTTPNotFound()
        app = match['controller']
        return app

    @webob.dec.wsgify
    def __call__(self, req):
        return self._router


class Resource(Application):
    @webob.dec.wsgify
    def __call__(self, req):
        import pdb; pdb.set_trace()
        args = req.environ['wsgiorg.routing_args'][1].copy()
        del args['controller']
        try:
            del args['format']
        except KeyError:
            pass
        action = args.pop('action', None)

        content_type = req.content_type
        body = req.body
        accept = 'application/json'

        resp = self.index(req)

        body = jsonutils.dumps(resp)
        resp = webob.Response(body=body)
        resp.headers['Content-Type'] = 'application/json'
        return resp
