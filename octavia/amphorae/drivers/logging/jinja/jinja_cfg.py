# Copyright 2015 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

import jinja2
from oslo_config import cfg
import six

from octavia.amphorae.backends.agent.api_server import util
from octavia.common import constants


FILEBEAT_TEMPLATE = os.path.abspath(
    os.path.join(os.path.dirname(__file__),
                 'templates/filebeat_base.template'))
CONF = cfg.CONF


class FilebeatJinjaTemplater(object):

    def __init__(self, filebeat_template=None):
        """Keepalived configuration generation

        :param filebeat_template: Absolute path to filebeat Jinja template
        """
        super(FilebeatJinjaTemplater, self).__init__()
        self.filebeat_template = (filebeat_template if
                                  filebeat_template else
                                  FILEBEAT_TEMPLATE)
        self._jinja_env = None

    def get_template(self, template_file):
        """Returns the specified Jinja configuration template."""
        if not self._jinja_env:
            template_loader = jinja2.FileSystemLoader(
                searchpath=os.path.dirname(template_file))
            self._jinja_env = jinja2.Environment(
                autoescape=True,
                loader=template_loader,
                trim_blocks=True,
                lstrip_blocks=True)
        return self._jinja_env.get_template(os.path.basename(template_file))

    def build_filebeat_config(self, loadbalancer, filebeat_config):
        """Renders the loadblanacer filebeat for amphora

        :param loadbalancer: A loadbalancer object
        :param filebeat_config: Filebeat config object
        """
        return self.get_template(self.filebeat_template).render(
            {'logstash_host': filebeat_config['logstash_host'],
             'loadbalancer_id': loadbalancer.id},
            constants=constants)
