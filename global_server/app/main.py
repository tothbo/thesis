import uvicorn, jwt, asyncio, uuid, requests, json, os, base64, pyotp, io

from fastapi import FastAPI, Request, Depends, HTTPException, status, Response, Cookie, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError

from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from typing import Annotated, Dict, Union, Any
from datetime import timedelta, datetime, timezone
from passlib.context import CryptContext

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

from db.database import SessionLocal, engine
import db.models as models
import db.crud as crud

from ddrpc import DDRPC

required_keys = [('host_port',int),('cert_storage',str),('secret_key',str),('algorith',str),('key_expires',int),('rpc_host',str),('db_host',str)]
with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
models.Base.metadata.create_all(bind=engine)

async def get_ddrpc():
    rpc = DDRPC.DDRPCClient()
    await rpc.connect(amqp_server=CONFIG['rpc_host'])
    try:
        yield rpc
    finally:
        await rpc.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_devmode():
    if CONFIG['devmode']:
        return True
    raise HTTPException(status_code=404,detail="Endpoint turned off")

app = FastAPI(docs_url="/docs" if CONFIG['devmode'] else None, redoc_url=None)
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# PAGEK

'''
    AUTH - v2
    JWS token kiadasa, elmentese cookieba
'''

class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    username: str | None = None
class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
class MeUser(BaseModel):
    email: str
    full_name: str | None = None
class DppAuthLoginData(BaseModel):
    emailaddr: EmailStr
    passwd: str = Field(min_length=8, max_length=128)
    deviceinfo: str = Field(min_length=2, max_length=128)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, CONFIG['secret_key'], algorithms=[CONFIG['algorith']])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = crud.get_user(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user
async def get_current_user_cookie(req: Request, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"Authenticate": "Bearer"},
    )
    token = req.cookies.get('token')
    try:
        payload = jwt.decode(token, CONFIG['secret_key'], algorithms=[CONFIG['algorith']])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = crud.get_user(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user
async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)],):
    return current_user
async def get_current_active_user_cookie(current_user: Annotated[User, Depends(get_current_user_cookie)],):
    return current_user
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, CONFIG['secret_key'], algorithm=CONFIG['algorith'])
    return encoded_jwt

## page
@app.post("/token")
async def token(req: Request, response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)) -> Token:
    user = crud.auth_user(db, form_data.username, form_data.password, req.client.host, 'random_info')
    if user[0] == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=CONFIG['key_expires'])
    access_token = create_access_token(
        data={"sub": user[1]}, expires_delta=access_token_expires
    )
    token = {"access_token":access_token, "token_type":"bearer"}
    response = JSONResponse(content=token)
    if CONFIG['devmode']:
        response.set_cookie(
            key="token",
            value=access_token,
            max_age=CONFIG['key_expires'] * 120
        )
    else:
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Strict",
            max_age=CONFIG['key_expires'] * 120
        )
    return response
@app.get("/auth/me/", response_model=MeUser)
async def auth_me(current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user)]):
    return {"email":current_user.emailaddr, "full_name":current_user.fullname}
@app.get("/auth")
async def auth(req: Request):
    return templates.TemplateResponse("auth.html", {"request": req, "page_title":"Auth"})
@app.get("/logout")
async def logout(req: Request, response: Response, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)],  db: Session = Depends(get_db)):
    crud.logout_user(db, current_user.global_userid)
    response = RedirectResponse(url="/auth")
    response.set_cookie(
        key="token",
        value='',
        max_age=datetime.now() - timedelta(hours=24)
    )
    return response

class DppChangePassword(BaseModel):
    password: str = Field(min_length=4, max_length=32)
@app.post("/_api/passchange")
async def api_passchange(req: Request, data:DppChangePassword, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db)):
    a = crud.change_pass(db,current_user.global_userid, data.password)
    return a


'''
    ROOT - main page
'''
# static
@app.get("/u_static/index.js")
async def pstatic_index(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)]):
    return FileResponse('u_static/index.js')
