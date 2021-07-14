import logging
import os
import stat
import subprocess

import flask
import jinja2
import webob

from octavia.amphorae.backends.agent.api_server import listener
from octavia.amphorae.backends.agent.api_server import util
from octavia.common import constants as consts


BUFFER = 1000

LOG = logging.getLogger(__name__)


SYSTEMD_TEMPLATE = os.path.dirname(os.path.realpath(__file__)) + consts.AGENT_API_TEMPLATES + '/' + consts.FILEBEAT_JINJA2_SYSTEMD
filebeat_dir = '/etc/filebeat/'
conf_file = '/etc/filebeat/filebeat.yml'


class Filebeat(object):

    def upload_filebeat_config(self):
        stream = listener.Wrapped(flask.request.stream)

        if not os.path.exists(filebeat_dir):
            os.makedirs(filebeat_dir)

        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        # mode 00644
        mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
        # Ghi file cau hinh filebeat
        with os.fdopen(os.open(conf_file, flags, mode), 'wb') as f:
            b = stream.read(BUFFER)
            while b:
                f.write(b)
                b = stream.read(BUFFER)

        init_system = util.get_os_init_system()

        file_path = util.filebeat_init_path(init_system)

        if init_system == consts.INIT_SYSTEMD:
            template = SYSTEMD_TEMPLATE
            init_enable_cmd = "systemctl enable filebeat"
        else:
            raise util.UnknownInitError()

        if not os.path.exists(file_path):
            with os.fdopen(os.open(file_path, flags, mode), 'w') as text_file:
                with open(template, 'r') as f:
                    text = f.read()
                text_file.write(text)

        # Make sure the new service is enabled on boot
        if init_system != consts.INIT_UPSTART:
            try:
                subprocess.check_output(init_enable_cmd.split(),
                                        stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                LOG.debug('Failed to enable filebeat service: '
                          '%(err)s %(output)s', {'err': e, 'output': e.output})
                return webob.Response(json=dict(
                    message="Error enabling filebeat service",
                    details=e.output), status=500)

        res = webob.Response(json={'message': 'OK'}, status=200)
        res.headers['ETag'] = stream.get_md5()

        return res

    def manager_filebeat_service(self, action):
        action = action.lower()
        if action not in [consts.AMP_ACTION_START,
                          consts.AMP_ACTION_STOP,
                          'restart']:
            return webob.Response(json=dict(
                message='Invalid Request',
                details="Unknown action: {0}".format(action)), status=400)

        if action == consts.AMP_ACTION_START:
            action = 'restart'

        cmd = ("systemctl {action} filebeat".format(
            action=action))

        try:
            subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            LOG.debug('Failed to %s filebeat service: %s %s',
                      action, e, e.output)
            return webob.Response(json=dict(
                message="Failed to {0} filebeat service".format(
                    action), details=e.output), status=500)

        return webob.Response(
            json=dict(message='OK',
                      details='filebeat {action}ed'.format(action=action)),
            status=202)
