from sqlalchemy.orm import Session
from pydantic import BaseModel

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

import numpy as np

from db.database import SessionLocal, engine
import db.models as models
import db.crud as crud
import os, json, requests, base64, sys, asyncio, socket, cv2, pyotp, time

from PIL import Image
from io import BytesIO

from deepface import DeepFace

from ddrpc.DDRPC import DDRPCServer

required_keys = [('host_port',int),('cert_storage',str),('secret_key',str),('algorith',str),('key_expires',int),('rpc_host',str),('db_host',str)]
with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)
#assert all(key in CONFIG and isinstance(CONFIG[key], vartype) and (vartype is str and CONFIG[key] != '') for key, vartype in required_keys)


async def on_message(jsn: dict, serverid: str) -> dict:
    db = SessionLocal()

    """
        HANDLING INCOMMING IMAGES
        - user sends in one image at a time
        - this is saved to the database as base64 text
        {
            destination = self.serverid,
            upload = 'image',
            image = 'binary of the image'
        }
    """


    if jsn.get('upload') == 'image' and jsn.get('destination') == serverid:
        crud.log_message(db,'rpc_handler','user_selfservice',jsn.get('userid','?'),jsn.get('caller','?')+' uploaded images for '+jsn.get('userid','?'))
        return_dict = {
            "status":"OK",
            "code":"200",
            "answer":[]
        }

        try:
            img1_data = jsn.get('image1','').encode('utf-8')
            img1_base = base64.b64decode(img1_data)
            img2_data = jsn.get('image2','').encode('utf-8')
            img2_base = base64.b64decode(img2_data)

            img1_array = np.frombuffer(img1_base, np.uint8)
            img1_num = cv2.imdecode(img1_array, cv2.IMREAD_COLOR)

            img2_array = np.frombuffer(img2_base, np.uint8)
            img2_num = cv2.imdecode(img2_array, cv2.IMREAD_COLOR)

            res = DeepFace.verify(img1_num, img2_num)
            if res['verified'] and np.array_equal(img1_num, img2_num) == False:
                crud.fid_addimg(db, jsn.get('userid'), img1_base)
                return_dict['answer'] = 'Images saved to user.'
            else:
                return_dict = {
                    "status": "ERR",
                    "code": "409",
                    "exception": "Given faces do not match eachother."
                }
        except:
            return_dict = {
                "status": "ERR",
                "code": "400",
                "exception": "Exception while processing images."
            }


        """
            USER / SERVER connection
            - Server connection (has a "destination" tag) > from admin users
            - User connection (has a "processor" tag) > from non-admin users, who have a global id
        """

    elif jsn.get('upload','') != 'image' and jsn.get('destination') == serverid:
        return_dict = {
            "status":"OK",
            "code":"200",
            "answer":[]
        }

        print(" > ["+jsn.get('caller','unknown')+"] "+jsn.get('entitytype','unknwon entitytype')+" - "+jsn.get('action','unknwon action')+" - "+jsn.get('entityid', 'unknown entityid')+"")


        ### STATs

        ### here entityid is the page! 1 page = 100 entries.
        ### stat requests are NOT logged, because it would make it impossible to go back to the first log - and its a bit unnecessary,
        ### since theres no interface provided to directly delete them
        if jsn.get('entitytype') == "statistics" and jsn.get('action') == "get" and jsn.get('entityid', None) == None:
            entries = crud.get_log(db)
            for en in entries:
                cm = {
                    'id':en.id,
                    'broker':en.broker,
                    'entitytype':en.entitytype,
                    'entityid':en.entityid,
                    'teltx':en.teltx,
                    'created':en.created.strftime('%Y.%m.%d. %H:%M')
                }
                return_dict['answer'].append(cm)
        elif jsn.get('entitytype') == "statistics" and jsn.get('action') == "get" and jsn.get('entityid', None) != None:
            ## entityid is the page number in this instance
            entries = crud.get_log(db,jsn.get('entityid', 0))
            for en in entries:
                cm = {
                    'id':en.id,
                    'broker':en.broker,
                    'entitytype':en.entitytype,
                    'entityid':en.entityid,
                    'teltx':en.teltx,
                    'created':en.created.strftime('%Y.%m.%d. %H:%M')
                }
                return_dict['answer'].append(cm)

        ### CAMERAS
        elif jsn.get('entitytype') == "camera" and jsn.get('action') == "get" and jsn.get('entityid', None) == None:
            crud.log_message(db,'rpc_handler','camera','all',jsn.get('caller','?')+' requested all cameras')
            dbdata = crud.get_camera(db)
            for x in dbdata:
                camera = {
                    "local_correlid":x.local_correlid,
                    "rtsp_host":x.rtsp_host,
                    "modified":x.modified.strftime('%Y.%m.%d. %H:%M')
                }
                return_dict['answer'].append(camera)
        elif jsn.get('entitytype') == "camera" and jsn.get('action') == "get" and jsn.get('entityid', None) != None:
            crud.log_message(db,'rpc_handler','camera',jsn.get('entityid','?'),jsn.get('caller','?')+' requested camera '+jsn.get('entityid','?'))
            dbdata = crud.get_camera(db, local_correlid=jsn.get('entityid'))[0]
            camera = {
                "local_correlid":dbdata.local_correlid,
                "rtsp_host":dbdata.rtsp_host,
                "modified":dbdata.modified.strftime('%Y.%m.%d. %H:%M')
            }
            return_dict['answer'] = camera
        elif jsn.get('entitytype') == "camera" and (jsn.get('action') == "add" or jsn.get('action') == "remove") and jsn.get('entityid',None) != None:
            if jsn.get('action') == "add":
                crud.log_message(db,'rpc_handler','camera',jsn.get('entityid','?'),jsn.get('caller','?')+' added camera '+jsn.get('entityid','?'))
                ## itt az entityid egy string lesz, ami gyakorlatilag a név!
                validated = dict()
                if isinstance(jsn.get('extra'), dict):
                    validated = {key: value for key, value in jsn.get('extra').items() if hasattr(models.CameraLink, key)}
                if crud.add_camera(db,jsn.get('entityid'), **validated):
                    return_dict['answer'] = True
                else:
                    return_dict['answer'] = False
            elif jsn.get('action') == "remove":
                crud.log_message(db,'rpc_handler','camera',jsn.get('entityid','?'),jsn.get('caller','?')+' removed camera '+jsn.get('entityid','?'))
                ## törlésnél nem név kell, hanem maga az id!
                if crud.remove_camera(db,jsn.get('entityid')):
                    return_dict['answer'] = True
                else:
                    return_dict['answer'] = False
        elif jsn.get('entitytype') == "camera" and jsn.get('action') == "modify" and jsn.get('entityid',None) != None:
            if isinstance(jsn.get('extra'), dict):
                crud.log_message(db,'rpc_handler','camera',jsn.get('entityid','?'),jsn.get('caller','?')+' made modifications for camera '+jsn.get('entityid','?'))
                validated = {key: value for key, value in jsn.get('extra').items() if hasattr(models.CameraLink, key)}
                newdata = crud.modify_camera(db, jsn.get('entityid'), **validated)
                if newdata:
                    camera = {
                        "local_correlid":newdata.local_correlid,
                        "rtsp_host":newdata.rtsp_host,
                        "modified":newdata.modified.strftime('%Y.%m.%d. %H:%M')
                    }
                    return_dict['answer'] = camera
                else:
                    return_dict['answer'] = None


        ### DOOR
        elif jsn.get('entitytype') == "door" and jsn.get('action') == "get" and jsn.get('entityid', None) == None:
            crud.log_message(db,'rpc_handler','door','all',jsn.get('caller','?')+' requested all doors')
            dbdata = crud.get_doordata(db)
            for x in dbdata:
                door = {
                    "local_correlid":x.local_correlid,
                    "nickname":x.nickname,
                    "location":x.location,
                    "authorized":x.authorized,
                    "color":x.color
                }
                return_dict['answer'].append(door)
        elif jsn.get('entitytype') == "door" and jsn.get('action') == "get" and jsn.get('entityid',None) != None:
            crud.log_message(db,'rpc_handler','door',jsn.get('entityid','?'),jsn.get('caller','?')+' requested door '+jsn.get('entityid','?'))
            dbdata = crud.get_doordata(db, local_correlid=jsn.get('entityid'))[0]
            door = {
                "local_correlid":dbdata.local_correlid,
                "location":dbdata.location,
                "nickname":dbdata.nickname,
                "ont":dbdata.ont,
                "camera_link":dbdata.camera_link,
                "authorized":dbdata.authorized,
                "color":dbdata.color
            }
            return_dict['answer'] = door
        elif jsn.get('entitytype') == "door" and (jsn.get('action') == "add" or jsn.get('action') == "remove") and jsn.get('entityid',None) != None:
            if jsn.get('action') == "add":
                crud.log_message(db,'rpc_handler','door',jsn.get('entityid','?'),jsn.get('caller','?')+' added door '+jsn.get('entityid','?'))
                if crud.auth_door(db,jsn.get('entityid'),True):
                    return_dict['answer'] = True
                else:
                    return_dict['answer'] = False
            elif jsn.get('action') == "remove":
                crud.log_message(db,'rpc_handler','door',jsn.get('entityid','?'),jsn.get('caller','?')+' removed door '+jsn.get('entityid','?'))
                if crud.auth_door(db,jsn.get('entityid'),False):
                    return_dict['answer'] = True
                else:
                    return_dict['answer'] = False
        elif jsn.get('entitytype') == "door" and jsn.get('action') == "modify" and jsn.get('entityid',None) != None:
            if isinstance(jsn.get('extra'), dict):
                crud.log_message(db,'rpc_handler','door',jsn.get('entityid','?'),jsn.get('caller','?')+' made modifications for door '+jsn.get('entityid','?'))
                validated = {key: value for key, value in jsn.get('extra').items() if hasattr(models.DoorData, key)}
                newdata = crud.modify_doordata(db, jsn.get('entityid'), **validated)
                if newdata:
                    door = {
                        "local_correlid":newdata.local_correlid,
                        "location":newdata.location,
                        "nickname":newdata.nickname,
                        "ont":newdata.ont,
                        "camera_link":newdata.camera_link,
                        "authorized":newdata.authorized,
                        "color":newdata.color
                    }
                    return_dict['answer'] = door
                else:
                    return_dict['answer'] = None

        ### USER
        elif jsn.get('entitytype') == "user" and jsn.get('action') == "get" and jsn.get('entityid', None) == None:
            crud.log_message(db,'rpc_handler','user','all',jsn.get('caller','?')+' requested all users')
            dbdata = crud.get_userdata(db)
            for x in dbdata:
                mask_fid = False if x.fid is None else True
                mask_staticunq = False if x.static_unq is None else True
                user = {
                    "local_userid":x.local_userid,
                    "global_userid":x.global_userid,
                    "name":x.name,
                    "fid":mask_fid,
                    "static_unq":mask_staticunq,
                    "dynamic_unq":x.dynamic_unq,
                    "last_logged":x.last_logged.strftime('%Y.%m.%d. %H:%M')
                }
                return_dict['answer'].append(user)
        elif jsn.get('entitytype') == "user" and jsn.get('action') == "get" and jsn.get('entityid', None) != None:
            crud.log_message(db,'rpc_handler','user',jsn.get('entityid','?'),jsn.get('caller','?')+' requested user '+jsn.get('entityid','?'))
            dbdata = crud.get_userdata(db, local_userid=jsn.get('entityid'))[0]
            mask_fid = False if dbdata.fid is None else True
            mask_staticunq = False if dbdata.static_unq is None else True
            user = {
                "local_userid":dbdata.local_userid,
                "global_userid":dbdata.global_userid,
                "name":dbdata.name,
                "fid":mask_fid,
                "static_unq":mask_staticunq,
                "dynamic_unq":dbdata.dynamic_unq,
                "last_logged":dbdata.last_logged.strftime('%Y.%m.%d. %H:%M')
            }
            return_dict['answer'] = user
        elif jsn.get('entitytype') == "user" and (jsn.get('action') == "add" or jsn.get('action') == "remove") and jsn.get('entityid',None) != None:
            if jsn.get('action') == "add":
                crud.log_message(db,'rpc_handler','user',jsn.get('entityid','?'),jsn.get('caller','?')+' added user '+jsn.get('entityid','?'))
                ## itt az entityid egy string lesz, ami gyakorlatilag a név!
                validated = dict()
                if isinstance(jsn.get('extra'), dict):
                    validated = {key: value for key, value in jsn.get('extra').items() if hasattr(models.UserData, key)}
                if crud.add_userdata(db,jsn.get('entityid'), **validated):
                    return_dict['answer'] = True
                else:
                    return_dict['answer'] = False
            elif jsn.get('action') == "remove":
                crud.log_message(db,'rpc_handler','user',jsn.get('entityid','?'),jsn.get('caller','?')+' removed user '+jsn.get('entityid','?'))
                ## törlésnél nem név kell, hanem maga az id!
                if crud.remove_userdata(db,jsn.get('entityid')):
                    return_dict['answer'] = True
                else:
                    return_dict['answer'] = False
        elif jsn.get('entitytype') == "user" and jsn.get('action') == "modify" and jsn.get('entityid',None) != None:
            if isinstance(jsn.get('extra'), dict):
                crud.log_message(db,'rpc_handler','user',jsn.get('entityid','?'),jsn.get('caller','?')+' made modifications for user '+jsn.get('entityid','?'))
                validated = {key: value for key, value in jsn.get('extra').items() if hasattr(models.UserData, key)}
                if validated.get('global_userid','') != '':
                    validated['dynamic_unq'] = '0#'+str(pyotp.random_base32())
                else:
                    validated['dynamic_unq'] = None
                newdata = crud.modify_userdata(db, jsn.get('entityid'), **validated)
                if newdata:
                    mask_fid = False if newdata.fid is None else True
                    mask_staticunq = False if newdata.static_unq is None else True
                    user = {
                        "local_userid":newdata.local_userid,
                        "global_userid":newdata.global_userid,
                        "name":newdata.name,
                        "fid":mask_fid,
                        "static_unq":mask_staticunq,
                        "dynamic_unq":newdata.dynamic_unq,
                        "last_logged":newdata.last_logged.strftime('%Y.%m.%d. %H:%M')
                    }
                    return_dict['answer'] = user
                else:
                    return_dict['answer'] = None

        ### NumPlate
        elif jsn.get('entitytype') == "numberplate" and jsn.get('action') == "get" and jsn.get('entityid', None) == None:
            crud.log_message(db,'rpc_handler','numberplate','all',jsn.get('caller','?')+' requested all numberplates')
            dbdata = crud.get_numplatedata(db)
            for x in dbdata:
                numplate = {
                    "numplateid":x.numplateid,
                    "numplate":x.numplate,
                    "nickname":x.nickname,
                    "last_logged":x.last_logged.strftime('%Y.%m.%d. %H:%M')
                }
                return_dict['answer'].append(numplate)
        elif jsn.get('entitytype') == "numberplate" and jsn.get('action') == "get" and jsn.get('entityid', None) != None:
            crud.log_message(db,'rpc_handler','numberplate',jsn.get('entityid','?'),jsn.get('caller','?')+' requested numberplate '+jsn.get('entityid','?'))
            row = crud.get_numplatedata(db,numplateid=jsn.get('entityid'))[0]
            numplate = {
                "numplateid":row.numplateid,
                "numplate":row.numplate,
                "nickname":row.nickname,
                "last_logged":row.last_logged.strftime('%Y.%m.%d. %H:%M')
            }
            return_dict['answer'] = numplate
        elif jsn.get('entitytype') == "numberplate" and (jsn.get('action') == "add" or jsn.get('action') == "remove") and jsn.get('entityid',None) != None:
            if jsn.get('action') == "add":
                crud.log_message(db,'rpc_handler','numberplate',jsn.get('entityid','?'),jsn.get('caller','?')+' added numberplate '+jsn.get('entityid','?'))
                ## itt (is) az entityid egy string lesz, ami gyakorlatilag a név!
                validated = dict()
                if isinstance(jsn.get('extra'), dict):
                    validated = {key: value for key, value in jsn.get('extra').items() if hasattr(models.NumPlateData, key)}
                if crud.add_numplatedata(db,jsn.get('entityid'), **validated):
                    return_dict['answer'] = True
                else:
                    return_dict['answer'] = False
            elif jsn.get('action') == "remove":
                crud.log_message(db,'rpc_handler','numberplate',jsn.get('entityid','?'),jsn.get('caller','?')+' removed numberplate '+jsn.get('entityid','?'))
                ## törlésnél nem név kell, hanem maga az id!
                if crud.remove_numplatedata(db,jsn.get('entityid')):
                    return_dict['answer'] = True
                else:
                    return_dict['answer'] = False
        elif jsn.get('entitytype') == "numberplate" and jsn.get('action') == "modify" and jsn.get('entityid',None) != None:
            if isinstance(jsn.get('extra'), dict):
                crud.log_message(db,'rpc_handler','numberplate',jsn.get('entityid','?'),jsn.get('caller','?')+' made modifications for numberplate '+jsn.get('entityid','?'))
                validated = {key: value for key, value in jsn.get('extra').items() if hasattr(models.NumPlateData, key)}
                newdata = crud.modify_numplatedata(db, jsn.get('entityid'), **validated)
                if newdata:
                    numplate = {
                        "numplateid":newdata.numplateid,
                        "numplate":newdata.numplate,
                        "nickname":newdata.nickname,
                        "last_logged":newdata.last_logged.strftime('%Y.%m.%d. %H:%M')
                    }
                    return_dict['answer'] = numplate
                else:
                    return_dict['answer'] = None

        ### Permission
        elif jsn.get('entitytype') == "permission" and jsn.get('action') == "get" and jsn.get('entityid', None) == None:
            crud.log_message(db,'rpc_handler','permission','all',jsn.get('caller','?')+' requested all permissions')
            dbdata = crud.get_permission(db)
            for x in dbdata:
                perm = {
                    "permid":x.id,
                    "group_name":x.group_name,
                    "user_enabled":x.user_enabled,
                    "numplate_enabled":x.numplate_enabled
                }
                return_dict['answer'].append(perm)
        elif jsn.get('entitytype') == "permission" and jsn.get('action') == "get" and jsn.get('entityid', None) != None:
            crud.log_message(db,'rpc_handler','permission',jsn.get('entityid','?'),jsn.get('caller','?')+' requested permission '+jsn.get('entityid','?'))
            row = crud.get_permission(db,id=jsn.get('entityid'))[0]
            perm = {
                "permid":row.id,
                "group_name":row.group_name,
                "user_enabled":row.user_enabled,
                "numplate_enabled":row.numplate_enabled,
                "numplates":[str(x.numplateid) for x in row.numplatedata if hasattr(x, 'numplateid')],
                "doors":[str(x.local_correlid) for x in row.doordata if hasattr(x, 'local_correlid')],
                "users":[str(x.local_userid) for x in row.userdata if hasattr(x, 'local_userid')]
            }
            return_dict['answer'] = perm
        elif jsn.get('entitytype') == "permission" and (jsn.get('action') == "add" or jsn.get('action') == "remove") and jsn.get('entityid',None) != None:
            if jsn.get('action') == "add":
                crud.log_message(db,'rpc_handler','permission',jsn.get('entityid','?'),jsn.get('caller','?')+' added permission '+jsn.get('entityid','?'))
                ## itt (is) az entityid egy string lesz, ami gyakorlatilag a név!
                validated = dict()
                if isinstance(jsn.get('extra'), dict):
                    validated = {key: value for key, value in jsn.get('extra').items() if hasattr(models.Permission, key)}
                if crud.add_permission(db,jsn.get('entityid'), **validated):
                    return_dict['answer'] = True
                else:
                    return_dict['answer'] = False
            elif jsn.get('action') == "remove":
                crud.log_message(db,'rpc_handler','permission',jsn.get('entityid','?'),jsn.get('caller','?')+' removed permission '+jsn.get('entityid','?'))
                ## törlésnél nem név kell, hanem maga az id!
                if crud.remove_permission(db,jsn.get('entityid')):
                    return_dict['answer'] = True
                else:
                    return_dict['answer'] = False
        elif jsn.get('entitytype') == "permission" and jsn.get('action') == "modify" and jsn.get('entityid',None) != None:
            if isinstance(jsn.get('extra'), dict):
                crud.log_message(db,'rpc_handler','permission',jsn.get('entityid','?'),jsn.get('caller','?')+' made modifications for permission '+jsn.get('entityid','?'))
                validated = {key: value for key, value in jsn.get('extra').items() if hasattr(models.Permission, key)}
                newdata = crud.modify_permission(db, jsn.get('entityid'), **validated)
                if newdata:
                    perm = {
                        "permid":newdata.id,
                        "group_name":newdata.group_name,
                        "user_enabled":newdata.user_enabled,
                        "numplate_enabled":newdata.numplate_enabled
                    }
                    return_dict['answer'] = perm
                else:
                    return_dict['answer'] = None


        ### Assign NFC
        elif jsn.get('entitytype') == "user" and jsn.get('action') == "register" and jsn.get('mainid', None) != None:
            ## reg
            crud.log_message(db,'rpc_handler','user',jsn.get('mainid','?'),jsn.get('caller','?')+' started NFC assignment for user '+jsn.get('mainid','?'))
            user = crud.get_userdata(db, local_userid=jsn.get('mainid', None))[0]
            door = crud.get_doordata(db, local_correlid=jsn.get('secondaryid',None))[0]
            if type(user) == models.UserData and type(door) == models.DoorData:
                for l in range(0,3):
                    success = False
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock.settimeout(10)
                        server_address = (str(door.ipaddr), 25962)
                        sock.connect(server_address)
                        sock.sendall('REGUSER'.encode())
                        response = sock.recv(1024).decode()
                        if response == 'ERR':
                            print("recieved error from door")
                            return_dict = {
                                "status":"ERR",
                                "code":"400",
                                "exception":"No card was presented within timeout."
                            }
                            success = True
                        else:
                            print("recieved ID "+str(response.split('#')[1]))
                            crud.log_message(db,'rpc_handler','user','rpc_handler',jsn.get('caller','?')+' NFC id '+str(response.split('#')[1])+' assigned for user '+jsn.get('entityid','?'))
                            
                            prev_cards = crud.get_userdata(db,static_unq=str(response.split('#')[1]))
                            if len(prev_cards) > 0:
                                crud.log_message(db,'rpc_handler','user','rpc_handler','NFC id '+str(response.split('#')[1])+' was already present for '+str(prev_cards[0].local_userid)+', and now its removed')
                                crud.modify_userdata(db, prev_cards[0].local_userid, static_unq=None)

                            crud.modify_userdata(db, user.local_userid, static_unq=str(response.split('#')[1]))
                            
                            return_dict = {
                                "status":"OK",
                                "code":"200",
                                "answer":"SUCCESS"
                            }
                            success = True
                    except Exception as e:
                        print("exception in calling door: "+str(e))
                    finally:
                        sock.close()
                    if success:
                        break
                    print("Exception happened, trying again ("+str(l+1)+"/3)")
                    return_dict = {
                        "status":"ERR",
                        "code":"400",
                        "exception":"Exception while handling external connection."
                    }

        elif jsn.get('entitytype') == "user" and jsn.get('action') == "open" and jsn.get('mainid', None) != None:
            ## remote open
            crud.log_message(db,'rpc_handler','user',jsn.get('mainid','?'),jsn.get('caller','?')+' remote-opened door '+jsn.get('mainid','?'))
            door = crud.get_doordata(db, local_correlid=jsn.get('mainid',None))[0]
            if type(door) == models.DoorData:
                for l in range(0,3):
                    success = False
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sock.settimeout(10)
                        server_address = (str(door.ipaddr), 25962)
                        sock.connect(server_address)
                        sock.sendall('OPEN'.encode())
                        response = sock.recv(1024).decode()
                        if response == 'ERR':
                            print("recieved error from door")
                            return_dict = {
                                "status":"ERR",
                                "code":"400",
                                "exception":"Exception happened while communicating with door."
                            }
                            success = True
                        else:
                            print("recieved response "+str(response))
                            return_dict = {
                                "status":"OK",
                                "code":"200",
                                "answer":"SUCCESS"
                            }
                            success = True
                    except Exception as e:
                        print("exception in calling door: "+str(e))
                    finally:
                        sock.close()
                    if success:
                        break
                    print("Exception happened, trying again ("+str(l+1)+"/3)")
                    return_dict = {
                        "status":"ERR",
                        "code":"400",
                        "exception":"Exception while handling external connection."
                    }
        
        # read camera feed remotely
        elif jsn.get('entitytype') == "camera" and jsn.get('action') == "open" and jsn.get('mainid', None) != None:
            camurl = crud.get_camera(db,local_correlid=jsn.get('mainid',''))[0]
            if type(camurl) != models.CameraLink:
                return_dict = None
            else:
                cap = cv2.VideoCapture(camurl.rtsp_host)
                if not cap.isOpened():
                    return_dict = {
                        "status":"ERR",
                        "code":"400",
                        "exception":"couldnt connect to camera"
                    }
                else:
                    for _ in range(0,3):
                        ret, frame = cap.read()
                        if ret:
                            buffer = BytesIO()
                            frame = cv2.resize(frame,(854,480))
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            img = Image.fromarray(frame)
                            img.save(buffer, format="WebP", quality=50)

                            buffer_val = buffer.getvalue()
                            img_bin = base64.b64encode(buffer_val).decode('utf-8')
                            return_dict['answer'] = str(img_bin)
                            buffer = None
                            break
                        time.sleep(2)
                    if return_dict['answer'] == []:
                        return_dict = {
                            "status":"ERR",
                            "code":"400",
                            "exception":"coulndt take picture"
                        }
                cap.release()
                cap = None


        ### AssignPermission
        elif jsn.get('entitytype') == "numberplate" and jsn.get('action') == "assign" and jsn.get('mainid', None) != None:
            crud.log_message(db,'rpc_handler','permission',jsn.get('entityid','?'),jsn.get('caller','?')+' assigned permission '+jsn.get('mainid','?')+' for numberplate '+jsn.get('secondaryid', '?'))
            row = crud.assign_numplgroup(db,jsn.get('mainid'),jsn.get('secondaryid'))
            return_dict['answer'] = row
        elif jsn.get('entitytype') == "numberplate" and jsn.get('action') == "revoke" and jsn.get('mainid', None) != None:
            crud.log_message(db,'rpc_handler','permission',jsn.get('entityid','?'),jsn.get('caller','?')+' revoked permission '+jsn.get('mainid','?')+' for numberplate '+jsn.get('secondaryid', '?'))
            row = crud.revoke_numplgroup(db,jsn.get('mainid'),jsn.get('secondaryid'))
            return_dict['answer'] = row
        elif jsn.get('entitytype') == "user" and jsn.get('action') == "assign" and jsn.get('mainid', None) != None:
            crud.log_message(db,'rpc_handler','permission',jsn.get('entityid','?'),jsn.get('caller','?')+' assigned permission '+jsn.get('mainid','?')+' for user '+jsn.get('secondaryid', '?'))
            row = crud.assign_pplgroup(db,jsn.get('mainid'),jsn.get('secondaryid'))
            return_dict['answer'] = row
        elif jsn.get('entitytype') == "user" and jsn.get('action') == "revoke" and jsn.get('mainid', None) != None:
            crud.log_message(db,'rpc_handler','permission',jsn.get('entityid','?'),jsn.get('caller','?')+' revoked permission '+jsn.get('mainid','?')+' for user '+jsn.get('secondaryid', '?'))
            row = crud.revoke_pplgroup(db,jsn.get('mainid'),jsn.get('secondaryid'))
            return_dict['answer'] = row
        elif jsn.get('entitytype') == "door" and jsn.get('action') == "assign" and jsn.get('mainid', None) != None:
            crud.log_message(db,'rpc_handler','permission',jsn.get('entityid','?'),jsn.get('caller','?')+' assigned permission '+jsn.get('mainid','?')+' for door '+jsn.get('secondaryid', '?'))
            row = crud.assign_doorgroup(db,jsn.get('mainid'),jsn.get('secondaryid'))
            return_dict['answer'] = row
        elif jsn.get('entitytype') == "door" and jsn.get('action') == "revoke" and jsn.get('mainid', None) != None:
            crud.log_message(db,'rpc_handler','permission',jsn.get('entityid','?'),jsn.get('caller','?')+' revoked permission '+jsn.get('mainid','?')+' for door '+jsn.get('secondaryid', '?'))
            row = crud.revoke_doorgroup(db,jsn.get('mainid'),jsn.get('secondaryid'))
            return_dict['answer'] = row

    elif jsn.get('processor') == serverid and jsn.get('caller',None) != None:
        print(" } ["+jsn.get('caller','unknown')+"] "+jsn.get('entitytype','unknwon entitytype')+" - "+jsn.get('action','unknwon action')+" - "+jsn.get('entityid', 'unknown entityid')+"")
        
        return_dict = {
            "status":"OK",
            "code":"200",
            "answer":[]
        }

        modifyable = ['fid','static_unq','dynamic_unq','global_userid']

        if jsn.get('action') == "get" and jsn.get('entityid', None) == None:
            crud.log_message(db,'rpc_handler','user_selfservice','all',jsn.get('caller','?')+' requested all users')
            dbdata = crud.get_userdata(db, global_userid=jsn.get('caller'))
            assert type(dbdata) == list
            for x in dbdata:
                assert type(x) == models.UserData
                user = {
                    "local_userid":x.local_userid,
                    "name":x.name,
                    "fid":False if x.fid is None else True,
                    "static_unq":x.static_unq,
                    "dynamic_unq":x.dynamic_unq,
                    "last_logged":x.last_logged.strftime('%Y.%m.%d. %H:%M')
                }
                return_dict['answer'].append(user)
        elif jsn.get('action') == "get" and jsn.get('entityid',None) != None:
            crud.log_message(db,'rpc_handler','user_selfservice',jsn.get('entityid','?'),jsn.get('caller','?')+' requested user '+jsn.get('entityid','?'))
            dbdata = crud.get_userdata(db, global_userid=jsn.get('caller'), local_userid=jsn.get('entityid'))[0]
            assert type(dbdata) == models.UserData
            user = {
                "local_userid":dbdata.local_userid,
                "name":dbdata.name,
                "fid":False if dbdata.fid is None else True,
                "static_unq":dbdata.static_unq,
                "dynamic_unq":dbdata.dynamic_unq,
                "last_logged":dbdata.last_logged.strftime('%Y.%m.%d. %H:%M')
            }
            return_dict['answer'] = user     
        elif jsn.get('action') == "modify" and jsn.get('entityid',None) != None:
            validated = dict()
            crud.log_message(db,'rpc_handler','user_selfservice',jsn.get('entityid','?'),jsn.get('caller','?')+' made modifications for user '+jsn.get('entityid','?'))
            if isinstance(jsn.get('extra'), dict):
                validated = {key: value for key, value in jsn.get('extra').items() if key in modifyable}
            newdata = crud.modify_userdata(db,jsn.get('entityid'), **validated)
            if newdata:
                mask_fid = False if newdata.fid is None else True
                user = {
                    "local_userid":newdata.local_userid,
                    "global_userid":newdata.global_userid,
                    "name":newdata.name,
                    "fid":mask_fid,
                    "static_unq":newdata.static_unq,
                    "dynamic_unq":newdata.dynamic_unq,
                    "last_logged":newdata.last_logged.strftime('%Y.%m.%d. %H:%M')
                }
                return_dict['answer'] = user
            else:
                return_dict['answer'] = None
        elif jsn.get('action') == 'empty':
            crud.log_message(db,'rpc_handler','user_selfservice',jsn.get('entityid','?'),jsn.get('caller','?')+' requested empty action')
            entities = crud.get_userdata(db, global_userid=jsn.get('caller'))
            validated = {
                "global_userid":None,
                "dynamic_unq":None
            }
            if type(entities) == list:
                for ent in entities:
                    crud.modify_userdata(db,ent, **validated)
                return_dict['answer'] = True
            elif type(entities) == models.UserData:
                crud.modify_userdata(db,entities, **validated)
                return_dict['answer'] = True
        elif jsn.get('caller') == 'user' and jsn.get('action') == 'healthcheck':
            return_dict['answer'] = 'OK'
    
    db.close()
    return return_dict


