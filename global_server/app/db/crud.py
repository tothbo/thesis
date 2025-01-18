from sqlalchemy.orm import Session
from sqlalchemy import delete, insert
from datetime import datetime

import db.models as models

from datetime import datetime
import secrets, string, uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

def gen_correlid(prefix: str = '', suffix: str = '') -> str:
    alphabet = string.ascii_letters + string.digits
    while True:
        result = ''.join(secrets.choice(alphabet) for _ in range(16))
        if (any(c.islower() for c in result) and
            any(c.isupper() for c in result) and
            sum(c.isdigit() for c in result) >= 3):
            return prefix+result+suffix

def get_user(db: Session, usertoken: str = None) -> models.GlobalUserData | None:
    # kikeresni a usert
    usersession = db.query(models.UserSessionData).filter(models.UserSessionData.global_usrcorrid == usertoken).first()
    try:
        assert type(usersession) == models.UserSessionData
    except AssertionError:
        return None
    user = db.query(models.GlobalUserData).filter(models.GlobalUserData.global_userid == usersession.global_userid).first()
    try:
        assert type(user) == models.GlobalUserData
    except AssertionError:
        return None
    
    return user

def auth_user(db: Session, emailaddr: str = None, passwd: str = None, ip: str = None, deviceinfo: str = None) -> tuple:
    # kikeresni a usert
    user = db.query(models.GlobalUserData).filter(models.GlobalUserData.emailaddr == emailaddr).first()
    try:
        assert type(user) == models.GlobalUserData
    except AssertionError:
        return (False,'invalid_username')
    
    try:
        ph.verify(user.passwd, passwd)
        
        sess = db.query(models.UserSessionData).filter(models.UserSessionData.global_userid == user.global_userid).first()
        try:
            assert type(sess) == models.UserSessionData
            db.delete(sess)
            db.commit()
        except AssertionError:
            pass

        sess = models.UserSessionData()
        sess.ip = ip
        sess.deviceinfo = deviceinfo
        sess.last_active = datetime.now()
        sess.global_userid = user.global_userid
        sess.global_usrcorrid = gen_correlid()
        
        db.add(sess)
        db.commit()

        return (True, sess.global_usrcorrid)

    except VerifyMismatchError:
        return (False,'invalid_pass')
    except Exception as e:
        raise AssertionError(e)


def change_pass(db: Session, userid: str = None, newpass: str = None) -> bool:
    # jelszo modosito
    user = db.query(models.GlobalUserData).filter(models.GlobalUserData.global_userid == userid).first()
    try:
        assert type(user) == models.GlobalUserData
    except AssertionError:
        return False

    user.passwd = ph.hash(newpass)
    user.modified = datetime.now()

    db.commit()

    return True

def register_user(db: Session, emailaddr: str = None, passwd: str = None, fullname: str = None) -> tuple:
    # kikeresni a usert
    user = db.query(models.GlobalUserData).filter(models.GlobalUserData.emailaddr == emailaddr).first()
    try:
        assert user == None
    except AssertionError:
        return (False,'already_registered')
    
    user = models.GlobalUserData()
    user.global_userid = emailaddr
    user.emailaddr = emailaddr
    user.fullname = fullname
    user.passwd = ph.hash(passwd)
    user.modified = datetime.now()

    db.add(user)
    db.commit()

    return (True,'')

def logout_user(db: Session, global_userid: str = None) -> None:
    sess = db.query(models.UserSessionData).filter(models.UserSessionData.global_userid == global_userid).first()
    db.delete(sess)
    db.commit()

def add_server(db: Session, nickname: str = '', color: str = '') -> str:
    serv = models.GlobalServerData()
    serv.color = '#ffffff'
    serv.color = '#f1f1f1' if color == '' else color
    serv.global_serverid = gen_correlid()
    serv.nickname = serv.global_serverid+"'s server" if nickname == '' else nickname
    
    db.add(serv)
    db.commit()

    return serv.global_serverid

def mod_server(db:Session, serverid: str, nickname: str = '', color: str = '#f1f1f1') -> bool:
    nickname == serverid if nickname == '' else nickname  
    serv = db.query(models.GlobalServerData).filter(models.GlobalServerData.global_serverid == serverid).first()

    try:
        assert type(serv) == models.GlobalServerData
    except AssertionError:
        return False
    
    serv.color = color
    serv.nickname = nickname
    db.commit()
    return True

