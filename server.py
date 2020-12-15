#importing the required libraries
import dlib, cv2
import socket, zmq
import numpy as np
import face_recognition
import os

# We have imoprted cv2 for opening cam and showing images, zmq for communication to server, np for help in transformation,
# dlib for predictions of face and landmarks, face_recognition for recognising and locating faces in the image and os for file operations.


context = zmq.Context()
# Here we build the context for communication to server
socket = context.socket(zmq.REP)                                                      # From the context we create a socket through which other clients will be connected
socket.bind("tcp://127.0.0.1:9999")                                                   # Here are taking port 9999 and localhost ip

# This function sends the array from one end to another in the form of a buffer
def send_array(socket, A, flags=0, copy=True, track=False):
    md = dict(
        dtype=str(A.dtype),                                                           # Made a dictionary of dtype of array and shape of array so that at server side we know
        shape=A.shape,                                                                # at the time of transforming array from  buffer we must know the shape to get it back.
    )


    socket.send_json(md, flags | zmq.SNDMORE)                                        # Sent the image using json to the server
    return socket.send(A, flags, copy=copy, track=track)                             # Finally sending the image in form of buffer to the server.


# This function receives the array from one end to another in the form of a buffer
def recv_array(socket, flags=0, copy=True, track=False):
    md = socket.recv_json(flags=flags)                                               # Recieves the json file containing dtype and shape of the required array
    msg = socket.recv(flags=flags, copy=copy, track=track)                           # msg is the buffer recived which contains the array
    A = np.frombuffer(msg, dtype=md["dtype"])                                        # Using numpy and shape known  we transform the buffer into the array and reshape it to required shape and then finally return it.
    return A.reshape(md['shape'])


path = "C:\\Users\\Jojy\\devincept\\images1"                           #this is the path where the images of known people are stored

images = []                                                            #to store pixel values of images
classnames = []                                                        #to store names of the people in image list.
myList = os.listdir(path)                                              # list of images with name and extension (eg, abc.jpg) in the path

for cl in myList:
    curim=cv2.imread(f"{path}\\{cl}")                                  #reading the path for each image
    images.append(curim)                                               #adding pixel values of images into image list
    classnames.append(os.path.splitext(cl)[0])                         #adding names of people in the classnames list

#function to find image encodings. I have used image encodings of face_recognition library which returns 128 dimensional encodings. For more information,
#  https://face-recognition.readthedocs.io/en/latest/face_recognition.html can be visited.
def findEncoding(images):
    enclist=[]
    for img in images:
        img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode=face_recognition.face_encodings(img)[0]
        enclist.append(encode)
    return enclist

enclistKnown=findEncoding(images)                                        #image encodings are found

frame = recv_array(socket)                                              #the array from the socket is recieved with this function command. This is the image on which we have to label.

imgs = cv2.resize(frame, (0, 0), None, 1.5, 1.5)                        #The image is enlarged 1.5 times

facesCurrFrame=face_recognition.face_locations(imgs)                    #the faces in the image are located and their 4 parameter location(top left and bottom right) is stored.
encCurrFrame=face_recognition.face_encodings(imgs, facesCurrFrame)      #their face encodings are obtained.

for encFace, faceLoc in zip(encCurrFrame, facesCurrFrame):
    matches=face_recognition.compare_faces(enclistKnown,encFace)        #gives a boolean array with True or False depending on whether matching faces are found or not
    facedist=face_recognition.face_distance(enclistKnown,encFace)       #this command finds the Euclidian distance for each comaprison face.
    matchindex=np.argmin(facedist)                                      #the index of the minimum Euclidian distance is stored
    if matches[matchindex]:
        name=classnames[matchindex].upper()                                               #capitalizing the names
        print(name)
        y1, x2, y2, x1=faceLoc                                                            #gives location of the face in a rectangular area
        imgs=cv2.rectangle(imgs, (x1-5,y1-5),(x2+5,y2+5),(255,0,0),2)                     #rectangle of required size is drawn around face
        imgs=cv2.rectangle(imgs, (x1-5,y2-10),(x2+5,y2+5),(255,0,0),cv2.FILLED)           #thick border under the rectangle to write the name
        imgs=cv2.putText(imgs, name,(x1-2,y2),cv2.FONT_HERSHEY_COMPLEX,0.4,(0,0,255),2)   #displays name of the identified person at the given loaction and parameters where 0.4 is size, (0,0,0) is black colour and 2 is thickness(integer)

frame=imgs                                                              #storing the new labelled image in frame variable


send_array(socket, frame)                                               #returning the new image back to the client as a buffer if server is still running.
