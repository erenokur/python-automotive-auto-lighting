import tkinter as tk
from tkinter import *
from tkinter import filedialog as fd
import cv2
import numpy as np
import random
import os.path
from os import path
from PIL import Image, ImageFont, ImageDraw, ImageTk
import sched, time
import threading
import moviepy.editor as mp
import serial

random.seed(100)


#arayüz tanımları
root = Tk() 
root.title("Etkin Araç Far Ayarlama Uygulaması") 
root.maxsize(900, 600) 
root.config(bg="#008000") 

left_frame = Frame(root, width=200, height=500, bg='grey')
left_frame.grid(row=0, column=0, padx=10, pady=5)
right_frame = Frame(root, width=650, height=400, bg='grey')
right_frame.grid(row=0, column=1, padx=10, pady=5)

def check_int(s):
    if s[0] in ('-', '+'):
        return s[1:].isdigit()
    return s.isdigit()

def DrawImageBox(image):
    for widget in right_frame.winfo_children():
        widget.destroy()
    Label(right_frame, image=image).grid(row=0,column=0, padx=5, pady=5)

schedule = sched.scheduler(time.time, time.sleep)
def PrintScreen(textString):
        img = Image.new('RGBA' ,(650,400), 'grey')
        font= ImageFont.truetype("arial.ttf",15)
        w,h= font.getsize(textString)
        draw = ImageDraw.Draw(img)
        draw.text(((650-w)/2,(400-h)/2), textString,font=font, fill='white')
        image = ImageTk.PhotoImage(img)
        schedule.enter(5, 1, DrawImageBox(image))
        schedule.run()

def ResizeVideo(videoPath):
    if path.exists("temp/movie_temp_" + os.path.basename(videoPath) +".mp4"):
        print ("video işlemiş" )
        #os.remove("movie_temp.mp4")
    else:
        clip = mp.VideoFileClip(videoPath)
        clip_resized = clip.resize(height=360) 
        clip_resized.write_videofile("temp/movie_temp_" + os.path.basename(videoPath) +".mp4")
   

Label(left_frame, text="Eren OKUR 21908613\nOtomotiv Proje Çalışması").grid(row=0, column=0, padx=5, pady=5)

def CreateDirectory(givenPath):
    try:
        os.makedirs(givenPath)
    except OSError:
        print ("dizin oluşturma yapılamadı: %s " % givenPath)
    else:
        print ("dizin başarılı şekilde oluşturuldu %s" % givenPath)


if path.exists('temp') and path.exists('data') and path.exists('data/student.jpg'):
    studentRawimage = Image.open("data/student.jpg")
    studentRawimage = studentRawimage.resize((150, 150), Image.ANTIALIAS)
    studentImage = ImageTk.PhotoImage(studentRawimage)
    Label(left_frame, image=studentImage).grid(row=1, column=0, padx=5, pady=5)
    img = Image.new('RGBA' ,(650,400), 'grey')
    textString = "Hoş geldiniz...\nÖnce bir video seçiniz \nSonra yola çıka tıklayınız"
    font= ImageFont.truetype("arial.ttf",15)
    w,h= font.getsize(textString)
    draw = ImageDraw.Draw(img)
    draw.text(((650-w)/2,(400-h)/2), textString,font=font, fill='white')
    image = ImageTk.PhotoImage(img)
    DrawImageBox(image)
else:
    if not path.exists('temp'):
        CreateDirectory('temp');
    if not path.exists('data'):
        CreateDirectory('data');
    img = Image.new('RGBA' ,(650,400), 'white')
    if not path.exists("data/student.jpg"):
        textString = "Hoş geldiniz...\nBir video seçerek işleme başlayabilirsiniz\nBir adet uyarı mavcut:\nÖğrenci resmi bulunamadı.\nÖğrenci resmini data dizininin içine student.jpg ismi ile yapıştırınız."
    else:
        textString = "Hoş geldiniz...\nÖnce bir video seçiniz \nSonra yola çıka tıklayınız"
    font= ImageFont.truetype("arial.ttf",15)
    w,h= font.getsize(textString)
    draw = ImageDraw.Draw(img)
    draw.text((100,150), textString,font=font, fill='white')
    image = ImageTk.PhotoImage(img)
    DrawImageBox(image)



