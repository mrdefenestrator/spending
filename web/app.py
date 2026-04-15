import os

from flask import Flask
from sqlalchemy import create_engine

from spending.models import metadata
from spending.repository.categories import seed_categories


def create_app(db_path: str | None = None) -> Flask:
    app = Flask(__name__)

    if db_path is None:
        db_path = os.environ.get("SPENDING_DB", "spending.db")

    engine = create_engine(f"sqlite:///{db_path}")
    metadata.create_all(engine)
    app.config["engine"] = engine

    with engine.connect() as conn:
        seed_categories(conn, "configs/categories.yaml")

    from web.routes import register_blueprints

    register_blueprints(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5002)
