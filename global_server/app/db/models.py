# coding: utf-8
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Table, Text, text
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from db.database import Base

Base = declarative_base()
metadata = Base.metadata


class GlobalServerData(Base):
    __tablename__ = 'globalserverdata'

    global_serverid = Column(Text, primary_key=True)
    nickname = Column(Text)
    color = Column(Text)


class GlobalUserData(Base):
    __tablename__ = 'globaluserdata'

    global_userid = Column(Text, primary_key=True)
    fullname = Column(Text, nullable=False)
    emailaddr = Column(Text, nullable=False, unique=True)
    passwd = Column(Text, nullable=False, unique=True)
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    modified = Column(DateTime, nullable=False)


t_junctionuserdataglobalserverdata = Table(
    'junctionuserdataglobalserverdata', metadata,
    Column('global_userid', ForeignKey('globaluserdata.global_userid')),
    Column('global_serverid', ForeignKey('globalserverdata.global_serverid')),
    Column('admin', Boolean, nullable=False)
)


class ServerSessionData(Base):
    __tablename__ = 'serversessiondata'

    global_servcorrid = Column(Text, primary_key=True)
    global_serverid = Column(ForeignKey('globalserverdata.global_serverid'))
    ip = Column(INET, nullable=False)
    ont = Column(Text, nullable=False, unique=True)
    deviceinfo = Column(Text, nullable=False)
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    last_active = Column(DateTime, nullable=False)

    globalserverdata = relationship('GlobalServerData')


class UserSessionData(Base):
    __tablename__ = 'usersessiondata'

    global_usrcorrid = Column(Text, primary_key=True)
    global_userid = Column(ForeignKey('globaluserdata.global_userid'), unique=True)
    ip = Column(INET, nullable=False)
    deviceinfo = Column(Text, nullable=False)
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    last_active = Column(DateTime, nullable=False)

    globaluserdata = relationship('GlobalUserData', uselist=False)