tool_bar = Frame(left_frame, width=180, height=185)
tool_bar.grid(row=2, column=0, padx=5, pady=5)

def ChooseVideo():
    ChooseVideo.VideoPath = ""
    file = fd.askopenfile()
    if file: 
        ChooseVideo.VideoPath = file.name
        ResizeVideo(ChooseVideo.VideoPath)
        PrintScreen("Video yolu:\n" + os.path.basename(ChooseVideo.VideoPath) + " seçildi")

def img_estim(img):
    thrshldsunnyMin= 60
    thrshldshortMax = 40
    thrshldshortMin = 20
    thrshldlongMax = 20
    thrshldlongMin = 0
    thrshlddayMax = 60
    thrshlddayMin = 40
    meanValue = np.mean(img)
    if   meanValue > thrshldsunnyMin :
        #return 'light' if is_light else 'dark'
        return 'nolight'
    if thrshldshortMax > meanValue > thrshldshortMin:
        return 'nightshort'
    if  thrshldlongMax > meanValue > thrshldlongMin:
        return 'nightshort'
    if  thrshlddayMax > meanValue > thrshlddayMin:
        return 'daylight'

def ProcessTravel(IsComActive):
    if hasattr(ChooseVideo, 'VideoPath'):
        cap = cv2.VideoCapture("temp/movie_temp_" + os.path.basename(ChooseVideo.VideoPath) +".mp4")
        fgbg = cv2.createBackgroundSubtractorMOG2(history=500, detectShadows=True) # filter model detec gery shadows for removing
        size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))) 
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        out = cv2.VideoWriter('temp/video.avi',fourcc ,20,size) #20 number of frames per second
        frameID = 0
        contours_info = []
        static_back = None
        time = []
        dayEstimationStringTemp = "Degerlendiriliyor"
        MotionAliasTemp = "Degerlendiriliyor"
        dayEstimationStringAlias = "Degerlendiriliyor"
        MotionAlias = "Degerlendiriliyor"
        actionBufferCycle= 60;
        dayEstimationCycle= 0;
        MotionAliasCycle= 0;
        areaOfVideoFrame = size[0]* size[1] 
        notification = FALSE
        # main loop:
        while True:
            ret, frame = cap.read()
            if ret:
                original_frame = frame.copy()
                motion_frame = frame.copy()
                carMotion = 0
                gray = cv2.cvtColor(motion_frame, cv2.COLOR_BGR2GRAY) 
                gray = cv2.GaussianBlur(gray, (21, 21), 0) 
                if static_back is None: 
                   static_back = gray 
                   continue
                diff_frame = cv2.absdiff(static_back, gray) 
                thresh_frame = cv2.threshold(diff_frame, 30, 255, cv2.THRESH_BINARY)[1] 
                thresh_frame = cv2.dilate(thresh_frame, None, iterations = 2) 
                cnts,_ = cv2.findContours(thresh_frame.copy(),  
                       cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 
                for contour in cnts: 
                    motionValue = cv2.contourArea(contour)
                    if  motionValue < 10000: 
                        carMotion = 0 
                    else:
                        carMotion = 1
                        break
                fgmask = fgbg.apply(frame)
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
                closing = cv2.morphologyEx(fgmask, cv2.MORPH_CLOSE, kernel)
                opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, kernel)
                dilation = cv2.dilate(opening, kernel, iterations = 2)
                dilation[dilation < 240] = 0
                dayEstimationString = img_estim(original_frame)
                contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                LightSourceDetectionCount = 0
                ListSourceSize = (0,0)
                for cID, contour in enumerate(contours):
                    M = cv2.moments(contour)
                    if M['m00'] < 400:
                        continue
                    c_centroid = int(M['m10']/M['m00']), int(M['m01']/M['m00'])
                    c_area = M['m00']
                    try:
                        c_perimeter = cv2.arcLength(contour, True)
                    except:
                        c_perimeter = cv2.arcLength(contour, False)
                    c_convexity = cv2.isContourConvex(contour)
                    (x, y, w, h) = cv2.boundingRect(contour)
                    br_centroid = (x + int(w/2), y + int(h/2)) 
                    LightSourceDetectionCount = LightSourceDetectionCount + 1
                    if x+w * y+h > ListSourceSize[0] * ListSourceSize[1]:
                        ListSourceSize = (x+w,y+h)
                    if dayEstimationString != "nolight":
                        cv2.rectangle(original_frame,(x,y),(x+w,y+h),(0,255,0),2)
                        cv2.putText(original_frame, str(cID), (x+w,y+h), cv2.FONT_HERSHEY_PLAIN, 3, (127, 255, 255), 1)
                    contours_info.append([cID,frameID,c_centroid,br_centroid,c_area,c_perimeter,c_convexity,w,h])
                cv2.moveWindow('fg', 40,30)
                cv2.imshow('fg',dilation)
                font = cv2.FONT_HERSHEY_SIMPLEX 
                textColor = color = (255, 255, 255)
                IsNodifyActive = False
                areaOfLightSource = ListSourceSize[0]*ListSourceSize[1]
                if dayEstimationString  == "nolight" or dayEstimationString  == "daylight" :
                    if areaOfLightSource > areaOfVideoFrame / 2 and dayEstimationStringTemp == "nightshort" :
                        notification = True
                        dayEstimationString = "nightshort"
                        IsNodifyActive = True
                    else:
                         notification = False


                if dayEstimationStringTemp == "nightshort" and dayEstimationString  == "nightshort" and LightSourceDetectionCount == 0:
                    dayEstimationString = "nightlong"

                if carMotion:
                    MotionAliasTemp = "haretli"       
                else:
                    dayEstimationStringAlias = dayEstimationStringAlias 
                    MotionAliasTemp = "arac duruyor"

                if MotionAliasTemp != MotionAlias:
                    MotionAliasCycle = MotionAliasCycle + 1
                    if MotionAliasCycle >= actionBufferCycle:
                        MotionAlias = MotionAliasTemp
                        MotionAliasCycle = 0

                if dayEstimationStringTemp != dayEstimationString:
                    dayEstimationCycle = dayEstimationCycle + 1
                    if dayEstimationCycle >= actionBufferCycle:
                        dayEstimationCycle = 0
                        if MotionAlias == "haretli":
                            if dayEstimationString == "nolight":
                                dayEstimationStringTemp = "nolight"
                                if IsComActive:
                                    CloseLights()
                                dayEstimationStringAlias = "isiklar kapali(Gunduz)"
                            if dayEstimationString == "nightlong":
                                dayEstimationStringTemp = "nightlong"
                                if IsComActive:
                                    LongLights()
                                dayEstimationStringAlias = "isiklar acik(cok karanlik)"
                            if dayEstimationString == "nightshort":
                                dayEstimationStringTemp = "nightshort"
                                if IsComActive:
                                    ShortLights()
                                dayEstimationStringAlias = "isiklar acik(sehir ici yada otoban)"
                            if dayEstimationString == "daylight":
                                dayEstimationStringTemp = "daylight"
                                if IsComActive:
                                    DayLights()
                                dayEstimationStringAlias = "isiklar acik(aksam vakti)"
                if IsNodifyActive:
                          if IsComActive:
                            LongLights()
                            ShortLights()
                          cv2.putText(original_frame, "uyari", (50, 150), 
                            font, 0.8, textColor, 2, cv2.LINE_AA) 
                cv2.putText(original_frame, dayEstimationStringAlias, (50, 50), 
                    font, 0.8, textColor, 2, cv2.LINE_AA)
                cv2.putText(original_frame, MotionAlias, (50, 100), 
                    font, 0.8, textColor, 2, cv2.LINE_AA) 
                cv2.moveWindow('origin', 680,30)
                cv2.imshow('origin',original_frame)
                LightSourceDetectionCount = 0
                ListSourceSize = (0,0)
                frameID += 1
                k = cv2.waitKey(30) & 0xff
                if k == 27:
                    cap.release()
                    cv2.destroyAllWindows()
                    break
            else:
                break
    else:   
       PrintScreen("Henüz Dosya Seçmediniz")

