import socket
import pickle
from ultralytics import YOLO
from PIL import Image
from io import BytesIO
# Function to perform object detection using YOLOv8
def object_detection(image_data):
    model = YOLO("yolov8m.pt")
    results = model.predict(image_data)
    result = results[0]

    detected_objects = []
    for obj in result.boxes:
        class_id = obj.cls[0].item()
        detected_objects.append(result.names[class_id])
    return detected_objects

# Function to perform image classification on a node
def node_function(node_address):
    # Create a socket to listen for image data from the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(node_address)
        s.listen()
        print("Listening on address:", node_address[0], "PORT:", node_address[1])
        
        while True:
            conn, addr = s.accept()
            with conn:
                image_data = b''
                receiving = False
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    if b'ImageStart' in data:
                        receiving = True
                        data = data.replace(b'ImageStart', b'')
                    if b'ImageEnd' in data:
                        receiving = False
                        data = data.replace(b'ImageEnd', b'')
                        image_data += data
                        
                        # Convert received image data to a PIL Image object
                        image = Image.open(BytesIO(image_data))
                        
                        # Perform object detection
                        detected_objects = object_detection(image)
                        
                        # Send detected objects back to the server
                        conn.sendall(pickle.dumps(detected_objects))
                        break
                    if receiving:
                        image_data += data

if __name__ == "__main__":
    # Define the node's IP and port
    node_address = ("192.168.43.63", 300)  # Replace with actual node IP and port
    
    # Start the node
    node_function(node_address)
