import json
import pandas as pd
from io import BytesIO
import base64
from PIL import Image
import argparse

from data_visualization import (
    element_visual,
    elements_visual,
    actions_visual
)

def read_json(path):
    with open(path, 'r', encoding='utf8') as f:
        data = json.loads(f.read())
    return data

def read_parquet(path):
    return pd.read_parquet(path, columns=None)

def decode_base64_to_image(base64_string):
    return Image.open(BytesIO(base64.b64decode(base64_string))).convert("RGB")

def read_image_from_qarquet(cur_df, image_id, b64decode=True):
    cur_image_str = cur_df.loc[image_id]["base64"]
    if b64decode:
        return decode_base64_to_image(cur_image_str)
    else:
        return Image.open(BytesIO(cur_image_str)).convert("RGB")



if __name__ == "__main__":
    """
    - guienv
        - ocr_grounding_test_data.json
        - ocr_grounding_test_images.parquet
    - guiact
        - web-single_test_data.json
        - web-single_test_images.parquet
        - web-multi_test_data.json
        - web-multi_test_images.parquet
        - smartphone_test_data.json
        - smartphone_test_images.parquet
    - guichat
        - guichat_data.json
        - guichat_images.parquet   

    """
    parser = argparse.ArgumentParser("")
    parser.add_argument("--data_path", default="./data/guichat_data.json")
    parser.add_argument("--img_path", default="./data/guichat_images.parquet")
    parser.add_argument("--dataset", default="guichat")
    args = parser.parse_args()

    data = read_json(args.data_path)
    cur_df = read_parquet(args.img_path)

    if args.dataset == "guienv":
        for sample in data:
            image_id, question, answer = sample["image_id"], sample["question"], sample["answer"]
            image = read_image_from_qarquet(cur_df, image_id)

            if sample["task_type"] == "text2bbox":
                img_with_box = element_visual(answer, image.copy(), question)
            elif sample["task_type"] == "bbox2text":
                img_with_box = element_visual(question, image.copy(), answer)
            else:
                print("unsupported task type.")

            img_with_box.save("1.png")
            breakpoint()
            
    elif args.dataset == "guiact":
        for sample in data:
            image_id, question, actions = sample["image_id"], sample["question"], sample["actions_label"]
            image = read_image_from_qarquet(cur_df, image_id)

            img_with_actions = actions_visual(actions, image.copy(), question)
            img_with_actions.save("1.png")

            img_with_elements = elements_visual(cur_df.loc[image_id]["elements"], image.copy())
            img_with_elements.save("2.png")

            image.save("3.png")
            breakpoint()
    elif args.dataset == "guichat":
        for sample in data:
            image_id = sample["image_id"]
            image = read_image_from_qarquet(cur_df, image_id, b64decode=False)
            image.save("1.png")
            breakpoint()
    else:
        print("unsupported dataset.")