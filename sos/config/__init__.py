# Copyright 2026 Red Hat, Inc. Jose Castillo <jcastillo@redhat.com>

# This file is part of the sos project: https://github.com/sosreport/sos
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.

import logging
from pathlib import Path

from sos import __version__
from sos.component import SoSComponent


class Config(SoSComponent):
    """
    This subsystem is designed to manage sos configuration files and
    configuration wizzard details.
    It can be invoked in the command line like other subsystems, or
    on the first execution of sos, to prepare the initial configuration.
    """

    desc = "Manage sos configuration files and details"

    arg_defaults = {
        'config_file': '/etc/sos/sos.conf'
    }

    default_config_file = '/etc/sos/sos.conf'

    def __init__(self, config_file=None, first_time=False):
        self.config_file = config_file if config_file else\
              self.default_config_file
        if first_time:
            # We are running the wizzard for the first time
            # check if there's a config file already
            cfile = Path(self.config_file)
            if cfile.exists():
                print(f"File {config_file} already exists.")
        else:
            self.from_cmdline = True

        self.soslog = logging.getLogger('sos')
        self.ui_log = logging.getLogger('sos_ui')

    @classmethod
    def add_config_options(cls, parser):
        parser.usage = 'sos config [options]'
        config_grp = parser.add_argument_group(
            'Configuration Assistant Options',
            'These options control how configuration is done'
        )

        config_grp.add_argument("-a", "--allsubsystems", action="store_true",
                                dest="all_options", default=False,
                                help="enable all options for loaded plugins")
        config_grp.add_argument("--report_config", action="store_true",
                                dest="report_config", default=False,
                                help="configuration options for the report "
                                "subsystem")
        config_grp.add_argument("--collect_config", action="store_true",
                                dest="collect_config", default=False,
                                help="configuration options for the collect "
                                "subsystem")
        config_grp.add_argument("--cleaner_config", action="store_true",
                                dest="cleaner_config", default=False,
                                help="configuration options for the cleaner "
                                "subsystem")
        config_grp.add_argument("--upload_config", action="store_true",
                                dest="upload_config", default=False,
                                help="configuration options for the upload "
                                "subsystem")

    def print_disclaimer(self):
        """When we are directly running `sos config`, rather than hooking into
        SoSConfig via first execution of other subsystems,
          print a disclaimer banner
        """
        msg = self._fmt_msg("""\
This command will help set up a sos configuration, walking through each \
section and asking a series of questions to ensure that the configuration is \
personalized to your needs. \
""")
        self.ui_log.info(f"\nsos clean (version {__version__})\n")
        self.ui_log.info(msg)

    def execute(self):
        """
        Start the main part of the configuration assistant
        """
        if self.from_cmdline:
            self.print_disclaimer()