@app.get("/p_static/server.js")
async def pstatic_index(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)]):
    return FileResponse('p_static/server.js')
@app.get("/p_static/stat.js")
async def pstatic_index(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)]):
    return FileResponse('p_static/stat.js')
@app.get("/u_static/user.js")
async def pstatic_index(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)]):
    return FileResponse('u_static/user.js')
@app.get("/u_static/jsOTP.min.js")
async def pstatic_index(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)]):
    return FileResponse('u_static/jsOTP.min.js')
@app.get("/u_static/qrcode.min.js")
async def pstatic_index(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)]):
    return FileResponse('u_static/qrcode.min.js')
@app.get("/u_static/jquery.min.js")
async def pstatic_index(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)]):
    return FileResponse('u_static/jquery.min.js')
@app.get("/u_static/bootstrap.bundle.min.js")
async def pstatic_index(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)]):
    return FileResponse('u_static/bootstrap.bundle.min.js')
@app.get("/u_static/bootstrap.min.css")
async def pstatic_index(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)]):
    return FileResponse('u_static/bootstrap.min.css')

## page
@app.get("/")
async def index(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)]):
    return templates.TemplateResponse("index.html", {"request": req, "page_title":"Index"})

## api
@app.post("/_api/clog/get_servers_v2")
async def index_api_getserversv2(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db)):
    ## összeszedni a szervereket
    servers = crud.get_servers2(db, current_user.global_userid)
    if len(servers) <= 0:
        return None
    for i,serv in enumerate(servers['user']):
        servers['user'][i]['live_status'] = True
    for i,serv in enumerate(servers['admin']):
        servers['admin'][i]['live_status'] = True
    return servers

class DppGetStatus(BaseModel):
    serverid: str = Field(min_length=16, max_length=16)
@app.post("/_api/clog/get_status")
async def index_api_getstatus(req: Request, data: DppGetStatus, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db)):
    ## összeszedni a szervereket
    serv = data.serverid
    rpc = DDRPC.DDRPCClient()
    await rpc.connect(amqp_server=CONFIG['rpc_host'])
    try:
        message = {
            "destination":serv,
            "caller":"user",
            "action":"healthcheck"
        }

        response = await rpc.call(serv, message,prio=1)

        if response['code'] == "200":
            rpc = None
            return True
    except Exception:
        rpc = None
        return False
    rpc = None
    return False

class DppServerLeave(BaseModel):
    serverid: str = Field(min_length=16, max_length=16)
@app.post("/_api/clog/leaveserver")
async def index_api_leaveserver(req: Request, data: DppServerLeave, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db)):
    if crud.auth_directaccess(db,data.serverid,current_user.global_userid,False):
        resp = crud.revoke_serveracc(db,current_user.global_userid,data.serverid)
        return resp
    return None

class DppServerUserListAction(Enum):
    GET = "get"
    ADD = "add"
    MOD = "modify"
    REM = "remove"
class DppServerUserList(BaseModel):
    serverid: str = Field(min_length=16, max_length=16)
    action: DppServerUserListAction
    extra: Union[str, Dict[str, Any]]
