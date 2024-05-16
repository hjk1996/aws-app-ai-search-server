from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()


class Picture(Base):
    __tablename__ = "Pictures"
    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, index=True)
    description = Column(String)
