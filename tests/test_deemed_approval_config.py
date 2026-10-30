"""
Test: deemed_approval.py reads the wrong config file path.

BUG: deemed_approval.py line 23 constructs:
    CONFIG_PATH = os.path.join(BASE_DIR, "config", "settings.ini")

But the config file was consolidated to "app.ini" in March 2026.
"settings.ini" does not exist. The cron job crashes every night
with FileNotFoundError, meaning no PENDING applications are ever
auto-approved under the RTPS Act.

This test verifies the config path used by the script matches the
file that actually exists on disk.
"""
import os
import ast


def get_config_path_from_source():
    script_path = os.path.join(
        os.path.dirname(__file__), '..', 'app', 'scripts', 'deemed_approval.py'
    )
    with open(script_path, encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'CONFIG_PATH':
                    if isinstance(node.value, ast.Call):
                        args = node.value.args
                        filename_nodes = [a for a in args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                        filename = filename_nodes[-1].value if filename_nodes else None
                        return filename
    return None


def test_deemed_approval_config_filename_is_app_ini():
    """
    The config filename referenced in deemed_approval.py must be 'app.ini',
    not 'settings.ini'. This test fails against the original code and passes
    after the fix.
    """
    filename = get_config_path_from_source()
    assert filename == 'app.ini', (
        f"deemed_approval.py references config file '{filename}' "
        f"but the actual config file is 'app.ini'. "
        f"The cron will crash with FileNotFoundError every night."
    )


def test_deemed_approval_config_file_exists_at_referenced_path():
    """
    Confirm that the config file the script references actually exists
    on disk relative to the app directory.
    """
    filename = get_config_path_from_source()
    config_dir = os.path.join(
        os.path.dirname(__file__), '..', 'app', 'config'
    )
    full_path = os.path.join(config_dir, filename)
    assert os.path.isfile(full_path), (
        f"Config file does not exist at: {full_path}"
    )