Comfields = ('COM port', 'Baudrate')

def makeform(root, fields):
    entries = {}
    for field in fields:
        print(field)
        row = tk.Frame(root)
        lab = tk.Label(row, width=22, text=field+": ", anchor='w')
        ent = tk.Entry(row)
        ent.insert(0, "0")
        row.pack(side=tk.TOP, 
                 fill=tk.X, 
                 padx=5, 
                 pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT, 
                 expand=tk.YES, 
                 fill=tk.X)
        entries[field] = ent
    return entries

Connected = False
Reading = False
MicrocontrollerSerial = serial.Serial()
def CheckMicrocontrollerCom():
    global Connected
    global MicrocontrollerSerial
    if not Connected:
        portName = "COM" + str(GetComValues.ComPortNumber)
        MicrocontrollerSerial = serial.Serial(portName, GetComValues.ComPortBaudRate)
        time.sleep(1) #give the connection a second to settle str.encode("Hello")
        Connected = True
        firstMessage = threading.Thread( target=StartListening, args= ( ))
        firstMessage.start()
 


def StartListening():
    global Reading
    if not Reading:
        global MicrocontrollerSerial
        Reading = True
        while True:
            data = MicrocontrollerSerial.read()
            if(data):
                print(data)

def VideoAdd():
    ChooseVideo()

