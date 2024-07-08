from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np
import time 

class Detection(QThread):

    def __init__(self):
        super(Detection,self).__init__()

    changePixmap = pyqtSignal(QImage)

    def run(self):
        self.running= True
        
        net= cv2.dnn.readNet("weights/yolov4.weights","cfg/yolov4.cfg")
        classes=[]
        with open("obj.names", "r") as f:
            classes = [line.strip() for line in f.readlines()]
        
        layerNames = net.getLayerNames()
        outputLayers = [layerNames[i[0] - 1 ]for i in net.getUnconnectedOutLayers()]
        colors=np.random.uniform(0, 255, size=(len(classes), 3))

        font = cv2.FONT_HERSHEY_PLAIN
        startingTime = time.time()

        cap=cv2.VideoCapture(0)

        while self.running:
            ret, frame =cap.read()

            if ret: 
                height, width,channels = frame.shape

                blob = cv2.dnn.blobFromImage(frame, 0.00392, (416,416),(0,0,0), True, crop=False)
                net.setInput(blob)
                outs=net.forward(outputLayers)

                classIds = []
                confidences = []
                boxes=[]
                for out in outs:
                    for detection in out:
                        scores = detection[5:]
                        classId= np.argmax(scores)
                        confidence = scores(classId)

                        if confidence >0.98:
                            center_x = int(detection[0]*width)
                            center_y = int(detection[1]*height)
                            w=int(detection[2]*width)
                            h=int(detection[3]*height)

                            x=int(center_x - w / 2)
                            y=int(center_y - w / 2)

                            boxes.append([x,y,w,h])
                            confidences.append(float(confidence))
                            classIds.append(classId)
                            
                            elapsedTime = startingTime - time.time()
                            if elapsedTime <= -10: 
                                startingTime = time.time()
                                self.saveDection(frame)

                indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.8, 0.3)
                for i in range(len(boxes)):
                    x,y,w,h=boxes[i]
                    label =str(classes[classIds[i]])
                    confidence= confidences[i]
                    color =(256,0,0)
                    cv2.rectangle(frame,(x,y),(x+w,y+h),color,2)
                    cv2.putText(frame, label + "{0:.1}".format(confidence),(x,y-20),font,3,color,3)


                rgbImage=cv2. cvtColor(frame, cv2.COLOR_BGR2RGB)
                bytesPerLine=channels*width
                convertToQtFormat = QImage(rgbImage.data, width, height,bytesPerLine,QImage.Format_RGB888)
                p= convertToQtFormat.scaled(854,480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)

    def saveDetection (self,frame):
        cv2.imwrite("savedFrame/frame.jpg",frame)
        print("Frame Guardado")

