"""Unit tests for the cross-stage schema validator.

The validator is the deterministic guard the whole stack-it pipeline leans on,
so its contract is pinned here. Run with:

    uv run --with pyyaml --with pytest pytest plugins/stack-it/scripts/test_validate_yaml.py
"""
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import validate_yaml as v  # noqa: E402

HERE = Path(__file__).parent


def errs(stage, text):
    doc = yaml.safe_load(text)
    e = []
    v.VALIDATORS[stage](doc, e)
    return e


VALID_SLOTS = """
project: {description: A small CLI, type: cli, platforms: [linux]}
slots:
  - {slot: language/runtime, required: true, rationale: core, preference: Go, source: null}
  - {slot: test framework, required: false, rationale: verification, preference: null, source: null}
"""

VALID_STACK = """
project: {description: A small CLI, type: cli, platforms: [linux]}
stack:
  - slot: language/runtime
    choice: Go
    version: "1.23.4"
    install: ["asdf install golang 1.23.4"]
    caveats: []
"""


# --- happy paths -----------------------------------------------------------
def test_valid_slots_passes():
    assert errs("slots", VALID_SLOTS) == []


def test_valid_stack_passes():
    assert errs("stack", VALID_STACK) == []


# --- project block ---------------------------------------------------------
def test_missing_project():
    assert errs("stack", "stack: [{slot: a, choice: b, version: '1', install: [x]}]")


def test_platforms_must_be_list():
    assert errs("slots", "project: {description: d, type: cli, platforms: linux}\nslots: [{slot: a, required: true, rationale: r}]")


# --- slots schema ----------------------------------------------------------
def test_empty_slots_list():
    assert errs("slots", "project: {description: d, type: cli, platforms: [l]}\nslots: []")


def test_slot_as_list_rejected():
    # truthy but not a category name -- must be caught
    assert errs("slots", "project: {description: d, type: cli, platforms: [l]}\nslots: [{slot: [a, b], required: true, rationale: r}]")


def test_required_must_be_bool():
    assert errs("slots", "project: {description: d, type: cli, platforms: [l]}\nslots: [{slot: a, required: maybe, rationale: r}]")


# --- the headline version bug ---------------------------------------------
def test_unquoted_two_component_version_rejected():
    # `version: 3.10` parses as the float 3.1 -- the pin silently changes. Must fail.
    e = errs("stack", "project: {description: d, type: cli, platforms: [l]}\nstack: [{slot: a, choice: b, version: 3.10, install: [x]}]")
    assert e and "quoted string" in e[0]


def test_quoted_two_component_version_passes():
    assert errs("stack", "project: {description: d, type: cli, platforms: [l]}\nstack: [{slot: a, choice: b, version: '3.10', install: [x]}]") == []


def test_bool_version_rejected():
    assert errs("stack", "project: {description: d, type: cli, platforms: [l]}\nstack: [{slot: a, choice: b, version: true, install: [x]}]")


def test_missing_version_rejected():
    assert errs("stack", "project: {description: d, type: cli, platforms: [l]}\nstack: [{slot: a, choice: b, install: [x]}]")


def test_latest_version_rejected():
    assert errs("stack", "project: {description: d, type: cli, platforms: [l]}\nstack: [{slot: a, choice: b, version: latest, install: [x]}]")


def test_three_component_unquoted_version_ok():
    # `1.23.4` has two dots so YAML keeps it a string -- existing fixtures rely on this
    assert errs("stack", "project: {description: d, type: cli, platforms: [l]}\nstack: [{slot: a, choice: b, version: 1.23.4, install: [x]}]") == []


# --- install steps ---------------------------------------------------------
def test_install_junk_items_rejected():
    e = errs("stack", "project: {description: d, type: cli, platforms: [l]}\nstack:\n  - {slot: a, choice: b, version: '1.0', install: ['', null, 12345]}")
    assert len(e) >= 1  # the empty string, the null, and the int are all caught


def test_install_must_be_nonempty_list():
    assert errs("stack", "project: {description: d, type: cli, platforms: [l]}\nstack: [{slot: a, choice: b, version: '1.0', install: []}]")


def test_choice_missing_rejected():
    assert errs("stack", "project: {description: d, type: cli, platforms: [l]}\nstack: [{slot: a, version: '1.0', install: [x]}]")


# --- the artifact layout stamp ---------------------------------------------
def _format_errs(value):
    return errs("stack", f"format: {value}\n" + VALID_STACK)


def _assert_rejected(value):
    e = _format_errs(value)
    assert len(e) == 1 and "'format'" in e[0]


def test_format_present_and_valid():
    assert _format_errs("2") == []


def test_format_explicit_one_passes():
    # migrate rewrites an explicit `format: 1` in place, so it has to validate
    assert _format_errs("1") == []


def test_format_ahead_of_current_still_passes():
    # the validator has no upper bound; refusing a newer layout is the skills' job
    assert _format_errs("3") == []


def test_format_absent_is_fine():
    assert errs("stack", VALID_STACK) == []


def test_format_string_rejected():
    _assert_rejected("'2'")


def test_format_float_rejected():
    _assert_rejected("2.0")


def test_format_bool_rejected():
    _assert_rejected("true")


def test_format_below_one_rejected():
    _assert_rejected("0")


def test_format_negative_rejected():
    _assert_rejected("-1")


def test_format_null_rejected():
    e = _format_errs("")
    assert len(e) == 1 and "'format'" in e[0] and "present but empty" in e[0]


def test_format_error_does_not_short_circuit_the_rest():
    # a bad format must not stop the stack checks: both problems have to surface
    e = errs("stack", "format: 'x'\nproject: {description: d, type: cli, platforms: [l]}\n"
                      "stack: [{slot: a, version: '1.0', install: [x]}]")
    assert len(e) == 2


# --- exit codes via the CLI ------------------------------------------------
def _run(*args):
    return subprocess.run([sys.executable, str(HERE / "validate_yaml.py"), *args],
                          capture_output=True, text=True)


def test_exit_2_on_missing_file():
    assert _run("--stage", "stack", str(HERE / "does-not-exist.yaml")).returncode == 2


def test_exit_2_on_directory(tmp_path):
    # a directory is an OSError, not FileNotFoundError -- must still be exit 2, not a traceback
    assert _run("--stage", "stack", str(tmp_path)).returncode == 2


def test_exit_0_on_valid(tmp_path):
    p = tmp_path / "stack.yaml"
    p.write_text(VALID_STACK)
    assert _run("--stage", "stack", str(p)).returncode == 0


def test_exit_1_on_invalid(tmp_path):
    p = tmp_path / "stack.yaml"
    p.write_text("project: {description: d, type: cli, platforms: [l]}\nstack: [{slot: a, choice: b, version: 3.10, install: [x]}]")
    assert _run("--stage", "stack", str(p)).returncode == 1
