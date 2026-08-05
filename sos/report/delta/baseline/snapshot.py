# Copyright (C) 2026 Jose Castillo <jcastillo@redhat.com>
#
# This file is part of the sos project: https://github.com/sosreport/sos
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.

import glob
import json
import logging
import os
import re
from datetime import datetime

_default_log = logging.getLogger('sos')

def find_latest_snapshot(baseline_dir='/etc/sos/.captures'):
    """Find the most recent baseline snapshot file. 

    Scans the baseline directory for files matchin ``baseline-*.json``
    and returns the path to the one with the newest modification time. 

    :param baseline_dir: Directory to scan for snapshots
    :type baseline_dir: str

    :returns: Path to the newest snapshot or None if none found
    :rtype: str or None    
    """
    files = sorted(
        glob.glob(os.path.join(baseline_dir, 'baseline-*.json')),
        key=os.path.getmtime, reverse=True)
    return files[0] if files else None

def load_snapshot(path, soslog=None):
    """Load and parse a baseline JSON snapshot file.

    :param path: Path to the baseline JSON file
    :type path: str

    :param soslog: Optional logger for error messages
    :type soslog: logging.Logger or None

    :returns: Parsed baseline data dict or None on error
    :rtype: dict or None
    """
    log = soslog or _default_log
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        log.error("Failed to load baseline snapshot "
                  f"'{path}' : {e}")
        return None

def save_snapshot(manifest_json, name='', baseline_dir='/etc/sos/.captures',
                  soslog=None):
    """Save manifest JSON as a dated baseline snapshot.

    Writes to: ``baseline[-NAME]-YYYY-MM-DD_HH-MM-SS.json``
    Permissions: ``0o444`` (read-only) after write.
    Directory: created with ``0o700`` if missing.

    :param manifest_json: Manifest JSON string to write
    :type manifest_json: str

    :param name: Optional baseline name (alphanumerics, dots, hypens, underscores only)
    :type name: str

    :param baseline_dir: Directory to write snapshot to
    :type baseline_dir: str

    :param soslog: Optional logger for indo/error messages
    :type soslog: logging.Logger or None

    :returns: Path to the saved snapshot or None on failure
    :rtype: str or None
    """
    log = soslog or _default_log

    if name and not re.match(r'^[a-zA-Z0-9._-]+$', name):
        log.error(f"Invalid baseline '{name}': "
                  "only alphanumerics, dots, hypens, "
                  "and underscores are allowed")
        return None

    date_str = datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')
    name = f"-{name}" if name else ''
    filename = f"baseline{name}-{date_str}.json"
    baseline_path = os.path.join(baseline_dir, filename)

    try:
        os.makedirs(baseline_dir, mode=0o700, exist_ok=True)

        # Remove write protection from previous snapshot if overwritting
        if os.path.exists(baseline_path):
            os.chmod(baseline_path, 0o644)

        with open(baseline_path, 'w', encoding='utf-8') as f:
            f.write(manifest_json)

        os.chmod(baseline_path, 0o444)

        log.info(f"Baseline snapshot saved to {baseline_path}")

        return baseline_path
    except PermissionError as e:
        log.error("Permission denied writing baseline snapshot to "
                  f"{baseline_path}: {e}")
    except OSError as e:
        log.error(
            "Failed to create baseline directory "
            f"{baseline_dir}: {e}"
        )
    except Exception as e:
        log.error("Unexpected error saving baseline snapshot: "
                  f"{e}")
    return None