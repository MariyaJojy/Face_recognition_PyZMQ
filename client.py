#importing the required libraries
import cv2
import zmq
import numpy as np
import face_recognition
import os
# We have imoprted cv2 for opening cam and showing images, zmq for communication to server, np for help in transformation,
# dlib for predictions of face and landmarks, face_recognition for recognising and locating faces in the image and os for file operations.

context= zmq.Context()                                            #Here we build the context for communication to server
socket = context.socket(zmq.REQ)                                  #From the context we create a request socket as we are client
socket.connect("tcp://127.0.0.1:9999")                            #Here we are taking port 9999 and localhost ip and as the server binds it we then can communicate

# This function sends the array from one end to another in the form of a buffer
def send_array(socket, A, flags=0, copy=True, track=False):
    md = dict(
        dtype = str(A.dtype),                                    # Makes a dictionary of dtype of array and shape of array so that at server side we know
        shape = A.shape,                                         # at the time of transforming array from  buffer we must know the shape to get it back.
    )

    socket.send_json(md, flags|zmq.SNDMORE)
    #Sent the image using json to the server
    return socket.send(A, flags, copy=copy, track=track)                # Finally sending the image in form of buffer to the server.


# This function receives images from one end to another in the form of a buffer
def recv_array(socket, flags=0, copy=True, track=False):
    md = socket.recv_json(flags=flags)                                  # Recieves the json file containing dtype and shape of the required array
    msg = socket.recv(flags=flags, copy=copy, track=track)              # msg is the buffer recived which contains the array
    A = np.frombuffer(msg, dtype=md["dtype"])                           # Using numpy and shape known  we transform the buffer into the array and reshape it to required shape and then finally return it.
    return A.reshape(md['shape'])

frame= cv2.imread('group3.jpg')                                         #reading the image to be labelled into the variable 'frame'
frame1= cv2.resize(frame, (0, 0), None, 1.5, 1.5)                       #resizing (enlarging 1.5 times) image for showing
cv2.imshow('Client side input', frame1)
send_array(socket,frame)                                                # Sent the frame to server for recognising faces and labelling them

frame = recv_array(socket)                                              #the frame with labelled names from server received

cv2.imshow('Client side output', frame)
cv2.waitKey(0)                                                          #show labelled image till 'Enter' button is pressed.
cv2.destroyAllWindows()                                                 #discarding all windows opened by the program