@app.post("/_api/clog/serveruserlist")
async def index_api_serveruserlist(req: Request, data: DppServerUserList, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db)):
    ## auth access to admin portal
    extr = data.extra

    '''
        {
            "serverid": server_id,
            "action": "modify",
            "extra": {
                "nickname":"",
                "color":"#ffffff"
                "users":[
                    {
                        "userid":"",
                        "admin":false
                    }
                ]
            }
        }
    '''

    if crud.auth_directaccess(db,data.serverid,current_user.global_userid,True):
        if data.action == DppServerUserListAction.GET:
            servls = {
                "name":"",
                "color":"",
                "users":[]
            }
            serv = crud.get_server(db, data.serverid)
            servls['name'] = serv.nickname
            servls['color'] = serv.color
            for x in crud.get_serveracc(db, data.serverid):
                if x.global_userid != current_user.global_userid:
                    servls['users'].append({
                        "global_userid":x.global_userid,
                        "admin":x.admin
                    })
            return servls
        elif data.action == DppServerUserListAction.ADD:
            resp = crud.assign_serveracc(db, extr.get('userid',''), data.serverid, False)
            return resp
        elif data.action == DppServerUserListAction.REM:
            resp = crud.revoke_serveracc(db,extr.get('userid',''),data.serverid)
            return resp
        elif data.action == DppServerUserListAction.MOD:
            try:
                md = crud.mod_server(db, data.serverid,extr.get('nickname',''),extr.get('color','#f1f1f1'))
                assert md
                for urow in extr.get('users',list()):
                    resp = crud.mod_serveraccess(db,urow.get('userid',''),data.serverid,urow.get('admin',False))
                    assert resp
                return True
            except:
                return False
    return None

'''
    SERVER - connection to the remote servers
    + API access
'''
## page
@app.get("/user")
async def server(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db)):
    if req.query_params.get('serverid') is None:
        return RedirectResponse('/')
    server = crud.get_server(db,req.query_params.get('serverid'))
    auth = crud.auth_directaccess(db,req.query_params.get('serverid'),current_user.global_userid, False)
    if auth:
        return templates.TemplateResponse("user.html", {"request": req, "page_title":"Server - "+server.nickname,"server_id":server.global_serverid,"nickname":server.nickname,"color":server.color})
    return RedirectResponse('/')
@app.get("/server")
async def server(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db)):
    if req.query_params.get('serverid') is None:
        return RedirectResponse('/')
    server = crud.get_server(db,req.query_params.get('serverid'))
    auth = crud.auth_directaccess(db,req.query_params.get('serverid'),current_user.global_userid, True)
    if auth:
        return templates.TemplateResponse("server.html", {"request": req, "page_title":"Server - "+server.nickname,"server_id":server.global_serverid,"nickname":server.nickname,"color":server.color})
    return RedirectResponse('/')
@app.get("/stat")
async def server(req: Request, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db)):
    if req.query_params.get('serverid') is None:
        return RedirectResponse('/')
    server = crud.get_server(db,req.query_params.get('serverid'))
    auth = crud.auth_directaccess(db,req.query_params.get('serverid'),current_user.global_userid, True)
    if auth:
        return templates.TemplateResponse("stat.html", {"request": req, "page_title":"Server - "+server.nickname,"server_id":server.global_serverid,"nickname":server.nickname,"color":server.color})
    return RedirectResponse('/')

"""
    Connection JSON encoder (necessary for enums)
"""
class ConnEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (SConnTyped, SConnAction, SConnAssignTyped, UConnAction)):
            return o.value
        return super().default(o)

"""
    SERVER CONNECTION APIs
    - get all doors / get one door/ authenticate door / deauthenticate door
    - open door
    - get all nfc cards / get one nfc card / add nfc card / remove nfc card / modify nfc card
    - get all cameras / get one camera / authenticate camera / deauthenticate camera
    - get all numberplates / get one numberplate / add numberplate / remove numberplate / modify numberplate (?)

    Possible combinations for EntityModel:
    - empty get door > get all doors
    - id get door > get door's details
    - id add door > authorise door
    - id remove door > deauthorise door
"""
class SConnAction(Enum):
    GET = "get"
    ADD = "add"
    MOD = "modify"
    REM = "remove"
class SConnTyped(Enum):
    DOOR = "door"
    CARD = "card"
    CAM = "camera"
    PERM = "permission"
    STAT = "statistics"
    USER = "user"
    NUMPLATE = "numberplate"
class SConnAssignTyped(Enum):
    ASSIGN = "assign"
    REVOKE = "revoke"
    REGISTER = "register"
    OPEN = "open"

class SConnServerModel(BaseModel):
    serverid: str = Field(min_length=16, max_length=16)
    entitytype: SConnTyped
