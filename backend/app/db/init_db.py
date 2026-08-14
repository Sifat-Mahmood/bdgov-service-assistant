from app.db.session import engine, Base
from app.models import db_models  # noqa: F401 - import so models register with Base.metadata

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Tables created (or already existed).")

if __name__ == "__main__":
    init_db()