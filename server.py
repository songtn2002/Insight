import pickle
import socket
import threading
import time
import numpy as np

HEADER = 50
PORT = 5051
SERVER = ""
#SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"

classrooms = {}
connected = {}

def removeStudent(meeting_id, name):
    if meeting_id == "%prev%" and name == "%prev%":
        return
    classroom = classrooms[meeting_id]
    removeIndex = -1
    for i in range (0, len(classroom)):
        if classroom[i][0] == name:
            removeIndex = i
            break
    if removeIndex != -1:
        classroom.pop(removeIndex)
    else:
        print("Cannot find student with name: "+name)

def addView (classroom, view):
    found = False
    for i in classroom:
        if i[0] == view[0]: #if the same name, then change the img and time_stamp
            i[1] = view[1]
            i[2] = view[2]
            found = True
            break
    if found == False:
        classroom.append(view)

def printClassrooms():
    result = "classrooms: {"
    for k in classrooms.keys():
        result += "\""+ k + "\":"+"["
        for item in classrooms[k]:
            result += "[" + item[0] +", "+ str(item[2]) +"], "
        result += "]"
    result += "}"
    print(result)

def printClassroomsThread():
    while True:
        printClassrooms()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 2}")
        time.sleep(2)

printThread = threading.Thread(target=printClassroomsThread, args=())

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")

    msg = conn.recv(HEADER).decode("utf-8")
    if msg == "Student":#student connection
        handle_student(conn, addr)
    else:#teacher
        handle_teacher(conn, addr, msg)

def handle_teacher(conn, addr, msg):
    meeting_id = msg.split("@")[1]

    if not (meeting_id in classrooms.keys()):
        classrooms[meeting_id] = []

    while True:
        try:
            conn.send(pickle.dumps(classrooms[meeting_id]))
        except ConnectionError:
            print("connection closed 2")
            break
        #sleep for a while
        time.sleep(1.5)

    conn.close()

def handle_student(conn, addr):
    while True:
        msg = conn.recv(400000)
        print("length of message: "+str(len(msg)))
        if len(msg) > HEADER:#This is an entire image
            #print("Handle Image")
            meeting_id = msg[0:300].decode(FORMAT).strip()
            print("meeting_id: "+meeting_id)
            name = msg[300:400].decode(FORMAT).strip()
            print("name: "+name)
            time_stamp = float(msg[400:500].decode(FORMAT).strip())
            print("time_stamp: "+str(time_stamp))
            img = np.frombuffer(msg[500:], dtype="uint8")
            img = img.reshape(200, 400, 3)
            #print("length of image bytes: "+str(len(img)))
            view = [name, img, time_stamp]

            if meeting_id in classrooms.keys():
                addView(classrooms[meeting_id], view)
            else:
                classrooms[meeting_id] = [view]

        else: #likely a disconnect message
            msg = msg.decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                break
            else:
                print("some bugs from student")
    removeStudent(meeting_id, name)
    conn.close()

def start():
    server.listen()
    printThread.start()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

print("[STARTING] server is starting...")
start()