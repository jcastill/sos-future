# Copyright (C) 2026 Jose Castillo <jcastillo@redhat.com>

# This file is part of the sos project: https://github.com/sosreport/sos
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.

from sos.component import SoSComponent
from sos.report.delta.baseline.comparison import (compare_baselines,
                                                   format_diff_text)

import glob
import json
import os

class SoSCompare(SoSComponent):

    desc = "Compare baseline snapshots for system diff detection"
    load_probe = False

    arg_defaults = {
        'action': '',
        'date1': '',
        'date2': '',
        'name': '',
        'baseline_dir': '/etc/sos/.captures',
        'output_format': 'text',
    }

    @classmethod
    def add_parser_options(cls, parser):
        parser.add_argument('action', choices=['diff', 'list'],
                            help='action to perform')
        parser.add_argument('date1', nargs='?', default='',
                            help="first baseline date or name")
        parser.add_argument('date2', nargs='?', default='',
                            help="second baseline date or name")
        parser.add_argument('--name', default='',
                            help='filter by baseline name')
        parser.add_argument('--output-format',
                            choices=['text', 'json'], default='text',
                            dest='output_format',
                            help='output format (default: text)')

    def execute(self):
        if self.opts.action == 'list':
            self._do_list()
        elif self.opts.action == 'diff':
            self._do_diff()

    def _load_baseline(self, identifier):
        """Load a baseline JSON file by date, name, or full path"""
        baseline_dir = self.opts.baseline_dir

        # Full path provided
        if os.path.isfile(identifier):
            with open(identifier, 'r', encoding='utf-8') as f:
                return json.load(f)
        # Exact match by date or name
        path = os.path.join(baseline_dir, f"baseline-{identifier}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        # Glob for named baselines
        matches = glob.glob(
            os.path.join(baseline_dir, f"baseline-*{identifier}*.json"))
        if matches:
            matches.sort(key=os.path.getmtime, reverse=True)
            with open(matches[0], 'r', encoding='utf-8') as f:
                return json.load(f)
        self.ui_log.error(f"No baseline found matching '{identifier}'")
        self._list_available()
        return None

    def _list_available(self):
        """Print available baselines"""
        baseline_dir = self.opts.baseline_dir
        files = sorted(
            glob.glob(os.path.join(baseline_dir, 'baseline-*.json')),
            key=os.path.getmtime, reverse=True)
        if not files:
            self.ui_log.info("No baseline snapshots found.")
            return
        for f in files:
            size = os.path.getsize(f)
            name = os.path.basename(f)
            self.ui_log.info(f"    {name}    ({size:,} bytes)")

    def _do_list(self):
        self._list_available()

    def _do_diff(self):
        if not self.opts.date1 or not self.opts.date2:
            self.ui_log.error(
                "diff requires two arguments: "
                "sos baseline diff <date1> <date2>")
            return
        old = self._load_baseline(self.opts.date1)
        new = self._load_baseline(self.opts.date2)
        if not old or not new:
            return
        result = compare_baselines(old, new)
        if self.opts.output_format == 'json':
            print(json.dumps(result, indent=4, default=str))
        else:
            print(format_diff_text(result))
