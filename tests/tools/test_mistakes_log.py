"""The mistakes log's script, and the log's generated tables being up to date.

tools/ isn't a package that project code or tests import, so the script is
loaded from its path.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "mistakes_log.py"

LOG = """# Log

<!-- generated: kinds -->
<!-- end generated -->

<!-- generated: patterns -->
<!-- end generated -->

<!-- generated: index -->
<!-- end generated -->

---

## Mistakes I had to point out

### 2026-11-02: Newer pointed out

- **Kind:** design.
- **Pattern:** weak-test.
- **Guard:** none yet.

---

## Mistakes Claude caught itself

### 2026-11-02: Newer caught

- **Kind:** testing.
- **Pattern:** weak-test.
- **Guard:** Q-01.

### 2026-11-02: Older caught

- **Kind:** testing. A longer note after the kind.
- **Pattern:** vocabulary.
- **Guard:** none yet.

### 2026-10-30: Oldest

- **Kind:** process.
- **Pattern:** vocabulary.
- **Guard:** none yet.
"""


def load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("mistakes_log", SCRIPT)
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture
def script(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    module = load_script()
    main = tmp_path / "claude-mistakes.md"
    main.write_text(LOG, encoding="utf-8")
    monkeypatch.setattr(module, "MAIN", main)
    monkeypatch.setattr(module, "ARCHIVE_DIR", tmp_path / "claude-mistakes")
    return module


def ids_by_title(module: ModuleType) -> dict[str, str]:
    return {e.title: e.mistake_id for e in module.all_entries()}


def test_the_real_log_is_up_to_date() -> None:
    module = load_script()
    assert module.problems(module.all_entries()) == []


def test_ids_go_oldest_first_and_pointed_out_first_on_a_day(script: ModuleType) -> None:
    script.main(["write"])
    assert ids_by_title(script) == {
        "Oldest": "M-001",
        "Newer pointed out": "M-002",
        "Older caught": "M-003",
        "Newer caught": "M-004",
    }


def test_a_new_entry_takes_the_next_id_and_old_ids_stay(script: ModuleType) -> None:
    script.main(["write"])
    text = script.MAIN.read_text(encoding="utf-8")
    new_entry = "### 2026-10-01: Added late\n\n- **Kind:** design.\n- **Pattern:** x.\n- **Guard:** none yet.\n\n"
    text = text.replace("### M-004", new_entry + "### M-004")
    script.MAIN.write_text(text, encoding="utf-8")
    script.main(["write"])
    ids = ids_by_title(script)
    assert ids["Added late"] == "M-005"
    assert ids["Oldest"] == "M-001"


def test_kind_table_counts_each_section(script: ModuleType) -> None:
    script.main(["write"])
    table = script.generated(script.MAIN.read_text(encoding="utf-8"))["kinds"]
    assert "| testing | 0 | 2 |" in table
    assert "| design | 1 | 0 |" in table
    assert "| **Total** | **1** | **3** |" in table


def test_check_reports_a_stale_table(script: ModuleType) -> None:
    script.main(["write"])
    text = script.MAIN.read_text(encoding="utf-8").replace("| testing | 0 | 2 |", "| testing | 0 | 1 |")
    script.MAIN.write_text(text, encoding="utf-8")
    assert script.main(["check"]) == 1


def test_check_reports_an_entry_without_a_guard(script: ModuleType) -> None:
    script.main(["write"])
    text = script.MAIN.read_text(encoding="utf-8").replace("- **Guard:** Q-01.\n", "")
    script.MAIN.write_text(text, encoding="utf-8")
    assert any("no Guard line" in p for p in script.problems(script.all_entries()))


def test_check_reports_a_malformed_heading(script: ModuleType) -> None:
    script.main(["write"])
    text = script.MAIN.read_text(encoding="utf-8").replace("### M-003, ", "### M-003 ")
    script.MAIN.write_text(text, encoding="utf-8")
    assert any("not an entry heading" in p for p in script.problems(script.all_entries()))


def test_a_malformed_headings_fields_stay_off_the_entry_above(script: ModuleType) -> None:
    script.main(["write"])
    text = script.MAIN.read_text(encoding="utf-8").replace("### M-003, ", "### M-003 ")
    script.MAIN.write_text(text, encoding="utf-8")
    patterns = {e.title: e.pattern for e in script.all_entries()}
    assert patterns["Newer caught"] == "weak-test"


def test_check_reports_an_unknown_pattern(script: ModuleType) -> None:
    script.main(["write"])
    text = script.MAIN.read_text(encoding="utf-8").replace("**Pattern:** vocabulary.", "**Pattern:** vocabulery.", 1)
    script.MAIN.write_text(text, encoding="utf-8")
    assert any("unknown pattern 'vocabulery'" in p for p in script.problems(script.all_entries()))


def test_check_reports_a_duplicate_id(script: ModuleType) -> None:
    script.main(["write"])
    text = script.MAIN.read_text(encoding="utf-8").replace("### M-003, ", "### M-004, ")
    script.MAIN.write_text(text, encoding="utf-8")
    assert "M-004: used by 2 entries" in script.problems(script.all_entries())


def test_an_unknown_command_is_refused(script: ModuleType) -> None:
    assert script.main(["wirte"]) == 2


def test_archive_moves_a_month_and_the_index_links_it(script: ModuleType) -> None:
    script.main(["write"])
    script.main(["archive", "2026-10"])
    archived = (script.ARCHIVE_DIR / "2026-10.md").read_text(encoding="utf-8")
    main = script.MAIN.read_text(encoding="utf-8")
    assert "Oldest" in archived
    assert "### M-001" not in main
    assert "[M-001](claude-mistakes/2026-10.md)" in main
    assert script.main(["check"]) == 0
