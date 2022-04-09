import pickle
import socket
import sys
import threading
import time

from PyQt5.QtGui import QIcon, QImage, QPixmap, QPainter, QPen, QColor, QBrush, QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QApplication, QGridLayout
from PyQt5.QtCore import Qt, QTimer

window = None
labels = [[None, None, None, None], [None, None, None, None], [None, None, None, None], [None, None, None, None]]
students = []

connect_last_clicked = time.time()

def printStudents():
    res = "["
    for block in students:
        bStr = "[" + block[0] + ", "+str(block[2])+"]"
        res += bStr + ", "
    res += "]"
    print(res)

client = None
prev_meeting_id = ""
DISCONNECT_MESSAGE = "!DISCONNECT"
ADDR = ("180.76.147.175", 5051)
#ADDR = ("192.168.50.31", 5051)

def closeClient():
    global client
    if client:
        client.close()

def terminate():
    try:
        closeClient()
    except Exception as err:
        print(err)
    finally:
        sys.exit()

def reconnect():
    global clientIsOn
    #limit the interval between click to more than 0.5 seconds
    if (time.time() - connect_last_clicked) <= 0.5:
        return

    #do nothing if meeting id is blank
    if window.meeting_id_textField.text() == "":
        return

    #do nothing if client is on and meeting id has not yet changed
    if window.meeting_id_textField.text() == prev_meeting_id:
        return

    closeClient()

    def clientAction():
        global window, students, client, prev_meeting_id
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)
        meeting_id = window.meeting_id_textField.text()
        startString = "Teacher@"+ meeting_id
        client.send(startString.encode("utf-8"))
        prev_meeting_id = meeting_id
        while True:
            try:
                students = pickle.loads(client.recv(400000*16))
            except OSError:
                break
            printStudents() #print all the student views received
        print("client closed")

    thread = threading.Thread(target=clientAction, args=())
    thread.start()

class MainWindow(QWidget):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.main_layout = QVBoxLayout()
        self.top_bar = QHBoxLayout()
        self.bottom_area = QGridLayout()

        self.meeting_id_textField = QLineEdit()
        self.meeting_id_textField.setEchoMode(QLineEdit.Normal)
        self.meeting_id_textField.setMinimumWidth(150)

        self.meeting_id_label = QLabel("meeting_id: ")
        self.meeting_id_label.setBuddy(self.meeting_id_textField)

        self.connect_buttton = QPushButton("connect")
        self.connect_buttton.clicked.connect(reconnect)

        self.top_bar.addWidget(self.meeting_id_label)
        self.top_bar.addWidget(self.meeting_id_textField)
        self.top_bar.addWidget(self.connect_buttton)
        self.top_bar.setAlignment(Qt.AlignTop)

        #initialize all the labels
        for i in range(0, 4):
            for j in range(0, 4):
                label = QLabel()
                label.setFixedWidth(400)
                label.setFixedHeight(200)
                self.bottom_area.addWidget(label, i, j)
                labels[i][j] = label

        self.main_layout.addLayout(self.top_bar)
        self.main_layout.addLayout(self.bottom_area)

        self.setLayout(self.main_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.updateImages())
        self.timer.start(2000)

    def closeEvent(self, event):
        QWidget.closeEvent(self, event)
        terminate()

    def updateImages(self):
        for x in range(0, 4):
            for y in range(0, 4):
                labels[x][y].clear()
        for i in range (0, len(students)):
            x = int(i/4)
            y = i%4
            image = QImage(students[i][1], 400, 200, QImage.Format_RGB888)

            painter = QPainter(image)
            rectWidth = len(students[i][0])*12+5
            rectHeight = 30
            painter.fillRect(400-rectWidth, 200-rectHeight, rectWidth, rectHeight, 1)
            painter.setFont(QFont("Times", 12, QFont.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(400-rectWidth, 195, students[i][0])
            labels[x][y].setPixmap(QPixmap.fromImage(image))
            painter.end()


if __name__ == '__main__':
    app = QApplication([])
    app.setApplicationName("Zoom监视器")
    window = MainWindow()
    window.setFixedWidth(1650)
    window.setFixedHeight(900)
    window.setWindowIcon(QIcon("tray.jpg"))
    window.show()
    app.exec_()