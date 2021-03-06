import pickle
import sys
import threading
import time
import numpy as np
import cv2
from PyQt5 import QtGui
from mss import mss
import PyQt5
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon

from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QProgressDialog, \
    QSystemTrayIcon, QAction, QMenu
import socket

client = None
clientIsOn = False
DISCONNECT_MESSAGE = "!DISCONNECT"
ADDR = ("180.76.147.175", 5051)
MY = "dlskk90105kdlslnvnsl"
#ADDR = ("192.168.50.31", 5051)


window = None
app = None
tray_icon = None

idTextField = None
nameTextField = None

start_last_clicked = time.time()
prev_meeting_id = "%prev_meeting_id%"
prev_name = "%prev_name%"

class MainWindow (QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.layout = QHBoxLayout()

        global idTextField
        idTextField = QLineEdit()
        idTextField.setEchoMode(QLineEdit.Normal)
        idTextField.setFixedWidth(200)

        label1 = QLabel("Meeting ID: ")#label 1 is Meeting ID Label
        label1.setBuddy(idTextField)

        global nameTextField
        nameTextField = QLineEdit()
        nameTextField.setEchoMode(QLineEdit.Normal)
        nameTextField.setFixedWidth(150)

        label2 = QLabel("Guest Name: ")  # label 1 is Meeting ID Label
        label2.setBuddy(idTextField)

        buttonStart = QPushButton("")
        buttonStart.setIcon(QIcon("start.png"))
        buttonStart.setIconSize(QSize(24, 24))
        buttonStart.clicked.connect(startStreaming)

        buttonStop = QPushButton("")
        buttonStop.setIcon(QIcon("stop.png"))
        buttonStop.setIconSize(QSize(24, 24))
        buttonStop.clicked.connect(closeClient)

        global tray_icon
        tray_icon = QSystemTrayIcon(self)
        tray_icon.setIcon(QIcon("tray.jpg"))

        open_action = QAction("open", self)
        open_action.triggered.connect(self.show)
        close_action = QAction("close", self)
        close_action.triggered.connect(terminate)

        tray_menu = QMenu()
        tray_menu.addAction(open_action)
        tray_menu.addAction(close_action)
        tray_icon.setContextMenu(tray_menu)
        tray_icon.activated.connect(self.show)
        tray_icon.show()

        self.layout.addWidget(label1)
        self.layout.addWidget(idTextField)
        self.layout.addWidget(label2)
        self.layout.addWidget(nameTextField)
        self.layout.addWidget(buttonStart)
        self.layout.addWidget(buttonStop)

        self.setLayout(self.layout)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

def terminate():
    try:
        closeClient()
    except Exception as err:
        print(err)
    finally:
        global tray_icon
        tray_icon.hide()
        sys.exit()

def closeClient():
    global clientIsOn, client
    if clientIsOn:
        client.close()
        clientIsOn = False
    else:
        return

def collectMsg(name, meeting_id):
    screen = None

    with mss() as sct:
        # Get information of monitor 2
        monitor_number = 1
        mon = sct.monitors[monitor_number]
        screen = sct.grab(mon)

    screen = np.array(screen)
    screen = cv2.resize(screen, (400, 200))
    screen = cv2.cvtColor(screen, cv2.COLOR_RGBA2RGB)
    screen = screen.tobytes()
    print("screen_length: " + str(len(screen)))

    b_meeting_id = meeting_id.encode("utf-8")
    b_meeting_id = b_meeting_id + b' ' * (300 - len(b_meeting_id))
    print("meeting_id: " + meeting_id)

    b_name = name.encode("utf-8")
    b_name = b_name + b' ' * (100 - len(b_name))
    print("name:" + nameTextField.text())

    timeStamp = str(time.time()).encode("utf-8")
    timeStamp = timeStamp + b' ' * (100 - len(timeStamp))
    print("timeStamp:" + str(time.time()))

    msg = b_meeting_id + b_name + timeStamp + screen
    # print("image size: " + str(len(screen)))
    print("length sent: " + str(len(msg)))
    return msg

def clientSend(client, msg):
    beg = 0
    while beg < len(msg):
        end = beg + 1000
        sent = msg[beg:min(end, len(msg))]
        client.send(sent)
        beg = end

def startStreaming():
    global clientIsOn, start_last_clicked, prev_name, prev_meeting_id

    #protection against violent operations
    if (time.time() - start_last_clicked) <= 0.5:
        print("useless click")
        return
    else:
        start_last_clicked = time.time()

    #if meeting_id or name is blank, do nothing
    if nameTextField.text().strip() == "" or idTextField.text().strip() == "":
        print("useless click")
        return

    #if client is on, and name+meeting_id remain the same, do nothing
    if nameTextField.text() == prev_name and idTextField.text() == prev_meeting_id and clientIsOn:
        print("useless click")
        return

    #make sure client is closed, now clientIsOn = False
    if clientIsOn:
        closeClient()

    #if client is turned off, make sure that previous thread exits
    while len(threading.enumerate()) >= 2:
        print("wait for previous connection exit")
        time.sleep(0.01)

    def clientAction(name, meeting_id):
        global client, clientIsOn, prev_name, prev_meeting_id
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)
        print("Connected to ["+str(ADDR)+"]")

        clientIsOn = True
        prev_meeting_id = meeting_id
        prev_name = name

        startMsg = "Student".encode("utf-8")
        startMsg = MY.encode("utf-8")+startMsg
        startMsg = startMsg + b" "*(64-len(startMsg))
        client.send(startMsg)

        while clientIsOn:
            print("loop")
            msg = collectMsg(name, meeting_id)
            try:
                clientSend(client, msg)
            except OSError:
                print("client closed")
                break
            except Exception as exp:
                print("client closed with exception @"+str(exp))
                break
            # sleep for 1.2 seconds
            for i in range (0, 12):
                if clientIsOn:
                    time.sleep(0.1)
                else:
                    print("client closed")
                    break

    thread = threading.Thread(target=clientAction, args=(nameTextField.text(), idTextField.text()))
    thread.start()
    #window.hide()


if __name__ == '__main__':
    app = QApplication([])
    app.setApplicationName("Zoom???????????????")
    #TODO: set application window icon
    window = MainWindow()
    window.setFixedHeight(80)
    window.setWindowIcon(QIcon("tray.jpg"))
    window.show()
    app.exec_()
