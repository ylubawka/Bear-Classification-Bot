from imageai.Detection import ObjectDetection
from tf_keras.models import load_model
from PIL import Image, ImageOps 
import numpy as np
import os

def load_keras_model(model_path='./cv_models/keras_model.h5',labels_path='./cv_models/labels.txt'):
    np.set_printoptions(suppress=True)
    model = load_model(model_path, compile=False)
    with open(labels_path, "r", encoding='utf-8') as file:
        class_names = file.readlines()
    return model, class_names

def classify_image(image_path, model, class_names):
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

    image = Image.open(image_path).convert("RGB")
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image)

    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
    data[0] = normalized_image_array

    prediction = model.predict(data)
    index = np.argmax(prediction)
    class_name = class_names[index]
    confidence_score = prediction[0][index]

    return class_name.split()[1], round(confidence_score*100)

def detect_objects(image_path, model_path='./cv_models/yolov3.pt'):
    detector = ObjectDetection()
    detector.setModelTypeAsYOLOv3()
    detector.setModelPath(model_path)
    detector.loadModel()
    detections = detector.detectObjectsFromImage(input_image=image_path,
                                                output_image_path=image_path.split('.')[0] + '_result.jpg',
                                                minimum_percentage_probability=30)
    return detections

def handle_image(image_path):
    detections = detect_objects(image_path)

    model, class_names = load_keras_model()
    result = []
    for i, detection in enumerate(detections):
        try:
            
            if detection.get('name') == 'bear':
                # получаем координаты объекта
                box_points = detection.get('box_points')

                if box_points:
                    # открываем исходное изображение
                    original_image = Image.open(image_path)

                    # вырезаем область с объектом
                    x1, y1, x2, y2 = box_points
                    cropped_image = original_image.crop((x1, y1, x2, y2))

                    # временно сохраняем результат
                    object_path = f'./images/object_{i}.png'
                    cropped_image.save(object_path)

                    # классификация
                    class_name, confidence = classify_image(object_path, model, class_names)
                    result.append({'class': class_name, 'confidence': confidence})

                    if os.path.exists(object_path):
                        os.remove(object_path)

        except Exception as e:
            print(f'Ошибка при обработке объекта {i}: {e}')       

    return result