"""Render validated DB/domain records into deterministic XCube YAML.

The renderer intentionally supports only the XCube configuration subset owned by
the platform.  It does not merge existing YAML files and never reads or writes the
developer's XEE config.yml.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import re
import unicodedata
from typing import Collection, Iterable, Sequence


_INVALID_IDENTIFIER = re.compile(r"[^a-z0-9-]+")
_MULTIPLE_DASHES = re.compile(r"-+")


class ConfigRenderError(ValueError):
    """Raised when domain input cannot safely produce an XCube config."""


def canonical_identifier(value: str) -> str:
    """Return a stable XCube-safe identifier derived from a domain identifier."""

    normalized = unicodedata.normalize("NFKD", value.strip()).encode("ascii", "ignore").decode()
    normalized = _INVALID_IDENTIFIER.sub("-", normalized.lower())
    normalized = _MULTIPLE_DASHES.sub("-", normalized).strip("-")
    if not normalized:
        raise ConfigRenderError("identifier must contain an ASCII letter or number")
    if not normalized[0].isalnum():
        raise ConfigRenderError("identifier must start with a letter or number")
    if len(normalized) > 120:
        raise ConfigRenderError("canonical identifier must not exceed 120 characters")
    return normalized


@dataclass(frozen=True)
class BandStyle:
    variable: str
    color_bar: str
    value_min: float
    value_max: float


@dataclass(frozen=True)
class RgbChannel:
    variable: str
    value_min: float
    value_max: float


@dataclass(frozen=True)
class RgbStyle:
    red: RgbChannel
    green: RgbChannel
    blue: RgbChannel


@dataclass(frozen=True)
class DatasetConfig:
    """DB/domain projection required to render one XCube dataset."""

    identifier: str
    path: str
    title: str
    description: str = ""
    variables: Sequence[str] = field(default_factory=tuple)
    bands: Sequence[BandStyle] = field(default_factory=tuple)
    rgb: RgbStyle | None = None
    style_identifier: str | None = None


@dataclass(frozen=True)
class RenderedConfig:
    yaml: str
    sha256: str
    dataset_count: int
    style_count: int


@dataclass(frozen=True)
class _PreparedDataset:
    identifier: str
    path: str
    title: str
    description: str
    style_identifier: str | None
    bands: tuple[BandStyle, ...]
    rgb: RgbStyle | None


def _quoted(value: str) -> str:
    # A JSON string is a valid YAML double-quoted scalar and is deterministic.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _number(value: float) -> str:
    number = float(value)
    if not math.isfinite(number):
        raise ConfigRenderError("style ranges must contain finite numbers")
    if number == 0:
        number = 0.0  # normalize negative zero
    rendered = format(number, ".15g")
    return rendered if any(char in rendered for char in ".eE") else f"{rendered}.0"


def _validate_range(minimum: float, maximum: float, label: str) -> None:
    if not math.isfinite(float(minimum)) or not math.isfinite(float(maximum)):
        raise ConfigRenderError(f"{label} range must contain finite numbers")
    if float(minimum) >= float(maximum):
        raise ConfigRenderError(f"{label} range must satisfy min < max")


def _prepare(record: DatasetConfig, allowed_color_bars: Collection[str]) -> _PreparedDataset:
    identifier = canonical_identifier(record.identifier)
    if not record.path.strip():
        raise ConfigRenderError(f"dataset {identifier}: path is required")
    if not record.title.strip():
        raise ConfigRenderError(f"dataset {identifier}: title is required")

    variables = {variable.strip() for variable in record.variables if variable.strip()}
    bands: list[BandStyle] = []
    seen_variables: set[str] = set()
    for band in record.bands:
        variable = band.variable.strip()
        if not variable:
            raise ConfigRenderError(f"dataset {identifier}: band variable is required")
        if variable in seen_variables:
            raise ConfigRenderError(f"dataset {identifier}: duplicate band variable {variable}")
        if variables and variable not in variables:
            raise ConfigRenderError(f"dataset {identifier}: unknown band variable {variable}")
        if band.color_bar not in allowed_color_bars:
            raise ConfigRenderError(
                f"dataset {identifier}: unsupported ColorBar {band.color_bar}"
            )
        _validate_range(band.value_min, band.value_max, f"band {variable}")
        bands.append(BandStyle(variable, band.color_bar, band.value_min, band.value_max))
        seen_variables.add(variable)

    rgb = record.rgb
    if rgb is not None:
        for name, channel in (("red", rgb.red), ("green", rgb.green), ("blue", rgb.blue)):
            variable = channel.variable.strip()
            if not variable:
                raise ConfigRenderError(f"dataset {identifier}: RGB {name} variable is required")
            if variables and variable not in variables:
                raise ConfigRenderError(
                    f"dataset {identifier}: unknown RGB {name} variable {variable}"
                )
            _validate_range(channel.value_min, channel.value_max, f"RGB {name}")

    has_style = bool(bands or rgb)
    style_identifier = None
    if has_style:
        style_identifier = canonical_identifier(
            record.style_identifier or f"{identifier}-style"
        )
    elif record.style_identifier:
        raise ConfigRenderError(
            f"dataset {identifier}: style identifier was provided without mappings"
        )

    return _PreparedDataset(
        identifier=identifier,
        path=record.path.strip(),
        title=record.title.strip(),
        description=record.description.strip(),
        style_identifier=style_identifier,
        bands=tuple(sorted(bands, key=lambda item: item.variable)),
        rgb=rgb,
    )


def render_config(
    datasets: Iterable[DatasetConfig], allowed_color_bars: Collection[str]
) -> RenderedConfig:
    """Validate, sort, and render datasets and styles to deterministic YAML."""

    allowed = frozenset(allowed_color_bars)
    if not allowed:
        raise ConfigRenderError("allowed ColorBar registry must not be empty")

    prepared = sorted((_prepare(item, allowed) for item in datasets), key=lambda item: item.identifier)
    dataset_ids = [item.identifier for item in prepared]
    if len(dataset_ids) != len(set(dataset_ids)):
        raise ConfigRenderError("dataset identifiers collide after canonicalization")
    style_ids = [item.style_identifier for item in prepared if item.style_identifier]
    if len(style_ids) != len(set(style_ids)):
        raise ConfigRenderError("style identifiers collide after canonicalization")

    lines: list[str] = ["Datasets:"]
    if not prepared:
        lines[0] = "Datasets: []"
    for item in prepared:
        lines.extend(
            [
                f"  - Identifier: {_quoted(item.identifier)}",
                f"    Path: {_quoted(item.path)}",
                f"    Title: {_quoted(item.title)}",
                f"    Description: {_quoted(item.description)}",
            ]
        )
        if item.style_identifier:
            lines.append(f"    Style: {_quoted(item.style_identifier)}")

    styled = [item for item in prepared if item.style_identifier]
    lines.append("Styles:" if styled else "Styles: []")
    for item in styled:
        lines.extend(
            [
                f"  - Identifier: {_quoted(item.style_identifier or '')}",
                "    ColorMappings:",
            ]
        )
        for band in item.bands:
            lines.extend(
                [
                    f"      {_quoted(band.variable)}:",
                    f"        ColorBar: {_quoted(band.color_bar)}",
                    f"        ValueRange: [{_number(band.value_min)}, {_number(band.value_max)}]",
                ]
            )
        if item.rgb:
            lines.append('      "rgb":')
            for yaml_name, channel in (
                ("Red", item.rgb.red),
                ("Green", item.rgb.green),
                ("Blue", item.rgb.blue),
            ):
                lines.extend(
                    [
                        f"        {yaml_name}:",
                        f"          Variable: {_quoted(channel.variable.strip())}",
                        f"          ValueRange: [{_number(channel.value_min)}, {_number(channel.value_max)}]",
                    ]
                )

    yaml = "\n".join(lines) + "\n"
    return RenderedConfig(
        yaml=yaml,
        sha256=hashlib.sha256(yaml.encode("utf-8")).hexdigest(),
        dataset_count=len(prepared),
        style_count=len(styled),
    )
