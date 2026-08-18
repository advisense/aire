from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path


TOOL = Path(__file__).resolve().parents[1] / "evidence"


class EvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.case = Path(self.temporary.name) / "case"
        self.case.mkdir()
        (self.case / "SCOPE.md").write_text("# Scope\n", encoding="utf-8")
        self.evidence = self.case / "EVIDENCE.jsonl"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_tool(self, *arguments: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [str(TOOL), *arguments],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(expected, result.returncode, result.stderr)
        return result

    def entries(self) -> list[dict]:
        if not self.evidence.is_file():
            return []
        return [
            json.loads(line)
            for line in self.evidence.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def add(self, observed: str = "S-box bytes present", **overrides: str) -> str:
        arguments = {
            "--artifact": "artifacts/fw.bin",
            "--location": "file offset 0x4A2C10",
            "--observed": observed,
            "--reproduce": "xxd -s 0x4A2C10 -l 256 artifacts/fw.bin",
        }
        arguments.update(overrides)
        flat: list[str] = []
        for key, value in arguments.items():
            flat.extend([key, value])
        return self.run_tool("add", str(self.case), *flat).stdout.strip()

    def test_add_allocates_monotonic_ids(self) -> None:
        self.assertEqual("O-001", self.add())
        self.assertEqual("O-002", self.add(observed="Second observation"))
        entries = self.entries()
        self.assertEqual(["O-001", "O-002"], [entry["id"] for entry in entries])
        self.assertFalse(entries[0]["verified"])
        # Every line is a valid JSON object with the full field set.
        self.assertEqual(entries[0]["supersedes"], None)
        self.run_tool("validate", str(self.case))

    def test_add_requires_all_observation_fields(self) -> None:
        self.run_tool(
            "add", str(self.case), "--artifact", "x", "--location", "y",
            "--observed", "z", expected=2,
        )

    def test_verified_flag_and_explicit_date(self) -> None:
        self.add(observed="bare verified", **{"--verified": ""})
        self.add(observed="dated verified", **{"--verified": "2026-08-14"})
        entries = self.entries()
        self.assertEqual(entries[0]["verified"], date.today().isoformat())
        self.assertEqual(entries[1]["verified"], "2026-08-14")

    def test_verify_command_records_date(self) -> None:
        observation = self.add()
        self.run_tool("verify", str(self.case), observation, "--date", "2026-08-18")
        self.assertEqual(self.entries()[0]["verified"], "2026-08-18")

    def test_supersede_links_both_directions(self) -> None:
        old = self.add(observed="AES tables at 0x4A2C10")
        new = self.run_tool(
            "supersede", str(self.case), old,
            "--artifact", "artifacts/fw.bin",
            "--location", "file offset 0x4A2C10",
            "--observed", "Bytes match the AES forward S-box specifically",
            "--reproduce", "xxd -s 0x4A2C10 -l 256 artifacts/fw.bin",
        ).stdout.strip()
        entries = {entry["id"]: entry for entry in self.entries()}
        self.assertEqual(entries[old]["superseded_by"], new)
        self.assertEqual(entries[new]["supersedes"], old)
        # A second supersede of the already-superseded original is rejected.
        self.run_tool(
            "supersede", str(self.case), old,
            "--artifact", "a", "--location", "b", "--observed", "c", "--reproduce", "d",
            expected=2,
        )

    def test_contradict_requires_resolution_and_existing_target(self) -> None:
        first = self.add(observed="VA 0x4A2C10 read as file offset")
        second = self.add(observed="Correct file offset is 0x2C10")
        self.run_tool(
            "contradict", str(self.case), second,
            "--by", first, "--resolution", "O-001 mistook the virtual address for a file offset",
        )
        entry = {row["id"]: row for row in self.entries()}[second]
        self.assertEqual(entry["contradicts"], first)
        self.assertIn("virtual address", entry["resolution"])
        # Contradicting a nonexistent observation fails.
        self.run_tool(
            "contradict", str(self.case), second, "--by", "O-999", "--resolution", "x",
            expected=2,
        )

    def test_list_unverified_filter(self) -> None:
        first = self.add(observed="first")
        self.add(observed="second")
        self.run_tool("verify", str(self.case), first)
        listed = self.run_tool("list", str(self.case), "--unverified").stdout
        self.assertNotIn("O-001", listed)
        self.assertIn("O-002", listed)

    def test_validate_rejects_dangling_link(self) -> None:
        self.add()
        rows = self.entries()
        rows[0]["superseded_by"] = "O-404"
        self.evidence.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        self.run_tool("validate", str(self.case), expected=2)

    def test_requires_case_directory(self) -> None:
        stray = Path(self.temporary.name) / "not-a-case"
        stray.mkdir()
        self.run_tool("list", str(stray), expected=2)


if __name__ == "__main__":
    unittest.main()
