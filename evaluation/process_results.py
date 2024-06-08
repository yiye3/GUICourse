import sys
sys.path.append('..')
import re

from utils import (
    attach_min_distance_element, 
    parse_box, 
    parse_point,
    parse_action_json, 
    parse_action_yaml, 
    parse_action_csv_string, 
    scale_point_format_by_rate_float,
    scale_point_format_by_rate,
    scale_box_format_by_rate, 
    generate_box_format,
    convert_list_to_dict
)


def parse_related_version1_box(box, image_size):
    x1, y1, x2, y2 = ["%.3f"%(x/1000) for x in parse_box(box, split_token=" ", keep_float=True)]
    w = image_size["width"]
    h = image_size["height"]
    return int(float(x1)*w), int(float(y1)*h), int(float(x2)*w), int(float(y2)*h)

def parse_related_version2_box(box, image_size):
    x1, y1, x2, y2 = ["%.3f"%(x) for x in parse_box(box, split_token=",", keep_float=True)]
    w = image_size["width"]
    h = image_size["height"]
    return int(float(x1)*w), int(float(y1)*h), int(float(x2)*w), int(float(y2)*h)

def process_guienv_results(pred_results, label_data):
    res = {}
    pred_dict = convert_list_to_dict(pred_results)

    for label in label_data:
      
        item = pred_dict[label["uid"]]
        image_size = label["image_size"]
        task_type = item["uid"].split("_")[-2]

        if task_type == "bbox2text":
            answer = item["pred"].split("\x04")[-1].strip()

        elif task_type == "text2bbox":
            answer = []
            matches = re.findall(r"<box>.*?</box>", item["pred"])
            for x in matches:
                try:
                    if item["position_format"] == "absolute":
                        x1, y1, x2, y2 = parse_box(x.strip())
                    elif item["position_format"] == "related_version1":
                        x1, y1, x2, y2 = parse_related_version1_box(x.strip(), image_size)
                    elif item["position_format"] == "related_version2":
                        x1, y1, x2, y2 = parse_related_version2_box(x.strip(), image_size)
                    pred = [x1, y1, max(0, x2-x1), max(0, y2-y1)]
                    answer.append(pred)
                except:
                    continue

        res[item["uid"]] = {
            "pred": item["pred"],
            "answer": answer
        }
    return res

def element_id_to_absolute_format(element_id, elements):
    for e in elements:
        if int(e["uid"]) == int(element_id):
            rect = e["rect"]
            break
    return generate_box_format(rect)

def convert_related_version1_to_stand_related(actions):
    for action in actions:
        # scale
        if "element" in action:
            position = ["%.3f"%(x/1000) for x in parse_box(action["element"], split_token=" ", keep_float=True)]
            action["element"] = "<box>{}</box>".format(", ".join(position))
        if "point" in action:
            position = ["%.3f"%(x/1000) for x in parse_point(action["point"], split_token=" ", keep_float=True)]
            action["point"] = "<point>{}</point>".format(", ".join(position))
        if "dual_point" in action:
            from_position = ["%.3f"%(x/1000) for x in parse_point(action["dual_point"]["from"], split_token=" ", keep_float=True)]
            to_position = ["%.3f"%(x/1000) for x in parse_point(action["dual_point"]["to"], split_token=" ", keep_float=True)]
            action["dual_point"] = {
                "from": "<point>{}</point>".format(", ".join(from_position)),
                "to": "<point>{}</point>".format(", ".join(to_position)),
            }
        if "scroll" in action:
            if "." in action["scroll"]["down"]:
                pass
            else:
                action["scroll"] = {
                    "down": "%.3f"%(int(action["scroll"]["down"])/1000),
                    "right": "%.3f"%(int(action["scroll"]["right"])/1000),
                }


def convert_stand_format_to_eval_format(actions, position_format, image_size, elements):
    image_w, image_h = image_size["width"], image_size["height"]

    for action in actions:    
        # -> absolute element
        if "element" in action:
            if position_format == "absolute":
                action["element_id"] = attach_min_distance_element(action["element"], elements)

            elif position_format == "related":
                action["element"] = scale_box_format_by_rate(action["element"], image_w, image_h, parse_keep_float=True)
                action["element_id"] = attach_min_distance_element(action["element"], elements)
    
            elif position_format == "element_id":
                action["element"] = element_id_to_absolute_format(action["element_id"], elements)
            
            else:
                print("unsupported position format")

        # -> related point
        if "point" in action:
            if position_format == "absolute":
                action["point"] = scale_point_format_by_rate_float(action["point"], 1/image_w , 1/image_h)
            
        # scroll (related ok, absolute ok)
        if "scroll" in action:
            if position_format == "related":
                action["scroll"] = {
                    "down": int(float(action["scroll"]["down"]) * image_h),
                    "right": int(float(action["scroll"]["right"]) * image_w)
                }
        # -> absolute dual point 
        if "dual_point" in action:
            if position_format == "related":
                action["dual_point"] = {
                    "from": scale_point_format_by_rate(action["dual_point"]["from"], image_w , image_h, parse_keep_float=True),
                    "to": scale_point_format_by_rate(action["dual_point"]["to"], image_w , image_h, parse_keep_float=True)
                }
                
def convert_pred_string_to_action_group(
    pred, 
    parse_format, 
    position_format,
    image_size, 
    elements, 
    ):
    """
    absolute: 
    related:
    related_version1
    related_version2
    """

    if "actions:" in pred:
        pred = pred.split("actions:")[-1].strip()
    elif "## Next Actions" in pred:
        pred = pred.split("## Next Actions")[-1].strip()

    if parse_format == "JSON":
        def process_string(pred):
            return parse_action_json(pred)
    elif parse_format == "YAML":
        def process_string(pred):
            return parse_action_yaml(pred)
    elif parse_format == "JSONL":
        def process_string(pred):
            return parse_action_json(pred)
    elif parse_format == "CSV_String" or parse_format == "CSV_string":
        def process_string(pred):
            return parse_action_csv_string(pred)
    else:
        print("unsupported string format")

    try:
        action_group = process_string(pred)
    except:
        print("parse error: ", pred)
        action_group = []

    if position_format == "related_version1":
        try:
            convert_related_version1_to_stand_related(action_group)
            position_format = "related"
        except:
            # breakpoint()
            print("convert related_version1 to stand_related error: ", action_group)
            return []

    convert_stand_format_to_eval_format(action_group, position_format, image_size, elements)

    # try:
    # except:
    #     breakpoint()
    #     print("convert stand_format to eval_format error: ", action_group)
    #     return []

    return action_group
    
def process_guiact_results(pred_results, label_data, cur_df):
    new_res = {}
    pred_dict = convert_list_to_dict(pred_results)

    for label in label_data:
      
        item = pred_dict[label["uid"]]
        image_size = label["image_size"]

        image_id = item["image_id"]
        elements = cur_df.loc[image_id]["elements"]

        if "\x04" in item['pred']:
            item['pred'] = item['pred'].split("\x04")[-1].strip()

        action_group = convert_pred_string_to_action_group(
            pred = item['pred'], 
            parse_format = item["parse_format"] if "parse_format" in item else item["string_format"], 
            position_format = item["position_format"],
            image_size = image_size, 
            elements = elements)
        
        new_res[item["uid"]] = {
            "pred": item["pred"],
            "answer": action_group
        }
    
    return new_res