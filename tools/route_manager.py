#!/usr/bin/env python3
"""Route manager for the CFMAT course: one manifest, many views.

``course/course.yaml`` is the single source of truth for the programme's structure,
schedule, fees and learner routes. This tool checks it against the repository and
renders the tables that the Markdown docs show, so the docs can never drift from
the manifest.

    python tools/route_manager.py check            validate manifest + repository (CI runs this)
    python tools/route_manager.py render [--check] rewrite generated doc sections (or fail if stale)
    python tools/route_manager.py status           modules and labs: ready vs planned
    python tools/route_manager.py week 25          what happens in week 25
    python tools/route_manager.py route algo-developer
    python tools/route_manager.py routes           list learner routes
    python tools/route_manager.py coverage         the 15 committed topics x modules
    python tools/route_manager.py fees             fee split, plans and unit economics
    python tools/route_manager.py labs [--ready]   lab paths, e.g. for scripts

Generated sections live between ``<!-- BEGIN GENERATED: name -->`` and
``<!-- END GENERATED: name -->`` markers. Edit the manifest, not those sections.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "course" / "course.yaml"
CURRICULUM = ROOT / "curriculum"
HOURS_PER_MODULE_WEEK = 12
PAISA = Decimal("0.01")
MODULE_README_SECTIONS = (
    "## Why this module",
    "## Learning outcomes",
    "## Before you start",
    "## Weekly plan",
    "## Labs",
    "## Assessment",
    "## Common mistakes",
    "## Readings",
    "## Instructor notes",
)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

@dataclass
class Lab:
    file: str
    status: str
    runtime_s: int
    title: str
    module: Module
    extras: tuple[str, ...] = ()      # optional pip extras (pyproject) that unlock sections or exercises

    @property
    def path(self) -> Path:
        return self.module.folder / self.file

    @property
    def code(self) -> str:
        m = re.match(r"lab_(\d{2}[a-z])_", self.file)
        return m.group(1) if m else self.file


@dataclass
class Module:
    id: str
    slug: str
    title: str
    term: str
    weeks: tuple[int, int]
    week_themes: list[str]
    library: list[str]
    topics: list[str]
    prerequisites: list[str]
    guided_hours: int
    self_paced_hours: int = 0
    labs: list[Lab] = field(default_factory=list)

    @property
    def number(self) -> int:
        return int(self.id[1:])

    @property
    def folder(self) -> Path:
        return CURRICULUM / f"{self.id.lower()}-{self.slug}"

    @property
    def readme(self) -> Path:
        return self.folder / "README.md"

    @property
    def n_weeks(self) -> int:
        return self.weeks[1] - self.weeks[0] + 1

    @property
    def status(self) -> str:
        if not self.labs:
            return "ready"
        ready = sum(lab.status == "ready" for lab in self.labs)
        return "ready" if ready == len(self.labs) else ("partial" if ready else "planned")

    def week_list(self) -> list[int]:
        return list(range(self.weeks[0], self.weeks[1] + 1))


class Course:
    def __init__(self, data: dict):
        self.data = data
        self.program = data["program"]
        self.fee = data["fee"]
        self.economics = data["unit_economics"]
        self.terms = {t["id"]: t for t in data["terms"]}
        self.blocks = data["blocks"]
        self.topics = {t["id"]: t for t in data["topics"]}
        self.assessment = data["assessment"]
        self.routes = {r["id"]: r for r in data["routes"]}
        self.modules: dict[str, Module] = {}
        for m in data["modules"]:
            weeks = tuple(m["weeks"])
            default_hours = 0 if m["id"] == "M00" else HOURS_PER_MODULE_WEEK * (weeks[1] - weeks[0] + 1)
            mod = Module(id=m["id"], slug=m["slug"], title=m["title"], term=m["term"], weeks=weeks,
                         week_themes=list(m["week_themes"]), library=list(m.get("library", [])),
                         topics=list(m.get("topics", [])), prerequisites=list(m.get("prerequisites", [])),
                         guided_hours=int(m.get("guided_hours", default_hours)),
                         self_paced_hours=int(m.get("self_paced_hours", 0)))
            mod.labs = [Lab(file=lab["file"], status=lab["status"], runtime_s=int(lab.get("runtime_s", 0)),
                            title=lab["title"], module=mod, extras=tuple(lab.get("extras", [])))
                        for lab in m.get("labs", [])]
            self.modules[mod.id] = mod

    @classmethod
    def load(cls, path: Path = MANIFEST) -> Course:
        with open(path, encoding="utf-8") as fh:
            return cls(yaml.safe_load(fh))

    # -- derived facts ---------------------------------------------------------
    def labs(self) -> list[Lab]:
        return [lab for m in self.modules.values() for lab in m.labs]

    def teaching_modules(self) -> list[Module]:
        return [m for m in self.modules.values() if m.id != "M00"]

    def calendar_blocks(self) -> list[dict]:
        return [b for b in self.blocks if "week" in b]

    def concurrent_blocks(self) -> list[dict]:
        return [b for b in self.blocks if "weeks" in b]

    def hours(self) -> dict[str, int]:
        capstone_module = sum(m.guided_hours for m in self.modules.values() if m.id == "M24")
        return {
            "Module weeks (44 × 12 h)": sum(m.guided_hours for m in self.teaching_modules() if m.id != "M24"),
            "Review and exam weeks": sum(b["guided_hours"] for b in self.calendar_blocks()),
            "In-person bootcamps": sum(b.get("bootcamp_hours", 0) for b in self.calendar_blocks()),
            "Capstone (studio weeks + track)": capstone_module + sum(b["guided_hours"] for b in self.concurrent_blocks()),
            "1:1 mentoring": int(self.program["mentoring_hours"]),
        }

    def guided_hours(self) -> int:
        return sum(self.hours().values())

    def slot(self, week: int) -> tuple[str, object]:
        for b in self.calendar_blocks():
            if b["week"] == week:
                return "block", b
        for m in self.modules.values():
            if m.weeks[0] <= week <= m.weeks[1]:
                return "module", m
        return "none", None

    def term_of_week(self, week: int) -> dict | None:
        for t in self.terms.values():
            if t["weeks"][0] <= week <= t["weeks"][1]:
                return t
        return None


# ---------------------------------------------------------------------------
# Money
# ---------------------------------------------------------------------------

def D(x) -> Decimal:
    return Decimal(str(x))


def inr(amount, paise: bool = False) -> str:
    """Indian digit grouping: 1000000 -> ₹10,00,000 (or ₹10,00,000.00)."""
    q = D(amount).quantize(PAISA if paise else Decimal("1"), rounding=ROUND_HALF_UP)
    sign = "−" if q < 0 else ""
    q = abs(q)
    rupees, frac = divmod(q, 1)
    s = str(int(rupees))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = ",".join(re.findall(r"\d{1,2}", head[::-1]))[::-1]
        s = f"{head},{tail}"
    return f"{sign}₹{s}" + (f".{int(frac * 100):02d}" if paise else "")


def pct(x, digits: int = 1) -> str:
    """A percentage with a proper minus sign: -0.123 -> −12.3%."""
    v = float(x) * 100
    return f"{'−' if v < 0 else ''}{abs(v):.{digits}f}%"


def split_gst(total, rate) -> tuple[Decimal, Decimal]:
    """(base, gst) for a GST-inclusive amount, to the paisa, adding up exactly."""
    total, rate = D(total), D(rate)
    base = (total / (1 + rate)).quantize(PAISA, rounding=ROUND_HALF_UP)
    return base, total - base


def economics(course: Course, learners: int, total_override=None) -> dict[str, Decimal]:
    e, f = course.economics, course.fee
    total = D(total_override if total_override is not None else f["total_all_inclusive"])
    base, _ = split_gst(total, f["gst_rate"])
    fixed = sum(D(x["amount"]) for x in e["fixed_costs"])
    variable = sum(D(x["amount"]) for x in e["variable_costs_per_learner"])
    per_learner = {
        "Fee before GST": base,
        "Scholarships": -(base * D(e["scholarship_share_of_base"])),
        "Marketing and admissions": -(base * D(e["marketing_share_of_base"])),
        "Payment processing": -(total * D(e["payment_processing_share"])),
        "Direct per-learner costs": -variable,
    }
    contribution = sum(per_learner.values())
    revenue = base * learners
    surplus = contribution * learners - fixed
    return {**{k: v * learners for k, v in per_learner.items()}, "contribution": contribution * learners,
            "fixed": -fixed, "surplus": surplus, "margin": surplus / revenue if revenue else D(0),
            "contribution_per_learner": contribution, "fixed_total": fixed,
            "break_even": fixed / contribution if contribution > 0 else D("Infinity")}


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

SCHEMA = {  # allowed keys per record type; catches YAML flow-mapping values split by unquoted commas
    "lab": {"file", "status", "runtime_s", "title", "extras"},
    "module": {"id", "slug", "title", "term", "weeks", "week_themes", "labs", "library", "topics", "prerequisites",
               "guided_hours", "self_paced_hours"},
    "block": {"id", "term", "week", "weeks", "name", "guided_hours", "bootcamp_hours", "covers"},
    "term": {"id", "name", "weeks"},
    "topic": {"id", "name", "required"},
    "route": {"id", "name", "for", "deepen", "test_out", "capstone"},
    "component": {"name", "weight"},
    "rubric": {"criterion", "marks"},
    "band": {"band", "min_score", "capstone_min"},
    "rhythm": {"code", "day", "time", "hours", "kind"},
    "plan": {"id", "name", "note", "schedule"},
    "instalment": {"due", "amount"},
    "scholarship": {"name", "max_share", "criteria"},
    "refund": {"when", "refund"},
    "cost": {"item", "basis", "amount"},
}


def schema_errors(data: dict) -> list[str]:
    records = [("module", m) for m in data["modules"]]
    records += [("lab", lab) for m in data["modules"] for lab in m.get("labs", [])]
    records += [("block", b) for b in data["blocks"]] + [("term", t) for t in data["terms"]]
    records += [("topic", t) for t in data["topics"]] + [("route", r) for r in data["routes"]]
    records += [("component", c) for c in data["assessment"]["components"]]
    records += [("rubric", r) for r in data["assessment"]["capstone_rubric"]]
    records += [("band", b) for b in data["assessment"]["bands"]]
    records += [("rhythm", r) for r in data["program"]["weekly_rhythm"]]
    records += [("plan", p) for p in data["fee"]["payment_plans"]]
    records += [("instalment", x) for p in data["fee"]["payment_plans"] for x in p["schedule"]]
    records += [("scholarship", s) for s in data["fee"]["scholarships"]["categories"]]
    records += [("refund", r) for r in data["fee"]["refund_policy"]]
    records += [("cost", c) for c in data["unit_economics"]["fixed_costs"] + data["unit_economics"]["variable_costs_per_learner"]]
    out = []
    text_lists = {"fee.inclusions": data["fee"]["inclusions"], "fee.exclusions": data["fee"]["exclusions"],
                  "program.intakes": data["program"]["intakes"]}
    for m in data["modules"]:
        for key in ("week_themes", "library", "topics", "prerequisites"):
            text_lists[f"{m['id']}.{key}"] = m.get(key, [])
    for r in data["routes"]:
        for key in ("deepen", "test_out", "capstone"):
            text_lists[f"route {r['id']}.{key}"] = r[key]
    for where, items in text_lists.items():
        for item in items:
            if not isinstance(item, str):
                out.append(f"{where}: {item!r} is not text — quote values that contain ': ' or commas")
    for kind, rec in records:
        extra = set(rec) - SCHEMA[kind]
        if extra:
            label = rec.get("id") or rec.get("file") or rec.get("name") or rec.get("item") or rec.get("due") or rec
            out.append(f"{kind} {label!r}: unexpected keys {sorted(map(str, extra))} — quote values that contain commas")
        for key, value in rec.items():
            if value is None and key in SCHEMA[kind]:
                out.append(f"{kind} {rec}: '{key}' has no value")
    return out


def check(course: Course) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    err, warn = errors.append, warnings.append
    data = course.data
    if data.get("schema_version") != 1:
        err("schema_version must be 1")
    errors += schema_errors(data)

    # modules, folders, READMEs
    ids = list(course.modules)
    expected = [f"M{i:02d}" for i in range(len(ids))]
    if ids != expected:
        err(f"module ids must run M00, M01, ... in order; found {ids}")
    slugs = [m.slug for m in course.modules.values()]
    if len(set(slugs)) != len(slugs):
        err("module slugs must be unique")
    for m in course.modules.values():
        if m.term not in course.terms:
            err(f"{m.id}: unknown term {m.term}")
        if not m.folder.is_dir():
            err(f"{m.id}: missing folder {m.folder.relative_to(ROOT)}")
            continue
        if not m.readme.exists():
            err(f"{m.id}: missing {m.readme.relative_to(ROOT)}")
        else:
            text = m.readme.read_text(encoding="utf-8")
            if not text.startswith(f"# {m.id} · "):
                err(f"{m.id}: README must start with '# {m.id} · <title>'")
            for heading in MODULE_README_SECTIONS:
                if f"\n{heading}" not in text:
                    err(f"{m.id}: README lacks section '{heading}'")
            for w in m.week_list():
                if m.id not in ("M00",) and f"### Week {w} " not in text:
                    err(f"{m.id}: README lacks a '### Week {w} ...' plan")
        if len(m.week_themes) != m.n_weeks:
            err(f"{m.id}: {m.n_weeks} weeks but {len(m.week_themes)} week themes")
        t = course.terms.get(m.term)
        if t and not (t["weeks"][0] <= m.weeks[0] <= m.weeks[1] <= t["weeks"][1]):
            err(f"{m.id}: weeks {m.weeks} fall outside term {m.term} {t['weeks']}")
        for p in m.prerequisites:
            if p not in course.modules:
                err(f"{m.id}: unknown prerequisite {p}")
            elif course.modules[p].weeks[1] >= m.weeks[0] and p != "M00":
                err(f"{m.id}: prerequisite {p} does not finish before {m.id} starts")
        for t_id in m.topics:
            if t_id not in course.topics:
                err(f"{m.id}: unknown topic {t_id}")
        for lib in m.library:
            if importlib.util.find_spec(lib) is None:
                err(f"{m.id}: library module {lib} does not exist")

    # labs
    listed = {}
    for lab in course.labs():
        if not re.fullmatch(rf"lab_{lab.module.number:02d}[a-z]_[a-z0-9_]+\.py", lab.file):
            err(f"{lab.module.id}: lab name {lab.file} must look like lab_{lab.module.number:02d}a_topic.py")
        if lab.status not in ("ready", "planned"):
            err(f"{lab.file}: status must be ready or planned")
        if lab.status == "ready" and not lab.path.exists():
            err(f"{lab.file}: marked ready but {lab.path.relative_to(ROOT)} does not exist")
        if lab.status == "planned" and lab.path.exists():
            warn(f"{lab.file}: file exists but is marked planned — mark it ready")
        unknown = sorted(set(lab.extras) - set(pip_extras()))
        if unknown:
            err(f"{lab.file}: extras {unknown} are not optional dependencies in pyproject.toml "
                f"(choose from {pip_extras()})")
        listed[lab.path] = lab
    for path in sorted(CURRICULUM.glob("*/lab_*.py")):
        if path not in listed:
            err(f"{path.relative_to(ROOT)} is not listed in the manifest")

    # calendar: weeks 1..N covered exactly once by modules and calendar blocks
    n_weeks = int(course.program["duration_weeks"])
    owners: dict[int, list[str]] = {}
    for m in course.teaching_modules():
        for w in m.week_list():
            owners.setdefault(w, []).append(m.id)
    for b in course.calendar_blocks():
        owners.setdefault(b["week"], []).append(b["id"])
    for w in range(1, n_weeks + 1):
        if len(owners.get(w, [])) != 1:
            err(f"week {w} is covered by {owners.get(w, [])} (expected exactly one module or block)")
    extra = sorted(w for w in owners if not 1 <= w <= n_weeks)
    if extra:
        err(f"weeks outside 1..{n_weeks} in use: {extra}")
    for b in course.calendar_blocks():
        for mid in b.get("covers", []):
            if mid not in course.modules or course.modules[mid].weeks[1] >= b["week"]:
                err(f"{b['id']}: covers {mid}, which is unknown or not finished by week {b['week']}")
    for b in course.concurrent_blocks():
        lo, hi = b["weeks"]
        if not (1 <= lo <= hi <= n_weeks):
            err(f"{b['id']}: weeks {b['weeks']} outside the programme")

    # topics
    covered = {t for m in course.modules.values() for t in m.topics}
    for t in course.topics.values():
        if t["required"] and t["id"] not in covered:
            err(f"required topic '{t['name']}' is not covered by any module")

    # hours
    rhythm = sum(s["hours"] for s in course.program["weekly_rhythm"])
    if rhythm != HOURS_PER_MODULE_WEEK:
        err(f"weekly rhythm adds up to {rhythm} h, expected {HOURS_PER_MODULE_WEEK} h")

    # fee arithmetic
    f = course.fee
    total = D(f["total_all_inclusive"])
    base, gst = split_gst(total, f["gst_rate"])
    if abs(base * D(f["gst_rate"]) - gst) > PAISA:
        err(f"GST {gst} is not {f['gst_rate']} of the base {base} to the paisa")
    for plan in f["payment_plans"]:
        paid = sum(D(x["amount"]) for x in plan["schedule"])
        if paid != total:
            err(f"payment plan {plan['id']} adds up to {paid}, not {total}")
        if any(D(x["amount"]) <= 0 for x in plan["schedule"]):
            err(f"payment plan {plan['id']} has a non-positive instalment")
    for s in f["scholarships"]["categories"]:
        if not 0 < s["max_share"] <= 1:
            err(f"scholarship {s['name']}: max_share must be in (0, 1]")
    if not f["refund_policy"]:
        err("refund policy is empty")

    # unit economics
    e = course.economics
    if D(e["scholarship_share_of_base"]) > D(f["scholarships"]["budget_share_of_base"]):
        err("budgeted scholarships exceed the scholarship cap")
    ue = economics(course, int(course.program["cohort"]["target"]))
    be = ue["break_even"]
    cohort = course.program["cohort"]
    if be > cohort["maximum"]:
        err(f"break-even cohort {be:.1f} exceeds the maximum cohort {cohort['maximum']}")
    elif be > cohort["minimum_to_run"]:
        warn(f"break-even cohort {be:.1f} is above the minimum-to-run size {cohort['minimum_to_run']}")

    # cost lines whose basis is a product ("528 h × ₹8,000") must multiply out to the amount
    for c in e["fixed_costs"]:
        if "×" in c["basis"]:
            factors = [D(re.sub(r"[^\d.]", "", part)) for part in c["basis"].split("×")]
            product = D(1)
            for x in factors:
                product *= x
            if product != D(c["amount"]):
                err(f"fixed cost '{c['item']}': basis {c['basis']} = {product}, but amount is {c['amount']}")

    # assessment
    a = course.assessment
    weight = sum(D(c["weight"]) for c in a["components"])
    if weight != 1:
        err(f"assessment weights add up to {weight}, not 1")
    if sum(r["marks"] for r in a["capstone_rubric"]) != 100:
        err("capstone rubric marks must add up to 100")
    mins = [b["min_score"] for b in a["bands"]]
    if mins != sorted(mins, reverse=True):
        err("grade bands must be in descending order")

    # routes
    for r in course.routes.values():
        for mid in r["deepen"] + r["test_out"]:
            if mid not in course.modules:
                err(f"route {r['id']}: unknown module {mid}")
        if set(r["deepen"]) & set(r["test_out"]):
            err(f"route {r['id']}: a module cannot be both deepened and tested out")
    return errors, warnings


# ---------------------------------------------------------------------------
# Rendering generated sections
# ---------------------------------------------------------------------------

def md_table(header: list[str], rows: list[list], align: str | None = None) -> str:
    sep = align or "|".join("---" for _ in header)
    lines = ["| " + " | ".join(header) + " |", "|" + sep + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def rel_link(from_file: Path, to: Path) -> str:
    import os

    return os.path.relpath(to, from_file.parent).replace(os.sep, "/")


def lab_cell(lab: Lab, from_file: Path) -> str:
    if lab.status == "ready":
        return f"[{lab.code}]({rel_link(from_file, lab.path)})"
    return f"{lab.code} (planned)"


def pip_extras() -> list[str]:
    """Optional-dependency groups a learner may install (``pyproject.toml``, without ``dev``)."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    section = re.search(r"^\[project\.optional-dependencies\]\n(.*?)(?=^\[)", text, re.S | re.M)
    names = re.findall(r"^([a-z0-9_-]+)\s*=", section.group(1), re.M) if section else []
    return [n for n in names if n != "dev"]


def weeks_text(m: Module) -> str:
    if m.id == "M00":
        return "−3 to 0"
    return str(m.weeks[0]) if m.weeks[0] == m.weeks[1] else f"{m.weeks[0]}–{m.weeks[1]}"


def section_program_summary(course: Course, target: Path) -> str:
    p, f = course.program, course.fee
    base, gst = split_gst(f["total_all_inclusive"], f["gst_rate"])
    ready = sum(lab.status == "ready" for lab in course.labs())
    rows = [
        ["Duration", f"{p['duration_weeks']} weeks + {p['prework_weeks']} weeks of self-paced pre-work"],
        ["Format", p["format"]],
        ["Guided hours", f"{course.guided_hours()} (plus {p['prework_hours']} h pre-work and about "
                         f"{p['self_study_hours_per_week']} h/week self-study)"],
        ["Structure", f"{len(course.terms) - 1} terms, {len(course.teaching_modules())} modules + pre-work, "
                      f"{len(course.labs())} labs ({ready} ready)"],
        ["Cohort", f"target {p['cohort']['target']}, maximum {p['cohort']['maximum']}; intakes "
                   f"{' and '.join(p['intakes'])}"],
        ["Programme fee", f"**{inr(f['total_all_inclusive'], True)} all-inclusive** = {inr(base, True)} + "
                          f"GST {int(D(f['gst_rate']) * 100)}% {inr(gst, True)}"],
        ["Fee per guided hour", f"{inr(D(f['total_all_inclusive']) / course.guided_hours(), True)} "
                                f"({inr(base / course.guided_hours(), True)} before GST)"],
    ]
    return md_table(["", ""], rows)


def section_hours(course: Course, target: Path) -> str:
    rows = [[k, v] for k, v in course.hours().items()]
    rows.append(["**Total guided hours**", f"**{course.guided_hours()}**"])
    return md_table(["Component", "Hours"], rows, "---|---:")


def section_module_table(course: Course, target: Path) -> str:
    rows = []
    for m in course.modules.values():
        hours = f"{m.self_paced_hours} self-paced" if m.id == "M00" else m.guided_hours
        labs = ", ".join(lab_cell(lab, target) for lab in m.labs) or "–"
        title = f"[{m.title}]({rel_link(target, m.readme)})"
        rows.append([m.id, title, m.term, weeks_text(m), hours, labs, m.status])
    for b in course.calendar_blocks():
        rows.append(["–", f"{b['name']}", b["term"], b["week"], f"{b['guided_hours']} + {b['bootcamp_hours']} bootcamp",
                     "–", "–"])
    rows.sort(key=lambda r: (int(str(r[3]).split("–")[0].replace("−3 to 0", "-3")) if r[3] != "−3 to 0" else -3))
    return md_table(["#", "Module", "Term", "Weeks", "Guided h", "Labs", "Status"], rows)


def section_topic_coverage(course: Course, target: Path) -> str:
    rows = []
    for t in course.topics.values():
        mods = [m for m in course.modules.values() if t["id"] in m.topics]
        ready = [m.id for m in mods if m.status == "ready"]
        partial = [m.id for m in mods if m.status != "ready"]
        state = "covered" if ready else ("planned" if mods else "**missing**")
        cells = ", ".join([*ready, *(f"{x} (lab planned)" for x in partial)]) or "–"
        rows.append([t["name"] + ("" if t["required"] else " *(supporting)*"), cells, state])
    return md_table(["Topic", "Modules", "State"], rows)


def section_prerequisites(course: Course, target: Path) -> str:
    rows = [[m.id, m.title, ", ".join(m.prerequisites) or "–"] for m in course.modules.values()]
    return md_table(["Module", "Title", "Needs"], rows)


def section_lab_index(course: Course, target: Path) -> str:
    rows = []
    for lab in course.labs():
        link = f"[{lab.file}]({rel_link(target, lab.path)})" if lab.status == "ready" else lab.file
        rt = f"~{lab.runtime_s} s" if lab.status == "ready" else "–"
        rows.append([lab.code, lab.module.id, link, lab.title, lab.status, rt])
    return md_table(["Lab", "Module", "File", "What it does", "Status", "Runtime*"], rows)


def section_run_order(course: Course, target: Path) -> str:
    rows = []
    for i, lab in enumerate((lab for lab in course.labs() if lab.status == "ready"), start=1):
        extras = ", ".join(f"`{e}`" for e in lab.extras) or "–"
        rows.append([i, weeks_text(lab.module), f"[{lab.code}]({rel_link(target, lab.path)})", lab.module.id,
                     lab.title, f"~{lab.runtime_s} s", extras])
    planned = ", ".join(lab.code for lab in course.labs() if lab.status == "planned")
    table = md_table(["#", "Week", "Lab", "Module", "What it does", "Runtime", "Optional extras"], rows)
    return table + (f"\n\nPlanned, not yet released: {planned}." if planned else "")


def section_fee_breakup(course: Course, target: Path) -> str:
    f = course.fee
    base, gst = split_gst(f["total_all_inclusive"], f["gst_rate"])
    rows = [["Programme fee (before GST)", inr(base, True)],
            [f"GST @ {int(D(f['gst_rate']) * 100)}%", inr(gst, True)],
            ["**Total payable (all-inclusive)**", f"**{inr(f['total_all_inclusive'], True)}**"],
            ["Application fee (adjusted against the first payment)", inr(f["application_fee"], True)],
            ["Per guided hour, all-inclusive", inr(D(f["total_all_inclusive"]) / course.guided_hours(), True)]]
    return md_table(["Item", "Amount"], rows, "---|---:")


def section_payment_plans(course: Course, target: Path) -> str:
    f, out = course.fee, []
    for plan in f["payment_plans"]:
        rows, fee_sum, gst_sum = [], D(0), D(0)
        for x in plan["schedule"]:
            b, g = split_gst(x["amount"], f["gst_rate"])
            fee_sum, gst_sum = fee_sum + b, gst_sum + g
            rows.append([x["due"], inr(b, True), inr(g, True), inr(x["amount"], True)])
        if len(rows) > 1:
            rows.append(["**Total**", f"**{inr(fee_sum, True)}**", f"**{inr(gst_sum, True)}**",
                         f"**{inr(fee_sum + gst_sum, True)}**"])
        out.append(f"**Plan {plan['id']} — {plan['name']}.** {plan['note']}\n\n"
                   + md_table(["When", "Fee", "GST", "Total"], rows, "---|---:|---:|---:"))
    return "\n\n".join(out)


def section_scholarships(course: Course, target: Path) -> str:
    f = course.fee
    base, _ = split_gst(f["total_all_inclusive"], f["gst_rate"])
    rows = [[s["name"], f"up to {int(s['max_share'] * 100)}% of the fee before GST ({inr(base * D(s['max_share']))})",
             s["criteria"]] for s in f["scholarships"]["categories"]]
    cap = f["scholarships"]["budget_share_of_base"]
    return (md_table(["Scholarship", "Benefit", "Criteria"], rows)
            + f"\n\nOne scholarship per learner. Total scholarships are capped at {int(cap * 100)}% of the cohort's "
              "fee revenue before GST. GST is charged on the fee after the scholarship.")


def section_refunds(course: Course, target: Path) -> str:
    rows = [[r["when"], r["refund"]] for r in course.fee["refund_policy"]]
    return md_table(["When the learner withdraws", "Refund"], rows)


def section_unit_economics(course: Course, target: Path) -> str:
    sizes = course.economics["plan_cohort_sizes"]
    ues = {n: economics(course, n) for n in sizes}
    keys = ["Fee before GST", "Scholarships", "Marketing and admissions", "Payment processing",
            "Direct per-learner costs"]
    rows = [[k, *(inr(ues[n][k]) for n in sizes)] for k in keys]
    rows.append(["**Contribution**", *(f"**{inr(ues[n]['contribution'])}**" for n in sizes)])
    rows.append(["Fixed delivery costs", *(inr(ues[n]["fixed"]) for n in sizes)])
    rows.append(["**Surplus**", *(f"**{inr(ues[n]['surplus'])}** ({pct(ues[n]['margin'])})" for n in sizes)])
    ue = ues[sizes[0]]
    table = md_table(["Per cohort", *(f"{n} learners" for n in sizes)], rows, "---|" + "|".join("---:" for _ in sizes))
    return (table + f"\n\nContribution per learner: **{inr(ue['contribution_per_learner'])}**. "
            f"Fixed costs: **{inr(ue['fixed_total'])}** per cohort. "
            f"Break-even: **{ue['break_even']:.1f} learners** (the cohort runs only with "
            f"{course.program['cohort']['minimum_to_run']} or more).")


def section_fee_allocation(course: Course, target: Path) -> str:
    n = int(course.program["cohort"]["target"])
    ue = economics(course, n)
    f = course.fee
    total = D(f["total_all_inclusive"])
    _, gst = split_gst(total, f["gst_rate"])
    per = {k: -ue[k] / n for k in ("Scholarships", "Marketing and admissions", "Payment processing",
                                   "Direct per-learner costs")}
    fixed_share = ue["fixed_total"] / n
    surplus = ue["surplus"] / n
    rows = [["GST (paid to the government)", inr(gst), pct(gst / total)]]
    rows += [[k, inr(v), pct(v / total)] for k, v in per.items()]
    rows += [[f"Share of fixed delivery costs (÷ {n})", inr(fixed_share), pct(fixed_share / total)],
             ["Surplus (reinvestment and risk buffer)", inr(surplus), pct(surplus / total)],
             ["**Total**", f"**{inr(total)}**", "**100%**"]]
    return (md_table([f"Where one learner's fee goes (cohort of {n})", "Amount", "Share"], rows, "---|---:|---:")
            + "\n\nAmounts are rounded to the rupee. Scholarships are a cohort average: a learner without a "
              "scholarship funds part of another's.")


def section_price_sensitivity(course: Course, target: Path) -> str:
    sens = course.economics["sensitivity"]
    cohorts = sens["cohorts"]
    rows = []
    for t in sens["totals"]:
        cells = []
        for n in cohorts:
            ue = economics(course, n, total_override=t)
            cells.append(f"{inr(ue['surplus'])} ({pct(ue['margin'], 0)})")
        be = economics(course, cohorts[0], total_override=t)["break_even"]
        label = f"{inr(t)}" + (" ← plan" if D(t) == D(course.fee["total_all_inclusive"]) else "")
        rows.append([label, f"{be:.1f}", *cells])
    return md_table(["All-inclusive price", "Break-even learners", *(f"{n} learners" for n in cohorts)], rows,
                    "---|---:|" + "|".join("---:" for _ in cohorts))


def section_fixed_costs(course: Course, target: Path) -> str:
    items = course.economics["fixed_costs"]
    rows = [[x["item"], x["basis"], inr(x["amount"])] for x in items]
    rows.append(["**Total**", "", f"**{inr(sum(D(x['amount']) for x in items))}**"])
    return md_table(["Fixed cost (per cohort)", "Basis", "Amount"], rows, "---|---|---:")


def section_variable_costs(course: Course, target: Path) -> str:
    items = course.economics["variable_costs_per_learner"]
    rows = [[x["item"], inr(x["amount"])] for x in items]
    rows.append(["**Total per learner**", f"**{inr(sum(D(x['amount']) for x in items))}**"])
    return md_table(["Direct cost per learner", "Amount"], rows, "---|---:")


def section_inclusions(course: Course, target: Path) -> str:
    inc = "\n".join(f"- {x}" for x in course.fee["inclusions"])
    exc = "\n".join(f"- {x}" for x in course.fee["exclusions"])
    return f"**Included**\n\n{inc}\n\n**Not included**\n\n{exc}"


def section_weekly_rhythm(course: Course, target: Path) -> str:
    rows = [[s["code"], s["day"], s["time"], s["hours"], s["kind"]] for s in course.program["weekly_rhythm"]]
    total = sum(s["hours"] for s in course.program["weekly_rhythm"])
    rows.append(["", "", "", f"**{total}**", "**Guided hours per module week**"])
    return md_table(["Code", "Day", "Time (IST)", "Hours", "Session"], rows)


def section_calendar(course: Course, target: Path) -> str:
    rows = []
    m0 = course.modules["M00"]
    for i, theme in enumerate(m0.week_themes):
        rows.append([m0.weeks[0] + i, "T0", "M00 Pre-work", theme, "self-paced"])
    concurrent = course.concurrent_blocks()
    for w in range(1, int(course.program["duration_weeks"]) + 1):
        kind, obj = course.slot(w)
        term = course.term_of_week(w)["id"]
        notes = [b["id"] for b in concurrent if b["weeks"][0] <= w <= b["weeks"][1]]
        if kind == "module":
            theme = obj.week_themes[w - obj.weeks[0]]
            labs = [lab.code for lab in obj.labs] if w == obj.weeks[1] else []
            what = f"[{obj.id}]({rel_link(target, obj.readme)}) {obj.title}"
            extra = ", ".join([*(f"lab {c}" for c in labs), *(f"{n} +2 h" for n in notes)])
            rows.append([w, term, what, theme, extra or ""])
        else:
            rows.append([w, term, f"**{obj['id']}**", obj["name"], "exam + in-person bootcamp"])
    return md_table(["Week", "Term", "Module / block", "Theme", "Due / notes"], rows)


def section_assessment(course: Course, target: Path) -> str:
    a = course.assessment
    comp = md_table(["Component", "Weight"], [[c["name"], f"{int(D(c['weight']) * 100)}%"] for c in a["components"]], "---|---:")
    bands = md_table(["Band", "Overall score", "Capstone score"],
                     [[b["band"], f"≥ {b['min_score']}%", f"≥ {b['capstone_min']}%"] for b in a["bands"]])
    rubric = md_table(["Capstone criterion", "Marks"], [[r["criterion"], r["marks"]] for r in a["capstone_rubric"]], "---|---:")
    req = a["requirements"]
    return (f"{comp}\n\n{rubric}\n\n{bands}\n\nCertificate requirements: attendance of at least "
            f"{int(req['attendance_min'] * 100)}% of live sessions, all {req['bootcamps_required']} bootcamps, every "
            "ready lab submitted, and no upheld academic-integrity violation.")


def section_routes(course: Course, target: Path) -> str:
    rows = [[f"`{r['id']}`", r["name"], r["for"], ", ".join(r["deepen"]), ", ".join(r["test_out"]) or "–",
             "; ".join(r["capstone"])] for r in course.routes.values()]
    return md_table(["Route", "Persona", "For", "Go deeper in", "May test out of", "Suggested capstones"], rows)


def section_module_header(course: Course, module: Module, target: Path) -> str:
    term = course.terms[module.term]
    hours = f"{module.self_paced_hours} self-paced" if module.id == "M00" else f"{module.guided_hours} guided"
    labs = "<br>".join(f"{lab_cell(lab, target)} — {lab.title}" for lab in module.labs) or "–"
    prereq = ", ".join(f"[{p}]({rel_link(target, course.modules[p].readme)})" for p in module.prerequisites) or "–"
    topics = ", ".join(course.topics[t]["name"] for t in module.topics) or "–"
    lib = ", ".join(f"`{x}`" for x in module.library) or "–"
    rows = [["Term", f"{term['id']} · {term['name']}"], ["Weeks", weeks_text(module)], ["Hours", hours],
            ["Labs", labs], ["Library", lib], ["Prerequisites", prereq], ["Committed topics", topics],
            ["Status", module.status]]
    return md_table(["", ""], rows)


SECTIONS = {
    "program-summary": section_program_summary,
    "hours": section_hours,
    "module-table": section_module_table,
    "topic-coverage": section_topic_coverage,
    "prerequisites": section_prerequisites,
    "lab-index": section_lab_index,
    "run-order": section_run_order,
    "fee-breakup": section_fee_breakup,
    "inclusions": section_inclusions,
    "payment-plans": section_payment_plans,
    "scholarships": section_scholarships,
    "refund-policy": section_refunds,
    "unit-economics": section_unit_economics,
    "fixed-costs": section_fixed_costs,
    "fee-allocation": section_fee_allocation,
    "price-sensitivity": section_price_sensitivity,
    "variable-costs": section_variable_costs,
    "weekly-rhythm": section_weekly_rhythm,
    "calendar": section_calendar,
    "assessment": section_assessment,
    "routes": section_routes,
}
MARKER = re.compile(r"(<!-- BEGIN GENERATED: ([a-z-]+) -->\n)(.*?)(<!-- END GENERATED: \2 -->)", re.S)


def targets(course: Course) -> list[Path]:
    files = [ROOT / "README.md", CURRICULUM / "README.md", *sorted((ROOT / "course").glob("*.md"))]
    files += [m.readme for m in course.modules.values()]
    return [f for f in files if f.exists()]


def render_text(course: Course, path: Path, text: str) -> tuple[str, list[str]]:
    unknown = []
    module = next((m for m in course.modules.values() if m.readme == path), None)

    def replace(match: re.Match) -> str:
        name = match.group(2)
        if name == "module-header" and module is not None:
            body = section_module_header(course, module, path)
        elif name in SECTIONS:
            body = SECTIONS[name](course, path)
        else:
            unknown.append(name)
            return match.group(0)
        note = "<!-- generated from course/course.yaml by tools/route_manager.py; do not edit -->\n"
        return f"{match.group(1)}{note}{body}\n{match.group(4)}"

    return MARKER.sub(replace, text), unknown


def render(course: Course, check_only: bool = False) -> list[str]:
    problems = []
    for path in targets(course):
        text = path.read_text(encoding="utf-8")
        new, unknown = render_text(course, path, text)
        for name in unknown:
            problems.append(f"{path.relative_to(ROOT)}: unknown generated section '{name}'")
        if path in [m.readme for m in course.modules.values()] and "<!-- BEGIN GENERATED: module-header -->" not in text:
            problems.append(f"{path.relative_to(ROOT)}: missing the module-header generated section")
        if new != text:
            if check_only:
                problems.append(f"{path.relative_to(ROOT)} is out of date; run: python tools/route_manager.py render")
            else:
                path.write_text(new, encoding="utf-8")
                print(f"rendered {path.relative_to(ROOT)}")
    return problems


# ---------------------------------------------------------------------------
# Terminal views
# ---------------------------------------------------------------------------

def show_status(course: Course) -> None:
    labs = course.labs()
    ready = [lab for lab in labs if lab.status == "ready"]
    print(f"{course.program['code']} {course.program['version']}: {len(course.modules)} modules, "
          f"{len(labs)} labs ({len(ready)} ready, {len(labs) - len(ready)} planned), {course.guided_hours()} guided hours")
    for term in course.terms.values():
        mods = [m for m in course.modules.values() if m.term == term["id"]]
        print(f"\n{term['id']} {term['name']} (weeks {term['weeks'][0]}–{term['weeks'][1]})")
        for m in mods:
            marks = " ".join(f"{lab.code}{'' if lab.status == 'ready' else '*'}" for lab in m.labs)
            print(f"  {m.id} {m.title:<62} {weeks_text(m):>8}  {m.status:<8} {marks}")
    print("\n* = planned lab")


def show_week(course: Course, week: int) -> None:
    kind, obj = course.slot(week)
    if kind == "none":
        m0 = course.modules["M00"]
        if m0.weeks[0] <= week <= m0.weeks[1]:
            print(f"Week {week}: pre-work — {m0.week_themes[week - m0.weeks[0]]} (self-paced)")
            return
        sys.exit(f"week {week} is not in the programme")
    term = course.term_of_week(week)
    print(f"Week {week} · {term['id']} {term['name']}")
    if kind == "block":
        print(f"  {obj['id']}: {obj['name']} ({obj['guided_hours']} h + {obj['bootcamp_hours']} h bootcamp)")
        print(f"  Exam covers: {', '.join(obj['covers'])}")
    else:
        i = week - obj.weeks[0]
        print(f"  {obj.id} {obj.title} — week {i + 1} of {obj.n_weeks}: {obj.week_themes[i]}")
        for s in course.program["weekly_rhythm"]:
            print(f"    {s['day']:<9} {s['time']:<12} {s['code']}  {s['kind']}")
        if week == obj.weeks[1]:
            for lab in obj.labs:
                where = lab.path.relative_to(ROOT) if lab.status == "ready" else "(planned)"
                print(f"  Lab due: {lab.code} {lab.title} — {where}")
        print(f"  Guide: {obj.readme.relative_to(ROOT)}")
    for b in course.concurrent_blocks():
        if b["weeks"][0] <= week <= b["weeks"][1]:
            print(f"  Also: {b['name']}")


def show_route(course: Course, route_id: str) -> None:
    r = course.routes.get(route_id)
    if r is None:
        sys.exit(f"unknown route {route_id!r}; choose from {', '.join(course.routes)}")
    print(f"Route: {r['name']} — {r['for']}\n")
    for m in course.modules.values():
        mode = "deepen" if m.id in r["deepen"] else ("test-out option" if m.id in r["test_out"] else "core")
        marker = {"deepen": "▲", "test-out option": "○", "core": "·"}[mode]
        print(f"  {marker} {m.id} {m.title:<62} weeks {weeks_text(m):>8}  {mode}")
    print("\n▲ go deeper: stretch exercises, optional readings and the matching capstone options")
    print("○ test-out option: pass the module's challenge quiz in Week 0 and use the clinics for extension work")
    print(f"Suggested capstones: {'; '.join(r['capstone'])}")


def show_coverage(course: Course) -> None:
    for t in course.topics.values():
        mods = [m for m in course.modules.values() if t["id"] in m.topics]
        cells = ", ".join(f"{m.id}{'' if m.status == 'ready' else '*'}" for m in mods) or "MISSING"
        flag = "" if t["required"] else "  (supporting)"
        print(f"  {t['name']:<66} {cells}{flag}")
    print("\n* = module with a planned lab")


def show_fees(course: Course) -> None:
    f = course.fee
    base, gst = split_gst(f["total_all_inclusive"], f["gst_rate"])
    print(f"All-inclusive fee {inr(f['total_all_inclusive'], True)} = {inr(base, True)} + GST {inr(gst, True)}")
    print(f"Guided hours {course.guided_hours()} → {inr(D(f['total_all_inclusive']) / course.guided_hours(), True)} per hour")
    for plan in f["payment_plans"]:
        print(f"  Plan {plan['id']} {plan['name']}: " + " + ".join(inr(x["amount"]) for x in plan["schedule"]))
    for n in course.economics["plan_cohort_sizes"]:
        ue = economics(course, n)
        print(f"  {n} learners: surplus {inr(ue['surplus'])} ({pct(ue['margin'])} of fee revenue)")
    ue = economics(course, course.program["cohort"]["target"])
    print(f"Break-even: {ue['break_even']:.1f} learners; contribution per learner {inr(ue['contribution_per_learner'])}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="validate the manifest against the repository")
    r = sub.add_parser("render", help="rewrite generated sections in the docs")
    r.add_argument("--check", action="store_true", help="fail instead of writing if anything is stale")
    sub.add_parser("status")
    w = sub.add_parser("week")
    w.add_argument("n", type=int)
    rt = sub.add_parser("route")
    rt.add_argument("id")
    sub.add_parser("routes")
    sub.add_parser("coverage")
    sub.add_parser("fees")
    lb = sub.add_parser("labs")
    lb.add_argument("--ready", action="store_true")
    args = parser.parse_args(argv)

    course = Course.load()
    if args.cmd == "check":
        errors, warnings = check(course)
        errors += render(course, check_only=True)
        for w_ in warnings:
            print(f"warning: {w_}")
        for e in errors:
            print(f"error: {e}")
        if errors:
            return 1
        labs = course.labs()
        print(f"OK — {len(course.modules)} modules, {len(labs)} labs "
              f"({sum(lab.status == 'ready' for lab in labs)} ready), {course.guided_hours()} guided hours, "
              f"fee {inr(course.fee['total_all_inclusive'], True)}")
        return 0
    if args.cmd == "render":
        problems = render(course, check_only=args.check)
        for p in problems:
            print(f"error: {p}")
        return 1 if problems else 0
    if args.cmd == "status":
        show_status(course)
    elif args.cmd == "week":
        show_week(course, args.n)
    elif args.cmd == "route":
        show_route(course, args.id)
    elif args.cmd == "routes":
        for r_ in course.routes.values():
            print(f"  {r_['id']:<20} {r_['name']} — {r_['for']}")
    elif args.cmd == "coverage":
        show_coverage(course)
    elif args.cmd == "fees":
        show_fees(course)
    elif args.cmd == "labs":
        for lab in course.labs():
            if lab.status == "ready" or not args.ready:
                print(lab.path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
