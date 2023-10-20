from flask_socketio import SocketIO, emit
import os
import socket
import concurrent.futures
import threading
import pickle
import datetime

UPLOADS_FOLDER = 'uploads/'  # Specify the folder where you want to store the images
# Create a dictionary to store locks for each image
image_locks = {}
image_list = []
node_availability = [True] * 2
imagesSent = {}
predictions = {}
imageConnection = {}
counter = 0
counter_lock = threading.Lock()  # Create a lock for counter access
node_availability_locks = threading.Lock()

def send_image_to_node(node_address, image_data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(node_address)
        s.sendall(b'ImageStart')  # Start the image transmission
        s.sendall(image_data)  # Send the image data
        s.sendall(b'ImageEnd')  # End the image transmission
        response = s.recv(1024)
        return pickle.loads(response)

def handle_connection(connection, address):
    print(f"Connected to {address}")
    image_data = b''
    receiving = False

    while True:
        data = connection.recv(1024)
        if not data:
            break
        if b'ImageStart' in data:
            receiving = True
            data = data.replace(b'ImageStart', b'')
        if b'ImageEnd' in data:
            receiving = False
            data = data.replace(b'ImageEnd', b'')
            image_data += data
            # Generate a unique filename for each image
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            global counter
            image_path = os.path.join(UPLOADS_FOLDER, f'received_image_{timestamp}_{counter}.jpg')
            with counter_lock:
                counter += 1
            with open(image_path, 'wb') as image_file:
                image_file.write(image_data)
            image_list.append(image_path)
            imageConnection[image_path] = connection
            # Clear the image data after saving the image
            image_data = b''
        if receiving:
            image_data += data

def run_app():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('192.168.43.63', 100))
        server_socket.listen()

        print(f"Server listening on {'192.168.43.63'}:{100}")

        while True:
            connection, address = server_socket.accept()
            threading.Thread(target=handle_connection, args=(connection, address)).start()

def process_images():
    num_nodes = 2
    node_addresses = [("192.168.43.171", 200), ("192.168.43.63", 300)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_nodes) as executor:
        futures = []
        print(image_list)
        while True:
            for j in range(num_nodes):
                if not image_list:
                    break
                with node_availability_locks:
                    if node_availability[j]:
                        image_path = image_list.pop(0)
                        imagesSent[image_path] = j
                # Create a new lock for this image
                        image_locks[image_path] = threading.Lock()
                        node_availability[j] = False

                        # Read the image data
                        with open(image_path, 'rb') as image_file:
                            image_data = image_file.read()

                        future = executor.submit(send_image_to_node, node_addresses[j], image_data)
                        futures.append((future, image_path))

            for future, image_path in futures:
                if future.done():
                    response = future.result()
                    node_index = imagesSent[image_path]
                    print(f"Objects detected by Node {node_index + 1}: {response}")
                    futures.remove((future, image_path))
                    node_availability[node_index] = True
                    predictions[image_path] = response
                    # Acquire the lock before deleting the image
                    with image_locks[image_path]:
                        if os.path.exists(image_path):
                            os.remove(image_path)
                    # Send acknowledgment
                    if image_path in imageConnection:
                        imageConnection[image_path].send(bytes('\n'.join(response), 'utf-8'))
                        del imageConnection[image_path]


if __name__ == "__main__":
    threading.Thread(target=run_app).start()
    process_images()
