import os
import json
import pandas as pd
import argparse
from PIL import ImageDraw

import sys
sys.path.append('..')
from utils import parse_box

from process_results import (
    process_guienv_results,
    process_guiact_results
)
from eval_single_action import (
    eval_action_group,
    eval_bbox2text,
    eval_text2bbox,
)

from data_visualization import draw_rectangle, actions_visual
from data_load import read_image_from_qarquet

def visualize_text2bbox_error_sample(path, cur_image, pred_boxes, label_boxes):
    draw = ImageDraw.Draw(cur_image)
    for box in pred_boxes:
        box = (box[0], box[1], box[0]+box[2], box[1]+box[3])
        draw_rectangle(draw, box, outline_color="red")
    for box in label_boxes:
        box = parse_box(box)
        draw_rectangle(draw, box, outline_color="green")
    cur_image.save(path)

def visualize_task2action_error_sample(path, cur_image, prompt, pred_action_group, label_action_group):

    label_image = actions_visual(label_action_group, cur_image.copy(), prompt, color="green", from_eval=True)
    label_image.save(f"{path}_label.png")

    cur_image = actions_visual(pred_action_group, cur_image, prompt, color="red", from_eval=True)
    cur_image.save(f"{path}_pred.png")


def read_json(path):
    with open(path, 'r', encoding='utf8') as f:
        data = json.loads(f.read())
    return data

def read_parquet(path):
    return pd.read_parquet(path, columns=None)

