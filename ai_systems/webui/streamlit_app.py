"""Module for streamlit app."""

from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st

DEFAULT_API_BASE = os.environ.get("AI_API_BASE_URL", "http://localhost:8000")
DEFAULT_API_KEY = os.environ.get("AI_API_KEY", "")
TIMEOUT_SECONDS = 30.0


st.set_page_config(page_title="AOIP WebUI", page_icon="📊", layout="wide")
st.title("AOIP WebUI")
st.caption("Streamlit interface for the Agentic Operational Intelligence Platform API")


with st.sidebar:
    st.header("Connection")
    api_base = st.text_input("API Base URL", value=DEFAULT_API_BASE)
    api_key = st.text_input("X-API-Key", value=DEFAULT_API_KEY, type="password")
    st.markdown("Expected local defaults: `http://localhost:8000`, key `aoip-local-admin`.")


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


def _post(path: str, payload: dict[str, Any]) -> tuple[bool, Any]:
    url = f"{api_base.rstrip('/')}{path}"
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            resp = client.post(url, json=payload, headers=_headers())
        if resp.status_code >= 400:
            return False, {"status_code": resp.status_code, "detail": resp.text}
        return True, resp.json()
    except Exception as exc:  # pragma: no cover - UI error path
        return False, {"detail": str(exc)}


def _get(path: str, expect_json: bool = True) -> tuple[bool, Any]:
    url = f"{api_base.rstrip('/')}{path}"
    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
            resp = client.get(url, headers=_headers())
        if resp.status_code >= 400:
            return False, {"status_code": resp.status_code, "detail": resp.text}
        return True, resp.json() if expect_json else resp.text
    except Exception as exc:  # pragma: no cover - UI error path
        return False, {"detail": str(exc)}


tab_ask, tab_kpi, tab_obs = st.tabs(["Ask", "KPI", "Observability"])

with tab_ask:
    st.subheader("Ask the orchestration pipeline")
    col1, col2, col3 = st.columns(3)
    with col1:
        store_id = st.text_input("Store ID", value="245")
    with col2:
        region = st.text_input("Region", value="")
    with col3:
        persona = st.selectbox("Persona", ["store_manager", "executive"], index=0)

    question = st.text_area(
        "Question",
        value="Why are sales down and what actions should we take this week?",
        height=120,
    )

    if st.button("Run /ask", type="primary"):
        payload = {
            "question": question,
            "store_id": store_id or None,
            "region": region or None,
            "persona": persona,
            "session_id": "streamlit-ui",
        }
        ok, result = _post("/ask", payload)
        if not ok:
            st.error("Request failed")
            st.json(result)
        else:
            if isinstance(result, dict) and result.get("answer"):
                st.markdown("### Answer")
                st.write(result.get("answer"))
            if isinstance(result, dict) and result.get("recommendation"):
                st.markdown("### Recommendation")
                st.write(result.get("recommendation"))
            with st.expander("Raw response", expanded=False):
                st.json(result)

with tab_kpi:
    st.subheader("KPI snapshot")
    c1, c2 = st.columns(2)
    with c1:
        kpi_store_id = st.text_input("Store ID", value="245", key="kpi_store")
    with c2:
        kpi_region = st.text_input("Region", value="", key="kpi_region")

    if st.button("Run /kpi/enriched"):
        payload = {
            "store_id": kpi_store_id or None,
            "region": kpi_region or None,
        }
        ok, result = _post("/kpi/enriched", payload)
        if not ok:
            st.error("Request failed")
            st.json(result)
        else:
            records = result.get("records", []) if isinstance(result, dict) else []
            anomalies = result.get("anomalies", []) if isinstance(result, dict) else []
            st.metric("Records", len(records))
            st.metric("Anomalies", len(anomalies))
            if records:
                st.markdown("### Records")
                st.dataframe(records, use_container_width=True)
            if anomalies:
                st.markdown("### Anomalies")
                st.dataframe(anomalies, use_container_width=True)

with tab_obs:
    st.subheader("Observability")
    col_usage, col_metrics = st.columns(2)

    with col_usage:
        if st.button("Load /usage"):
            ok, result = _get("/usage", expect_json=True)
            if not ok:
                st.error("/usage failed")
                st.json(result)
            else:
                st.json(result)

    with col_metrics:
        if st.button("Load /metrics"):
            ok, result = _get("/metrics", expect_json=False)
            if not ok:
                st.error("/metrics failed")
                st.json(result)
            else:
                st.code(result[:5000], language="text")
