from db.database import SessionLocal, engine
import db.models as models
import db.crud as crud
import numpy as np
from PIL import Image
from pyzbar.pyzbar import decode
from deepface import DeepFace
import socket, select, io, pyotp, cv2, time


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_addr = ("",25961)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.settimeout(100.0)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(server_addr)

server.listen(50)

inputs = [server]

def read_qr(bindata):
    # Convert binary data to an image
    locbin = bindata
    counter = 1
    while True:
        bindata = row.recv(1024)
        if not bindata or b'_EOF' in bindata:
            locbin += bindata[:-4]
            break
        locbin += bindata
        print("chunk recieved "+str(counter))
        counter += 1

    print("waiting door id")
    doorid = row.recv(1024)
    doorid = doorid.decode()

    if doorid is None:
        return 'NONE'

    image = Image.open(io.BytesIO(locbin))
    decoded_obj = decode(image)

    qr_data = [obj.data.decode("utf-8") for obj in decoded_obj]
    print("found codes "+str(len(qr_data)))
    return 'QR#'+qr_data[0]+'#'+doorid if len(qr_data) >= 1 else 'NONE'

db = SessionLocal()

print('Ready to recieve messages...')

while inputs:
    timeout = 1
    read,write,error = select.select(inputs,inputs,inputs,timeout)
    if not (read or write or error):
        continue
        
    for i, row in enumerate(read):
        print(row)
        ## érkező requestek feldolgozása
        try:
            assert type(row) == socket.socket
            if row is server:
                client, clientaddr = row.accept()
                inputs.append(client)
            else:
                ### feldolgozás
                data = row.recv(10240)

                ## this means its an image
                if data.startswith(b'\xff\xd8'):
                    data = read_qr(data)
                else:
                    data = data.decode()
                
                print(data)

                if not data:
                    inputs.remove(row)
                    if row in write:
                        write.remove(row)
                    row.close()
                elif(data == 'HEALTHCHECK'):
                    row.sendall('OK'.encode())
                elif('HEALTHCHECK#' in data):
                    _, id, addr = data.split('#')
                    crud.log_message(db,'door_controller','door',addr,id+' health-checked')
                    #print(addr+" and "+id+" health-checked")
                    if crud.doordata_authcheck(db,id)[0]:
                        resp = crud.doordata_healthcheck(db, id, addr)
                        row.sendall(resp.encode())
                    else:
                        crud.log_message(db,'door_controller','door',addr,id+' is no longer authorized.')
                        row.sendall('NOTAUTHORIZED'.encode())
                    #print("hc response is "+str(resp))
                elif('REGISTER#' in data):
                    ## return back the settings
                    _, address = data.split('#')
                    new_id = crud.doordata_register(db, address)
                    #print(address+" tryied register and got "+str(new_id))
                    if type(new_id) == str:
                        crud.log_message(db,'door_controller','door','',address+' requested auth status')
                        resp = 'OK#'+new_id
                        row.sendall(resp.encode())
                    else:
                        row.sendall('ERR'.encode())
                    pass
                elif('QR#' in data):
                    ## local_userid#current_code
                    _, uid, otp, doorid = data.split('#')
                    bs = crud.get_userdata(db, local_userid=uid)

                    if bs != []:
                        bs = bs[0]
                        hotp = pyotp.HOTP(bs.dynamic_unq.split('#')[1])
                        checkcode = hotp.at(int(bs.dynamic_unq.split('#')[0]))
                        if checkcode == otp:
                            group = crud.doordata_checkaccess(db, doorid, dync=uid)
                            if group[0] and group[1] is None:
                                # ha group 1 valami akkor kamerat ellenorizni
                                crud.log_message(db,'door_controller','user',str(bs.local_userid),doorid+' QR authenticated '+str(bs.local_userid)+' with HOTP at '+str(bs.dynamic_unq.split('#')[0]))
                                row.sendall('OK'.encode())
                                crud.doordata_raisedynotp(db,uid)
                            elif group[0] and udata[0].fid is not None:
                                cam = crud.get_camera(db,local_correlid=group[1])[0]
                                img_array = np.frombuffer(udata[0].fid, np.uint8)
                                img_num = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                                try:
                                    print("calling cam image")
                                    time.sleep(2)
                                    cap = cv2.VideoCapture(cam.rtsp_host)
                                    if cap.isOpened():
                                        success, frame = cap.read()
                                        if success:
                                            #norm_array = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                                            res = DeepFace.verify(img1_path=img_num,img2_path=frame)
                                            if res['verified']:
                                                crud.log_message(db, 'door_controller', 'user', str(data.split('#')[1]),doorid + ' authenticated (with FID) ' + str(data.split('#')[1]))
                                                row.sendall('OK'.encode())
                                                print("image verified")
                                            else:
                                                crud.log_message(db, 'door_controller', 'user',
                                                                 str(data.split('#')[1]),
                                                                 doorid + ' FAILED (FID img not satisfied) to authenticate ' +
                                                                 str(data.split('#')[1]))
                                                row.sendall('NONE'.encode())
                                                print("image verification failed")
                                    cap.release()
                                except Exception as e:
                                    crud.log_message(db, 'door_controller', 'user', str(data.split('#')[1]),doorid + ' FAILED (FID img doesnt have a person) to authenticate ' + str(data.split('#')[1]))
                                    print(e)
                                    row.sendall('NONE'.encode())
                            else:
                                crud.log_message(db,'door_controller','user',str(bs.local_userid),doorid+' QR FAILED (groupcheck) to authenticate '+str(bs.local_userid)+' with HOTP at '+str(bs.dynamic_unq.split('#')[0]))
                                row.sendall('NONE'.encode())
                        else:
                            crud.log_message(db, 'door_controller', 'user', str(bs.local_userid),doorid + ' QR FAILED (wrong HOTP) to authenticate ' + str(bs.local_userid) + ' with HOTP at ' + str(bs.dynamic_unq.split('#')[0]))
                            row.sendall('NONE'.encode())
                    else:
                        crud.log_message(db, 'door_controller', 'user','',doorid + ' QR FAILED (unknown user) to authenticate ')
                        row.sendall('NONE'.encode())

                elif('INC#' in data):
                    '''
                        test if after # its a valid UNQ or DYNNQ
                    '''
                    _, id, staticunq = data.split('#')
                    authcheck = crud.doordata_authcheck(db,id)
                    camlink = authcheck[1]
                    if authcheck[0]:
                        udata = crud.get_userdata(db, static_unq=staticunq)
                        if len(udata) == 1:
                            ## here check user groups
                            group = crud.doordata_checkaccess(db,id,usernc=staticunq)
                            if group[0] and group[1] is None:
                                # ha group 1 valami akkor kamerat ellenorizni
                                crud.log_message(db,'door_controller','user',staticunq,id+' authenticated '+str(staticunq))
                                row.sendall('OK'.encode())
                            elif group[0] and udata[0].fid is not None:
                                cam = crud.get_camera(db,local_correlid=group[1])[0]
                                img_array = np.frombuffer(udata[0].fid, np.uint8)
                                img_num = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                                try:
                                    print("calling cam image")
                                    time.sleep(2)
                                    cap = cv2.VideoCapture(cam.rtsp_host)
                                    if cap.isOpened():
                                        success, frame = cap.read()
                                        if success:
                                            #norm_array = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                                            res = DeepFace.verify(img1_path=img_num,img2_path=frame)
                                            if res['verified']:
                                                crud.log_message(db, 'door_controller', 'user', str(data.split('#')[1]),str(clientaddr[0]) + ' authenticated (with FID) ' + str(data.split('#')[1]))
                                                row.sendall('OK'.encode())
                                                print("image verified")
                                            else:
                                                crud.log_message(db, 'door_controller', 'user',
                                                                 str(data.split('#')[1]),
                                                                 str(clientaddr[0]) + ' FAILED (FID img not satisfied) to authenticate ' +
                                                                 str(data.split('#')[1]))
                                                row.sendall('NONE'.encode())
                                                print("image verification failed")
                                    cap.release()
                                except Exception as e:
                                    crud.log_message(db, 'door_controller', 'user', str(data.split('#')[1]),str(clientaddr[0]) + ' FAILED (FID img doesnt have a person) to authenticate ' + str(data.split('#')[1]))
                                    print(e)
                                    row.sendall('NONE'.encode())
                            else:
                                if udata[0].fid is not None:
                                    crud.log_message(db, 'door_controller', 'user', str(data.split('#')[1]), str(clientaddr[0]) + ' FAILED (group check) to authenticate ' + str(data.split('#')[1]))
                                else:
                                    crud.log_message(db, 'door_controller', 'user', str(data.split('#')[1]),str(clientaddr[0]) + ' FAILED (group check and/or no FID image stored) to authenticate ' + str(data.split('#')[1]))
                                row.sendall('NONE'.encode())
                        else:
                            crud.log_message(db,'door_controller','user',str(data.split('#')[1]),str(clientaddr[0])+' FAILED to authenticate '+str(data.split('#')[1]))
                            row.sendall('NONE'.encode())
                    else:
                        crud.log_message(db,'door_controller','door',str(data.split('#')[1]),str(clientaddr[0])+' is no longer authorized.')
                        row.sendall('NOTAUTHORIZED'.encode())
                else:
                    row.sendall('NONE'.encode())
        except socket.error as e:
            print("hiba ",e)
            inputs.remove(row)
            if row in write:
                write.remove(row)
            row.close()
        except Exception as e:
            print(e)
            break