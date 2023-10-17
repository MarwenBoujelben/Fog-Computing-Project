import socket
import pickle
from ultralytics import YOLO

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
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(node_address)
            s.listen()
            print("Listening on address: ",node_address[0]," PORT: ",node_address[1])

            conn, addr = s.accept()
            with conn:
                image_data = pickle.loads(conn.recv(1024))

            # Perform object detection
                detected_objects = object_detection(image_data)

            # Send detected objects back to the server
                conn.sendall(pickle.dumps(detected_objects))

if __name__ == "__main__":
    # Define the node's IP and port
    node_address = ("192.168.1.18", 300)  # Replace with actual node IP and port

    # Start the node
    node_function(node_address)
