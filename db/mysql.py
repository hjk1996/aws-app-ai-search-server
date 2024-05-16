import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils import get_secret


# 환경변수에서 비밀 설정을 가져와서 SQLAlchemy 엔진을 생성
def get_engine():
    mysql_config = get_secret(os.environ["MYSQL_SECRET_NAME"])
    # SQLAlchemy 연결 문자열 생성
    connection_string = (
        f"mysql+mysqlconnector://{mysql_config['username']}:{mysql_config['password']}@"
        f"{mysql_config['host']}/{mysql_config['dbname']}?connect_timeout=3000"
    )
    engine = create_engine(connection_string, echo=True, pool_pre_ping=True)
    return engine


# SQLAlchemy 세션을 생성하여 반환
def get_db():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