def StartTravel():
    ProcessTravel(False)

def GetComValues(entries):
    GetComValues.ComPortNumber = int(entries['COM port'].get()) if check_int(entries['COM port'].get()) else 0 
    GetComValues.ComPortBaudRate =int(entries['Baudrate'].get()) if check_int(entries['Baudrate'].get()) else 0 


def SetupEmbeded():
    rootInput = tk.Tk()
    ents = makeform(rootInput, Comfields)
    b1 = tk.Button(rootInput, text='Değerleri Kaydet',
           command=(lambda e=ents: GetComValues(e)))
    b1.pack(side=tk.LEFT, padx=5, pady=5)
    #b2 = tk.Button(rootInput, text='Kapat', command=rootInput.quit)
    #b2.pack(side=tk.LEFT, padx=5, pady=5)
    rootInput.mainloop()

def StartWithEmbeded():
    CheckMicrocontrollerCom()
    ProcessTravel(True)

def LongLights():
    CheckMicrocontrollerCom()
    global MicrocontrollerSerial
    MicrocontrollerSerial.write('u'.encode())

def ShortLights():
    CheckMicrocontrollerCom()
    global MicrocontrollerSerial
    MicrocontrollerSerial.write('k'.encode())

def DayLights():
    CheckMicrocontrollerCom()
    global MicrocontrollerSerial
    MicrocontrollerSerial.write('g'.encode())

def CloseLights():
    CheckMicrocontrollerCom()
    global MicrocontrollerSerial
    MicrocontrollerSerial.write('y'.encode())

Button(tool_bar, text="Video Seçimi Yap",command=VideoAdd,bg='brown',fg='white').grid(row=1, column=0, padx=5, pady=5)
Button(tool_bar, text="Yola Çık",command=StartTravel,bg='brown',fg='white').grid(row=2, column=0, padx=5, pady=5)
Button(tool_bar, text="Gömülü Sistlem ayarla",command=SetupEmbeded,bg='brown',fg='white').grid(row=3, column=0, padx=5, pady=5)
Button(tool_bar, text="Gömülü ile Yola Çık",command=StartWithEmbeded,bg='brown',fg='white').grid(row=4, column=0, padx=5, pady=5)
Button(tool_bar, text="Uzun Farları Yak",command=LongLights,bg='brown',fg='white').grid(row=5, column=0, padx=5, pady=5)
Button(tool_bar, text="Kısa Farları Yak",command=ShortLights,bg='brown',fg='white').grid(row=6, column=0, padx=5, pady=5)
Button(tool_bar, text="Gündüz Farları Yak",command=DayLights,bg='brown',fg='white').grid(row=7, column=0, padx=5, pady=5)
Button(tool_bar, text="Tüm Farları Kapat",command=CloseLights,bg='brown',fg='white').grid(row=8, column=0, padx=5, pady=5)
root.mainloop()