async def main():
    print("starting registration process...")

    for i in range(1,6):
        try:
            r = requests.post(CONFIG['main_host']+'/_api/dd/challenge', json={
                'serverid':CONFIG['ident'],
                'deviceinfo':'LOCAL_SERVER'
            })
            break
        except Exception as e:
            print('Couldnt connect to the main server provided. Trying again... ('+str(i)+'/5)')
            r = None
    
    if r is None:
        print('Couldnt connect to the main server provided.')
        return
    elif r.status_code == 200 and r.json()['status'] == 'OK':
        with open(os.path.join(CONFIG['cert_storage'],CONFIG['ident']+'_private.pem'), "rb") as pem_file:
            private_key = serialization.load_pem_private_key(
                pem_file.read(),
                password=None,
                backend=default_backend()
            )
            challenge = r.json()['challenge'].encode(encoding="utf-8") 
            signature_bytes = private_key.sign(
                challenge,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            signature = base64.b64encode(signature_bytes).decode('utf-8')
            r = requests.post(CONFIG['main_host']+'/_api/dd/answer', json={
                'serverid':CONFIG['ident'],
                'answer':signature
            })
            if r.status_code == 200:
                server_id = CONFIG['ident']
                rpc = DDRPCServer()
                await rpc.connect(server_id,rpc_host=CONFIG['rpc_host'])

                print(" [x] Awaiting Queue requests")

                callback = lambda msg: rpc.new_message(msg,on_message)
                await rpc.queue.consume(callback,timeout=60)

                await asyncio.Future()
    
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)