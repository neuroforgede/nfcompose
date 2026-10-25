"""Policy regression tests; run with python -m unittest discover -s tools."""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skipper"))

import check_licenses as checker
from packaging.requirements import Requirement


POLICY = """[Licenses]
authorized_licenses:
    mit
    bsd
    Apache-2.0
unauthorized_licenses:
    GPL-3.0-only

[Authorized Packages]
    exceptional-package==1.3
    deliberate-exception==*
"""


def package_metadata(classifiers=(), license=None, expression=None):
    result = Message()
    for classifier in classifiers:
        result["Classifier"] = classifier
    if license is not None:
        result["License"] = license
    if expression is not None:
        result["License-Expression"] = expression
    return result


class LicensePolicyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.policy_path = Path(self.directory.name) / "liccheck.ini"
        self.policy_path.write_text(POLICY, encoding="utf-8")
        self.policy = checker.read_policy(self.policy_path)

    def violation(self, licenses, name="ordinary-package", version="1.0"):
        return checker.violation(self.policy, name, version, licenses)

    def test_all_reported_licenses_must_be_allowed(self):
        self.assertIsNone(self.violation(("mit", "bsd")))
        self.assertIn("unapproved", self.violation(("mit", "unlisted")))

    def test_explicitly_denied_license_fails_with_an_allowed_license(self):
        self.assertIn("denied", self.violation(("mit", "gpl-3.0-only")))

    def test_denial_wins_if_policy_also_allows_the_license(self):
        policy = checker.Policy(frozenset({"mit"}), frozenset({"mit"}), ())
        self.assertIn("denied", checker.violation(policy, "ordinary", "1", ("mit",)))

    def test_matching_is_exact_not_substring_or_regex(self):
        for name in ("not-mit", "mit-like", "mit or proprietary", "m.t"):
            with self.subTest(name=name):
                self.assertIn("unapproved", self.violation((name,)))

    def test_missing_license_fails(self):
        self.assertIn("missing", self.violation(()))

    def test_package_exception_is_limited_to_its_version(self):
        self.assertIsNone(self.violation((), "exceptional-package", "1.3"))
        self.assertIn("missing", self.violation((), "exceptional-package", "1.4"))

    def test_package_names_are_normalized(self):
        self.assertIsNone(self.violation((), "Exceptional_Package", "1.3"))

    def test_explicit_wildcard_exception(self):
        self.assertIsNone(self.violation((), "deliberate-exception", "99.0"))

    def test_version_specifiers_support_ranges(self):
        self.policy_path.write_text(POLICY + "    range-package>=1,<2\n", encoding="utf-8")
        policy = checker.read_policy(self.policy_path)
        self.assertIsNone(checker.violation(policy, "range-package", "1.4", ()))
        self.assertIn("missing", checker.violation(policy, "range-package", "2.0", ()))

    def test_versionless_exception_is_invalid(self):
        self.policy_path.write_text(POLICY + "    accidental-exception\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            checker.read_policy(self.policy_path)

    def test_empty_allowlist_is_invalid(self):
        self.policy_path.write_text("[Licenses]\nauthorized_licenses:\nunauthorized_licenses:\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            checker.read_policy(self.policy_path)

    def test_missing_and_malformed_policy_fail(self):
        self.policy_path.unlink()
        with self.assertRaises(OSError):
            checker.read_policy(self.policy_path)
        self.policy_path.write_text("not an ini file", encoding="utf-8")
        with self.assertRaises(checker.configparser.Error):
            checker.read_policy(self.policy_path)

    def test_classifier_first_and_legacy_suffix_normalization(self):
        info = package_metadata(["License :: OSI Approved :: MIT License"], expression="unlisted")
        self.assertEqual(("mit",), checker.license_names(info))

    def test_generic_classifier_falls_back_to_spdx_metadata(self):
        info = package_metadata(["License :: OSI Approved"], expression="Apache-2.0")
        self.assertEqual(("apache-2.0",), checker.license_names(info))

    def test_legacy_license_first_line_and_case(self):
        info = package_metadata(license="MIT License\n\nFull license document")
        self.assertEqual(("mit",), checker.license_names(info))

    def test_all_or_alternatives_must_be_approved(self):
        info = package_metadata(expression="MIT OR proprietary")
        names = checker.license_names(info)
        self.assertIn("unapproved", self.violation(names))

    def test_and_expressions_need_an_explicit_policy_entry(self):
        info = package_metadata(expression="MIT AND BSD")
        names = checker.license_names(info)
        self.assertIn("unapproved", self.violation(names))
        policy = checker.Policy(frozenset({"mit and bsd"}), frozenset(), ())
        self.assertIsNone(checker.violation(policy, "ordinary", "1", names))

    def test_unknown_and_absent_metadata_are_not_licenses(self):
        for info in (package_metadata(), package_metadata(license="UNKNOWN"), package_metadata(expression="")):
            self.assertIn("missing", self.violation(checker.license_names(info)))

    def test_unknown_license_is_not_discarded_alongside_an_allowed_license(self):
        info = package_metadata(expression="MIT OR UNKNOWN")
        self.assertIn("unknown", self.violation(checker.license_names(info)))

    def test_multiline_spdx_expression_is_not_truncated_to_an_allowed_name(self):
        info = package_metadata(expression="MIT\n AND proprietary")
        self.assertIn("unapproved", self.violation(checker.license_names(info)))

    def test_requirements_scope_and_markers(self):
        text = "# Generated list\n-i https://pypi.org/simple\n-e /client\nrequests==2.34.2\nabsent; python_version < '1'\n"
        self.assertEqual(["requests"], [r.name for r in checker.read_requirements(io.StringIO(text))])

    def test_empty_invalid_and_unresolved_requirements_fail(self):
        for text in ("", "# only comments\n", "-r other.txt\n", "--invalid-option\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                checker.read_requirements(io.StringIO(text))

    @patch.object(checker.metadata, "distribution")
    def test_missing_installed_package_fails(self, distribution):
        distribution.side_effect = checker.metadata.PackageNotFoundError("absent")
        output = io.StringIO()
        self.assertEqual(1, checker.check(self.policy, [Requirement("absent==1")], output))
        self.assertIn("not installed", output.getvalue())

    @patch.object(checker.metadata, "distribution")
    def test_installed_version_must_match_every_requirement(self, distribution):
        distribution.return_value = SimpleNamespace(version="1.0", metadata=package_metadata(license="MIT"))
        requirements = [Requirement("ordinary==1.0"), Requirement("ordinary>=2")]
        self.assertEqual(1, checker.check(self.policy, requirements, io.StringIO()))

    @patch.object(checker.metadata, "distribution")
    def test_scope_is_only_the_provided_requirements(self, distribution):
        distribution.return_value = SimpleNamespace(version="1.0", metadata=package_metadata(license="MIT"))
        self.assertEqual(0, checker.check(self.policy, [Requirement("ordinary==1.0")], io.StringIO()))
        distribution.assert_called_once_with("ordinary")

    def test_cli_missing_file_and_empty_stdin_exit_nonzero(self):
        for requirements in ("missing.txt", "-"):
            with patch.object(sys, "stdin", io.StringIO("")), redirect_stderr(io.StringIO()):
                self.assertEqual(2, checker.main(["--policy", str(self.policy_path), "--requirements", requirements]))

    @patch.object(checker.metadata, "distribution")
    def test_cli_rejects_mixed_licenses(self, distribution):
        distribution.return_value = SimpleNamespace(version="1", metadata=package_metadata(expression="MIT OR unlisted"))
        with patch.object(sys, "stdin", io.StringIO("ordinary==1")), redirect_stdout(io.StringIO()):
            self.assertEqual(1, checker.main(["--policy", str(self.policy_path), "--requirements", "-"]))

    def test_distributed_copies_match_canonical_source(self):
        source = (ROOT / "skipper/check_licenses.py").read_bytes()
        for relative in ("client/check_licenses.py", "deploy/local/integration/check_licenses.py"):
            with self.subTest(path=relative):
                self.assertEqual(source, (ROOT / relative).read_bytes(), "Run python tools/sync_license_checker.py")


if __name__ == "__main__":
    unittest.main()