def get_server(db: Session, serverid: str) -> models.GlobalServerData | None:
    serv = db.query(models.GlobalServerData).filter(models.GlobalServerData.global_serverid == serverid).first()
    try:
        assert type(serv) == models.GlobalServerData
    except AssertionError:
        return None
    return serv

def add_challenged_session(db: Session, serverid: str, ip: str, deviceinfo: str) -> str | None:
    challenge = secrets.token_urlsafe(32)
    serv = db.query(models.GlobalServerData).filter(models.GlobalServerData.global_serverid == serverid).first()
    
    try:
        assert type(serv) == models.GlobalServerData
    except AssertionError:
        return None
    
    sessi = db.query(models.ServerSessionData).filter(models.ServerSessionData.global_serverid == serverid).first()
    if type(sessi) == models.ServerSessionData:
        db.delete(sessi)
        db.commit()
    
    sessi = models.ServerSessionData()
    sessi.global_servcorrid = uuid.uuid4()
    sessi.global_serverid = serverid
    sessi.ip = ip
    sessi.last_active = datetime.now()
    sessi.deviceinfo = deviceinfo
    sessi.ont = challenge
    
    db.add(sessi)
    db.commit()
    return challenge

def get_session(db: Session, serverid: str) -> models.ServerSessionData | None:
    sess = db.query(models.ServerSessionData).filter(models.ServerSessionData.global_serverid == serverid).first()
    try:
        assert type(sess) == models.ServerSessionData
    except AssertionError:
        return None
    return sess

def assign_serveracc(db: Session, userid: str = '', serverid: str = '', admin: bool = False) -> bool:
    print('6')
    user = db.query(models.GlobalUserData).filter(models.GlobalUserData.global_userid == userid).first()
    print('6.5')
    try:
        assert type(user) == models.GlobalUserData
    except AssertionError:
        return False
    
    server = db.query(models.GlobalServerData).filter(models.GlobalServerData.global_serverid == serverid).first()
    print('7')
    try:
        assert type(server) == models.GlobalServerData
    except AssertionError:
        return False
    
    junction_data = [
        {'global_userid': user.global_userid, 'global_serverid': server.global_serverid, 'admin': admin}
    ]
    print('8')
    db.execute(insert(models.t_junctionuserdataglobalserverdata), junction_data)
    db.commit()

    return True

def revoke_serveracc(db: Session, userid: str = '', serverid: str = '') -> bool:
    user = db.query(models.GlobalUserData).filter(models.GlobalUserData.global_userid == userid).first()
    try:
        assert type(user) == models.GlobalUserData
    except AssertionError:
        return False

    server = db.query(models.GlobalServerData).filter(models.GlobalServerData.global_serverid == serverid).first()
    try:
        assert type(server) == models.GlobalServerData
    except AssertionError:
        return False

    statement = delete(models.t_junctionuserdataglobalserverdata).where(
        models.t_junctionuserdataglobalserverdata.c.global_userid == user.global_userid,
        models.t_junctionuserdataglobalserverdata.c.global_serverid == server.global_serverid
    )

    try:
        db.execute(statement)
        db.commit()
        return True
    except Exception as e:
        print(e)
    
    return False

def mod_serveraccess(db:Session,userid: str = '', serverid: str = '', admin: bool = False) -> bool:
    result = db.query(models.t_junctionuserdataglobalserverdata).filter(
        models.t_junctionuserdataglobalserverdata.c.global_userid == userid,
        models.t_junctionuserdataglobalserverdata.c.global_serverid == serverid
    ).update({"admin": admin})
    if result:
        db.commit()
        return True
    return False

def get_serveracc(db: Session, serverid: str = '') -> list:
    server = db.query(models.GlobalServerData).filter(models.GlobalServerData.global_serverid == serverid).first()
    try:
        assert type(server) == models.GlobalServerData
    except AssertionError:
        return []

    junction = db.query(models.t_junctionuserdataglobalserverdata).filter(
        models.t_junctionuserdataglobalserverdata.c.global_serverid == server.global_serverid
    ).all()

    if junction is None:
        return []
    return junction

