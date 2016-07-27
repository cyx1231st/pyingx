import eventlet
eventlet.monkey_patch(os=False)
from paste import deploy

from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service


CONF = cfg.CONF
LOG = logging.getLogger(__name__)

logging.register_options(CONF)
logging.set_defaults(default_log_levels=logging.get_default_log_levels())
CONF(['--config-file', '/home/vagrant/test_wsgi/test_server.conf'],
     project='test_server_conf')
logging.setup(CONF, 'test_server_log')

# config
wsgi_group = cfg.OptGroup(
      'wsgi',
      title='WSGI Options')

api_paste_config = cfg.StrOpt(
      'api_paste_config',
      default="api-paste.ini",
      help='File name for the paste.deploy config')
app = cfg.StrOpt(
      'app',
      default="test",
      help='Paste app to load')

CONF.register_group(wsgi_group)
CONF.register_opts([app, api_paste_config], group=wsgi_group)


class Service(service.Service):
    def __init__(self):
        super(Service, self).__init__()
        import pdb; pdb.set_trace()

        # paste
        paste_config = CONF.wsgi.api_paste_config
        app = CONF.wsgi.app
        self.app = deploy.loadapp("config:%s" % paste_config, name=app)

    def start(self):
        LOG.info("Service started")

    def stop(self):
        LOG.info("Service stopped")

    def reset(self):
        LOG.info("Service reset")


if __name__ == "__main__":
    test_server = Service()
    launcher = service.launch(CONF, test_server, workers=1)
    launcher.wait()
