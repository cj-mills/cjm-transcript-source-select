"""Demo application for cjm-transcript-source-select library.

Showcases the source selection component with real or mock transcription data.
Uses a real transcription database if available, falls back to mock data.

Run with: python demo_app.py
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path


# =============================================================================
# Configuration
# =============================================================================

# Real transcription database (relative to this file)
TEST_DB_PATH = Path(__file__).parent / "test_files" / "voxtral_hf_transcriptions.db"


# =============================================================================
# Mock Data Provider
# =============================================================================

@dataclass
class MockTranscriptionProvider:
    """Mock provider that returns sample transcription data."""

    _id: str = "mock:demo-transcriptions"
    _name: str = "Demo Transcriptions"
    _records: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Initialize with sample transcription data."""
        if not self._records:
            self._records = self._generate_sample_data()

    @property
    def provider_id(self) -> str:
        return self._id

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def provider_type(self) -> str:
        return "transcription_db"

    def is_available(self) -> bool:
        return True

    def query_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return mock records as SourceRecord-compatible dicts."""
        from cjm_source_provider.models import SourceRecord

        records = []
        for rec in self._records[:limit]:
            records.append(SourceRecord(
                record_id=rec["job_id"],
                media_path=rec.get("audio_path", ""),
                text=rec.get("text", ""),
                metadata=rec.get("metadata", {}),
                created_at=rec.get("created_at", ""),
                provider_id=self._id
            ))
        return records

    def get_source_block(self, record_id: str):
        """Get a specific record as a SourceBlock."""
        from cjm_source_provider.models import SourceBlock

        for rec in self._records:
            if rec["job_id"] == record_id:
                return SourceBlock(
                    id=rec["job_id"],
                    provider_id=self._id,
                    text=rec.get("text", ""),
                    media_path=rec.get("audio_path"),
                    metadata=rec.get("metadata", {})
                )
        return None

    def _generate_sample_data(self) -> List[Dict[str, Any]]:
        """Generate sample transcription records."""
        samples = [
            {
                "job_id": "job_demo_001",
                "audio_path": "/audio/sun_tzu_ch1.mp3",
                "text": (
                    "Laying Plans. Sun Tzu said: The art of war is of vital importance "
                    "to the State. It is a matter of life and death, a road either to "
                    "safety or to ruin. Hence it is a subject of inquiry which can on "
                    "no account be neglected."
                ),
                "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
                "metadata": {"chapter": 1, "duration": 45.2}
            },
            {
                "job_id": "job_demo_002",
                "audio_path": "/audio/sun_tzu_ch1.mp3",
                "text": (
                    "The art of war, then, is governed by five constant factors, to be "
                    "taken into account in one's deliberations, when seeking to determine "
                    "the conditions obtaining in the field."
                ),
                "created_at": (datetime.now() - timedelta(days=1, hours=1)).isoformat(),
                "metadata": {"chapter": 1, "duration": 32.1}
            },
            {
                "job_id": "job_demo_003",
                "audio_path": "/audio/sun_tzu_ch2.mp3",
                "text": (
                    "Waging War. Sun Tzu said: In the operations of war, where there are "
                    "in the field a thousand swift chariots, as many heavy chariots, and "
                    "a hundred thousand mail-clad soldiers, with provisions enough to "
                    "carry them a thousand li, the expenditure at home and at the front "
                    "will reach the total of a thousand ounces of silver per day."
                ),
                "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "metadata": {"chapter": 2, "duration": 58.7}
            },
            {
                "job_id": "job_demo_004",
                "audio_path": "/audio/sun_tzu_ch3.mp3",
                "text": (
                    "Attack by Stratagem. Sun Tzu said: In the practical art of war, the "
                    "best thing of all is to take the enemy's country whole and intact; "
                    "to shatter and destroy it is not so good."
                ),
                "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
                "metadata": {"chapter": 3, "duration": 41.5}
            },
            {
                "job_id": "job_demo_005",
                "audio_path": "/audio/sun_tzu_ch3.mp3",
                "text": (
                    "So, too, it is better to recapture an army entire than to destroy it, "
                    "to capture a regiment, a detachment or a company entire than to "
                    "destroy them."
                ),
                "created_at": (datetime.now() - timedelta(days=3, hours=2)).isoformat(),
                "metadata": {"chapter": 3, "duration": 28.3}
            },
        ]
        return samples


# =============================================================================
# Demo Application
# =============================================================================

def main():
    """Initialize source selection demo and start the server."""
    from fasthtml.common import fast_app, Div, H1, H2, P, Span, A, APIRouter

    from cjm_fasthtml_daisyui.core.resources import get_daisyui_headers
    from cjm_fasthtml_daisyui.core.testing import create_theme_persistence_script
    from cjm_fasthtml_daisyui.components.data_display.badge import badge, badge_colors
    from cjm_fasthtml_daisyui.utilities.semantic_colors import bg_dui, text_dui

    from cjm_fasthtml_tailwind.utilities.spacing import p, m
    from cjm_fasthtml_tailwind.utilities.sizing import container, max_w, w, h
    from cjm_fasthtml_tailwind.utilities.typography import font_size, font_weight, text_align
    from cjm_fasthtml_tailwind.core.base import combine_classes

    from cjm_fasthtml_app_core.components.navbar import create_navbar
    from cjm_fasthtml_app_core.core.routing import register_routes
    from cjm_fasthtml_app_core.core.htmx import handle_htmx_request
    from cjm_fasthtml_app_core.core.layout import wrap_with_layout

    # Import workflow state for state management
    from cjm_workflow_state.state_store import SQLiteWorkflowStateStore

    # Import selection library components
    from cjm_transcript_source_select.models import SelectionUrls
    from cjm_transcript_source_select.routes.init import init_selection_routers
    from cjm_transcript_source_select.components.step_renderer import render_selection_step

    # For SourceService we need a minimal plugin manager
    from cjm_plugin_system.core.manager import PluginManager
    from cjm_transcript_source_select.services.source import SourceService

    print("\n" + "=" * 70)
    print("Initializing cjm-transcript-source-select Demo")
    print("=" * 70)

    # Create FastHTML app
    app, rt = fast_app(
        pico=False,
        hdrs=[*get_daisyui_headers(), create_theme_persistence_script()],
        title="Source Selection Demo",
        htmlkw={'data-theme': 'light'},
        secret_key="demo-secret-key"
    )

    router = APIRouter(prefix="")

    print("  FastHTML app created")

    # -------------------------------------------------------------------------
    # Set up state store and source service
    # -------------------------------------------------------------------------

    # Create SQLite state store (temp file for demo)
    import tempfile
    temp_db = Path(tempfile.gettempdir()) / "cjm_source_select_demo_state.db"
    state_store = SQLiteWorkflowStateStore(temp_db)
    workflow_id = "demo-selection"
    print(f"  State store: {temp_db}")

    # Create mock plugin manager (no real plugins)
    plugin_manager = PluginManager()

    # Create source service
    source_service = SourceService(plugin_manager=plugin_manager)

    # Try to use real database, fall back to mock data
    from cjm_transcript_source_select.services.source import TranscriptionDBProvider

    # Track provider info for UI display
    provider_info = {"name": "", "record_count": 0, "is_mock": False}

    if TEST_DB_PATH.exists():
        # Use real transcription database
        real_provider = TranscriptionDBProvider(
            db_path=str(TEST_DB_PATH),
            name="Voxtral HF Transcriptions",
            provider_id="test:voxtral-hf"
        )
        source_service.add_provider(real_provider)
        records = real_provider.query_records(limit=100)
        provider_info = {"name": real_provider.provider_name, "record_count": len(records), "is_mock": False}
        print(f"  Real database loaded: {provider_info['name']}")
        print(f"  Records available: {provider_info['record_count']}")
    else:
        # Fall back to mock data
        mock_provider = MockTranscriptionProvider()
        source_service.add_provider(mock_provider)
        provider_info = {"name": mock_provider.provider_name, "record_count": len(mock_provider._records), "is_mock": True}
        print(f"  Mock provider added: {provider_info['name']}")
        print(f"  Sample records: {provider_info['record_count']}")

    # -------------------------------------------------------------------------
    # Initialize selection routes
    # -------------------------------------------------------------------------

    selection_routers, urls, routes = init_selection_routers(
        state_store=state_store,
        source_service=source_service,
        workflow_id=workflow_id,
        prefix="/selection"
    )

    print(f"  Selection routes initialized: {len(routes)} handlers")

    # -------------------------------------------------------------------------
    # Helper to get selection state
    # -------------------------------------------------------------------------

    def get_selection_state(sess) -> Dict[str, Any]:
        """Get current selection step state."""
        from cjm_fasthtml_interactions.core.state_store import get_session_id
        session_id = get_session_id(sess)

        # Get workflow state (returns empty dict if not found)
        state = state_store.get_state(workflow_id, session_id)

        # Initialize if empty
        if not state:
            state = {"step_states": {"selection": {}}, "source_tab": "db"}
            state_store.update_state(workflow_id, session_id, state)

        step_state = state.get("step_states", {}).get("selection", {})
        return {
            "selected_sources": step_state.get("selected_sources", []),
            "grouping_mode": step_state.get("grouping_mode", "media_path"),
            "external_db_paths": step_state.get("external_db_paths", []),
            "file_browser_state": step_state.get("file_browser_state", {}),
            "active_tab": state.get("source_tab", "db"),  # source_tab is at root level
        }

    # -------------------------------------------------------------------------
    # Page routes
    # -------------------------------------------------------------------------

    @router
    def index(request):
        """Homepage with demo overview."""

        def home_content():
            return Div(
                H1("Source Selection Demo",
                   cls=combine_classes(font_size._4xl, font_weight.bold, m.b(4))),

                P("A source selection component for transcript decomposition workflows.",
                  cls=combine_classes(font_size.lg, text_dui.base_content, m.b(6))),

                # Feature list
                Div(
                    H2("Features", cls=combine_classes(font_size._2xl, font_weight.bold, m.b(4))),
                    Div(
                        P("Federated database browsing via DuckDB", cls=m.b(2)),
                        P("Drag-drop queue ordering with SortableJS", cls=m.b(2)),
                        P("Two-zone keyboard navigation", cls=m.b(2)),
                        P("Collapsible preview panel", cls=m.b(2)),
                        P("External database file browser", cls=m.b(2)),
                        cls=combine_classes(text_align.left, max_w.md, m.x.auto, m.b(8))
                    ),
                ),

                # Status badge
                Div(
                    Span(
                        f"{provider_info['record_count']} {'sample' if provider_info['is_mock'] else ''} records",
                        cls=combine_classes(badge, badge_colors.success, m.r(2))
                    ),
                    Span(
                        provider_info['name'],
                        cls=combine_classes(badge, badge_colors.info)
                    ) if not provider_info['is_mock'] else None,
                    cls=m.b(8)
                ),

                # Demo link
                A(
                    "Open Selection Demo",
                    href=demo_selection.to(),
                    cls="btn btn-primary btn-lg"
                ),

                cls=combine_classes(
                    container, max_w._4xl, m.x.auto, p(8), text_align.center
                )
            )

        return handle_htmx_request(
            request, home_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    @router
    def demo_selection(request, sess):
        """Selection step demo page."""

        def selection_content():
            # Get current state
            state = get_selection_state(sess)

            # Get available sources and transcriptions
            sources = source_service.get_available_sources()
            transcriptions = source_service.query_transcriptions(limit=100)

            return Div(
                render_selection_step(
                    sources=sources,
                    transcriptions=transcriptions,
                    selected_sources=state["selected_sources"],
                    grouping_mode=state["grouping_mode"],
                    external_db_paths=state["external_db_paths"],
                    file_browser_state=state["file_browser_state"],
                    active_tab=state["active_tab"],
                    urls=urls,
                ),
                cls=combine_classes(w.full, h.full)
            )

        return handle_htmx_request(
            request, selection_content,
            wrap_fn=lambda content: wrap_with_layout(content, navbar=navbar)
        )

    # -------------------------------------------------------------------------
    # Navbar and route registration
    # -------------------------------------------------------------------------

    navbar = create_navbar(
        title="Source Selection Demo",
        nav_items=[
            ("Home", index),
            ("Selection", demo_selection),
        ],
        home_route=index,
        theme_selector=True
    )

    register_routes(
        app, router,
        *selection_routers
    )

    # Debug output
    print("\n" + "=" * 70)
    print("Registered Routes:")
    print("=" * 70)
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  {route.path}")
    print("=" * 70)
    print("Demo App Ready!")
    print("=" * 70 + "\n")

    return app


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading

    app = main()

    port = 5034
    host = "0.0.0.0"
    display_host = 'localhost' if host in ['0.0.0.0', '127.0.0.1'] else host

    print(f"Server: http://{display_host}:{port}")
    print(f"\n  http://{display_host}:{port}/                — Homepage")
    print(f"  http://{display_host}:{port}/demo_selection   — Selection demo")
    print()

    timer = threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{port}"))
    timer.daemon = True
    timer.start()

    uvicorn.run(app, host=host, port=port)
