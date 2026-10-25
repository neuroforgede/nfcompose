"""Check a fully resolved requirements list against liccheck.ini.

Canonical source: skipper/check_licenses.py. After editing, run
python tools/sync_license_checker.py to update the standalone test environments.

This is a policy check, not a dependency resolver or an SPDX expression evaluator.
Use pip freeze or pipenv requirements as input. Every reported license (including
every OR alternative) must be explicitly allowed, unless a package/version has an
explicit exception. Names match exactly, ignoring case and the legacy trailing
" License" suffix in package metadata. Composite AND expressions need an explicit
policy entry. Missing metadata and unknown expressions fail closed.
"""

import argparse
import configparser
import re
import sys
from dataclasses import dataclass
from email.message import Message
from importlib import metadata
from pathlib import Path
from typing import FrozenSet, Iterable, List, Optional, Sequence, TextIO, Tuple

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


@dataclass(frozen=True)
class Policy:
    allowed: FrozenSet[str]
    denied: FrozenSet[str]
    exceptions: Tuple[Requirement, ...]


def read_policy(path: Path) -> Policy:
    # ':' is the delimiter; '==' belongs to package exception specifiers.
    config = configparser.ConfigParser(allow_no_value=True, delimiters=(":",), interpolation=None)
    with path.open(encoding="utf-8") as stream:
        config.read_file(stream)
    section = config["Licenses"]
    allowed = frozenset(line.strip().casefold() for line in section["authorized_licenses"].splitlines() if line.strip())
    denied = frozenset(line.strip().casefold() for line in section["unauthorized_licenses"].splitlines() if line.strip())
    if not allowed:
        raise ValueError("authorized_licenses must not be empty")
    exceptions = []
    if config.has_section("Authorized Packages"):
        for value in config["Authorized Packages"]:
            wildcard = value.endswith("==*")
            requirement = Requirement(value[:-3] if wildcard else value)
            if (
                (not wildcard and not requirement.specifier)
                or requirement.url or requirement.extras or requirement.marker
            ):
                raise ValueError("package exceptions need a version specifier (use ==* for all versions)")
            exceptions.append(requirement)
    return Policy(allowed, denied, tuple(exceptions))


def read_requirements(stream: TextIO) -> List[Requirement]:
    requirements = []
    for number, raw_line in enumerate(stream, 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # These are emitted by pipenv requirements / pip freeze. They do not
        # select packages; editable installs were also skipped by liccheck.
        if line.startswith(("-i ", "--index-url ", "--extra-index-url ", "--trusted-host ", "-e ", "--editable ")):
            continue
        try:
            requirement = Requirement(line)
        except ValueError as error:
            raise ValueError("invalid requirement on line {}: {}".format(number, line)) from error
        if requirement.marker is None or requirement.marker.evaluate({"extra": ""}):
            requirements.append(requirement)
    if not requirements:
        raise ValueError("requirements list selects no packages")
    return requirements


def license_names(package_metadata: Message) -> Tuple[str, ...]:
    classifiers = []
    for classifier in package_metadata.get_all("Classifier", []):
        if classifier.startswith("License :: "):
            parts = classifier.split(" :: ")[1:]
            if parts[0] == "OSI Approved":
                parts = parts[1:]
            if parts:
                classifiers.append(" :: ".join(parts))
    # Preserve liccheck's classifier-first behavior, supporting modern SPDX
    # metadata when classifiers have been removed from a distribution.
    values = classifiers or package_metadata.get_all("License-Expression", [])
    if not values:
        # Legacy License fields can contain a complete license document.
        # liccheck used its first line, rather than matching arbitrary prose.
        values = [value.splitlines()[0] if value else "" for value in package_metadata.get_all("License", [])]
    names = []
    for value in values:
        value = value.strip()
        if value.casefold().endswith(" license"):
            value = value[:-len(" license")]
        for alternative in re.split(r"\s+OR\s+", value, flags=re.IGNORECASE):
            name = alternative.strip().casefold()
            if name:
                names.append(name)
    return tuple(sorted(set(names)))


def violation(policy: Policy, name: str, version: str, licenses: Sequence[str]) -> Optional[str]:
    for exception in policy.exceptions:
        if canonicalize_name(exception.name) == canonicalize_name(name) and exception.specifier.contains(version, prereleases=True):
            return None
    if not licenses or "unknown" in licenses:
        return "missing or unknown license metadata"
    # Explicit denial wins even if the same name was accidentally allowed.
    denied = sorted(set(licenses) & policy.denied)
    if denied:
        return "denied license(s): " + "; ".join(denied)
    unknown = sorted(set(licenses) - policy.allowed)
    if unknown:
        return "unapproved license(s): " + "; ".join(unknown)
    return None


def check(policy: Policy, requirements: Iterable[Requirement], output: TextIO) -> int:
    failures = 0
    seen = set()
    for requirement in requirements:
        key = canonicalize_name(requirement.name)
        try:
            distribution = metadata.distribution(requirement.name)
        except metadata.PackageNotFoundError:
            print("FAIL {}: package is not installed".format(requirement.name), file=output)
            failures += 1
            continue
        version = distribution.version
        if not requirement.specifier.contains(version, prereleases=True):
            print("FAIL {}=={}: does not satisfy {}".format(requirement.name, version, requirement.specifier), file=output)
            failures += 1
            continue
        if key in seen:
            continue
        seen.add(key)
        problem = violation(policy, requirement.name, version, license_names(distribution.metadata))
        if problem:
            print("FAIL {}=={}: {}".format(requirement.name, version, problem), file=output)
            failures += 1
    print("Checked {} package(s); {} failure(s).".format(len(seen), failures), file=output)
    return 1 if failures else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=Path("liccheck.ini"))
    parser.add_argument("--requirements", required=True, help="fully resolved requirements file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        policy = read_policy(args.policy)
        if args.requirements == "-":
            requirements = read_requirements(sys.stdin)
        else:
            with Path(args.requirements).open(encoding="utf-8") as stream:
                requirements = read_requirements(stream)
        return check(policy, requirements, sys.stdout)
    except (OSError, ValueError, KeyError, configparser.Error) as error:
        print("License check configuration/input error: {}".format(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
