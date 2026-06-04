"""Audio player widget: position updates must be marshaled to the main thread."""
import threading
import pytest

tk = pytest.importorskip("tkinter")


@pytest.fixture
def tk_root():
    """A withdrawn Tk root, or skip if no display is available."""
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no Tk display available")
    root.withdraw()
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass


@pytest.mark.gui
def test_off_thread_update_is_queued_not_applied(tk_root):
    from rss_audio_player_ui import AudioPlayerWidget
    w = AudioPlayerWidget(tk_root)

    main_tid = threading.get_ident()
    applied = {}
    orig = w._apply_player_update

    def traced(pos, dur):
        applied["tid"] = threading.get_ident()
        orig(pos, dur)

    w._apply_player_update = traced

    # Fire the player callback from a background thread (the monitor thread).
    t = threading.Thread(target=lambda: w._on_player_update(30.0, 60.0))
    t.start()
    t.join()

    # Off-thread call must NOT have touched widgets yet.
    assert w.time_label.cget("text") == "0:00"

    # Pump the event loop so the main-thread poller drains the queue.
    import time
    time.sleep(0.3)
    tk_root.update()

    assert w.time_label.cget("text") == "0:30"
    assert applied.get("tid") == main_tid  # applied on the main thread
    w.cleanup()
