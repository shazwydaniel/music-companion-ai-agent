"""Session-owned live hierarchy driven by actual ADK callbacks, never a timer."""

# 1. A closed node registry keeps prompts, arguments and identifiers out of the UI.
from datetime import datetime
from html import escape
import json
from pathlib import Path

import streamlit as st

NODES = {
    'riffin_coordinator': ('Riffin’', 'Coordinator'),
    'songbook': ('Songbook', 'Guitar & piano chords'),
    'music_theory': ('Music Theory', 'Internal lessons'),
    'google_search_specialist': ('Web Search', 'Google grounding'),
    'music_math': ('Music Math', 'Python calculations'),
}
ERRORS = {'error', 'quota', 'timeout', 'credentials_unavailable', 'calibration_error', 'no_sources', 'blocked', 'out_of_scope', 'invalid_input'}
BENCHMARK = Path(__file__).resolve().parents[1] / 'docs' / 'EVALUATION_BENCHMARK_REPORT.json'


def activity_html(activity: dict) -> str:
    """Render source-free runtime states; node names come only from the registry."""
    nodes = []
    for name, (title, role) in NODES.items():
        current = activity.get(name, {})
        status = current.get('status', 'idle')
        kind = 'running' if status == 'running' else 'error' if status in ERRORS else 'done' if status != 'idle' else 'idle'
        label = 'Working' if kind == 'running' else status.replace('_', ' ').capitalize()
        nodes.append(
            f'<div class="agent-node {kind}" data-agent="{name}" data-state="{kind}">'
            f'<span class="agent-dot" aria-hidden="true"></span><div><strong>{title}</strong>'
            f'<small>{role}</small></div><span class="agent-state">{escape(label)}</span></div>'
        )
    # 1a. Keep the privacy note below the hierarchy without a redundant latest-event card.
    footer = (
        '<div class="agent-panel-footer">'
        '<small class="agent-privacy">Real routing events <span aria-hidden="true">·</span> Prompts hidden</small>'
        '</div>'
    )
    return (f'<div class="agent-graph" data-turn="{int(activity.get("_turn", 0))}" role="status" aria-live="polite">' + nodes[0]
            + '<div class="agent-branches" aria-hidden="true">↓ specialist agents</div>'
            + ''.join(nodes[1:]) + footer + '</div>')


# 2. The evaluation card reads a dated public artifact instead of a hardcoded score.
def evaluation_card_html() -> str:
    """Show the last generated benchmark's score and assistant-plus-judge spend."""
    try:
        data = json.loads(BENCHMARK.read_text(encoding='utf-8'))
        summary = data['summary']
        total = summary['total']
        passed, cases = int(summary['passed']), int(summary['cases'])
        run_date = datetime.fromisoformat(data['run_utc']).strftime('%d %b %Y')
        calls = int(total['model_calls'])
        input_tokens, output_tokens = int(total['input_tokens']), int(total['output_tokens'])
        estimate = total['estimated_usd']
        cost = f'≈ ${float(estimate):.6f} USD' if estimate is not None else 'Cost unavailable'
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        return ('<section class="riffin-eval-card" aria-label="Automated evaluation harness">'
                '<div class="riffin-eval-title"><span aria-hidden="true">✓</span>'
                '<strong>Automated evaluation</strong></div>'
                '<p>Run the golden cases to generate a score and telemetry report.</p>'
                '<code>python scripts/evaluate_agent.py --report docs/EVALUATION_BENCHMARK_REPORT.md</code>'
                '</section>')
    return ('<section class="riffin-eval-card" aria-label="Automated evaluation harness">'
            '<div class="riffin-eval-title"><span aria-hidden="true">✓</span>'
            '<strong>Automated evaluation</strong></div>'
            '<div class="riffin-eval-stats">'
            f'<strong>{passed}/{cases} passed</strong><strong>{escape(cost)}</strong></div>'
            f'<small>Gemini LLM-as-a-Judge <span aria-hidden="true">·</span> {run_date}</small>'
            f'<small>{calls:,} model calls <span aria-hidden="true">·</span> {input_tokens:,} input '
            f'<span aria-hidden="true">·</span> {output_tokens:,} output/thinking tokens</small>'
            '<small>Assistant + judge generation estimate; other API costs excluded.</small>'
            '<code>docs/EVALUATION_BENCHMARK_REPORT.md</code>'
            '</section>')


# 3. Native disclosure stays interactive while the inner graph receives live updates.
def render_activity_panel():
    """Return a per-session callback that writes only to this panel's placeholder."""
    with st.container(key='riffin-agent-pip'):
        st.html('<div class="riffin-pip-grip" title="Drag to move">⠿ &nbsp; Inside Riffin’</div>')
        with st.expander('Live Agent View', expanded=False, key='agent-disclosure'):
            target = st.empty()
            target.html(activity_html(st.session_state['agent_activity']))
        st.html('<div class="riffin-panel-spacer" aria-hidden="true"></div>')
        # 3a. Evaluation is a dated local check, separate from live session routing.
        with st.expander('Evaluation Harness', expanded=False, key='evaluation-disclosure'):
            st.html(evaluation_card_html())

    def update(event: dict) -> None:
        """Observe before/after callbacks in the current Streamlit script thread."""
        agent = event.get('agent')
        if agent not in NODES:
            return
        state = st.session_state['agent_activity']
        previous = state.get(agent, {})
        if previous.get('status') in ERRORS and event['status'] == 'completed':
            return
        state[agent] = {'tool': event['tool'], 'status': event['status']}
        state['_latest'] = state[agent]
        target.html(activity_html(state))

    return update