class SConnEntityModel(BaseModel):
    serverid: str = Field(min_length=16, max_length=16)
    entityid: Union[str, int] = Field(min_length=1, max_length=256)
    action: SConnAction
    entitytype: SConnTyped
    extra: Union[str, bool, Dict[str, Any]]
class SConnAssign(BaseModel):
    serverid: str = Field(min_length=16,max_length=16)
    entitytype: SConnTyped
    action: SConnAssignTyped
    mainid: str = Field(min_length=1,max_length=32)
    secondaryid: str = Field(min_length=1,max_length=32)
class SConnOpen(BaseModel):
    serverid: str = Field(min_length=16,max_length=16)
    entityid: Union[str, int] = Field(min_length=1, max_length=256)


## sconnservermodel
@app.post("/_api/sconn/servermodel")
async def api_sconn_servermodel(req: Request, data: SConnServerModel, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db), rpc: DDRPC.DDRPCClient = Depends(get_ddrpc)):
    message = {
        "destination":data.serverid,
        "caller":current_user.global_userid,
        "action":"get",
        "entitytype":data.entitytype
    }

    try:
        response = await rpc.call(data.serverid, json.dumps(message, cls=ConnEncoder))
        return response
    except AssertionError as e:
        d = {
            "code":"300",
            "exception":"Server no longer online."
        }
    except Exception as e:
        d = {
            "code":"400",
            "exception":str(e)
        }
        return d

## sconnentitymodel
@app.post("/_api/sconn/entitymodel")
async def api_sconn_entitymodel(req: Request, data: SConnEntityModel, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db), rpc: DDRPC.DDRPCClient = Depends(get_ddrpc)):
    message = {
        "destination":data.serverid,
        "caller":current_user.global_userid,
        "action":data.action,
        "entityid":data.entityid,
        "entitytype":data.entitytype,
        "extra":data.extra if data.extra != 'req_user_list' or 'req_qr_data' else ''
    }

    try:
        response = await rpc.call(data.serverid,
                                  json.dumps(message, cls=ConnEncoder),
                                  prio=3 if data.entitytype == SConnTyped.CAM else 2,
                                  tmout=60 if data.entitytype == SConnTyped.CAM else 5)
        if data.extra == 'req_user_list':
            response['userlist'] = []
            for x in crud.get_serveracc(db, data.serverid):
                if x.global_userid != current_user.global_userid:
                    response['userlist'].append({
                        "global_userid":x.global_userid,
                        "admin":x.admin
                    })
        elif data.extra == 'req_qr_data':
            hotp = pyotp.HOTP(response['answer']['dynamic_unq'].split('#')[1])
            code = hotp.at(int(response['answer']['dynamic_unq'].split('#')[0]))
            response['qrcode'] = str(response['answer']['local_userid'])+'#'+str(code)
        return response
    except AssertionError as e:
        d = {
            "code":"300",
            "exception":"Server no longer online."
        }
    except Exception as e:
        d = {
            "code":"400",
            "exception":str(e)
        }
        return d

## sconnassign
@app.post("/_api/sconn/assign")
async def api_sconn_entitymodel(req: Request, data: SConnAssign, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db), rpc: DDRPC.DDRPCClient = Depends(get_ddrpc)):
    message = {
        "destination":data.serverid,
        "caller":current_user.global_userid,
        "entitytype":data.entitytype,
        "action":data.action,
        "mainid":data.mainid,
        "secondaryid":data.secondaryid
    }

    try:
        response = await rpc.call(data.serverid, json.dumps(message, cls=ConnEncoder), tmout=15, prio=3 if data.entitytype == SConnTyped.USER else 2)
        return response
    except AssertionError as e:
        d = {
            "code":"300",
            "exception":"Server no longer online."
        }
    except Exception as e:
        d = {
            "code":"400",
            "exception":str(e)
        }
        return d

