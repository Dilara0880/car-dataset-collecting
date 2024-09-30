# Overview

This project focuses on parsing car images from https://platesmania.com/al/ and detecting car license plates using pre-trained YOLO model. 

## Data collecting
Car images are parsed and stored in a specific structure within a JSON file:

<img width="280" alt="Снимок экрана 2024-09-29 в 01 16 46" src="https://github.com/user-attachments/assets/04e9623e-6dde-4856-9a80-e033e16346cb">

JSON object:

<img width="672" alt="image" src="https://github.com/user-attachments/assets/956e9c15-d31f-4317-b049-d65b1ea42418">

Bbox format -- x y w h, **where x y -- coordinates of bbox's center**.

Parsing is headless and autamated, as Seleniumbase undetected Driver solves web-site's captchas.
```
  driver = Driver(uc=True, headless=True)
```

## Licence plate detecting
Approaches for plate detection:

**1. Retraining YOLO**
```
  + Highly accurate once trained, as YOLO is designed for object detection and can detect multiple objects simultaneously.
  + Real-time detection is possible due to its speed.
  + Can handle varying lighting conditions, angles, and perspectives after sufficient training.
  - Requires a significant amount of annotated data to retrain the model effectively.
  - Requires computational resources for training.
```

**2. Feature Matching in OpenCV**
  ```
  + Works well for finding specific patterns or shapes (matching a generated image of the plate with the original one).
  + Doesn't require training, making it quicker to implement and test.
  - Sensitive to scale (as on the picture below), rotation, and lighting differences, which may require additional preprocessing.
  - Slower than YOLO, especially when dealing with large images or multiple features.
  - Requires a good match between the template and the main image.
  ```
<img width="309" alt="image" src="https://github.com/user-attachments/assets/3647f1aa-1a40-4a81-ba6e-4c6374e65481">


**3. OCR (Optical Character Recognition)**
```
  + Doesn’t necessarily require training.
  - Not ideal for detecting the plate itself (i.e., the bounding box).
  - May fail when the license plate is at an angle, in poor lighting, or is partially obstructed.
  - Less effective in noisy backgrounds or low-resolution images.
```

**As collected data is appropriate and enough for YOLO training, and it is more efficient and accurate to detect car plates, I used trained model of yolov8n.pt.**

The model trained on a dataset of parsed 316 images (4 types + no labels) and announced in CVAT. 
The [notebook of train](https://github.com/Dilara0880/car-dataset-parsing/blob/main/model-train.ipynb) (with examples of using of YOLO model before and after train).

# Installation

To run this project, you'll need to set up your environment. 
1. Clone the repository:
  ```
  git clone https://github.com/Dilara0880/car-dataset-parsing.git
  cd car-dataset-parsing
  ```

2. Create and activate environment:
```
python3 -m venv .venv
source .venv/bin/activate
```
   
3. Install the required dependencies:
```
pip install -r requirements.txt
```
4. Run the main script:
```
python3 parse_car_dataset.py
```

# Usage 

Parsed data will stored in directory ".images/". 
In parsing.logging will logged all information about parsed id of cars and pages (link for image type -- page number):

<img width="707" alt="image" src="https://github.com/user-attachments/assets/8e5ed34f-aa52-4710-b2a1-eeefb5e6fa91">

***

# Examples

### 1. **Partial result in [sample output directory](https://github.com/Dilara0880/car-dataset-collecting/tree/main/sample)**

### 2. Web-site data:

<img width="578" alt="image" src="https://github.com/user-attachments/assets/54a95f68-6a40-441c-9ae9-7d9cae93f805">

Parsed data:
```
    "/al/nomer25971381": {
        "ads_link": "https://platesmania.com/al/nomer25971381",
        "link_text": "Toyota Yaris",
        "main_img": "https://img03.platesmania.com/240925/m/25971381.jpg",
        "generated_img": "https://img03.platesmania.com/240925/inf/25971381d1c62c.png",
        "place_meta": "1st gen 3-door Hatch (XP10), 1999–2005",
        "plate_number": "AA 811 BT",
        "bbox": "323 156 59 11"
    }
```
Image with plate's bbox:

<img width="487" alt="image" src="https://github.com/user-attachments/assets/ba547bb5-59c9-4b94-b4bb-41fbe9db284a">

***

### 3. Web-site data:
<img width="574" alt="image" src="https://github.com/user-attachments/assets/b9a2c827-9c00-466c-9ba6-bfdba8a071da">

Parsed data:
```
    "/al/nomer24970425": {
        "ads_link": "https://platesmania.com/al/nomer24970425",
        "link_text": "Aprilia SportCity",
        "main_img": "https://img03.platesmania.com/240612/m/24970425.jpg",
        "generated_img": "https://img03.platesmania.com/240612/inf/2497042588f252.png",
        "place_meta": [],
        "plate_number": "AG 455",
        "bbox": "143 211 34 48"
    }
```

Image with plate's bbox:

<img width="457" alt="image" src="https://github.com/user-attachments/assets/f035425a-8733-4eee-88d6-a71de83de497">






