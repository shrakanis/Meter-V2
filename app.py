from flask import Flask

from web.pages import pages


def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "EnergyMonitorV2"

    app.register_blueprint(pages)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )