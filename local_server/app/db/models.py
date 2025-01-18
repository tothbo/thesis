# coding: utf-8
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Table, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET, BYTEA
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

class Statistic(Base):
    __tablename__ = 'statistics'

    id = Column(Integer, primary_key=True, server_default=text("nextval('statistics_id_seq'::regclass)"))
    broker = Column(Text, nullable=False)
    entitytype = Column(Text, nullable=False)
    entityid = Column(Text, nullable=False)
    teltx = Column(Text, nullable=False)
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

class CameraLink(Base):
    __tablename__ = 'cameralink'

    local_correlid = Column(Text, primary_key=True)
    rtsp_host = Column(Text, nullable=False)
    created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    modified = Column(DateTime, nullable=False)


class NumPlateData(Base):
    __tablename__ = 'numplatedata'

    numplateid = Column(Integer, primary_key=True, server_default=text("nextval('numplatedata_numplateid_seq'::regclass)"))
    numplate = Column(Text, nullable=False)
    nickname = Column(Text)
    last_logged = Column(DateTime, nullable=False)


class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, server_default=text("nextval('permissions_id_seq'::regclass)"))
    group_name = Column(Text, nullable=False, unique=True)
    user_enabled = Column(Boolean, nullable=False, server_default=text("false"))
    numplate_enabled = Column(Boolean, nullable=False, server_default=text("false"))

    doordata = relationship('DoorData', secondary='junctionpermissionsdoordata')
    userdata = relationship('UserData', secondary='junctionpermissionuserdata')
    numplatedata = relationship('NumPlateData', secondary='junctionpermissionnumplatedata')


class UserData(Base):
    __tablename__ = 'userdata'

    local_userid = Column(Integer, primary_key=True, server_default=text("nextval('userdata_local_userid_seq'::regclass)"))
    global_userid = Column(Text)
    name = Column(Text, nullable=False)
    fid = Column(BYTEA)
    static_unq = Column(Text)
    dynamic_unq = Column(Text)
    last_logged = Column(DateTime, nullable=False)


class DoorData(Base):
    __tablename__ = 'doordata'

    local_correlid = Column(Text, primary_key=True)
    ipaddr = Column(INET, nullable=False, unique=True)
    ont = Column(Text, unique=True)
    nickname = Column(Text, nullable=False)
    location = Column(Text)
    color = Column(Text)
    authorized = Column(Boolean, nullable=False)
    created = Column(DateTime, server_default=text("now()"))
    modified = Column(DateTime, nullable=False)
    camera_link = Column(ForeignKey('cameralink.local_correlid', ondelete='SET NULL', onupdate='CASCADE'),nullable=True)

    cameralink = relationship('CameraLink')


t_junctionpermissionnumplatedata = Table(
    'junctionpermissionnumplatedata', metadata,
    Column('ref_id', ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('ref_numplateid', ForeignKey('numplatedata.numplateid', ondelete='CASCADE'), primary_key=True, nullable=False)
)


t_junctionpermissionuserdata = Table(
    'junctionpermissionuserdata', metadata,
    Column('ref_id', ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('ref_local_userid', ForeignKey('userdata.local_userid', ondelete='CASCADE'), primary_key=True, nullable=False)
)


t_junctionpermissionsdoordata = Table(
    'junctionpermissionsdoordata', metadata,
    Column('ref_id', ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('ref_local_correlid', ForeignKey('doordata.local_correlid', ondelete='CASCADE'), primary_key=True, nullable=False)
)
