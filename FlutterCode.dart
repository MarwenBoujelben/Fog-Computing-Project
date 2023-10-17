import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

void main() {
  runApp(MaterialApp(
    home: MyApp(),
  ));
}

class MyApp extends StatefulWidget {
  @override
  _MyAppState createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  File? image;
  final picker = ImagePicker();
  Socket? socket;
  String acknowledgmentMessage = '';

  Future getImage(bool isCamera) async {
    final pickedFile = await picker.pickImage(
        source: isCamera ? ImageSource.camera : ImageSource.gallery);

    setState(() {
      if (pickedFile != null) {
        image = File(pickedFile.path);
      } else {
        print('No image selected.');
      }
    });
  }

  Future sendImageToServer() async {
    if (image == null) return;

    try {
      socket = await Socket.connect('192.168.1.18', 100);
      listenForMessages();
    } catch (e) {
      print(e.toString());
    }
    if (image == null) {
      print('No image selected');
      return;
    }

    final File imageFile = File(image!.path);
    final List<int> imageBytes = await imageFile.readAsBytes();

    socket?.add(utf8.encode('ImageStart'));
    socket?.add(imageBytes);
    socket?.add(utf8.encode('ImageEnd'));
  }

  void listenForMessages() {
    socket?.listen((List<int> event) {
      final message = String.fromCharCodes(event);
      setState(() {
        acknowledgmentMessage = message;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Image Picker Example'),
      ),
      body: Center(
        child: Column(
          children: <Widget>[
            image == null ? Text('No image selected.') : Image.file(image!),
            SizedBox(
                height: 20), // Add space between the image and acknowledgment
            Text(
              acknowledgmentMessage,
              style: TextStyle(fontSize: 18, color: Colors.green),
            ),
          ],
        ),
      ),
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: <Widget>[
          FloatingActionButton(
            onPressed: () => getImage(true),
            tooltip: 'Pick Image from camera',
            child: Icon(Icons.add_a_photo),
          ),
          SizedBox(
            height: 20,
          ),
          FloatingActionButton(
            onPressed: () => getImage(false),
            tooltip: 'Pick Image from gallery',
            child: Icon(Icons.photo_library),
          ),
          SizedBox(
            height: 20,
          ),
          FloatingActionButton(
            onPressed: sendImageToServer,
            tooltip: 'Predict Image',
            child: Icon(Icons.send),
          ),
        ],
      ),
    );
  }
}
