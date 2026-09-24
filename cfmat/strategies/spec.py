"""``StrategySpec``: a strategy as data (rules, exits, parameters), JSON round-trip (Module 12).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path


@dataclass
class StrategySpec:
    name: str
    long_entry: list[str] = field(default_factory=list)
    long_exit: list[str] = field(default_factory=list)
    short_entry: list[str] = field(default_factory=list)
    short_exit: list[str] = field(default_factory=list)
    stop_atr: float | str | None = None      # protective stop, in ATRs from entry
    target_atr: float | str | None = None    # profit target, in ATRs from entry
    trail_atr: float | str | None = None     # trailing stop, in ATRs from the close
    max_bars: int | str | None = None        # time exit after this many bars
    atr_period: int = 14
    params: dict = field(default_factory=dict)
    category: str = "custom"
    description: str = ""

    def resolve(self, **overrides) -> StrategySpec:
        """Fill ``{placeholders}`` from ``params`` updated with ``overrides``."""
        p = {**self.params, **overrides}

        def fmt_rules(rules):
            return [r.format(**p) for r in rules]

        def fmt_num(v, cast):
            if isinstance(v, str):
                return cast(float(v.format(**p)))
            return v

        try:
            return replace(
                self, params=p,
                long_entry=fmt_rules(self.long_entry), long_exit=fmt_rules(self.long_exit),
                short_entry=fmt_rules(self.short_entry), short_exit=fmt_rules(self.short_exit),
                stop_atr=fmt_num(self.stop_atr, float), target_atr=fmt_num(self.target_atr, float),
                trail_atr=fmt_num(self.trail_atr, float), max_bars=fmt_num(self.max_bars, int),
            )
        except KeyError as exc:
            raise ValueError(f"strategy {self.name!r} needs a value for parameter {exc}") from exc

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, path: str | os.PathLike | None = None) -> str:
        """The spec as JSON text; also written to ``path`` when given."""
        text = json.dumps(self.to_dict(), indent=2)
        if path is not None:
            Path(path).write_text(text, encoding="utf-8")
        return text

    @classmethod
    def from_dict(cls, d: dict) -> StrategySpec:
        known = {f.name for f in fields(cls)}
        unknown = set(d) - known
        if unknown:
            raise ValueError(f"unknown strategy fields: {sorted(unknown)}")
        return cls(**d)

    @classmethod
    def from_json(cls, text_or_path: str | os.PathLike) -> StrategySpec:
        """Load from JSON text or from a file path (``str`` or ``Path``)."""
        if isinstance(text_or_path, str) and text_or_path.lstrip().startswith("{"):
            text = text_or_path
        else:
            text = Path(text_or_path).read_text(encoding="utf-8")
        return cls.from_dict(json.loads(text))
