from db.database import SessionLocal, engine
import db.models as models
import db.crud as crud

from PIL import Image
from ultralytics import YOLO

import easyocr, cv2, socket, time

print("Loading modell and db...")

model = YOLO("/app/numplate_weights.pt")
db = SessionLocal()

print("Running...")

class Caps:
    def __init__(self):
        self.check_cams = []
        self.input_cams = []

    def LoadCaps(self):
        cams = crud.get_camera(db)
        if self.check_cams != cams:
            for cpp in self.input_cams:
                cpp[0].release()
            self.check_cams = cams
            self.input_cams = []
            for row in self.check_cams:
                doorlink = crud.get_doordata(db,camera_link=row.local_correlid)
                if len(doorlink) > 0:
                    for door in doorlink:
                        self.input_cams.append((row,door))
                else:
                    self.input_cams.append((row,None))

cap = Caps()
charlist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
reader = easyocr.Reader(['en'])

while True:
    cap = Caps()
    cap.LoadCaps()
    #print("figyelt kamerak db: "+str(len(cap.input_cams)))
    for cpp in cap.input_cams:
        cam = cv2.VideoCapture(cpp[0].rtsp_host)
        for _ in range(0,3):
            success, frame = cam.read()
            if success:
                break
            time.sleep(2)
        #print("siker: "+str(success))
        if success:
            results = model(frame,conf=0.8,show_labels=True,show_conf=True,verbose=False)
            tens = results[0].boxes.conf.item() if len(results[0].boxes.conf) > 0 else 0.0
            #print("tensor:"+str(tens))
            if len(results) > 0 and (tens >= 0.8):
                xmin,ymin,xmax,ymax = results[0].boxes[0].xyxy[0].int().tolist()

                cutout_frame = frame[ymin:ymax, xmin:xmax]

                gray = cv2.cvtColor(cutout_frame, cv2.COLOR_BGR2GRAY) #convert image to gray
                bfilter = cv2.bilateralFilter(gray, 11, 17, 17) #noise reduction
                normalized_img = cv2.cvtColor(bfilter, cv2.COLOR_BGR2RGB)

                print("text olvasas")
                result = reader.readtext(normalized_img,allowlist=charlist)

                frame_string = None
                if len(result) == 1:
                    ## egy soros rendszamtabla
                    frame_string = result[0][-2][1:]
                elif len(result) == 2:
                    if len(result[0][-2]) > 3:
                        frame_string = result[0][-2][1:] + result[1][-2]
                    elif len(result[1][-2]) > 3:
                        frame_string = result[0][-2] + result[1][-2][1:]
                    else:
                        frame_string = result[0][-2] + result[1][-2]

                print(str(frame_string))
                if frame_string is not None:
                    user = crud.get_numplatedata(db,numplate=frame_string)
                    if len(user) >= 1:
                        crud.log_message(db,'camera_controller','numberplate',str(cpp[0].local_correlid),str(cpp[0].local_correlid)+' noticed '+str(frame_string)+' numberplate')
                        if cpp[1] != None:
                            print(user[0].nickname)
                            access = crud.doordata_checknumplateaccess(db,doorid=cpp[1].local_correlid,numplid=user[0].numplateid)
                            if access:
                                crud.log_message(db,'camera_controller','numberplate',str(cpp[0].local_correlid),str(cpp[0].local_correlid)+' authenticated '+str(frame_string)+' numberplate')
                                for l in range(0,3):
                                    success = False
                                    try:
                                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                                        sock.settimeout(10)
                                        server_address = (str(cpp[1].ipaddr), 25962)
                                        sock.connect(server_address)
                                        sock.sendall('OPEN'.encode())
                                        response = sock.recv(1024).decode()
                                        if response == 'ERR':
                                            print("recieved error from door")
                                            success = True
                                        else:
                                            print("recieved response "+str(response))
                                            success = True
                                    except Exception as e:
                                        print("exception in calling door: "+str(e))
                                    finally:
                                        sock.close()
                                        print("sock closed, waiting before next read")
                                        time.sleep(5)
                                    if success:
                                        break
                                    print("Exception happened, trying again ("+str(l+1)+"/3)")
                            else:
                                crud.log_message(db,'camera_controller','numberplate',str(cpp[0].local_correlid),str(cpp[0].local_correlid)+' FAILED (group check) to authenticate '+str(frame_string)+' numberplate')