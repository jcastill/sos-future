# Copyright (C) 2026 Jose Castillo <jcastillo@redhat.com>

# This file is part of the sos project: https://github.com/sosreport/sos
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.

def extract_files_metadata(manifest_data):
    """Walk manifest JSON and return dict keyed by source_path.

    Walks components.report.plugins.<plugin>.files[*].files_metadata[*]
    and returns {source_path: metadata_dict}.
    """
    result = {}
    plugins = (manifest_data.get('components', {})
               .get('report', {}).get('plugins', {}))
    for plugin in plugins.values():
        for file_entry in plugin.get('files', []):
            for meta in file_entry.get('files_metadata', []):
                source_path = meta.get('source_path')
                if source_path:
                    result[source_path] = meta
    return result


def compare_baselines(old_data, new_data):
    """Compare two baseline manifest dicts.

    Returns dict with summary counts and lists of added, removed,
    and changed files with per-field change details.
    """
    old_files = extract_files_metadata(old_data)
    new_files = extract_files_metadata(new_data)

    compare_fields = ('mode', 'uid', 'gid', 'owner', 'group',
                      'size', 'sha256', 'selinux_context')

    added = []
    removed = []
    changed = []
    unchanged = 0

    for path, meta in new_files.items():
        if path not in old_files:
            added.append(meta)
            continue
        old_meta = old_files[path]
        changes = {}
        for field in compare_fields:
            old_val = old_meta.get(field)
            new_val = meta.get(field)
            if old_val != new_val:
                changes[field] = {'old': old_val, 'new': new_val}
        if changes:
            changed.append({'path': path, 'changes': changes})
        else:
            unchanged += 1

    for path, meta in old_files.items():
        if path not in new_files:
            removed.append(meta)

    return {
        'summary': {
            'added_count': len(added),
            'removed_count': len(removed),
            'changed_count': len(changed),
            'unchanged_count': unchanged,
        },
        'added': added,
        'removed': removed,
        'changed': changed,
    }


def format_diff_text(diff_result):
    """Format comparison result as human-readable terminal output"""
    lines = []
    s = diff_result['summary']
    lines.append(f"Summary: {s['added_count']} added, "
                 f"{s['removed_count']} removed, "
                 f"{s['changed_count']} changed, "
                 f"{s['unchanged_count']} unchanged")
    lines.append('')

    if diff_result['added']:
        lines.append('ADDED FILES:')
        for f in diff_result['added']:
            lines.append(f"   {f.get('source_path', f.get('path'))}")
        lines.append('')

    if diff_result['removed']:
        lines.append('REMOVED FILES:')
        for f in diff_result['removed']:
            lines.append(f"   {f.get('source_path', f.get('path'))}")
        lines.append('')

    if diff_result['changed']:
        lines.append('CHANGED FILES:')
        for item in diff_result['changed']:
            lines.append(f"   {item['path']}")
            for field, vals in item['changes'].items():
                lines.append(f"    {field}: {vals['old']} -> {vals['new']}")
        lines.append('')

    return '\n'.join(lines)
