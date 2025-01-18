from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Union, List
import re, secrets, string

import db.models as models


'''
    API-hoz
'''


### DOOR
def get_doordata(db: Session, **kwargs) ->  Union[models.DoorData, List[models.DoorData]]:
    query = db.query(models.DoorData).order_by(models.DoorData.nickname)
    for key, value in kwargs.items():
        if hasattr(models.DoorData, key):
            query = query.filter(getattr(models.DoorData, key) == value)
    return query.all()
def auth_door(db: Session, local_correlid: str, auth: bool) -> bool:
    row = db.query(models.DoorData).filter(models.DoorData.local_correlid == local_correlid).first()
    if row is not None:
        row.authorized = auth
        modified=datetime.now()
        db.commit()
        db.refresh(row)
        return True
    return False
def modify_doordata(db: Session, local_correlid: str, **kwargs) -> Optional[models.DoorData]:
    row = db.query(models.DoorData).filter(models.DoorData.local_correlid == local_correlid).first()
    if row is not None:
        for key, value in kwargs.items():
            if hasattr(models.DoorData, key):
                setattr(row,key,value if value != '' else None)
        row.modified = datetime.now()
        db.commit()
        db.expire(row)
        db.refresh(row)
        return row
    return None

### USER
def get_userdata(db: Session, **kwargs) ->  Union[models.UserData, List[models.UserData]]:
    query = db.query(models.UserData).order_by(models.UserData.name)
    for key, value in kwargs.items():
        if hasattr(models.UserData, key):
            query = query.filter(getattr(models.UserData, key) == value)
    return query.all()
def add_userdata(db: Session, name: str, **kwargs) -> bool:
    row = models.UserData()
    row.name = name
    for key, value in kwargs.items():
        if hasattr(models.DoorData, key):
            setattr(row,key,value if value != '' else None)
    row.last_logged = datetime.now()
    db.add(row)
    db.commit()
    db.refresh(row)
    return True
def remove_userdata(db: Session, local_userid: int) -> bool:
    row = db.query(models.UserData).filter(models.UserData.local_userid == local_userid).first()
    if row is not None:
        db.delete(row)
        db.commit()
        return True
    return False
def modify_userdata(db: Session, local_userid: int, **kwargs) -> models.UserData:
    row = db.query(models.UserData).filter(models.UserData.local_userid == local_userid).first()
    for key, value in kwargs.items():
        if hasattr(models.UserData, key):
            setattr(row,key,value if value != '' else None)
    row.last_logged = datetime.now()
    db.commit()
    db.refresh(row)
    return row
def fid_addimg(db: Session, local_userid: int, fid: bytes) -> bool:
    row = db.query(models.UserData).filter(models.UserData.local_userid == local_userid).first()
    try:
        assert type(row) == models.UserData
        row.fid = fid
        db.commit()
        db.refresh(row)
        return True
    except Exception as e:
        print(e)
        return False
    
### numplatedata
def get_numplatedata(db: Session, **kwargs) ->  Union[models.NumPlateData, List[models.NumPlateData]]:
    query = db.query(models.NumPlateData).order_by(models.NumPlateData.numplate)
    for key, value in kwargs.items():
        if hasattr(models.NumPlateData, key):
            query = query.filter(getattr(models.NumPlateData, key) == value)
    return query.all()
def add_numplatedata(db: Session, numplate: str, **kwargs) -> bool:
    row = models.NumPlateData()
    row.numplate = numplate
    for key, value in kwargs.items():
        if hasattr(models.DoorData, key):
            setattr(row,key,value if value != '' else None)
    row.last_logged = datetime.now()
    db.add(row)
    db.commit()
    db.refresh(row)
    return True
def remove_numplatedata(db: Session, numplateid: int) -> bool:
    row = db.query(models.NumPlateData).filter(models.NumPlateData.numplateid == numplateid).first()
    if row is not None:
        db.delete(row)
        db.commit()
        return True
    return False
def modify_numplatedata(db: Session, numplateid: int, **kwargs) -> models.NumPlateData:
    row = db.query(models.NumPlateData).filter(models.NumPlateData.numplateid == numplateid).first()
    for key, value in kwargs.items():
        if hasattr(models.NumPlateData, key):
            setattr(row,key,value if value != '' else None)
    row.last_logged = datetime.now()
    db.commit()
    db.refresh(row)
    return row

### Permission
def get_permission(db: Session, **kwargs) ->  Union[models.Permission, List[models.Permission]]:
    query = db.query(models.Permission)
    for key, value in kwargs.items():
        if hasattr(models.Permission, key):
            query = query.filter(getattr(models.Permission, key) == value)
    return query.all()
def add_permission(db: Session, group_name: str, **kwargs) -> bool:
    row = models.Permission()
    row.group_name = group_name
    for key, value in kwargs.items():
        if hasattr(models.Permission, key):
            setattr(row,key,value if value != '' else None)
    db.add(row)
    db.commit()
    db.refresh(row)
    return True
