import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

postgres_user = os.getenv("POSTGRES_USER")
postgres_pass = os.getenv("POSTGRES_PASSWORD")
postgres_db_name = os.getenv("POSTGRES_DB")
postgres_port = os.getenv("POSTGRES_PORT")
postgres_host = os.getenv("POSTGRES_HOST")


def get_engine_url():
    return f"postgresql://{postgres_user}:{postgres_pass}@{postgres_host}:{postgres_port}/{postgres_db_name}"


engine = create_engine(get_engine_url())

# a sessionmaker(), also in the same scope as the engine
Session = sessionmaker(engine)


def db():
    '''
    callback function that should be used to retrieve a DB session for whatever function that needs to use it

    you must commit you session manually

    session is automatically closed after use (no need to do that manually)
    '''
    with Session() as session:
        yield session