"""
    USER CONNECTION APIs
    - get my keys / remove my globalid
    - add fid / add NFCtag / add DynamicTag (QR)
    - modify fid / modify NFCtag / modify DynamicTag (QR)
    - remove fid / remove NFCtag / remove DynamicTag (QR)

    extra: {
        ""
    }

"""
class UConnAction(Enum):
    GET = "get"
    MOD = "modify"
    EMP = "empty"
class UConnServerModel(BaseModel):
    serverid: str = Field(min_length=16, max_length=16)
class UConnEntityModel(BaseModel):
    serverid: str = Field(min_length=16, max_length=16)
    entityid: Union[str, int] = Field(min_length=1, max_length=256)
    action: UConnAction
    extra: Union[str, bool, Dict[str, Any]]

## uconnservermodel
@app.post("/_api/uconn/servermodel")
async def api_uconn_servermodel(req: Request, data: UConnServerModel, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db), rpc: DDRPC.DDRPCClient = Depends(get_ddrpc)):
    message = {
        "processor":data.serverid,
        "caller":current_user.global_userid,
        "action":"get"
    }

    try:
        response = await rpc.call(data.serverid, json.dumps(message, cls=ConnEncoder))
        return response
    except AssertionError as e:
        d = {
            "code":"300",
            "exception":"Server no longer online."
        }
    except Exception as e:
        d = {
            "code":"400",
            "exception":str(e)
        }
        return d

## uconnentitymodel
@app.post("/_api/uconn/entitymodel")
async def api_uconn_entitymodel(req: Request, data: UConnEntityModel, current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)], db: Session = Depends(get_db), rpc: DDRPC.DDRPCClient = Depends(get_ddrpc)):
    message = {
        "processor":data.serverid,
        "caller":current_user.global_userid,
        "action":data.action,
        "entityid":data.entityid,
        "extra": dict() if data.extra == 'req_qr_data' else data.extra
    }

    try:
        response = await rpc.call(data.serverid, json.dumps(message, cls=ConnEncoder))
        if data.extra == 'req_qr_data':
            hotp = pyotp.HOTP(response['answer']['dynamic_unq'].split('#')[1])
            code = hotp.at(int(response['answer']['dynamic_unq'].split('#')[0]))
            response['qrcode'] = str(response['answer']['local_userid'])+'#'+str(code)
        return response
    except AssertionError as e:
        d = {
            "code":"300",
            "exception":"Server no longer online."
        }
    except Exception as e:
        d = {
            "code":"400",
            "exception":str(e)
        }
        return d

## uconn upload image
@app.post("/_api/uconn/imageupload")
async def api_uconn_imageupload(
        req: Request,
        destination: Annotated[str, Form()],
        userid: Annotated[str, Form()],
        image1: Annotated[UploadFile, Form()],
        image2: Annotated[UploadFile, Form()],
        current_user: Annotated[models.GlobalUserData, Depends(get_current_active_user_cookie)],
        db: Session = Depends(get_db),
        rpc: DDRPC.DDRPCClient = Depends(get_ddrpc)
    ):

    if(image1.content_type != 'image/jpeg' or image1.filename.split('.')[-1] != 'jpg') or (image2.content_type != 'image/jpeg' or image2.filename.split('.')[-1] != 'jpg'):
        return {
            "code":"400",
            "exception":"Image not in right format."
        }

    fdata1 = await image1.read()
    fdata2 = await image2.read()

    message = {
        "destination":destination,
        "caller":current_user.global_userid,
        "userid":userid,
        "upload":"image",
        "image1":base64.b64encode(fdata1).decode('utf-8'),
        "image2":base64.b64encode(fdata2).decode('utf-8')
    }

    try:
        response = await rpc.call(destination, json.dumps(message, cls=ConnEncoder), tmout=60,prio=3)
        return response
    except AssertionError as e:
        d = {
            "code":"300",
            "exception":"Server no longer online."
        }
    except Exception as e:
        d = {
            "code":"400",
            "exception":str(e)
        }
        return d