def remove_permission(db: Session, id: int) -> bool:
    row = db.query(models.Permission).filter(models.Permission.id == id).first()
    if row is not None:
        db.delete(row)
        db.commit()
        return True
    return False
def modify_permission(db: Session, id: int, **kwargs) -> models.Permission:
    row = db.query(models.Permission).filter(models.Permission.id == id).first()
    for key, value in kwargs.items():
        if hasattr(models.Permission, key):
            setattr(row,key,value if value != '' else None)
    db.commit()
    db.refresh(row)
    return row


### Permission connections
'''
    Permission connection contraints:
    - Only 2 operations are necessary per junction:
        - Add person/numplate to a group - CHECK BEFORE INSERT, that feature is enabled
        - Remove person/numplate from group
    - Because cascade option is present, separately removing entries isn't necessary, it will be done automatically
'''

def assign_pplgroup(db: Session, perm_id: int, local_userid: int) -> bool:
    perm = db.query(models.Permission).filter(models.Permission.id == perm_id).first()
    user = db.query(models.UserData).filter(models.UserData.local_userid == local_userid).first()
    if perm is not None and user is not None:
        perm.userdata.append(user)
        db.commit()
        return True
    return False
def revoke_pplgroup(db: Session, perm_id: int, local_userid: int) -> bool:
    perm = db.query(models.Permission).filter(models.Permission.id == perm_id).first()
    user = db.query(models.UserData).filter(models.UserData.local_userid == local_userid).first()
    if perm is not None and user is not None and user in perm.userdata:
        perm.userdata.remove(user)
        db.commit()
        return True
    return False
def assign_numplgroup(db: Session, perm_id: int, numplateid: int) -> bool:
    perm = db.query(models.Permission).filter(models.Permission.id == perm_id).first()
    numplate = db.query(models.NumPlateData).filter(models.NumPlateData.numplateid == numplateid).first()
    if perm is not None and numplate is not None:
        perm.numplatedata.append(numplate)
        db.commit()
        return True
    return False
def revoke_numplgroup(db: Session, perm_id: int, numplateid: int) -> bool:
    perm = db.query(models.Permission).filter(models.Permission.id == perm_id).first()
    numplate = db.query(models.NumPlateData).filter(models.NumPlateData.numplateid == numplateid).first()
    if perm is not None and numplate is not None and numplate in perm.numplatedata:
        perm.numplatedata.remove(numplate)
        db.commit()
        return True
    return False
def assign_doorgroup(db: Session, perm_id: int, correl_id: int) -> bool:
    perm = db.query(models.Permission).filter(models.Permission.id == perm_id).first()
    door = db.query(models.DoorData).filter(models.DoorData.local_correlid == correl_id).first()
    if perm is not None and door is not None:
        perm.doordata.append(door)
        db.commit()
        return True
    return False
def revoke_doorgroup(db: Session, perm_id: int, correl_id: int) -> bool:
    perm = db.query(models.Permission).filter(models.Permission.id == perm_id).first()
    door = db.query(models.DoorData).filter(models.DoorData.local_correlid == correl_id).first()
    if perm is not None and door is not None and door in perm.doordata:
        perm.doordata.remove(door)
        db.commit()
        return True
    return False

### DOOR AUTO COMM
def doordata_register(db: Session, ipaddr: str) -> str:
    if re.match(r'^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$', ipaddr):
        for _ in range(0,100):
            genr_cid = gen_correlid('DODA_serv_') 
            if db.query(models.DoorData).filter(models.DoorData.local_correlid == genr_cid).first() == None:
                row = models.DoorData(
                    local_correlid=genr_cid,
                    ipaddr=ipaddr,
                    nickname=ipaddr+"-s door",
                    location="out in the wilderness",
                    authorized=False,
                    modified=datetime.now()
                )
                db.add(row)
                db.commit()
                db.refresh(row)
                return genr_cid
    return None
def doordata_healthcheck(db: Session, local_correlid: str, ipaddr: str) -> str:
    if re.match(r'^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$', ipaddr):
        door = db.query(models.DoorData).filter(models.DoorData.local_correlid == local_correlid).first()
        if door != None:
            door.ipaddr = ipaddr
            door.modified = datetime.now()
            db.commit()
            db.refresh(door)
            if(door.authorized):
                return 'OK#1#1#0'
            else:
                return 'UNAUTHORIZED'
    return 'ERR'
def doordata_authcheck(db: Session, id: str) -> bool:
    door = db.query(models.DoorData).filter(models.DoorData.local_correlid == id).first()
    if door == None or door.authorized == False:
        return (False,None)
    return (True, None) if door.camera_link is not None else (True, door.camera_link)
