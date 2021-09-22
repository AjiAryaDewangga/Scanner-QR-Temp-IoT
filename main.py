import os
import qrcode
from PIL.ImageQt import ImageQt
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtCore import Qt
import MySQLdb
global c
global db

import time
import datetime
# import system module
import sys

# import some PyQt5 modules
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer

##library suhu
import board
import busio as io
import adafruit_mlx90614

# import Opencv module
import cv2

from time import sleep
import time
from gui import *

class MainWindow(QWidget):
    # class constructor
    def __init__(self):
        # call QWidget constructor
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # create a timer
        self.timer = QTimer()
        # set timer timeout callback function
        self.timer.timeout.connect(self.viewCam)
        # set control_bt callback clicked  function
        self.ui.control_bt.clicked.connect(self.controlTimer)
        self.ui.pushButton.clicked.connect(self.read_from_db)
        self.ui.buttonClear.clicked.connect(self.clear_fields)
        self.ui.buttonSaveImage.clicked.connect(self.save_qr_code)
        self.qrCode = True
        self.waitsuhu = 0
        self.loop = 0
        self.loop2 = 0
        self.ukurSuhu = True
        self.data = 'null'
        self.status = 'null'
        self.late = 0
        
    def time_late(self):
        jammasuk = 15
        timemenit = (datetime.datetime.fromtimestamp(time.time()).strftime("%M"))
        timejam = (datetime.datetime.fromtimestamp(time.time()).strftime("%H"))
        if ((int(timejam) - jammasuk) == 1):
            self.late = (int(timemenit))
        elif ((int(timejam) - jammasuk) == 2):
            self.late = (int(timemenit)) + 60
        else:
            self.late = 0
        
        print(self.late)
        
    def clear_fields(self):
        self.ui.textEdit.clear()
        self.ui.textEdit_username.clear()
        self.ui.image_qr.clear()
        
        
    def create_qr_code(self):
        text = self.ui.textEdit_username.text()
        
        img = qrcode.make(text)
        qr = ImageQt(img)
        pix = QPixmap.fromImage(qr)
        self.ui.image_qr.setPixmap(pix)
        
    def save_qr_code(self):
        current_dir = os.getcwd()
        file_name = self.ui.textEdit.text()
        if file_name:
            print(file_name, '.png tersimpan')
            self.ui.image_qr.pixmap().save(os.path.join(current_dir, 'User' , file_name + '.png'))
            

    def countdown(self):
        t = 2
        while t:
            mins, secs = divmod(t, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            time.sleep(1)
            t -= 1
        
    def cekSuhu(self):
        if self.ukurSuhu == True:           
            i2c = io.I2C(board.SCL, board.SDA, frequency=100000)
            mlx = adafruit_mlx90614.MLX90614(i2c)

            targetTemp = float("{:.2f}".format(mlx.object_temperature))
            self.suhu = targetTemp + 1
            self.ui.label_suhu_2.setText(str(self.suhu))
        
        if 34 < self.suhu < 36:           
            if self.loop2 > 10:
                self.ukurSuhu = False
            if self.loop2 < 200:
                self.loop2 += 1
                self.ui.label_keterangan.setText("Absensi Berhasil")
                print("loop 2", self.loop2)
            else:
                self.status = "Absensi Berhasil"
                self.insert_datamasuk_to_db()
                self.resetValue()
                self.controlTimer()
                self.qrCode = True
                self.ukurSuhu = True
                self.controlTimer()
                
        else:
            if self.loop < 300:
                self.loop += 1
                self.ui.label_keterangan.setText("Absensi Ditolak")
                print("loop 1", self.loop)
            else:
                self.status = "Absensi Ditolak"
                self.insert_datamasuk_to_db()
                self.controlTimer()
                self.resetValue()
                self.qrCode = True
                self.controlTimer()

    # view camera
    def viewCam(self):
        if self.qrCode == True:
            # read image in BGR format
            ret, image = self.cap.read()
            self.data, bbox, _ = self.detector.detectAndDecode(image)
            # convert image to RGB format
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # get image infos
            height, width, channel = image.shape
            step = channel * width
            # create QImage from image
            qImg = QImage(image.data, width, height, step, QImage.Format_RGB888)
            # show image in img_label
            
            if bbox is not None:
                for i in range(len(bbox)):
                    cv2.line(image, tuple(bbox[i][0]), tuple(bbox[(i+1) % len(bbox)][0]), color=(255, 0, 0), thickness=2)
                    
                cv2.putText(image, self.data, (int(bbox[0][0][0]), int(bbox[0][0][1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                if self.data:
                    self.read_from_db_absensi()
                    
            self.ui.image_label.setPixmap(QPixmap.fromImage(qImg))
            
        else:
            self.ui.image_label.setText("Cek Suhu Anda")
            self.cekSuhu()
            
    def resetValue(self):
        self.ui.label_nama.setText("-")
        self.ui.label_suhu_2.setText("-")
        self.ui.label_keterangan.setText("-")
        self.loop2 = 0
        self.loop = 0
    
    def read_from_db_absensi(self):
        try:
            code = (str(self.data))
            c.execute("SELECT * FROM db_users WHERE code = " + code)       
            result = c.fetchall()
            if result is not None:
                print("User: ",result[0][1])
                self.ui.label_nama.setText(result[0][1])
                self.qrCode = False
                
        except:
            self.ui.label_nama.setText("Tidak Terdeteksi")
            print ("Tidak Terdeteksi")
            
    # start/stop timer
    def controlTimer(self):
        # if timer is stopped
        if not self.timer.isActive():
            # create video capture
            self.cap = cv2.VideoCapture(0)
            self.detector = cv2.QRCodeDetector()
            # start timer
            self.timer.start(20)
            # update control_bt text
            self.ui.control_bt.setText("Stop")
        # if timer is started
        else:
            # stop timer
            self.timer.stop()
            # release video capture
            self.cap.release()
            # update control_bt text
            self.ui.image_label.setText("Aktifkan Scan QR Code")
            self.ui.control_bt.setText("Start")
    
    def insert_datamasuk_to_db(self):
        self.time_late()
        code = (str(self.data))
        c.execute("SELECT * FROM db_users WHERE code = " + code)        
        result = c.fetchall()
        sql =  "INSERT INTO db_datamasuk (name, temp, status, late_time) VALUES (%s, %s , %s, %s)" 
        try:
            c.execute(sql,(str(result[0][1]) , str(self.suhu) , str(self.status) , str(self.late)))
            db.commit()
        except:
            db.rollback()
        #db.close()

    def insert_to_db(self):
        insert_name = self.ui.textEdit.text()
        insert_username = self.ui.textEdit_username.text()
        sql =  "INSERT INTO db_users (name, code) VALUES (%s, %s)" 
        try:
            c.execute(sql,( str(insert_name) , str(insert_username)))
            db.commit()
            self.create_qr_code()
        except:
            db.rollback()
        

    def read_from_db(self):
        insert_username = self.ui.textEdit_username.text()
        try:
            code = (str(insert_username))
            
            #c.execute("SELECT * FROM TAB_CPU WHERE ID = (SELCET MAX(ID) FROM TAB_CPU)")
            c.execute("SELECT * FROM db_users WHERE code = " + code)       
            result = c.fetchall()
            if result is not None:
                print ('No: ' , result[0][0], '| Nama: ' , result[0][1], ' | Kode: ' , result[0][2])
                print ("Username Sudah Terpakai")
                self.ui.image_qr.setText("ID Sudah Terpakai!")
                
        except:
            self.insert_to_db()
            print ("Create User Berhasil")

if __name__ == '__main__':
    try:
        db = MySQLdb.connect("139.99.121.149","ptckitco_andhika","andhika12345678","ptckitco_absensi_tracing")
        c= db.cursor()
    except:
        print ("Koneksi GAGAL")
        
    app = QApplication(sys.argv)

    # create and show mainWindow
    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec_())