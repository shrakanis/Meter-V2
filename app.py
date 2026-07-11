"""
app.py

Energy Monitor V2
"""

from bootstrap import create_app

app = create_app()

if __name__ == "__main__":

    app.application.start()

    try:

        app.run(
            host="0.0.0.0",
            port=5000,
            debug=True,
            use_reloader=False,
        )

    finally:

        app.application.stop()