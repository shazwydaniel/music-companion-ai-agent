"""Native local calculators and display of authoritative agent tool results."""

# 1. One safe renderer serves both local controls and ADK function-tool evidence.
import streamlit as st

from music_agent.calculations import transpose_progression, rhythm_numbers, practice_projection
from music_agent.presentation import chart_section_html, metadata_tags_html


def render_calculation(result: dict) -> None:
    """Show computed values, source-preserving chord lines and explicit assumptions."""
    if result.get("status") == "invalid_input":
        st.warning(result["message"])
        return
    st.write(result["summary"])
    outputs = result["outputs"]
    if "chords" in outputs:
        st.code(outputs["chords"], language=None)
    if "content" in outputs:
        for section in outputs["content"]:
            st.subheader(section["name"])
            st.html(chart_section_html(section))
    values = {key: value for key, value in outputs.items() if key not in {"content", "chords"}}
    if values:
        st.html(metadata_tags_html([(key.replace("_", " ").capitalize(), str(value)) for key, value in values.items()]))
    # Estimates must be qualified even when the detailed disclosure is closed.
    st.caption(result["assumptions"][0])
    with st.expander("Inputs, formula & assumptions"):
        st.json(result["inputs"])
        st.code(result["formula"], language=None, wrap_lines=True)
        for assumption in result["assumptions"]:
            st.write(assumption)


# 2. Local form submissions use exactly the same arithmetic as specialist tools.
def render_music_calculator(on_activity=None, *, expanded: bool = False) -> None:
    """Offer useful no-key calculations without submitting anything to Gemini."""
    with st.expander("Music calculator · works without AI", expanded=expanded):
        st.caption("Local Python calculations. For a situational question, ask Music Math in Chat when AI is available.")
        operation = st.selectbox("Calculation", ("Transpose chords", "Rhythm timing", "Practice scenario"), key="music-calculation-kind")
        with st.form("music-calculation-form"):
            if operation == "Transpose chords":
                chords = st.text_input("Chords to transpose", "C Am F G/B", key="calc-chords")
                source = st.text_input("From key", "C major", key="calc-source")
                target = st.text_input("To key", "D major", key="calc-target")
                action = lambda: transpose_progression(chords, source, target)
            elif operation == "Rhythm timing":
                bpm = st.number_input("Tempo (BPM)", 1.0, 400.0, 120.0, key="calc-bpm")
                bars = st.number_input("Bars", 1, 10000, 16, key="calc-bars")
                beats = st.number_input("Counted beats per bar", 1, 16, 4, key="calc-beats")
                subdivision = st.number_input("Equal subdivisions per beat", 1, 16, 2, key="calc-subdivision")
                st.caption("Use the same beat unit for BPM and beats per bar. In 6/8, choose 2 for dotted-quarter beats or 6 for eighth-note beats.")
                action = lambda: rhythm_numbers(bpm, bars, beats, subdivision)
            else:
                current = st.number_input("Current clean tempo (BPM)", 1.0, 400.0, 80.0, key="calc-current")
                target = st.number_input("Target clean tempo (BPM)", 1.0, 400.0, 120.0, key="calc-goal")
                gain = st.number_input("Assumed gain per week (BPM)", .1, 60.0, 5.0, key="calc-gain")
                minutes = st.number_input("Minutes per practice session", 1.0, 240.0, 20.0, key="calc-minutes")
                days = st.number_input("Practice days per week", 1, 7, 5, key="calc-days")
                adherence = st.number_input("Expected attendance (%)", 1.0, 100.0, 100.0, key="calc-attendance")
                st.caption("A planning scenario, not a skill prediction. Weekly gain is an assumption you choose; actual learning varies.")
                action = lambda: practice_projection(current, target, gain, minutes, days, adherence)
            submitted = st.form_submit_button("Calculate", key="music-calculate")
        if submitted:
            tool = "local_" + operation.lower().replace(" ", "_")
            if on_activity:
                on_activity({"agent": "music_math", "tool": tool, "status": "running"})
            result = action()
            st.session_state["last_music_calculation"] = result
            if on_activity:
                on_activity({"agent": "music_math", "tool": tool, "status": result["status"]})
        if result := st.session_state.get("last_music_calculation"):
            render_calculation(result)
