import pandas as pd 
from PIL import Image
from io import BytesIO
import base64
import os
import json
import glob

def write_json(data, path):
    with open(path, 'w', encoding='utf8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))

def read_data(paths):
    images = {}
    for path in paths:
        df = pd.read_parquet(path)
        for index, row in df.iterrows():
            images[index] = row["base64"]
    return images

def write_images(images, base_path):
    image2path = {}
    chunk_id = 0
    os.mkdir(f"{base_path}/chunk_{chunk_id}")

    i = 0
    for k, v in images.items():
        image = Image.open(BytesIO(base64.b64decode(v))).convert("RGB")
        image_path = f"{base_path}/chunk_{chunk_id}/{k}.png"
        image.save(image_path)
        image2path[k] = image_path

        i +=1 
        if i >= 999:
            i = 0
            chunk_id += 1
            os.mkdir(f"{base_path}/chunk_{chunk_id}")
            print("new chunk")

    write_json(image2path, f"{base_path}/image_id2path.json")


def write_images_version1(images, base_path):
    image2path = {}
    for k, v in images.items():
        image = Image.open(BytesIO(base64.b64decode(v))).convert("RGB")
        
        _, _, record, _, step = k.split("_")
        record_path = f"{base_path}/record_{record}"
        if not os.path.exists(record_path):
            os.mkdir(record_path)

        path = f"{record_path}/step_{step}.png"
        image.save(path)
        image2path[k] = path
    
    write_json(image2path, f"{base_path}/image_id2path.json")

def write_images_version2(images, base_path):
    image2path = {}
    for k, v in images.items():
        image = Image.open(BytesIO(v)).convert("RGB")
        image_path = f"{base_path}/chunk_{chunk_id}/{k}.png"
        image.save(image_path)
        image2path[k] = image_path

        i +=1 
        if i >= 999:
            i = 0
            chunk_id += 1
            os.mkdir(f"{base_path}/chunk_{chunk_id}")
            print("new chunk")

    write_json(image2path, f"{base_path}/image_id2path.json")


def process_ocr_grounding():
    out_path = "./images/guienv"
    images = read_data([
        "./data/ocr_grounding_test_images.parquet",
        "./data/ocr_grounding_train_stage1_images.parquet",
        "./data/ocr_grounding_train_stage2_images.parquet"
    ])
    print(len(list(images.keys())))
    os.mkdir(out_path)
    write_images(images, out_path)

def process_guiact_web_single():
    out_path = "./images/guiact/web-single"
    images = read_data([
        "./data/web-single_test_images.parquet"
        "./data/web-single_train_images.parquet",
    ])
    os.makedirs(out_path)
    print(len(list(images.keys())))
    write_images(images, out_path)

def process_guiact_web_multi():
    out_path = "./images/guiact/web-multi"
    images = read_data([
        "./data/web-multi_test_images.parquet"
        "./data/web-multi_train_images.parquet",
    ])
    os.makedirs(out_path)
    print(len(list(images.keys())))
    write_images_version1(images, out_path)

def process_guiact_smartphone():
    out_path = "./images/guiact/smartphone"
    images = read_data([
        "./data/smartphone_test_images.parquet"
        "./data/smartphone_train_images.parquet",
    ])
    os.makedirs(out_path)
    print(len(list(images.keys())))
    write_images_version1(images, out_path)

def process_guichat():
    out_path = "./images/guichat"
    images = read_data([
        "./data/guichat_images.parquet"
    ])
    os.makedirs(out_path)
    print(len(list(images.keys())))
    write_images_version2(images, out_path)


if __name__ == "__main__":
    process_ocr_grounding()
    process_guiact_web_single()
    process_guiact_web_multi()
    process_guiact_smartphone()
    process_guichat()
