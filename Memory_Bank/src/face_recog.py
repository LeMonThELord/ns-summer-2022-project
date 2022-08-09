# pip install opencv_contrib_python
import speech
import database_operations as do
import numpy as np
import pickle
from util import *
import cv2
import time
import sys
import os

face_detection_model = "../resources/models/face_detection_yunet_2022mar.onnx"
face_recognition_model = "../resources/models/face_recognition_sface_2021dec.onnx"
score_threshold = 0.9
nms_threshold = 0.3
top_k = 5000

face_font = cv2.FONT_HERSHEY_SIMPLEX
thickness = 2
line_type = cv2.FILLED

## [initialize_FaceDetectorYN]
detector = cv2.FaceDetectorYN.create(
    face_detection_model,
    "",
    (640, 640),
    score_threshold,
    nms_threshold,
    top_k,
)
## [initialize_FaceDetectorYN]

## [initialize_FaceRecognizerSF]
recognizer = cv2.FaceRecognizerSF.create(face_recognition_model, "")
## [initialize_FaceRecognizerSF]


def same_identity(feature1, feature2):
    cosine_score = recognizer.match(
        feature1, feature2, cv2.FaceRecognizerSF_FR_COSINE
    )
    l2_score = recognizer.match(
        feature1, feature2, cv2.FaceRecognizerSF_FR_NORM_L2
    )
    return (cosine_score >= 0.363) or (l2_score <= 1.128)


def display_info(conn, frame, face, face_id):
    profile = do.get_profile(conn, face_id)
    coords = face[:-1].astype(np.int32)
    offset_count = 0
    for key in profile:
        cv2.putText(
            frame,
            f'{key}: {profile[key]}',
            (coords[0] + coords[2] + 30, coords[1] + 30 * offset_count),
            face_font,
            0.75,
            (0, 255, 0),
            thickness,
            line_type,
            False,
        )
        offset_count += 1

def display_conversation(conn, frame, face, face_id):
    profile = do.get_conversations(conn, face_id)
    coords = face[:-1].astype(np.int32)
    offset_count = 0
    for id, time, keywords in profile:
        cv2.putText(
            frame,
            f'context_id: {id}',
            (coords[0] - 200, coords[1] + 30 * offset_count),
            face_font,
            0.5,
            (0, 255, 0),
            thickness,
            line_type,
            False,
        )
        offset_count += 1
        cv2.putText(
            frame,
            f'time: {time}',
            (coords[0] - 200, coords[1] + 30 * offset_count),
            face_font,
            0.5,
            (0, 255, 0),
            thickness,
            line_type,
            False,
        )
        offset_count += 1
        cv2.putText(
            frame,
            f'keywords: {keywords}',
            (coords[0] - 200, coords[1] + 30 * offset_count),
            face_font,
            0.5,
            (0, 255, 0),
            thickness,
            line_type,
            False,
        )
        offset_count += 1


