from oslo_log import log as logging
import six

from octavia.amphorae.drivers import driver_base
from octavia.amphorae.drivers.logging.jinja import jinja_cfg
from octavia.common import constants
from oslo_config import cfg


LOG = logging.getLogger(__name__)
API_VERSION = constants.API_VERSION

CONF = cfg.CONF


class FilebeatAmphoraDriverMixin(driver_base.LoggingDriverMixin):
    def __init__(self):
        super(FilebeatAmphoraDriverMixin, self).__init__()

        # The Mixed class must define a self.client object for the
        # AmphoraApiClient

    def update_logging_config(self, loadbalancer):
        """
        Update Logging config
        
        :param loadbalancer: loadbalancer object
        """
        templater = jinja_cfg.FilebeatJinjaTemplater()
        LOG.debug('Update loadblanacer %s amphora Filebeat config', loadbalancer.id)

        filebeat_config = {
            'logstash_host': CONF.filebeat.logstash_host,
            'loadbalancer_id': loadbalancer.id
            #'logstash_host': '10.10.10.10:5044',
        }
        for amp in six.moves.filter(
            lambda amp: amp.status == constants.AMPHORA_ALLOCATED,
                loadbalancer.amphorae):
            # Generate Filebeat configuration from loadbalancer object
            config = templater.build_filebeat_config(loadbalancer, filebeat_config)
            self.client.upload_filebeat_config(amp, config)

    def start_logging_service(self, loadbalancer):
        """
        Start logging service

        :param loadbalancer: loadbalancer object
        """
        LOG.info("Start loadbalancer %s amphora Logging Service.",
                 loadbalancer.id)
        for amp in six.moves.filter(
            lambda amp: amp.status == constants.AMPHORA_ALLOCATED,
                loadbalancer.amphorae):
            self.client.start_filebeat(amp)

    def stop_logging_service(self, loadbalancer):
        """
        Stop logging service

        :param loadbalancer: loadbalancer object
        """
        LOG.info("Stop loadbalancer %s amphora Logging Service.",
                 loadbalancer.id)
        for amp in six.moves.filter(
            lambda amp: amp.status == constants.AMPHORA_ALLOCATED,
                loadbalancer.amphorae):
            self.client.stop_filebeat(amp)


    def reload_logging_service(self, loadbalancer):
        """
        Reload logging service

        :param loadbalancer: loadbalancer object
        """
        LOG.info("Restart loadbalancer %s amphora Logging Service.",
                 loadbalancer.id)
        for amp in six.moves.filter(
            lambda amp: amp.status == constants.AMPHORA_ALLOCATED,
                loadbalancer.amphorae):
            self.client.restart_filebeat(amp)
