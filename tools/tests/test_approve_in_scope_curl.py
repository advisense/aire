from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "approve-in-scope-curl.py"
SPEC = importlib.util.spec_from_file_location("approve_in_scope_curl", HOOK)
assert SPEC is not None and SPEC.loader is not None
hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hook)


class ApproveInScopeCurlTests(unittest.TestCase):
    def test_only_read_only_requests_are_eligible(self) -> None:
        self.assertEqual(
            ["https://example.test/api"],
            hook.curl_urls("curl --request GET https://example.test/api"),
        )
        self.assertEqual(
            ["https://example.test/api"],
            hook.curl_urls("curl --head https://example.test/api"),
        )
        for command in (
            "curl -X DELETE https://example.test/api/resource",
            "curl --data value https://example.test/api",
            "curl --upload-file artifact.bin https://example.test/api",
            "curl --output SCOPE.md https://example.test/api",
            "curl -O https://example.test/api/file",
            "curl --header 'X-HTTP-Method-Override: DELETE' https://example.test/api",
            "curl -H 'X-HTTP-Method-Override: DELETE' https://example.test/api",
        ):
            with self.subTest(command=command):
                self.assertIsNone(hook.curl_urls(command))

    def test_active_scope_requires_interactive_analysis_permission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = root / "cases" / "demo"
            case.mkdir(parents=True)
            scope = case / "SCOPE.md"
            template = """# Scope

**Status:** ACTIVE

## Authorization

Approved by the owner.

## In scope

`https://example.test/api`

## Permitted activity

- [{marker}] Interactive analysis of the live application
"""
            scope.write_text(template.format(marker=" "), encoding="utf-8")
            self.assertEqual([], hook.active_scope_urls(root))

            scope.write_text(template.format(marker="x"), encoding="utf-8")
            approved = hook.active_scope_urls(root)
            self.assertEqual(1, len(approved))
            self.assertEqual("example.test", approved[0].hostname)


if __name__ == "__main__":
    unittest.main()
