"""Reusable Streamlit components and the downloadable digital epitaph."""

from __future__ import annotations

import base64
import html
import io
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List

import streamlit as st
from PIL import Image, ImageDraw, ImageFont


def load_css(path: str = "ui/styles.css", sidebar_art: str = "assets/sidebar-haunt.png") -> None:
    css = Path(path).read_text(encoding="utf-8")
    art_path = Path(sidebar_art)
    if art_path.exists():
        encoded = base64.b64encode(art_path.read_bytes()).decode("ascii")
        css += f"""
        [data-testid="stSidebar"] {{
            position: relative;
            overflow: hidden;
            isolation: isolate;
            background: #0a0506 !important;
        }}
        [data-testid="stSidebar"]::before {{
            content: "";
            position: absolute;
            z-index: -2;
            inset: 0;
            background: url("data:image/png;base64,{encoded}") center bottom / cover no-repeat;
            opacity: .86;
            filter: grayscale(.58) sepia(.55) saturate(2.2) hue-rotate(306deg) brightness(.56) contrast(1.22);
        }}
        [data-testid="stSidebar"]::after {{
            content: "";
            position: absolute;
            z-index: -1;
            inset: 0;
            pointer-events: none;
            background:
                linear-gradient(180deg, rgba(10,5,6,.98) 0%, rgba(13,6,8,.9) 31%, rgba(24,8,12,.66) 52%, rgba(20,5,8,.14) 75%, rgba(8,3,4,.7) 100%),
                linear-gradient(90deg, rgba(10,5,6,.62) 0%, transparent 13%, transparent 87%, rgba(10,5,6,.62) 100%);
        }}
        [data-testid="stSidebar"] > div {{ position: relative; z-index: 1; background: transparent !important; }}
        """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def repository_header(packet: Dict[str, Any], analysis: Dict[str, Any]) -> None:
    repo = packet["repository"]
    model = html.escape(str(analysis.get("model", "unknown")))
    mode = "GEMMA SYNTHESIS" if analysis.get("used_ai") else "DETERMINISTIC FALLBACK"
    st.markdown(
        f"""<section class="case-header">
        <div><span class="micro">CASE FILE · {mode}</span><h2>{html.escape(repo['full_name'])}</h2>
        <p>{html.escape(repo['description'])}</p></div>
        <div class="model-stamp"><span>INTERPRETER</span><strong>{model}</strong></div>
        </section>""",
        unsafe_allow_html=True,
    )


def metric_strip(packet: Dict[str, Any]) -> None:
    stats = packet["statistics"]
    metrics = [
        (f"{stats.get('days_inactive') or 0:,}", "DAYS INACTIVE"),
        (f"{stats.get('open_items', 0):,}", "OPEN ITEMS"),
        (f"{stats.get('stars', 0):,}", "STARS"),
        (f"{len(packet.get('evidence', [])):02d}", "EVIDENCE RECORDS"),
    ]
    st.markdown(
        '<div class="metric-strip">' + "".join(
            f'<div><strong>{value}</strong><span>{label}</span></div>' for value, label in metrics
        ) + "</div>", unsafe_allow_html=True,
    )


def evidence_list(records: Iterable[Dict[str, Any]]) -> None:
    items = []
    for record in records:
        source_url = record.get("source_url") or record.get("url") or "#"
        items.append(
            f"""<a class="evidence" href="{html.escape(source_url)}" target="_blank">
            <span>{html.escape(record['id'])}</span><div><strong>{html.escape(record['claim'])}</strong>
            <small>{html.escape(str(record['value']))}</small></div><b>↗</b></a>"""
        )
    st.markdown('<div class="evidence-list">' + "".join(items) + "</div>", unsafe_allow_html=True)


def findings_cards(findings: List[Dict[str, Any]]) -> None:
    for index, finding in enumerate(findings, 1):
        uncertainty = " · ".join(finding.get("uncertainties", [])) or "No additional uncertainty supplied."
        st.markdown(
            f"""<article class="finding-card"><header><span>WHISPER {index:02d}</span>
            <strong>{finding['confidence']:.0%} confidence</strong></header>
            <h3>{html.escape(finding['finding'])}</h3>
            <p><b>Uncertainty:</b> {html.escape(uncertainty)}</p>
            <footer><span>Evidence: {html.escape(', '.join(finding['evidence_ids']))}</span></footer></article>""",
            unsafe_allow_html=True,
        )


def roadmap_list(steps: List[Dict[str, Any]]) -> None:
    cards = []
    for index, step in enumerate(steps, 1):
        cards.append(
            f"""<article class="road-step"><span>{index:02d}</span><div><small>{html.escape(step['phase'].upper())}</small>
            <h3>{html.escape(step['title'])}</h3><p>{html.escape(step['action'])}</p></div>
            <em>{html.escape(step['effort'])}</em></article>"""
        )
    st.markdown('<div class="roadmap">' + "".join(cards) + "</div>", unsafe_allow_html=True)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def build_epitaph_png(packet: Dict[str, Any], analysis: Dict[str, Any]) -> bytes:
    image = Image.new("RGB", (1600, 1000), "#080506")
    draw = ImageDraw.Draw(image)
    draw.rectangle((55, 55, 1545, 945), outline="#4B292E", width=3)
    draw.rectangle((55, 55, 70, 235), fill="#C82F4A")
    draw.text((105, 100), "GHOSTCOMMITS / DIGITAL EPITAPH", font=_font(24, True), fill="#C82F4A")
    repo = packet["repository"]
    stats = packet["statistics"]
    draw.text((105, 225), repo["full_name"], font=_font(74, True), fill="#EEE5D7")
    epitaph = analysis.get("epitaph", "The repository left a trace worth preserving.")
    words, lines, current = epitaph.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=_font(32)) > 1300 and current:
            lines.append(current); current = word
        else:
            current = candidate
    lines.append(current)
    draw.multiline_text((105, 350), "\n".join(lines[:4]), font=_font(32), fill="#AA998D", spacing=14)
    values = [(stats.get("days_inactive") or 0, "DAYS INACTIVE"), (stats.get("open_items", 0), "OPEN ITEMS"), (len(packet["evidence"]), "EVIDENCE")]
    for index, (value, label) in enumerate(values):
        x = 105 + index * 475
        draw.text((x, 665), f"{value:,}", font=_font(58, True), fill="#EEE5D7")
        draw.text((x, 735), label, font=_font(18), fill="#8D7A70")
    draw.text((105, 860), f"OBSERVED {date.today().isoformat()} · EVIDENCE OVER SÉANCE", font=_font(18, True), fill="#C82F4A")
    output = io.BytesIO(); image.save(output, format="PNG", optimize=True); return output.getvalue()
