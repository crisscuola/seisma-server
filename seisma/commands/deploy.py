# -*- coding: utf-8 -*-

import os
import stat
from multiprocessing import cpu_count

from flask_script import Option
from flask_script import Command

from jinja2 import Environment
from jinja2 import FileSystemLoader

from .. import constants


CMD_OPTIONS = (
    Option(
        '--config', '-c',
        dest='config',
        default=os.getenv(
            constants.CONFIG_ENV_NAME, constants.DEFAULT_CONFIG,
        ),
        help='full path to seisma config file. default "{}"'.format(
            constants.DEFAULT_CONFIG,
        ),
    ),
    Option(
        '--port', '-p',
        type=int,
        dest='port',
        default=constants.DEFAULT_PORT,
        help='port when listen nginx. default "{}"'.format(
            constants.DEFAULT_PORT,
        ),
    ),
    Option(
        '--docs-port',
        type=int,
        dest='docs_port',
        default=0,
        help='port when listen nginx for documentation. default port + 1',
    ),
    Option(
        '--workers', '-w',
        type=int,
        dest='workers',
        default=cpu_count(),
        help='uwsgi workers count. cpu count by default',
    ),
    Option(
        '--nginx-config-folder',
        dest='nginx_config_folder',
        default=constants.DEFAULT_NGINX_CONFIG_FOLDER,
        help='full path to nginx site-enabled directory. default "{}"'.format(
            constants.DEFAULT_NGINX_CONFIG_FOLDER,
        ),
    ),
    Option(
        '--seisma-ui',
        type=str,
        dest='ui_path',
        default=constants.FRONTEND_FOLDER,
        help='Path to seisma ui application',
    ),
)


env = Environment(
    loader=FileSystemLoader(constants.TEMPLATES_FOLDER),
)


def create_initd_file(**options):
    with open(constants.INITD_FILE_PATH, 'w') as f:
        tpl = env.get_template('seisma.tpl')
        f.write(tpl.render(**options))

    st = os.stat(constants.INITD_FILE_PATH)
    os.chmod(constants.INITD_FILE_PATH, st.st_mode | stat.S_IEXEC)


def create_uwsgi_config(config, **options):
    with open(constants.UWSGI_CONFIG_FILE_PATH, 'w') as f:
        tpl = env.get_template('seisma.ini.tpl')
        f.write(tpl.render(config=config, **options))


def create_nginx_config(nginx_config_folder, **options):
    if not os.path.exists(nginx_config_folder):
        raise RuntimeError(
            'nginx config folder is not found. please install nginx.'
            'if you have installed nginx, please check config folder path "{}". '
            'use option "--nginx-config-folder" for change it'.format(nginx_config_folder),
        )

    options.update(
        docs_folder=constants.DOCS_FOLDER,
    )

    with open(os.path.join(nginx_config_folder, constants.NGINX_CONFIG_FILE_NAME), 'w') as f:
        tpl = env.get_template('nginx.conf.tpl')
        f.write(tpl.render(**options))


def install(config, port, docs_port, workers, nginx_config_folder, ui_path):
    docs_port = docs_port if docs_port != 0 else port + 1

    create_initd_file()
    create_nginx_config(
        nginx_config_folder,
        port=port,
        docs_port=docs_port,
        static_path=ui_path,
    )
    create_uwsgi_config(
        config,
        processes=workers,
        pythonpath=constants.PROJECT_ROOT_PATH,
    )


class AutoDeployCommand(Command):
    """
    Install seisma on operating system of linux family.
    """

    option_list = CMD_OPTIONS

    run = staticmethod(install)