def get_servers2(db: Session, userid: str) -> dict:
    user_servers = db.query(models.GlobalServerData).join(
        models.t_junctionuserdataglobalserverdata,
        models.GlobalServerData.global_serverid == models.t_junctionuserdataglobalserverdata.c.global_serverid
    ).filter(
        models.t_junctionuserdataglobalserverdata.c.global_userid == userid,
        models.t_junctionuserdataglobalserverdata.c.admin == False
    ).order_by(
        models.GlobalServerData.nickname
    ).all()

    admin_servers = db.query(models.GlobalServerData).join(
        models.t_junctionuserdataglobalserverdata,
        models.GlobalServerData.global_serverid == models.t_junctionuserdataglobalserverdata.c.global_serverid
    ).filter(
        models.t_junctionuserdataglobalserverdata.c.global_userid == userid,
        models.t_junctionuserdataglobalserverdata.c.admin == True
    ).order_by(
        models.GlobalServerData.nickname
    ).all()
    
    if len(user_servers) <= 0 and len(admin_servers) <= 0:
        return {}
    
    backdata = {
        'user':[],
        'admin':[],
        'offline':[]
    }

    for x in user_servers:
        stat = get_status(db, x.global_serverid)
        if stat['last_active'] == None:
            servdata = {
                'global_serverid':x.global_serverid,
                'color':x.color,
                'nickname':x.nickname
            }
            backdata['offline'].append(servdata)
        else:
            servdata = {
                'global_serverid':x.global_serverid,
                'color':x.color,
                'nickname':x.nickname
            }
            backdata['user'].append(servdata)
    for x in admin_servers:
        stat = get_status(db, x.global_serverid)
        if stat['last_active'] == None:
            servdata = {
                'global_serverid':x.global_serverid,
                'color':x.color,
                'nickname':x.nickname
            }
            backdata['offline'].append(servdata)
        else:
            servdata = {
                'global_serverid':x.global_serverid,
                'color':x.color,
                'nickname':x.nickname
            }
            backdata['admin'].append(servdata)
    return backdata


def get_servers(db: Session, userid: str, divided: bool = False) -> dict:
    servers = db.query(models.GlobalServerData).join(
        models.t_junctionuserdataglobalserverdata,
        models.GlobalServerData.global_serverid == models.t_junctionuserdataglobalserverdata.c.global_serverid
    ).filter(
        models.t_junctionuserdataglobalserverdata.c.global_userid == userid
    ).all()
    
    if len(servers) <= 0:
        return {}
    
    backdata = {
        'online':[],
        'offline':[]
    }

    if divided == False:
        backdata = {
            'servers':[],
        }
        for x in servers:
            servdata = {
                'global_serverid':x.global_serverid,
                'color':x.color,
                'nickname':x.nickname
            }
            backdata['servers'].append(servdata)
    else:
        for x in servers:
            stat = get_status(db, x.global_serverid)
            if stat['last_active'] == None:
                servdata = {
                    'global_serverid':x.global_serverid,
                    'color':x.color,
                    'nickname':x.nickname
                }
                backdata['offline'].append(servdata)
            else:
                servdata = {
                    'global_serverid':x.global_serverid,
                    'color':x.color,
                    'nickname':x.nickname
                }
                backdata['online'].append(servdata)
    return backdata

def get_status(db: Session, serverid: str) -> dict:
    server = db.query(models.GlobalServerData).filter(models.GlobalServerData.global_serverid == serverid).first()
    try:
        assert type(server) == models.GlobalServerData
    except AssertionError:
        return dict()
    
    status = db.query(models.ServerSessionData).filter(models.ServerSessionData.global_serverid == serverid).first()
    try:
        assert type(status) == models.ServerSessionData
    except AssertionError:
        return {'last_active':None}
    
    return {'last_active':status.last_active}

def auth_directaccess(db: Session, serverid: str, userid: str, admin: bool) -> bool:
    auth = db.query(models.t_junctionuserdataglobalserverdata).filter(models.t_junctionuserdataglobalserverdata.c.global_userid == userid,models.t_junctionuserdataglobalserverdata.c.global_serverid == serverid,models.t_junctionuserdataglobalserverdata.c.admin == admin).first()
    if auth is not None:
        return True
    return False