'''
    DOOR COMM - kommunikáció a lokális szerverekkel

    Hitelesítés >
        - Először a kliens csatlakozik az _api/dd/challenge endpointra, kér egy challenget (ont oszlop adatbben)
        - A választ elküldi az _api/dd/ws endpointnak, ami elfogadja vagy elutasítja
        - Visszaküld neki egy UUID-t, ezzel lesz innentől a kommunikáció

'''
class DppChallenge(BaseModel):
    serverid: str = Field(min_length=16, max_length=16)
    deviceinfo: str = Field(min_length=3, max_length=256)
@app.post("/_api/dd/challenge")
async def api_dd_challenge(req: Request, data: DppChallenge, db: Session = Depends(get_db)):
    challenge = crud.add_challenged_session(db, data.serverid, req.client.host, data.deviceinfo)
    if type(challenge) == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )

    jj = {
        'status':'OK',
        'challenge':challenge
    }

    return JSONResponse(content=jj)

class DppChallenge(BaseModel):
    serverid: str = Field(min_length=16, max_length=16)
    answer: str = Field(min_length=3, max_length=2560)
@app.post("/_api/dd/answer")
async def api_dd_answer(req: Request, data: DppChallenge, db: Session = Depends(get_db)):
    global channel
    try:
        sess = crud.get_session(db, data.serverid)
        oss = os.path.join(CONFIG['cert_storage'], data.serverid+'_public.pem')
        with open(oss,'rb') as pkpem:
            public_key = serialization.load_pem_public_key(pkpem.read(), backend=default_backend())
            chall = sess.ont.encode(encoding="utf-8")
            ans = base64.b64decode(data.answer)
            public_key.verify(
                ans,
                chall,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        return JSONResponse({'status':'OK'})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )


'''
    DEVONLY - should have proper security measures
'''
class DppAddServer(BaseModel):
    nickname: str = Field(min_length=3, max_length=256)
    color: str = Field(min_length=0, max_length=7)
@app.post("/_api/dev/addserver")
async def api_dev_addserver(req: Request, data: DppAddServer, db: Session = Depends(get_db), devmode: bool = Depends(get_devmode)):
    server_id = crud.add_server(db, data.nickname, data.color)
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,       
        backend=default_backend()
    )

    cert_io = io.BytesIO()
    cert_io.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
    )
    cert_io.seek(0)

    public_key = private_key.public_key()

    with open(os.path.join(CONFIG['cert_storage'],server_id+"_public.pem"), "wb") as f:
        f.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

    response = StreamingResponse(cert_io, media_type="application/x-pem-file")
    response.headers["Content-Disposition"] = f"attachment; filename={server_id}_private.pem"
    return response

class DppAssignUser(BaseModel):
    userid: EmailStr
    serverid: str = Field(min_length=16, max_length=16)
    admin: bool = False
@app.post("/_api/dev/assignuser")
async def api_dev_assignuser(req: Request, data: DppAssignUser, db: Session = Depends(get_db), devmode: bool = Depends(get_devmode)):
    crud.assign_serveracc(db, data.userid, data.serverid, data.admin)
    return True

class DppRegisterUser(BaseModel):
    userid: EmailStr
    passwd: str = Field(min_length=8, max_length=32)
    fullname: str = Field(min_length=2, max_length=256)
@app.post("/_api/dev/registeruser")
async def api_dev_registeruser(req: Request, data:DppRegisterUser, db: Session = Depends(get_db), devmode: bool = Depends(get_devmode)):
    a = crud.register_user(db, data.userid, data.passwd, data.fullname)
    return a


# technical stuff
@app.exception_handler(HTTPException)
async def authentication_error_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401 and not request.url.path.startswith("/auth") and not request.url.path.startswith("/p_static") and not request.url.path.startswith("/u_static") and not request.url.path.startswith("/_api"):
        return RedirectResponse(url="/auth")
    content={}
    return JSONResponse(content)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=CONFIG['host_port'])
