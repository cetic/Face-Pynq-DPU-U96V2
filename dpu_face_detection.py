from ctypes import *
from numpy import float32
from pynq_dpu import DpuOverlay
import sys
import numpy as np
import imutils
import time
import cv2
import screeninfo
import math


class FaceDetect():
  def __init__(self, dpu, detThreshold=0.55, nmsThreshold=0.35):
    self.dpu = dpu
    self.detThreshold = detThreshold
    self.nmsThreshold = nmsThreshold
    self.inputTensors = []
    self.outputTensors = []
    self.tensorFormat = []
    self.inputChannels = []
    self.inputHeight = []
    self.inputWidth = []
    self.inputShape = []
    self.output0Channels = []
    self.output0Height = []
    self.output0Width = []
    self.output0Size = []
    self.output0Shape = []
    self.output1Channels = []
    self.output1Height = []
    self.output1Width = []
    self.output1Size = []
    self.output1Shape = []

  def start(self):
    #"""Create Runner"""
    #dpu = runner.Runner("/usr/share/vitis_ai_library/models/densebox_640_360")[0]
    dpu = self.dpu

    inputTensors = dpu.get_input_tensors()
    print("[INFO] inputTensors=",inputTensors)
    outputTensors = dpu.get_output_tensors()
    print("[INFO] outputTensors=",outputTensors)
    tensorFormat = dpu.get_tensor_format()
    if tensorFormat == dpu.TensorFormat.NCHW:
        inputChannels = inputTensors[0].dims[1]
        inputHeight = inputTensors[0].dims[2]
        inputWidth = inputTensors[0].dims[3]
        print(*"[INFO] input tensor : format=NCHW, Channels=",inputChannels," Height=",inputHeight," Width=",inputWidth)
        output0Channels = outputTensors[0].dims[1]
        output0Height = outputTensors[0].dims[2]
        output0Width = outputTensors[0].dims[3]
        print("[INFO] output[0] tensor : format=NCHW, Channels=",output0Channels," Height=",output0Height," Width=",output0Width)
        output1Channels = outputTensors[1].dims[1]
        output1Height = outputTensors[1].dims[2]
        output1Width = outputTensors[1].dims[3]
        print("[INFO] output[1] tensor : format=NCHW, Channels=",output1Channels," Height=",output1Height," Width=",output1Width)
    elif tensorFormat == dpu.TensorFormat.NHWC:
        inputHeight = inputTensors[0].dims[1]
        inputWidth = inputTensors[0].dims[2]
        inputChannels = inputTensors[0].dims[3]
        print("[INFO] input tensor : format=NHWC, Height=",inputHeight," Width=",inputWidth,", Channels=", inputChannels)
        output0Height = outputTensors[0].dims[1]
        output0Width = outputTensors[0].dims[2]
        output0Channels = outputTensors[0].dims[3]
        print("[INFO] output[0] tensor : format=NHWC, height=",output0Height," width=",output0Width,", channels=",output0Channels)
        output1Height = outputTensors[1].dims[1]
        output1Width = outputTensors[1].dims[2]
        output1Channels = outputTensors[1].dims[3]
        print("[INFO] output[1] tensor : format=NHWC, height=",output1Height," width=",output1Width,", channels=",output1Channels)
    else:
        exit("[ERROR] DPU Runner Format Error")
    output0Size = output0Height*output0Width*output0Channels
    output1Size = output1Height*output1Width*output1Channels

    inputShape = (1,inputHeight,inputWidth,inputChannels)
    print("[INFO] inputShape=",inputShape)
    output0Shape = (1,output0Height,output0Width,output0Channels)
    print("[INFO] output0Shape=",output0Shape)
    output1Shape = (1,output1Height,output1Width,output1Channels)
    print("[INFO] output1Shape=",output1Shape)


    self.dpu = dpu
    self.inputTensors = inputTensors
    self.outputTensors = outputTensors
    self.tensorFormat = tensorFormat
    self.inputChannels = inputChannels
    self.inputHeight = inputHeight
    self.inputWidth = inputWidth
    self.inputShape = inputShape
    self.output0Channels = output0Channels
    self.output0Height = output0Height
    self.output0Width = output0Width
    self.output0Size = output0Size
    self.output0Shape = output0Shape
    self.output1Channels = output1Channels
    self.output1Height = output1Height
    self.output1Width = output1Width
    self.output1Size = output1Size
    self.output1Shape = output1Shape

  def nms_boxes(self,boxes, scores, nms_threshold):
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]
    areas = (x2-x1+1)*(y2-y1+1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w1 = np.maximum(0.0, xx2 - xx1 + 1)
        h1 = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w1 * h1
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        inds = np.where(ovr <= nms_threshold)[0]  # threshold
        order = order[inds + 1]
    return keep

  def softmax(self,data):
    data_exp = np.zeros(data.shape)
    data_sum = np.zeros(data.shape)
    result = np.zeros(data.shape)
    data_exp = np.exp(data)
    data_sum[:,0] = np.sum(data_exp, axis=1)
    data_sum[:,1] = data_sum[:,0]
    result = data_exp / data_sum
    return result

  def process(self,img):
    dpu = self.dpu
    inputChannels = self.inputChannels
    inputHeight = self.inputHeight
    inputWidth = self.inputWidth
    inputShape = self.inputShape
    output0Channels = self.output0Channels
    output0Height = self.output0Height
    output0Width = self.output0Width
    output0Size = self.output0Size
    output0Shape = self.output0Shape
    output1Channels = self.output1Channels
    output1Height = self.output1Height
    output1Width = self.output1Width
    output1Size = self.output1Size
    output1Shape = self.output1Shape
    imgHeight = img.shape[0]
    imgWidth  = img.shape[1]
    scale_h = imgHeight / inputHeight
    scale_w = imgWidth / inputWidth

    """ Image pre-processing """
    # normalize
    img = img - 128.0
    # resize
    img = cv2.resize(img,(inputWidth,inputHeight))

    """ Prepare input/output buffers """
    inputData = []
    inputData.append(np.empty((inputShape),dtype=np.float32,order='C'))
    inputImage = inputData[0]
    inputImage[0,...] = img
    #print("[INFO] input=",inputData)

    outputData = []
    outputData.append(np.empty((output0Shape),dtype=np.float32,order='C'))
    outputData.append(np.empty((output1Shape),dtype=np.float32,order='C'))
    #print("[INFO] out=",outputData)

    """ Execute model on DPU """
    job_id = dpu.execute_async( inputData, outputData )

    dpu.wait(job_id)

    """ Retrieve output results """
    OutputData0 = outputData[0].reshape(1,output0Size)
    bboxes = np.reshape( OutputData0, (-1, 4) )
    #
    outputData1 = outputData[1].reshape(1,output1Size)
    scores = np.reshape( outputData1, (-1, 2))

    """ Get original face boxes """
    gy = np.arange(0,output0Height)
    gx = np.arange(0,output0Width)
    [x,y] = np.meshgrid(gx,gy)
    x = x.ravel()*4
    y = y.ravel()*4
    bboxes[:,0] = bboxes[:,0] + x
    bboxes[:,1] = bboxes[:,1] + y
    bboxes[:,2] = bboxes[:,2] + x
    bboxes[:,3] = bboxes[:,3] + y

    """ Run softmax """
    softmax = self.softmax( scores )

    """ Only keep faces for which prob is above detection threshold """
    prob = softmax[:,1]
    keep_idx = prob.ravel() > self.detThreshold
    bboxes = bboxes[ keep_idx, : ]
    bboxes = np.array( bboxes, dtype=np.float32 )
    prob = prob[ keep_idx ]

    """ Perform Non-Maxima Suppression """
    face_indices = []
    if ( len(bboxes) > 0 ):
        face_indices = self.nms_boxes( bboxes, prob, self.nmsThreshold );

    faces = bboxes[face_indices]

    # extract bounding box for each face
    for i, face in enumerate(faces):
        xmin = max(face[0] * scale_w, 0 )
        ymin = max(face[1] * scale_h, 0 )
        xmax = min(face[2] * scale_w, imgWidth )
        ymax = min(face[3] * scale_h, imgHeight )
        faces[i] = ( int(xmin),int(ymin),int(xmax),int(ymax) )

    return faces

  def stop(self):
    #"""Destroy Runner"""
    #del self.dpu

    self.dpu = []
    self.inputTensors = []
    self.outputTensors = []
    self.tensorFormat = []
    self.input0Channels = []
    self.inputHeight = []
    self.inputWidth = []
    self.inputShape = []
    self.output0Channels = []
    self.output0Height = []
    self.output0Width = []
    self.output0Size = []
    self.output1Channels = []
    self.output1Height = []
    self.output1Width = []
    self.output1Size = []



if __name__ == "__main__":
    overlay = DpuOverlay("dpu.bit")
    print("[INFO] dpu overlay loaded")
    overlay.set_runtime("vart")
    overlay.load_model("dpu_densebox.elf")
    dpu = overlay.runner
    dpu_face_detector = FaceDetect(dpu,0.55,0.35)
    dpu_face_detector.start()
    print("[INFO] model densebox_640_360 loaded ")
    print("[INFO] starting camera input ...")
    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH,640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
    if not (cam.isOpened()):
        print("[ERROR] Failed to open camera ", inputId )
        exit()
    window_name = 'main'
    screen_id = 0
    screen = screeninfo.get_monitors()[screen_id]
    width, height = screen.width, screen.height
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.moveWindow(window_name, screen.x - 1, screen.y - 1)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    font = cv2.FONT_HERSHEY_SIMPLEX
    prev_frame_time = 0
    new_frame_time = 0
    print("[INFO] Begin dpu process")
    while True:
        new_frame_time = time.time()
        ret,frame = cam.read()
        faces = dpu_face_detector.process(frame)
        for i,(left,top,right,bottom) in enumerate(faces):
            cv2.rectangle( frame, (left,top), (right,bottom), (0,255,0), 2)
        fps = 1/(new_frame_time-prev_frame_time)
        prev_frame_time = new_frame_time
        fps = int(fps)
        cv2.putText(frame, "fps: "+str(fps), (7, 20), font, 0.5, (100, 255, 0), 1, cv2.LINE_AA)
        cv2.imshow(window_name, frame)
        cv2.waitKey(1)
    dpu_face_detector.stop()
    del dpu
    cv2.destroyAllWindows()
