"""Tests for the course manifest and the route manager (tools/route_manager.py)."""

import copy
from decimal import Decimal

import pytest

from tests.course_tools import load_route_manager

rm = load_route_manager()


@pytest.fixture(scope="module")
def course():
    return rm.Course.load()


def test_manifest_passes_every_check(course):
    errors, _ = rm.check(course)
    assert errors == []


def test_generated_docs_are_up_to_date(course):
    assert rm.render(course, check_only=True) == []


def test_programme_totals(course):
    assert course.guided_hours() == 736
    assert course.program["duration_weeks"] == 52
    assert len(course.teaching_modules()) == 24
    assert all(t in {m for mod in course.modules.values() for m in mod.topics}
               for t, topic in course.topics.items() if topic["required"])


def test_fee_split_is_exact_to_the_paisa(course):
    base, gst = rm.split_gst(course.fee["total_all_inclusive"], course.fee["gst_rate"])
    assert base == Decimal("847457.63") and gst == Decimal("152542.37")
    assert base + gst == Decimal("1000000.00")
    for plan in course.fee["payment_plans"]:
        parts = [rm.split_gst(x["amount"], course.fee["gst_rate"]) for x in plan["schedule"]]
        assert sum(b + g for b, g in parts) == Decimal("1000000.00")


def test_indian_number_formatting():
    assert rm.inr(1000000, paise=True) == "₹10,00,000.00"
    assert rm.inr(847457.625) == "₹8,47,458"
    assert rm.inr(-1234567.891, paise=True) == "−₹12,34,567.89"
    assert rm.inr(999) == "₹999"
    assert rm.pct(-0.1234) == "−12.3%"


def test_unit_economics_break_even_below_capacity(course):
    ue = rm.economics(course, course.program["cohort"]["target"])
    assert 0 < ue["break_even"] < course.program["cohort"]["maximum"]
    assert ue["surplus"] == ue["contribution"] + ue["fixed"]
    cheaper = rm.economics(course, 36, total_override=800000)
    assert cheaper["surplus"] < ue["surplus"]


def test_schema_catches_values_split_by_unquoted_commas(course):
    data = copy.deepcopy(course.data)
    data["modules"][1]["labs"][0] = {"file": "lab_01a_markets_instruments.py", "status": "ready", "runtime_s": 5,
                                     "title": "Notional", "margin": None}
    problems = rm.schema_errors(data)
    assert any("unexpected keys" in p and "margin" in p for p in problems)


def test_check_catches_structural_mistakes(course):
    broken = rm.Course(copy.deepcopy(course.data))
    broken.modules["M10"].prerequisites.append("M12")                  # forward reference
    broken.modules["M11"].weeks = (22, 24)                              # overlaps M10
    broken.fee["payment_plans"][1]["schedule"][0]["amount"] = 99999.0   # plan no longer sums to the fee
    errors, _ = rm.check(broken)
    text = "\n".join(errors)
    assert "prerequisite M12 does not finish before M10 starts" in text
    assert "week 22 is covered by" in text
    assert "payment plan B adds up to" in text


def test_week_and_route_views(course, capsys):
    rm.show_week(course, 26)
    out = capsys.readouterr().out
    assert "M12" in out and "Lab due: 12a" in out
    rm.show_route(course, "algo-developer")
    out = capsys.readouterr().out
    assert "▲ M16" in out and "○ M03" in out


def test_ready_labs_exist_and_planned_labs_do_not(course):
    for lab in course.labs():
        assert lab.path.exists() == (lab.status == "ready"), lab.file


def test_relative_markdown_links_resolve():
    import re

    root = rm.ROOT
    broken = []
    for md in root.rglob("*.md"):
        if any(part in {".git", "build", ".venv", "node_modules"} for part in md.relative_to(root).parts):
            continue
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
            if not target.startswith(("http://", "https://", "mailto:")) and not (md.parent / target).exists():
                broken.append(f"{md.relative_to(root)} -> {target}")
    assert broken == []


def test_schema_catches_values_parsed_as_mappings(course):
    data = copy.deepcopy(course.data)
    data["fee"]["inclusions"][0] = {"736 guided hours": "live classes"}   # unquoted ": " in a YAML list
    assert any("is not text" in p for p in rm.schema_errors(data))


def test_lab_extras_must_be_optional_dependencies_in_pyproject(course):
    assert set(rm.pip_extras()) == {"data", "boost", "llm", "dl"}
    broken = rm.Course(copy.deepcopy(course.data))
    lab = broken.modules["M23"].labs[0]
    broken.modules["M23"].labs[0] = rm.Lab(lab.file, lab.status, lab.runtime_s, lab.title, lab.module, ("gpu",))
    errors, _ = rm.check(broken)
    assert any("extras ['gpu']" in e for e in errors)
