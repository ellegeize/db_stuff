# postgres_client.py
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, create_engine, MetaData, Table, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"
POSTGRES_DB = "postgres"
# POSTGRES_HOST = "host.docker.internal"
POSTGRES_HOST = "localhost"
# POSTGRES_HOST = "127.0.0.1"
# POSTGRES_HOST = "172.18.0.5"
POSTGRES_PORT = "5432"


# Подключение к PostgreSQL
def get_postgres_session():
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    try:
        engine = create_engine(DATABASE_URL)
        connection = engine.connect()
        print("Соединение с PostgreSQL установлено.")
        connection.close()
        Session = sessionmaker(bind=engine)
        return Session(), engine
    except OperationalError as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
        exit(1)


# Определение таблицы
def create_files_table(session, engine):
    metadata = MetaData()

    # Таблица patients
    Table(
        "patients",
        metadata,
        Column("patient_id", Integer, primary_key=True),
        Column("first_name", String(100)),
        Column("last_name", String(100)),
        Column("birth_date", Date),
        Column("gender", String(10)),
        Column("contact_info", Text),
    )

    # Таблица files
    Table(
        "files",
        metadata,
        Column("file_id", Integer, primary_key=True),
        Column("file_name", String(255), nullable=False),
        Column("bucket_name", String(255), nullable=False),
        Column("file_path", String(255), nullable=False),
        Column("file_type", String(50), nullable=False),
        Column("patient_id", Integer, ForeignKey("patients.patient_id")),
        Column("image_type", String(50)),
        Column("processed", Boolean, default=False),
        Column("created_at", DateTime),
        Column("updated_at", DateTime),
    )

    # Таблица classification_results
    Table(
        "classification_results",
        metadata,
        Column("result_id", Integer, primary_key=True),
        Column("image_id", Integer, ForeignKey("files.file_id")),
        Column("classification_type", String(50)),
        Column("probability", Float),
        Column("model_version", String(50)),
        Column("created_at", DateTime),
    )

    # Таблица processed_data
    Table(
        "processed_data",
        metadata,
        Column("processed_data_id", Integer, primary_key=True),
        Column("image_id", Integer, ForeignKey("files.file_id")),
        Column("preprocessing_type", String(50)),
        Column("processed_data_path", String(255)),
        Column("created_at", DateTime),
    )

    # Таблица classification_models
    Table(
        "classification_models",
        metadata,
        Column("model_id", Integer, primary_key=True),
        Column("model_name", String(100)),
        Column("model_version", String(50)),
        Column("created_at", DateTime),
        Column("updated_at", DateTime),
    )

    # Таблица logs
    Table(
        "logs",
        metadata,
        Column("log_id", Integer, primary_key=True),
        Column("action", String(100)),
        Column("status", String(50)),
        Column("message", Text),
        Column("created_at", DateTime),
    )

    # Таблица users
    Table(
        "users",
        metadata,
        Column("user_id", Integer, primary_key=True),
        Column("username", String(100), unique=True),
        Column("password_hash", String(255)),
        Column("role", String(50)),
        Column("created_at", DateTime),
    )
    metadata.create_all(engine)

    metadata = MetaData()
    files_table = Table("files", metadata, autoload_with=engine)

    return files_table  # Возвращаем таблицу


def is_file_in_db(session, files_table, file_name):
    """Проверяет наличие записи о файле в базе данных."""
    result = session.execute(
        files_table.select().where(files_table.c.file_name == file_name)
    ).fetchone()
    return result is not None


def insert_file_record(session, files_table, file_name, bucket_name):
    """Добавляет запись о файле в базу данных."""
    try:
        session.execute(
            files_table.insert().values(
                file_name=file_name,
                bucket_name=bucket_name,
                file_path=f"s3://{bucket_name}/{file_name}",
            )
        )
        session.commit()
        print(f"Информация о файле {file_name} успешно добавлена в базу данных.")
    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении записи о файле {file_name}: {e}")