def doordata_checkaccess(db: Session, id: str, usernc: str='', dync:str='') -> tuple:
    door = db.query(models.DoorData).filter(models.DoorData.local_correlid == id).first()
    user = None
    if usernc != '':
        user = db.query(models.UserData).filter(models.UserData.static_unq == usernc).first()
    elif dync != '':
        user = db.query(models.UserData).filter(models.UserData.local_userid == dync).first()
    if user is None or door is None:
        return (False,None)
    user_perm = db.query(models.Permission).join(models.t_junctionpermissionuserdata).filter(models.t_junctionpermissionuserdata.c.ref_local_userid == user.local_userid).all()
    door_perm = db.query(models.Permission).join(models.t_junctionpermissionsdoordata).filter(models.t_junctionpermissionsdoordata.c.ref_local_correlid == door.local_correlid).all()
    if user_perm is None or len(user_perm) <= 0 or door_perm is None or len(door_perm) <= 0:
        return (False,None)
    hasacc = None
    for uperm in user_perm:
        for locdoor in uperm.doordata:
            if locdoor.local_correlid == door.local_correlid and uperm.user_enabled:
                hasacc = True if hasacc is None or hasacc == True else False
            elif locdoor.local_correlid == door.local_correlid:
                hasacc = False
    return (hasacc, door.camera_link)
def doordata_checknumplateaccess(db: Session, doorid: str, numplid: str='') -> bool:
    door = db.query(models.DoorData).filter(models.DoorData.local_correlid == doorid).first()
    numpl = db.query(models.NumPlateData).filter(models.NumPlateData.numplateid == numplid).first()
    if numpl is None or door is None:
        return (False,None)
    numpl_perm = db.query(models.Permission).join(models.t_junctionpermissionnumplatedata).filter(models.t_junctionpermissionnumplatedata.c.ref_numplateid == numpl.numplateid).all()
    door_perm = db.query(models.Permission).join(models.t_junctionpermissionsdoordata).filter(models.t_junctionpermissionsdoordata.c.ref_local_correlid == door.local_correlid).all()
    if numpl_perm is None or len(numpl_perm) <= 0 or door_perm is None or len(door_perm) <= 0:
        return (False,None)
    hasacc = None
    for uperm in numpl_perm:
        for locdoor in uperm.doordata:
            if locdoor.local_correlid == door.local_correlid and uperm.numplate_enabled:
                hasacc = True if hasacc is None or hasacc == True else False
            elif locdoor.local_correlid == door.local_correlid:
                hasacc = False
    return hasacc
def doordata_raisedynotp(db: Session, local_userid: str):
    user = db.query(models.UserData).filter(models.UserData.local_userid == local_userid).first()
    assert type(user) == models.UserData

    user.dynamic_unq = str(int(user.dynamic_unq.split('#')[0])+1) +'#'+ user.dynamic_unq.split('#')[1]
    db.commit()
    db.refresh(user)



### CAMERA
def get_camera(db: Session, **kwargs) ->  Union[models.CameraLink, List[models.CameraLink]]:
    query = db.query(models.CameraLink).order_by(models.CameraLink.local_correlid)
    for key, value in kwargs.items():
        if hasattr(models.CameraLink, key):
            query = query.filter(getattr(models.CameraLink, key) == value)
    return query.all()
def add_camera(db: Session, host: str, **kwargs) -> bool:
    row = models.CameraLink()
    for _ in range(0,100):
        correlid = gen_correlid('DODA_cam_')
        if get_camera(db,local_correlid=correlid) == []:
            row.local_correlid = correlid
            row.rtsp_host = host
            for key, value in kwargs.items():
                if hasattr(models.CameraLink, key):
                    setattr(row,key,value if value != '' else None)
            row.modified = datetime.now()
            db.add(row)
            db.commit()
            db.refresh(row)
            return True
    return False
def remove_camera(db: Session, local_correlid: int) -> bool:
    row = db.query(models.CameraLink).filter(models.CameraLink.local_correlid == local_correlid).first()
    if row is not None:
        db.delete(row)
        db.commit()
        return True
    return False
def modify_camera(db: Session, local_correlid: int, **kwargs) -> models.CameraLink:
    row = db.query(models.CameraLink).filter(models.CameraLink.local_correlid == local_correlid).first()
    for key, value in kwargs.items():
        if hasattr(models.CameraLink, key):
            setattr(row,key,value if value != '' else None)
    row.modified = datetime.now()
    db.commit()
    db.refresh(row)
    return row


## LOGGING
def log_message(db: Session, broker: str, entype:str, entid:str, text:str) -> bool:
    messg = models.Statistic()
    messg.broker = broker
    messg.entitytype = entype
    messg.entityid = entid
    messg.teltx = text
    db.add(messg)
    db.commit()

def get_log(db: Session, page: int = 0, lim: int = 50) ->  List[models.Statistic]:
    offs = int(page)*int(lim)
    query = db.query(models.Statistic).order_by(models.Statistic.id.desc()).offset(offs).limit(lim).all()
    return query if query else None

def gen_correlid(prefix: str = '', suffix: str = '') -> str:
    alphabet = string.ascii_letters + string.digits
    while True:
        result = ''.join(secrets.choice(alphabet) for _ in range(16))
        if (any(c.islower() for c in result) and
            any(c.isupper() for c in result) and
            sum(c.isdigit() for c in result) >= 3):
            return prefix+result+suffix