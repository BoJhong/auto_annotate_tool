import os
import shutil

import cv2

from src.core import TOMLConfig, YOLOv8
from src.utils.XmlWriter import write_xml, generate_xml

setting = TOMLConfig(os.path.join(__file__, "../config.toml"))
yolov8 = YOLOv8(setting.env["yolo"]["segment_model"])

directory = os.fsencode(setting.env["directory"])


def annotate(image, img_path, filename, video_frame=-1):
    results = yolov8(image)
    img_height, img_width = image.shape[:2]
    sorted = False
    count_name = f"_{video_frame}" if video_frame != -1 else ""

    for result in results:
        if not result.masks:
            continue


        for j, mask in enumerate(result.masks.data):
            sorted = True
            mask = mask.cpu().numpy() * 255
            mask = cv2.resize(mask, (img_width, img_height))

            if not os.path.exists(os.path.join(img_path, "../sorted")):
                os.mkdir(os.path.join(img_path, "../sorted"))

            cv2.imwrite(
                os.path.join(
                    os.fsdecode(directory),
                    "sorted",
                    os.path.splitext(filename)[0] + f"{count_name}.jpg",
                ),
                image,
            )

            cv2.imwrite(
                os.path.join(
                    os.fsdecode(directory),
                    "sorted",
                    os.path.splitext(filename)[0] + f"{count_name}_seg.jpg",
                ),
                mask,
            )

    if not sorted:
        if not os.path.exists(os.path.join(img_path, "../unsorted")):
            os.mkdir(os.path.join(img_path, "../unsorted"))

        cv2.imwrite(
            os.path.join(
                os.fsdecode(directory),
                "unsorted",
                os.path.splitext(filename)[0] + f"{count_name}.jpg",
            ),
            image,
        )


def is_image(file_name):
    for ext in setting.env["image_extensions"]:
        if file_name.lower().endswith(ext):
            return True


def is_video(file_name):
    for ext in setting.env["video_extensions"]:
        if file_name.lower().endswith(ext):
            return True


for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if is_image(filename):
        img_path = os.path.join(os.fsdecode(directory), filename)

        if not setting.env["xml_writer"]["overwrite"] and (
            os.path.exists(os.path.join(img_path, f"../sorted/{filename}"))
            or os.path.exists(os.path.join(img_path, f"../unsorted/{filename}"))
        ):
            continue

        print(img_path)
        img = cv2.imread(img_path)
        annotate(img, img_path, filename)

    elif is_video(filename):
        vid_path = os.path.join(os.fsdecode(directory), filename)

        if not setting.env["xml_writer"]["overwrite"] and (
            os.path.exists(os.path.join(vid_path, f"../sorted", filename))
            or os.path.exists(os.path.join(vid_path, f"../unsorted", filename))
        ):
            continue

        print(vid_path)
        count = 0
        if setting.env["video_skip_frame"] <= 0:
            setting.env["video_skip_frame"] = 1

        cap = cv2.VideoCapture(os.path.join(os.fsdecode(directory), filename))
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.release()
                break
            cap.set(cv2.CAP_PROP_POS_FRAMES, count)
            count += setting.env["video_skip_frame"]
            annotate(frame, vid_path, filename, count)
        cap.release()
