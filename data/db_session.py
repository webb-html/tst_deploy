import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

import os

SqlAlchemyBase = orm.declarative_base()

__factory = None

def global_init(db_file): # инициализация orm модели
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, '..', 'db', 'data.db')  # если db в корне проекта
    conn_str = f'sqlite:///{db_path}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)

def create_session() -> Session: # создание сессии
    global __factory
    return __factory()