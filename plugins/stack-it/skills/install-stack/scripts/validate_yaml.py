#!/usr/bin/env python3
"""Validate the YAML files that flow between the project-setup skills.

Three shapes are validated:

  slots  -- input to decide-stack (output of identify-stack-slots)
  stack  -- output of decide-stack / input to install-stack

Usage:
    python validate_yaml.py --stage slots path/to/slots.yaml
    python validate_yaml.py --stage stack path/to/stack.yaml
    python validate_yaml.py path/to/stack.yaml          # defaults to --stage stack

Exit code 0 means valid. Non-zero means problems, printed one per line.
This is a deterministic guard so a malformed handoff fails fast instead of
breaking a later stage in a confusing way.
"""
import argparse
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "PyYAML is required. Install it with: pip install pyyaml --break-system-packages\n"
    )
    sys.exit(2)


def _err(errors, msg):
    errors.append(msg)


def _check_project(doc, errors):
    project = doc.get("project")
    if not isinstance(project, dict):
        _err(errors, "top-level 'project' is missing or not a mapping")
        return
    if not project.get("description"):
        _err(errors, "project.description is missing or empty")
    if not project.get("type"):
        _err(errors, "project.type is missing or empty")
    platforms = project.get("platforms")
    if not isinstance(platforms, list):
        _err(errors, "project.platforms must be a list")


def validate_slots(doc, errors):
    _check_project(doc, errors)
    slots = doc.get("slots")
    if not isinstance(slots, list) or not slots:
        _err(errors, "'slots' must be a non-empty list")
        return
    for i, slot in enumerate(slots):
        where = f"slots[{i}]"
        if not isinstance(slot, dict):
            _err(errors, f"{where} is not a mapping")
            continue
        if not slot.get("slot"):
            _err(errors, f"{where}.slot (the category name) is missing")
        if not isinstance(slot.get("required"), bool):
            _err(errors, f"{where}.required must be true or false")
        if "rationale" not in slot:
            _err(errors, f"{where}.rationale is missing")
        # preference and source may be null; presence is not required.


def validate_stack(doc, errors):
    _check_project(doc, errors)
    stack = doc.get("stack")
    if not isinstance(stack, list) or not stack:
        _err(errors, "'stack' must be a non-empty list (and its order is the install order)")
        return
    for i, entry in enumerate(stack):
        where = f"stack[{i}]"
        if not isinstance(entry, dict):
            _err(errors, f"{where} is not a mapping")
            continue
        if not entry.get("slot"):
            _err(errors, f"{where}.slot is missing")
        if not entry.get("choice"):
            _err(errors, f"{where}.choice (the chosen tool) is missing")
        version = entry.get("version")
        if version is None or str(version).strip() == "":
            _err(errors, f"{where}.version is missing -- versions must be pinned, not 'latest'")
        elif str(version).strip().lower() in {"latest", "*", "newest"}:
            _err(errors, f"{where}.version is '{version}' -- pin an exact version instead")
        install = entry.get("install")
        if not isinstance(install, list) or not install:
            _err(errors, f"{where}.install must be a non-empty list of steps")
        caveats = entry.get("caveats", [])
        if caveats is not None and not isinstance(caveats, list):
            _err(errors, f"{where}.caveats must be a list (use [] for none)")


VALIDATORS = {"slots": validate_slots, "stack": validate_stack}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", help="Path to the YAML file to validate")
    parser.add_argument("--stage", choices=sorted(VALIDATORS), default="stack",
                        help="Which schema to validate against (default: stack)")
    args = parser.parse_args()

    try:
        with open(args.path, "r", encoding="utf-8") as fh:
            doc = yaml.safe_load(fh)
    except FileNotFoundError:
        print(f"file not found: {args.path}")
        sys.exit(2)
    except yaml.YAMLError as exc:
        print(f"YAML did not parse: {exc}")
        sys.exit(2)

    if not isinstance(doc, dict):
        print("top-level document must be a mapping")
        sys.exit(1)

    errors = []
    VALIDATORS[args.stage](doc, errors)

    if errors:
        print(f"INVALID ({args.stage}): {len(errors)} problem(s)")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"OK: '{args.path}' is a valid '{args.stage}' document")
    sys.exit(0)


if __name__ == "__main__":
    main()
