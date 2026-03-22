import os
"""Compatibility entrypoint for the full Poornima backend server."""

from server import app, socketio


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        use_reloader=False,
    )
