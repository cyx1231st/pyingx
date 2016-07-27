from oslo_config import cfg
from oslo_log import log as logging


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def setup():
    logging.register_options(CONF)
    logging.set_defaults(default_log_levels=logging.get_default_log_levels())
    CONF(['--config-file', '/etc/pyingx/pyingx.conf'],
         project='test_server_conf')
    logging.setup(CONF, 'test_server_log')
