from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


TOOL = Path(__file__).resolve().parents[1] / "corpus-lookup"


def entry(entry_id: str, title: str, category: str, summary: str) -> dict:
    return {
        "id": entry_id,
        "title": title,
        "summary": summary,
        "categories": [category],
        "tags": ["test"],
        "applicable_when": ["The construction is present."],
        "check": ["Inspect its use."],
        "evidence": ["A target-specific code or trace location."],
        "impact": "Security properties may fail.",
        "remediation": "Use the construction safely.",
        "false_positives": ["The prerequisite is absent."],
        "references": [{"title": "Example", "url": "https://example.test/reference"}],
    }


class CorpusLookupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.root = self.base / "corpora"
        corpus_dir = self.root / "crypto-core"
        corpus_dir.mkdir(parents=True)
        records = [
            entry("AEAD-001", "GCM nonce reuse", "aead", "A nonce repeats under one GCM key."),
            entry("KEY-001", "Hardcoded key", "key-management", "A secret key is shipped with the client."),
        ]
        (corpus_dir / "entries.jsonl").write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
        )
        self.registry = {
            "schema_version": 1,
            "corpora": [
                {
                    "name": "crypto-core",
                    "version": "1.0",
                    "description": "Test corpus",
                    "path": "crypto-core/entries.jsonl",
                    "updated": "2026-08-12",
                    "sources": [],
                }
            ],
        }
        self.write_registry()
        self.case = self.base / "case"
        self.case.mkdir()
        (self.case / "SCOPE.md").write_text("# Scope\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_registry(self) -> None:
        (self.root / "registry.json").write_text(
            json.dumps(self.registry), encoding="utf-8"
        )

    def run_tool(self, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [str(TOOL), "--root", str(self.root), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr)
        return result

    def test_list_search_show_and_pagination(self) -> None:
        listed = self.run_tool("list", "--limit", "1")
        self.assertIn("crypto-core:AEAD-001", listed.stdout)
        self.assertIn("next: --after crypto-core:AEAD-001", listed.stdout)

        continued = self.run_tool(
            "list", "--after", "crypto-core:AEAD-001", "--limit", "1"
        )
        self.assertIn("crypto-core:KEY-001", continued.stdout)
        self.assertNotIn("AEAD-001 |", continued.stdout)

        searched = self.run_tool("search", "nonce GCM")
        self.assertIn("crypto-core:AEAD-001", searched.stdout)
        self.assertNotIn("crypto-core:KEY-001", searched.stdout)

        shown = self.run_tool("show", "crypto-core:KEY-001")
        self.assertIn("# crypto-core:KEY-001", shown.stdout)
        self.assertIn("## Required evidence", shown.stdout)

    def test_category_selection_and_complete_ledger(self) -> None:
        preview = self.run_tool(
            "preview", "--select", "crypto-core:aead", "--limit", "1"
        )
        self.assertIn("crypto-core:aead | 1 entries", preview.stdout)
        self.assertIn("deduplicated | 1 entries", preview.stdout)

        initialized = self.run_tool(
            "ledger",
            "init",
            str(self.case),
            "--select",
            "crypto-core:aead",
        )
        self.assertIn("with 1 checks", initialized.stdout)

        pending = self.run_tool("ledger", "next", str(self.case))
        self.assertIn("crypto-core:AEAD-001", pending.stdout)
        self.assertNotIn("crypto-core:KEY-001", pending.stdout)

        missing_evidence = self.run_tool(
            "ledger",
            "set",
            str(self.case),
            "crypto-core:AEAD-001",
            "--status",
            "ruled-out",
            expected=2,
        )
        self.assertIn("require --evidence", missing_evidence.stderr)

        self.run_tool(
            "ledger",
            "set",
            str(self.case),
            "crypto-core:AEAD-001",
            "--status",
            "ruled-out",
            "--evidence",
            "Unique nonce at src/aead.c:84",
        )
        verified = self.run_tool("ledger", "verify", str(self.case))
        self.assertIn("complete coverage of 1", verified.stdout)

    def test_verify_rejects_unchecked_unknown_and_version_drift(self) -> None:
        self.run_tool(
            "ledger", "init", str(self.case), "--select", "crypto-core"
        )
        unchecked = self.run_tool("ledger", "verify", str(self.case), expected=2)
        self.assertIn("2 unchecked", unchecked.stderr)

        for entry_id in ("crypto-core:AEAD-001", "crypto-core:KEY-001"):
            self.run_tool(
                "ledger",
                "set",
                str(self.case),
                entry_id,
                "--status",
                "not-applicable",
                "--evidence",
                "Primitive absent from target.",
            )
        self.registry["corpora"][0]["version"] = "2.0"
        self.write_registry()
        blocked_next = self.run_tool(
            "ledger", "next", str(self.case), expected=2
        )
        self.assertIn("cannot continue a ledger against changed corpora", blocked_next.stderr)
        drift = self.run_tool("ledger", "verify", str(self.case), expected=2)
        self.assertIn("version drift", drift.stderr)

    def test_validate_rejects_unsorted_entries(self) -> None:
        path = self.root / "crypto-core" / "entries.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        path.write_text("\n".join(reversed(lines)) + "\n", encoding="utf-8")
        result = self.run_tool("validate", expected=2)
        self.assertIn("entries must be sorted by id", result.stderr)


if __name__ == "__main__":
    unittest.main()
