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
#ADDR = ("192.168.50.31", 5051)


window = None
app = None
tray_icon = None

idTextField = None
nameTextField = None

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
        client.send(DISCONNECT_MESSAGE.encode("utf-8"))
        client.close()
        clientIsOn = False
    else:
        return

def startStreaming():
    #if the client is already running, don't do anything. Otherwise, continue with clientIsOn = True
    global clientIsOn
    if clientIsOn:
        return
    else:
        clientIsOn = True

    def clientAction(meeting_id, name):
        global client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)
        client.send("Student".encode("utf-8"))
        while clientIsOn:
            print("loop")
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
            print("screen_length: "+str(len(screen)))

            b_meeting_id = meeting_id.encode("utf-8")
            b_meeting_id = b_meeting_id + b' '*(300-len(b_meeting_id))
            print("meeting_id " + idTextField.text())
            b_name = name.encode("utf-8")
            b_name = b_name + b' '*(100-len(b_name))
            print("name:" + nameTextField.text())
            timeStamp = str(time.time()).encode("utf-8")
            timeStamp = timeStamp + b' ' * (100 - len(timeStamp))
            print("timeStamp:" + str(time.time()))
            msg = b_meeting_id + b_name + timeStamp + screen
            #print("image size: " + str(len(screen)))
            print("length sent: "+ str(len(msg)) )
            client.send(msg)

            # sleep for 1.2 seconds
            for i in range (0, 12):
                if clientIsOn:
                    time.sleep(0.1)
                else:
                    break

    thread = threading.Thread(target=clientAction, args=(idTextField.text(), nameTextField.text()))
    thread.start()
    #window.hide()


if __name__ == '__main__':
    app = QApplication([])
    app.setApplicationName("Zoom视频加速器")
    #TODO: set application window icon
    window = MainWindow()
    window.setFixedHeight(80)
    window.setWindowIcon(QIcon("tray.jpg"))
    window.show()
    app.exec_()
