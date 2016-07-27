import eventlet
import eventlet.wsgi
from paste import deploy
import socket

from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


# config
wsgi_group = cfg.OptGroup(
    'wsgi',
    title='WSGI Options')

api_paste_config = cfg.StrOpt(
    'api_paste_config',
    default="/etc/pyingx/api-paste.ini",
    help='File name for the paste.deploy config')

client_socket_timeout = cfg.IntOpt(
    'client_socket_timeout',
    default=900,
    help="Timeout for client connections' socket operations. "
         "If an incoming connection is idle for this number of "
         "seconds it will be closed. A value of '0' means "
         "wait forever.")

app = cfg.StrOpt(
    'app',
    default="pyingx",
    help='Paste app to load')

wsgi_log_format = cfg.StrOpt(
    'wsgi_log_format',
    default='%(client_ip)s "%(request_line)s" status: %(status_code)s'
            ' len: %(body_length)s time: %(wall_seconds).7f',
    help='A python format string that is used as the template to '
         'generate log lines. The following values can be formatted '
         'into it: client_ip, date_time, request_line, status_code, '
         'body_length, wall_seconds.')

tcp_keepidle = cfg.IntOpt(
    'tcp_keepidle',
    default=600,
    help='Sets the value of TCP_KEEPIDLE in seconds for each '
         'server socket. Not supported on OS X.')

default_pool_size = cfg.IntOpt(
    'default_pool_size',
    default=1000,
    help='Size of the pool of greenthreads used by wsgi')

keep_alive = cfg.BoolOpt(
    'keep_alive',
    default=True,
    help='If False, closes the client socket connection explicitly.')

client_socket_timeout = cfg.IntOpt(
    'client_socket_timeout',
    default=900,
    help="Timeout for client connections' socket operations. "
         "If an incoming connection is idle for this number of "
         "seconds it will be closed. A value of '0' means "
         "wait forever.")


CONF.register_group(wsgi_group)
CONF.register_opts([api_paste_config,
                    app,
                    client_socket_timeout,
                    default_pool_size,
                    keep_alive,
                    tcp_keepidle,
                    wsgi_log_format,
                   ],
                   group=wsgi_group)


class Service(service.Service):
    def __init__(self):
        """ Init ONCE in the parent process """
        super(Service, self).__init__()

        self.is_child = False
        # paste
        paste_config = CONF.wsgi.api_paste_config
        app = CONF.wsgi.app
        self._app = deploy.loadapp("config:%s" % paste_config, name=app)
        # pool
        self._pool = eventlet.GreenPool(CONF.wsgi.default_pool_size)
        # logger
        self._logger = logging.getLogger("pyingx.wsgi.server")
        # socket
        info = socket.getaddrinfo('0.0.0.0',
                                  '1314',
                                  socket.AF_UNSPEC,
                                  socket.SOCK_STREAM)
        family = info[0][0]
        bind_addr = info[0][-1]
        self._socket = eventlet.listen(bind_addr,
                                       family=family,
                                       backlog=128)
        (self.host, self.port) = self._socket.getsockname()[0:2]
        LOG.info("pyingx listening on %(host)s:%(port)s",
                 {'host': self.host, 'port': self.port})

    def start(self):
        """ Init in child processes """
        self.is_child = True
        # dupsocket
        dup_socket = self._socket.dup()
        dup_socket.setsockopt(socket.SOL_SOCKET,
                              socket.SO_REUSEADDR, 1)
        # sockets can hang around forever without keepalive
        dup_socket.setsockopt(socket.SOL_SOCKET,
                              socket.SO_KEEPALIVE, 1)

        # This option isn't available in the OS X version of eventlet
        if hasattr(socket, 'TCP_KEEPIDLE'):
            dup_socket.setsockopt(socket.IPPROTO_TCP,
                                  socket.TCP_KEEPIDLE,
                                  CONF.wsgi.tcp_keepidle)
        wsgi_kwargs = {
            'func': eventlet.wsgi.server,
            'sock': dup_socket,
            'site': self._app,
            'protocol': eventlet.wsgi.HttpProtocol,
            'custom_pool': self._pool,
            'log': self._logger,
            'log_format': CONF.wsgi.wsgi_log_format,
            'debug': False,
            'keepalive': CONF.wsgi.keep_alive,
            'socket_timeout': CONF.wsgi.client_socket_timeout
        }
        self._server = eventlet.spawn(**wsgi_kwargs)
        LOG.info("Service started")

    def stop(self):
        if self.is_child:
            self._pool.resize(0)
            self._server.kill()
        LOG.info("Service stopped")

    def reset(self):
        LOG.info("Service reset")

    def wait(self):
        if self.is_child:
            self._pool.waitall()
            self._server.wait()
        LOG.info("Service wait")


def launch():
    test_server = Service()
    launcher = service.launch(CONF, test_server, workers=4)
    launcher.wait()
