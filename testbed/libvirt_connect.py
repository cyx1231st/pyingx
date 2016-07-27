import eventlet
eventlet.monkey_patch(os=False)

from eventlet import patcher
from eventlet import tpool
import libvirt
import six
import threading

from oslo_log import log as logging
from oslo_config import cfg


native_threading = patcher.original("threading")
native_queue = patcher.original("Queue" if six.PY2 else "queue")

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def init_logs(product="default_project"):
    logging.register_options(CONF)

    CONF.logging_exception_prefix = \
        "%(color)s%(asctime)s.%(msecs)03d " \
        "TRACE %(name)s [01;35m%(instance)s[00m"
    CONF.logging_debug_format_suffix = \
        "[00;33mfrom " \
        "(pid=%(process)d) %(funcName)s %(pathname)s:%(lineno)d[00m"
    CONF.logging_default_format_string = \
        "%(asctime)s.%(msecs)03d %(color)s%(levelname)s %(name)s " \
        "[[00;36m-%(color)s] [01;35m%(instance)s%(color)s%(message)s[00m"
    CONF.logging_context_format_string = \
        "%(asctime)s.%(msecs)03d %(color)s%(levelname)s %(name)s " \
        "[[01;36m%(request_id)s " \
        "[00;36m%(user_name)s %(project_name)s%(color)s] " \
        "[01;35m%(instance)s%(color)s%(message)s[00m"

    logging.set_defaults(default_log_levels=logging.get_default_log_levels())
    logging.setup(CONF, product)


# libvirt utils start >>>
def libvirt_test_conn(conn):
    try:
        conn.getLibVersion()
        return True
    except libvirt.libvirtError as ex:
        if (ex.get_error_code() in (libvirt.VIR_ERR_SYSTEM_ERROR,
                                    libvirt.VIR_ERR_INTERNAL_ERROR) and
            ex.get_error_domain() in (libvirt.VIR_FROM_REMOTE,
                                      libvirt.VIR_FROM_RPC)):
            LOG.warn("libvirt connection broken")
            return False
        raise


def _connect_auth_cb(creds, opaque):
        if len(creds) == 0:
            return 0
        raise RuntimeError(
            "Can not handle authentication request for %d credentials"
            % len(creds))


def libvirt_connect(uri, read_only):
    auth = [[libvirt.VIR_CRED_AUTHNAME,
             libvirt.VIR_CRED_ECHOPROMPT,
             libvirt.VIR_CRED_REALM,
             libvirt.VIR_CRED_PASSPHRASE,
             libvirt.VIR_CRED_NOECHOPROMPT,
             libvirt.VIR_CRED_EXTERNAL],
            _connect_auth_cb,
            None]

    flags = 0
    if read_only:
        flags = libvirt.VIR_CONNECT_RO
    # tpool.proxy_call creates a native thread. Due to limitations
    # with eventlet locking we cannot use the logging API inside
    # the called function.
    return tpool.proxy_call(
        (libvirt.virDomain, libvirt.virConnect),
        libvirt.openAuth, uri, auth, flags)

# libvirt utils end <<<


class LibvirtHost(object):
    def __init__(self, uri, read_only=False):
        self._native_event_queue = None

        self._event_thread = None

        self._uri = None
        self._read_only = read_only
        self._conn = None
        self._conn_lock = threading.Lock()

    def _native_event_lifecycle(self, conn, dom, event, detail, opaque):
        print("Event lifecycle, uuid: %s, event: %s" % (dom.uuid, event))

    def _native_close_callback(self, conn, reason, opaque):
        print("Close, reason: %s" % reason)

    def _native_thread(self):
        """Do not use LOG here!"""
        print("In native thread %s" % native_threading._get_ident())
        while True:
            libvirt.virEventRunDefaultImpl()

    def _dispatch_event(self):
        LOG.info("In green thread %s" % native_threading._get_ident())
        while True:
            eventlet.sleep(5)

    @staticmethod
    def _native_libvirt_error_handler(context, err):
        print("Error: %s" % err)

    def initialize(self):
        # prepare libvirt
        libvirt.registerErrorHandler(self._native_libvirt_error_handler, None)
        libvirt.virEventRegisterDefaultImpl()

        # start native listening thread
        self._native_event_queue = native_queue.Queue()
        self._event_thread = native_threading.Thread(
            target=self._native_thread)
        self._event_thread.setDaemon(True)
        self._event_thread.start()

        # prepare dispatching greenthread
        eventlet.spawn_n(self._dispatch_event)

    def get_connection(self):
        """:returns: a libvirt.virConnect object """
        with self._conn_lock:
            if not self._conn or not libvirt_test_conn(self._conn):
                LOG.info("Get new libvirt connection...")
                try:
                    self._conn = libvirt_connect(self._uri, self._read_only)
                finally:
                    if not self._conn:
                        LOG.warn("Failed to connect to libvirt!")

                try:
                    # NOTE: What is opaque?
                    self._conn.domainEventRegisterAny(
                        None,
                        libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE,
                        self._native_event_lifecycle,
                        self)
                except Exception as e:
                    LOG.warn("URI %(uri)s does not support events: %(error)s" %
                             {'uri': self._uri, 'error': e})

                try:
                    self._conn.registerCloseCallback(
                        self._native_close_callback,
                        None)
                except (TypeError, AttributeError) as e:
                    # NOTE: The registerCloseCallback of python-libvirt 1.0.1+
                    # is defined with 3 arguments, and the above registerClose-
                    # Callback succeeds. However, the one of python-libvirt
                    # 1.0.0 is defined with 4 arguments and TypeError happens
                    # here.  Then python-libvirt 0.9 does not define a method
                    # register- CloseCallback.
                    LOG.warn("The version of python-libvirt does not support "
                             "registerCloseCallback or is too old: %s", e)
                except libvirt.libvirtError as e:
                    LOG.warn("URI %(uri)s does not support connection"
                             " events: %(error)s" %
                             {'uri': self._uri, 'error': e})

        return self._conn

    def get_info(self):
        return self.get_connection().getInfo()


if __name__ == "__main__":
    init_logs(product="libvirt")

    host = LibvirtHost("qemu:///system")
    host.initialize()

    print(host.get_info())

    LOG.info("Start finished..")
    eventlet.hubs.get_hub().switch()