def get_face():

    cap = cv2.VideoCapture(0)
    frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    detector.setInputSize([frameWidth, frameHeight])

    while True:
        hasFrame, frame = cap.read()
        if not hasFrame:
            print('No frames grabbed!')
            break

        frame = cv2.resize(frame, (frameWidth, frameHeight))

        faces = detector.detect(frame)  # faces is a tuple

        key = cv2.waitKey(1) & 0xFF

        # Draw results on the input image
        if faces[1] is not None:
            for idx, face in enumerate(faces[1]):
                coords = face[:-1].astype(np.int32)
                cv2.rectangle(
                    frame,
                    (coords[0], coords[1]),
                    (coords[0] + coords[2], coords[1] + coords[3]),
                    (0, 255, 0),
                    thickness,
                )
                cv2.putText(
                    frame,
                    f'ID: {idx}',
                    (coords[0], coords[1] + coords[3] + 30),
                    face_font,
                    1.0,
                    (0, 255, 0),
                    thickness,
                    line_type,
                    False,
                )
            cv2.putText(
                frame,
                'Press F to capture faces',
                (1, 30),
                face_font,
                1.0,
                (0, 255, 0),
                thickness,
                line_type,
                False,
            )
            cv2.putText(
                frame,
                'Press Q to quit',
                (1, 60),
                face_font,
                1.0,
                (0, 255, 0),
                thickness,
                line_type,
                False,
            )
            cv2.imshow('Live', frame)
            if key == ord('f'):
                feature_ids = []
                for idx, face in enumerate(faces[1]):
                    face_align = recognizer.alignCrop(frame, face)
                    face_feature = recognizer.feature(face_align)
                    face_id = f"{time.time():5.5f}"
                    print(f"Captured: {face_id}")

                    np.save(f"../resources/features/{face_id}", face_feature)
                    cv2.imwrite(f"../resources/features/{face_id}.jpg", face_align)

                    feature_ids.append(face_id)
                print(f"Captured {len(faces[1])} Faces")

                cv2.destroyAllWindows()
                return feature_ids
        cv2.imshow('Live', frame)
        if key == ord('q'):
            break

    cv2.destroyAllWindows()


def run(conn):

    path = "../resources/features/"
    feature_infos = set()
    for file in os.listdir(path):
        if ".jpg" in file:
            continue
        face_id = file.strip(".npy")
        file_path = os.path.join(path, file)
        feature_info = (face_id, file_path)
        feature_infos.add(feature_info)
    log(f"feature_infos: {feature_infos}")
    features = []
    for face_id, file_path in feature_infos:
        feature = np.load(file_path, allow_pickle=True)
        features.append((face_id, feature))

    cap = cv2.VideoCapture(0)
    frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    detector.setInputSize([frameWidth, frameHeight])

    profile_toggle = False
    conversation_toggle = False
    recording = False

    while True:
        hasFrame, frame = cap.read()
        if not hasFrame:
            print('No frames grabbed!')
            break

        frame = cv2.resize(frame, (frameWidth, frameHeight))

        faces = detector.detect(frame)  # faces is a tuple

        key = cv2.waitKey(1) & 0xFF

        # Draw results on the input image
        thickness = 2
        if faces[1] is not None:
            for idx, face in enumerate(faces[1]):
                coords = face[:-1].astype(np.int32)
                cv2.rectangle(
                    frame,
                    (coords[0], coords[1]),
                    (coords[0] + coords[2], coords[1] + coords[3]),
                    (0, 255, 0),
                    thickness,
                )
                face_align = recognizer.alignCrop(frame, face)
                face_feature = recognizer.feature(face_align)

                for face_id, feature in features:
                    if same_identity(face_feature, feature):
                        # Display info
                        if profile_toggle:
                            display_info(conn, frame, face, face_id)

                        # Display conversation
                        if conversation_toggle:
                            display_conversation(conn, frame, face, face_id)

                        # Update feature
                        features.remove((face_id, feature))
                        features.insert(0, (face_id, feature))

                cv2.putText(
                    frame,
                    f'INDEX: {idx}',
                    (coords[0], coords[1] + coords[3] + 16),
                    face_font,
                    0.5,
                    (0, 255, 0),
                    thickness,
                    line_type,
                    False,
                )
            cv2.imshow('Live', frame)
            if key == ord('r') and not recording:
                print("Voice record started")
                recording = True
                speech.my_record()
                result = speech.speech2text(speech.get_audio("temp.wav"), speech.getBuiltInToken(), 1737)
                log(f"msg: {result}")
                log("keywords:")
                log(speech.keywordextraction(result))
                log("Faces:")
                log(faces[1])
                print("Voice recorded")
                recording = False
                # TODO
            pass
            if key == ord('p'):
                profile_toggle = not profile_toggle
                pass
            if key == ord('c'):
                conversation_toggle = not conversation_toggle
                pass
        cv2.imshow('Live', frame)
        if key == ord('q'):
            break

    cv2.destroyAllWindows()
