"""GhostCommits Streamlit application."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

import streamlit as st
from dotenv import load_dotenv

from core.claim_validator import validate_findings
from core.evidence_builder import build_evidence_packet
from core.gemma_engine import analyze_with_gemma
from core.git_analyzer import analyze_repository
from core.github_client import GitHubClient, GitHubClientError, parse_public_github_url
from core.resurrection import build_resurrection_plan
from ui.charts import activity_timeline, signal_profile
from ui.components import (
    build_epitaph_png,
    evidence_list,
    findings_cards,
    load_css,
    metric_strip,
    repository_header,
    roadmap_list,
    sidebar_brand,
)

load_dotenv()

st.set_page_config(page_title="GhostCommits", layout="wide", initial_sidebar_state="expanded")
load_css()


@st.cache_data(ttl=900, show_spinner=False)
def investigate(url: str, deep_clone: bool) -> Tuple[Dict[str, Any], Dict[str, Any], list, list]:
    client = GitHubClient()
    ref, github_data = client.collect(url)
    max_mb = int(os.getenv("GHOSTCOMMITS_MAX_REPO_MB", "250"))
    git_data = analyze_repository(ref, max_repository_mb=max_mb) if deep_clone else None
    packet = build_evidence_packet(github_data, git_data)
    raw_analysis = analyze_with_gemma(packet, allow_fallback=True)
    analysis, warnings = validate_findings(raw_analysis, packet)
    plan = build_resurrection_plan(packet, analysis)
    return packet, analysis, plan, warnings


def load_sample() -> Tuple[Dict[str, Any], Dict[str, Any], list, list]:
    sample = json.loads(Path("examples/sample_report.json").read_text(encoding="utf-8"))
    return sample["evidence_packet"], sample["analysis"], sample["resurrection_plan"], []


st.markdown('<div class="ghost-brand"><div><strong>Ghost<i>Commits</i></strong><span>EVIDENCE-GROUNDED SOFTWARE ARCHAEOLOGY</span></div></div>', unsafe_allow_html=True)

with st.sidebar:
    sidebar_brand()
    st.markdown("### Investigation controls")
    deep_clone = st.toggle("Deep Git archaeology", value=True, help="Shallow-clones the repository to mine commit history and TODO markers. Repository code is never executed.")
    st.caption("Safety: public GitHub only · bounded clone · text inspection only · no repository code execution")
    st.divider()
    st.markdown("**Inference runtime**")
    st.code(os.getenv("GHOSTCOMMITS_MODEL", "gemma3:1b"), language=None)
    st.caption("If Ollama is unavailable, the app transparently switches to a deterministic evidence-based fallback.")

st.markdown(
    """<section class="hero">
    <div class="ghost-watermark" aria-hidden="true"><span>DEAD CODE</span><b>STILL SPEAKS</b></div>
    <div class="fog-layer fog-one" aria-hidden="true"></div><div class="fog-layer fog-two" aria-hidden="true"></div>
    <svg class="thorn-frame" viewBox="0 0 1200 430" preserveAspectRatio="none" aria-hidden="true">
        <path d="M0 52 C80 34 102 74 170 42 C221 18 255 23 314 0 M116 50 L78 9 M154 46 L195 13 M251 20 L235 0 M14 48 L40 87"/>
        <path d="M1200 352 C1138 335 1105 373 1047 347 C998 325 960 348 920 430 M1118 349 L1140 305 M1065 350 L1028 306 M980 365 L1015 402 M1184 348 L1162 390"/>
    </svg>
    <div class="whisper-field" aria-hidden="true">
        <span>the branch remembers</span><span>no maintainer answers</span><span>do not execute the dead</span>
    </div>
    <div class="hero-copy">
        <span class="signal">THE REPOSITORY STILL SPEAKS</span>
        <h1>Listen to the ghosts of <em>forgotten software.</em></h1>
        <p>Mine the last heartbeat, trace every claim to evidence, and turn an abandoned codebase into a safe, contributor-ready resurrection blueprint.</p>
    </div>
    <div class="evp-recorder" aria-hidden="true">
        <header><span><i></i> EVP ARCHIVE</span><b>REC 00:13:07</b></header>
        <div class="evp-screen">
            <svg viewBox="0 0 300 130" preserveAspectRatio="none">
                <path class="evp-echo" d="M0 66 L12 64 L20 70 L31 62 L43 67 L51 65 L62 69 L71 52 L79 78 L88 61 L98 67 L109 64 L120 69 L129 25 L138 105 L147 45 L157 82 L166 58 L177 70 L188 64 L198 67 L209 60 L220 71 L230 63 L241 68 L252 65 L263 69 L274 61 L286 67 L300 64"/>
                <path class="evp-voice" d="M0 66 L32 66 L46 64 L59 68 L73 65 L87 67 L101 64 L113 69 L123 57 L130 82 L137 35 L144 101 L151 29 L159 88 L167 49 L176 74 L185 60 L195 69 L206 64 L220 66 L236 63 L252 68 L268 65 L284 67 L300 65"/>
                <line class="evp-playhead" x1="0" y1="8" x2="0" y2="122"/>
            </svg>
            <span class="evp-event">VOICE FRAGMENT / UNRESOLVED</span>
            <small>13.7s</small>
        </div>
        <footer><span>20 HZ</span><b>CHANNEL GC-04</b><span>20 KHZ</span></footer>
    </div>
    <div class="haunt-telemetry" aria-hidden="true"><span>ARCHIVE_0413</span><span>VOICE: UNRESOLVED</span><span>LAST_HEARTBEAT: LOST</span></div>
    <div class="signal-readout" aria-hidden="true"><span>TRACE 04.13</span><i></i><b>LISTENING</b></div>
    </section>""",
    unsafe_allow_html=True,
)

url = st.text_input("Public GitHub repository", value="https://github.com/angular/angular.js", placeholder="https://github.com/owner/repository")
col_run, col_demo, col_space = st.columns([1, 1, 3])
run = col_run.button("Begin autopsy →", width="stretch", type="primary")
demo = col_demo.button("Load sample", width="stretch")

if run:
    try:
        parse_public_github_url(url)
        with st.status("Reconstructing the repository…", expanded=True) as status:
            st.write("Reading public GitHub metadata and recent issues")
            if deep_clone:
                st.write("Shallow-cloning history and extracting unfinished work")
            st.write("Building an immutable evidence packet")
            st.write("Asking Gemma for schema-constrained interpretation")
            packet, analysis, plan, warnings = investigate(url, deep_clone)
            status.update(label="Investigation complete", state="complete", expanded=False)
        st.session_state.report = (packet, analysis, plan, warnings)
    except ValueError as exc:
        st.error(str(exc))
    except GitHubClientError as exc:
        st.error(str(exc))
        st.info("GitHub unavailable? Use **Load sample** to explore the complete investigation workflow offline.")
    except RuntimeError as exc:
        st.error(str(exc))
        st.info("If metadata loaded but cloning failed, turn off **Deep Git archaeology** and retry.")
elif demo:
    st.session_state.report = load_sample()

if "report" not in st.session_state:
    st.info("Run an investigation or load the bundled evidence-backed sample to enter the case file.")
    st.stop()

packet, analysis, plan, warnings = st.session_state.report
repository_header(packet, analysis)
metric_strip(packet)
if warnings:
    st.warning("Claim validator: " + " ".join(warnings))

tab_autopsy, tab_whispers, tab_revival, tab_epitaph, tab_json = st.tabs(["01  AUTOPSY", "02  WHISPERS", "03  REVIVE", "04  EPITAPH", "05  RAW EVIDENCE"])

with tab_autopsy:
    left, right = st.columns([1.7, 1])
    with left:
        st.markdown("#### Development heartbeat")
        timeline = packet.get("timeline") or [{"month":"No local history", "commits":0}]
        st.plotly_chart(activity_timeline(timeline), use_container_width=True, config={"displayModeBar":False})
        st.caption("Commit counts are observed. Silence is not treated as proof of motive.")
    with right:
        st.markdown("#### Signal profile")
        st.plotly_chart(signal_profile(packet), use_container_width=True, config={"displayModeBar":False})
    st.markdown("#### Verified evidence")
    evidence_list(packet["evidence"])

with tab_whispers:
    st.markdown("#### Evidence-grounded interpretation")
    st.caption("Every visible claim survived evidence-ID validation. Unsupported model claims are removed before rendering.")
    findings_cards(analysis.get("findings", []))

with tab_revival:
    st.markdown("#### Resurrection blueprint")
    st.caption("A sequenced recovery plan designed for a new contributor—not an autonomous code execution agent.")
    roadmap_list(plan)

with tab_epitaph:
    st.markdown("#### The digital epitaph")
    st.markdown(f"> {analysis.get('epitaph', 'This repository left a trace worth preserving.')}")
    png = build_epitaph_png(packet, analysis)
    st.image(png, width="stretch")
    st.download_button("Download memorial card (PNG)", png, file_name=f"ghostcommits-{packet['repository']['full_name'].replace('/', '-')}.png", mime="image/png")

with tab_json:
    report = {"evidence_packet":packet, "analysis":analysis, "resurrection_plan":plan, "claim_validator_warnings":warnings}
    st.json(report, expanded=False)
    st.download_button("Download evidence report (JSON)", json.dumps(report, indent=2), file_name="ghostcommits-report.json", mime="application/json")