def write_to_json(data, path):
    with open(path, "w", encoding='utf8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))

def eval_guienv_prediction_file(
    pred_data,
    label_data,
    cur_df, 
    output_path=None,
    log_error_samples=True,
    visualize_error_samples=True,
    ):

    em_bbox2text = 0.0
    score_bbox2text = 0.0 
    bbox2text_num = 0

    score_text2bbox_iou02 = 0.0
    score_text2bbox_iou05 = 0.0
    score_text2bbox_iou07 = 0.0
    score_text2bbox_iou09 = 0.0
    text2bbox_num = 0

    error_text = []
    error_bbox = []

    def _convert_absolute_box_to_xywh(boxes):
        res = []
        for box in boxes:
            x1, y1, x2, y2 = parse_box(box.strip())
            res.append([x1, y1, max(0, x2-x1), max(0, y2-y1)])
        return res

    for item in label_data:
        # preprocess 
        uid = item["uid"]
        image_id = item["image_id"]
        
        if item["task_type"] == "bbox2text":
            prompt = item["question"]["absolute"]
            label = item["answer"]
        else:
            prompt = item["question"]
            label = item["answer"]["absolute"]

        answer = pred_data[uid]["answer"]
        pred = pred_data[uid]["pred"]

        if log_error_samples:
            assert output_path is not None, "when choice log_error_samples=True, attention there is a output_path"
            
        if visualize_error_samples:
            assert output_path is not None, "when choice visualize_error_samples=True, attention there is a output_path"
            assert cur_df is not None, "when choice visualize_error_samples=True, attention there is a cur_df with base64-images"

        # make dir
        os.makedirs(f"{output_path}/bbox2text/", exist_ok=True)
        os.makedirs(f"{output_path}/text2bbox/", exist_ok=True)


         # different tasks
        if item["task_type"] == "bbox2text":
            em, score = eval_bbox2text(answer, label)
            em_bbox2text += em
            score_bbox2text += score 
            bbox2text_num += 1

            # error sample log and visualization
            if score < 0.5:
                if log_error_samples:
                    error_text.append({
                        "uid": uid,
                        "prompt": prompt,
                        "pred": pred,
                        "label": label
                    })
    
        elif item["task_type"] == "text2bbox":
            new_label = _convert_absolute_box_to_xywh(label)
            score = eval_text2bbox(answer, new_label)

            if score > 0.2:
                score_text2bbox_iou02 += 1.0
            if score > 0.5:
                score_text2bbox_iou05 += 1.0
            if score > 0.7:
                score_text2bbox_iou07 += 1.0
            if score > 0.9:
                score_text2bbox_iou09 += 1.0

            text2bbox_num += 1

            # error sample log and visualization
            if score < 0.7:
                if log_error_samples:
                    error_bbox.append({
                        "uid": uid,
                        "prompt": prompt,
                        "pred": pred,
                        "label": label
                    })
                if visualize_error_samples:
                    cur_image = read_image_from_qarquet(cur_df, image_id)
                    visualize_text2bbox_error_sample(f"{output_path}/text2bbox/{uid}.png", cur_image, answer, label)
                    breakpoint()

    if bbox2text_num != 0:
        score_bbox2text /= bbox2text_num
        em_bbox2text /= bbox2text_num
    if text2bbox_num != 0:
        score_text2bbox_iou02 /= text2bbox_num
        score_text2bbox_iou05 /= text2bbox_num
        score_text2bbox_iou07 /= text2bbox_num
        score_text2bbox_iou09 /= text2bbox_num
 
    ## print res
    logs = ""
    logs += f"em_bbox2text: {em_bbox2text}\n"
    logs += f"score_bbox2text: {score_bbox2text}\n"
    logs += f"bbox2text_num: {bbox2text_num}\n\n"
    logs += f"score_text2bbox_iou@0.2: {score_text2bbox_iou02}\n"
    logs += f"score_text2bbox_iou@0.5: {score_text2bbox_iou05}\n"
    logs += f"score_text2bbox_iou@0.7: {score_text2bbox_iou07}\n"
    logs += f"score_text2bbox_iou@0.9: {score_text2bbox_iou09}\n"
    logs += f"text2bbox_num: {text2bbox_num}\n\n"

    if output_path is not None:
        with open(f"{output_path}/results.log", "w", encoding='utf8') as f:
            f.write(logs)
    else:
        print(logs)

    if log_error_samples:
        write_to_json(error_text, f"{output_path}/bbox2text_error.json")
        write_to_json(error_bbox, f"{output_path}/text2bbox_error.json")


def eval_guiact_prediction_file(
    pred_data,
    label_data,
    cur_df, 
    output_path=None,
    log_error_samples=True,
    visualize_error_samples=True,
    ):

    score_action_em = 0.0 
    action_finish_function = 0.0
    action_score = 0.0

    action_num = 0
    score_action_split = {}
    finish_action_split = {}
    action_split_num = {}

    error_action = []

    def _convert_label_to_stand_label(actions):
        if isinstance(actions, dict):
            actions = [actions]
        res = []
        for action in actions:
            if "element" in action:
                action["element_id"] = action["element"]["id"]
                action["element"] = action["element"]["absolute"]
            if "point" in action:
                action["point"] = action["point"]["related"]
            if "dual_point" in action:
                action["dual_point"] = action["dual_point"]["absolute"]
            if "scroll" in action:
                action["scroll"] = action["scroll"]["absolute"]
            if "swipe" in action:
                action["swipe"] = action["swipe"]["absolute"]
            res.append(action)
        return res

    for item in label_data:
        # preprocess 
        uid = item["uid"]
        image_id = item["image_id"]
        question = item["question"]
        label = item["actions_label"]

        answer = pred_data[uid]["answer"]

        if log_error_samples:
            assert output_path is not None, "when choice log_error_samples=True, attention there is a output_path"
            
        if visualize_error_samples:
            assert output_path is not None, "when choice visualize_error_samples=True, attention there is a output_path"
            assert cur_df is not None, "when choice visualize_error_samples=True, attention there is a cur_df with base64-images"

        # make dir
        os.makedirs(f"{output_path}/task2action/", exist_ok=True)

        # testing
        stand_label = _convert_label_to_stand_label(label)
        try:
            act_list, action_em, is_finish_function, score = eval_action_group(answer, stand_label)
        except:
            print("parser answer error")
            print(answer)

        score_action_em += action_em
        action_finish_function += is_finish_function
        action_score += score

        action_num += 1
        if str(act_list) not in score_action_split:
            score_action_split[str(act_list)] = score
            finish_action_split[str(act_list)] = 1.0 if is_finish_function else 0
            action_split_num[str(act_list)] = 1
        else:
            score_action_split[str(act_list)] += score
            finish_action_split[str(act_list)] += 1.0 if is_finish_function else 0
            action_split_num[str(act_list)] += 1
        
        # error sample log and visualization
        if is_finish_function < 0.7:
            if log_error_samples:
                error_action.append({
                    "uid": uid,
                    "question": question,
                    "pred": answer,
                    "label": label
                })
            if visualize_error_samples:
                cur_image = read_image_from_qarquet(cur_df, image_id)
                visualize_task2action_error_sample(f"{output_path}/task2action/{uid}", cur_image, question, answer, stand_label)
                breakpoint()
                
    if action_num != 0:
        score_action_em /= action_num
        action_finish_function /= action_num
        action_score /= action_num
    for k in score_action_split:
        score_action_split[k] = "%.3f"%(score_action_split[k] / action_split_num[k])
        finish_action_split[k] = "%.3f"%(finish_action_split[k] / action_split_num[k])

    ## print res
    logs = ""
    logs += f"score_action_em: {score_action_em}\n"
    logs += f"action_finish_function: {action_finish_function}\n"
    logs += f"action_score: {action_score}\n"

    logs += f"finish_action_split: {finish_action_split}\n"
    logs += f"action_num: {action_num}\n"
    logs += str(score_action_split) + "\n"
    logs += str(action_split_num) + "\n"
    # breakpoint()
    if output_path is not None:
        with open(f"{output_path}/results.log", "w", encoding='utf8') as f:
            f.write(logs)
    else:
        print(logs)

    if log_error_samples:
        write_to_json(error_action, f"{output_path}/task2action_error.json")


def one_file_evaluation(file_name, task):
    if task == "guienv":
        label_data = read_json("../data/ocr_grounding_test_data.json")
        cur_df = read_parquet("../data/ocr_grounding_test_images.parquet")

    elif task == "guiact_web_single":
        label_data = read_json("../data/web-single_test_data.json")
        cur_df = read_parquet("../data/web-single_test_images.parquet")

    elif task == "guiact_web_multi":
        label_data = read_json("../data/web-multi_test_data.json")
        cur_df = read_parquet("../data/web-multi_test_images.parquet")
    
    elif task == "guiact_smartphone":
        label_data = read_json("../data/smartphone_test_data.json")
        cur_df = read_parquet("../data/smartphone_test_images.parquet")

    else:
        print("unsupported task.")

    pred_results = read_json(f"../results/{file_name}.json")

    if "guienv" in task:
        pred_data = process_guienv_results(pred_results, label_data)
        eval_guienv_prediction_file(
            pred_data,
            label_data,
            cur_df, 
            output_path=f"./logs/eval_{file_name}",
            log_error_samples=True,
            visualize_error_samples=False) 

    elif "guiact" in task:
        pred_data = process_guiact_results(pred_results, label_data, cur_df)
        eval_guiact_prediction_file(
            pred_data,
            label_data,
            cur_df, 
            output_path=f"./logs/eval_{file_name}",
            log_error_samples=True,
            visualize_error_samples=False)

def batch_evaluation():
    file_names = [
        "minicpm_guiagent_ocr_grounding",
        "minicpm_guiagent_web_single",
        "minicpm_guiagent_web_multi",
        "minicpm_guiagent_smartphone",
    ]
    
    tasks = [
        "guienv",
        "guiact_web_single",
        "guiact_web_multi",
        "guiact_smartphone"
    ]

    for file_name, task in zip(file_names, tasks):
        one_file_evaluation(file_name, task)


if __name__ == "__main__":
    """
    - eval_guienv 
        - ocr_grounding_test_data.json
        - ocr_grounding_test_images.parquet
    - eval_guiact_web_single
        - web-single_test_data.json
        - web-single_test_images.parquet
    - eval_guiact_web_multi
        - web-multi_test_data.json
        - web-multi_test_images.parquet
    - eval_guiact_smartphone
        - smartphone_test_data.json
        - smartphone_test_images.parquet
    """
    parser = argparse.ArgumentParser("")
    parser.add_argument("--file_name", default="minicpm_guiagent_web_multi")
    parser.add_argument("--task", default="guiact_web_multi")
    args = parser.parse_args()

    one_file_evaluation(args.file_name, args.task)
    # batch_evaluation()