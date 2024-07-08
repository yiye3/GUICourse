from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
torch.manual_seed(1234)
import argparse

from PIL import Image
import numpy as np 
import json
from tqdm import tqdm
import os
import json
import pandas as pd
from io import BytesIO
import base64
import glob

import re


def load_model_and_tokenizer(path, device):
    tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(path, device_map=device, trust_remote_code=True).eval()
    return model, tokenizer


def infer(model, tokenizer, image_path, text):
    query = tokenizer.from_list_format([
        {'image': image_path},
        {'text': text},
    ])
    response, history = model.chat(tokenizer, query=query, history=None)
    return response

def load_data(data_path, img_path):
    with open(data_path, "r", encoding='utf8') as f:
        data = json.loads(f.read())

    cur_df = pd.read_parquet(img_path, columns=None)
    return data, cur_df

def convert_to_qwen_format(question):
    for pos in re.findall(r"<box>(.*?)</box>", question):
        x1, y1, x2, y2 = pos.strip().split()
        question = question.replace(f"<box>{pos}</box>", f"<box>({x1},{y1}),({x2},{y2})</box>")
    return question

def infer_one_ckpt(
    data, 
    cur_df, 
    model,
    tokenizer, 
    res_path,
    device
    ):

    logs = []
    infer_error = 0

    for item in tqdm(data):
        question = item["prompt"]
        # question = convert_to_qwen_format(question)
        label = item["label"]
        image_id = item["image_id"]
        cur_image_str = cur_df.loc[image_id]["base64"]
        cur_image = Image.open(BytesIO(base64.urlsafe_b64decode(cur_image_str))).convert("RGB")
        # breakpoint()
        device_id = device.split(":")[-1]
        cur_image.save(f"./tmp_imgs/{device_id}.jpg")

        try: 
            pred = infer(model, tokenizer, f"./tmp_imgs/{device_id}.jpg", question)
        except:
            pred = "error"
            infer_error += 1
            continue

        logs.append({
            "uid": item["uid"],
            "image_id": item["image_id"],
            "prompt": item["prompt"],
            "pred": pred,
            "label": label,
            "task_name": "task2action",
            "parse_format": item["parse_format"],
            "position_format": item["position_format"]
        })

    with open(res_path, "w", encoding='utf8') as f:
        f.write(json.dumps(logs, ensure_ascii=False, indent=4))

if __name__ == "__main__":
    parser = argparse.ArgumentParser("")
    parser.add_argument("--model_path", default='')
    parser.add_argument("--data_path", default='./data/smartphone_test_instructions_related.json')
    parser.add_argument("--img_path", default="./data/smartphone__test_images.parquet")
    parser.add_argument("--output_path", default="False")
    parser.add_argument("--device", default='cuda:0')

    args = parser.parse_args()

    model, tokenizer = load_model_and_tokenizer(args.model_path, args.device)
    data, cur_df = load_data(
        data_path=args.data_path,
        img_path=args.img_path
    )

    infer_one_ckpt(
        data, 
        cur_df, 
        model,
        tokenizer, 
        args.output_path,
        args.device
    )