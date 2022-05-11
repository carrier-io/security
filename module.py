#!/usr/bin/python3
# coding=utf-8

#   Copyright 2021 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

""" Module """

from pylon.core.tools import log  # pylint: disable=E0611,E0401
from pylon.core.tools import module  # pylint: disable=E0611,E0401

from .init_db import init_db
from tools import theme


class Module(module.ModuleModel):
    """ Task module """

    def __init__(self, context, descriptor):
        self.context = context
        self.descriptor = descriptor
        #
        # self.settings = self.descriptor.config

    def init(self):
        """ Init module """
        log.info(f'Initializing module {self.descriptor.name}')
        init_db()

        self.descriptor.init_api()

        self.descriptor.init_rpcs()

        self.descriptor.init_blueprint()

        theme.register_section(
            "security",
            "Security",
            kind="holder",
            location="left",
        )
        theme.register_subsection(
            "security", "app",
            "App",
            title="Security Application",
            kind="slot",
            prefix="security_app_",
            weight=5,
        )

        theme.register_page(
            "security", "app",
            "results",
            title="Test Results",
            kind="slot",
            prefix="security_app_results_",
        )

        # security_app_styles
        # security_app_scripts
        # security_app_content

        self.descriptor.init_slots()

    def deinit(self):  # pylint: disable=R0201
        """ De-init module """
        log.info(f'De-initializing module {self.descriptor.name}')
