import json
import yaml
import re

def read_json(path):
    with open(path, 'r', encoding='utf8') as f:
        data = json.loads(f.read())
    return data

def write_json(res, path):
    with open(path, 'w', encoding='utf8') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=4))


def is_pass_check(item):
    image_w, image_h = item["image_size"]["width"], item["image_size"]["height"]

    pred_bbox = re.findall(r"(<box>.*?</box>)", item["question"] + str(item["actions_label"]))
    for bbox in pred_bbox:
        x1, y1, x2, y2 = parse_box(bbox)
        if x1 > image_w or x2 > image_w or y1 > image_h or y2 > image_h:
            return False
        if x1 < 0 or x2 < 0 or y1 < 0 or y2 < 0:
            return False

    pred_point = re.findall(r"(<point>.*?</point>)", item["question"] + str(item["actions_label"]))
    for point in pred_point:
        x, y = parse_point(point)
        if x > image_w or y > image_h:
            return False
        if x < 0 or y < 0:
            return False
    
    return True
    
def parse_box(box_str, keep_float=False, split_token=","):
    """
    input: <box>x1, y1, x2, y2</box>
    output: (x1, y1, x2, y2)
    """
    x1, y1, x2, y2 = box_str.split("<box>")[-1].split("</box>")[0].strip().split(split_token)
    x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)
    if keep_float:
        return x1, y1, x2, y2
    else:
        return int(x1), int(y1), int(x2), int(y2)

def parse_point(point_str, keep_float=False, split_token=","):
    """
    input: <point>x, y</point>
    output: (x, y)
    """
    x, y = point_str.split("<point>")[-1].split("</point>")[0].strip().split(split_token)
    x, y = float(x), float(y)
    if keep_float:
        return x, y
    else:
        return int(x), int(y)

def convert_related_format_to_related_version1(actions):
    for action in actions:
        if "element" in action:
            position = [str(int(x*1000)) for x in parse_box(action["element"], keep_float=True)]
            action["element"] = "<box>{}</box>".format(" ".join(position))
        if "point" in action:
            position = [str(int(x*1000)) for x in parse_point(action["point"], keep_float=True)]
            action["point"] = "<point>{}</point>".format(" ".join(position))
        if "dual_point" in action:
            from_position = [str(int(x*1000)) for x in parse_point(action["dual_point"]["from"], keep_float=True)]
            to_position = [str(int(x*1000)) for x in parse_point(action["dual_point"]["to"], keep_float=True)]
            action["dual_point"] = {
                "from": "<point>{}</point>".format(" ".join(from_position)),
                "to": "<point>{}</point>".format(" ".join(to_position))
            }
        if "scroll" in action:
            action["scroll"] = {
                "down": str(int(float(action["scroll"]["down"])*1000)),
                "right": str(int(float(action["scroll"]["down"])*1000))
            }
    return actions

def convert_related_format_to_related_version2(actions):
    """
    You can convert to the data to your own format here.
    """
    return actions


def action_to_json(actions):
    action_str = json.dumps(actions, ensure_ascii=False, indent=4)
    return f"```json\n{action_str}\n```"

def action_to_jsonl(actions):
    return json.dumps(actions, ensure_ascii=False)

def action_to_yaml(actions):
    return yaml.dump(actions, sort_keys=False, allow_unicode=True)

def action_to_csv_string(actions):
    res = ""
    for action in actions:
        if "dual_point" in action:
            action["dual_point"] = "from {} to {}".format(action["dual_point"]["from"], action["dual_point"]["to"])
        if "scroll" in action:
            action["scroll"] = "down {} right {}".format(action["scroll"]["down"], action["scroll"]["right"])

        res += "{}\n".format(", ".join(list(action.values())))
    return res
    
def clear_actions(actions, position_format):
    if isinstance(actions, dict):
        actions = [actions]
    res = []
    for action in actions: 
        action["name"] = action["name"].lower()     
        if action["name"] == "click":
            action = {
                "name": "click",
                "element": action["element"][position_format],
            }
        elif action["name"] == "hover":
            action = {
                "name": "hover",
                "element": action["element"][position_format],
            }
        elif action["name"] == "input":
            action = {
                "name": "input",
                "text": action["text"]
            }
        elif action["name"] == "enter":
            action = {
                "name": "enter"
            }
        elif action["name"] == "scroll":
            action = {
                "name": "scroll",
                "scroll": action["scroll"][position_format],
            }
        elif action["name"] == "select_text":
            action = {
                "name": "select_text",
                "dual_point": action["dual_point"][position_format],
            }
        elif action["name"] == "copy_text" or action["name"] == "copy":
            action = {
                "name": "copy",
            }
        elif action["name"] == "answer":
            action = {
                "name": "answer",
                "text": action["text"]
            }
        elif action["name"] == "select":
            action = {
                "name": "select",
                "element": action["element"][position_format],
                "text": action["text"]
            }
        elif action["name"] == "tap":
            action = {
                "name": "tap",
                "point": action["point"][position_format],
            }
        elif action["name"] == "swipe":
            action = {
                "name": "swipe",
                "dual_point": action["dual_point"][position_format],
            }
        elif action["name"] == "go_back":
            action = {
                "name": "go_back"
            } 
        elif action["name"] == "go_home":
            action = {
                "name": "go_home"
            }
        elif action["name"] == "task_complete":
            action = {
                "name": "task_complete"
            } 
        elif action["name"] == "task_impossible":
            action = {
                "name": "task_impossible"
            }

        else:
            print(action["name"])
            print("unsupported action name")
            continue
        res.append(action)
    return res


def element_to_related_version1_format(element):
    position = [str(int(x*1000)) for x in parse_box(element, keep_float=True)]
    return "<box>{}</box>".format(" ".join(position))

def convert_guienv_data_to_instructions(
    dataset,
    position_format="related"):

    instructions = []
    for item in dataset:
        if position_format == "absolue":
            if item["task_type"] == "bbox2text":
                item["question"] = item["question"]["absolute"]
            elif item["task_type"] == "text2bbox":
                item["answer"] = [x for x in item["answer"]["absolute"]]

        elif position_format == "related": 
            if item["task_type"] == "bbox2text":
                item["question"] = item["question"]["related"]
            elif item["task_type"] == "text2bbox":
                item["answer"] = [x for x in item["answer"]["related"]]
            
        elif position_format == "related_version1": 
            if item["task_type"] == "bbox2text":
                item["question"] = element_to_related_version1_format(item["question"]["related"])
            elif item["task_type"] == "text2bbox":
                item["answer"] = [element_to_related_version1_format(x) for x in item["answer"]["related"]]


        prompt = "## Your Task\nIf the input is a string, please give me the element regions including this string. Else if the input is a region, please give me the string (text) in this region." 
        prompt += "## Input\n{}\n## Output\n".format(item["question"])

        if isinstance(item["answer"], list):
            label = "\n".join(item["answer"])
        else:
            label = item["answer"]

        instructions.append({
            "uid": item["uid"],
            "image_id": item["image_id"],
            "image_size": item["image_size"],
            "task_type": item["task_type"],
            "prompt": prompt,
            "label": label,
            "position_format": position_format
        })
    return instructions

def convert_guiact_data_to_instructions(
    dataset,
    dataset_name,
    use_history=True,
    use_logs=True,
    use_thoughts=True,
    parse_format="CSV_String", # json, jsonl, natural string, yaml
    position_format="related",
    ):

    instructions = []
    for item in dataset:
        # check the elements out of image region
        if not is_pass_check(item):
            print(item)
            continue

        prompt = ""

        if use_history and item["actions_history"] != "":
            prompt += "Actions History\n{}\n".format(item["actions_history"])

        if use_logs and item["logs"] != "":
            prompt += "Informations\n{}\n".format(item["logs"])

        prompt += "Your Task\n{}\n".format(item["question"])
        prompt += "Generate next actions to do this task."

        label = ""

        if use_thoughts and item["thoughts"] != "":
            label += "thoughts: {}\n".format(item["thoughts"])
        else:
            label += ""
        label += "actions:\n"

        try:
            if "related" in position_format:
                actions = clear_actions(item["actions_label"], "related")
            else:
                actions = clear_actions(item["actions_label"], "absolute")
        except:
            print(item["actions_label"])
            continue

        if position_format == "related_version1":
            actions = convert_related_format_to_related_version1(actions)
        if position_format == "related_version2":
            actions = convert_related_format_to_related_version2(actions)
        
        if parse_format == "JSON": 
            action_str = action_to_json(actions)
        elif parse_format == "JSONL": 
            action_str = action_to_jsonl(actions)
        elif parse_format == "YAML":
            action_str = action_to_yaml(actions)
        elif parse_format == "CSV_String":
            action_str = action_to_csv_string(actions)

        label += action_str

        instructions.append({
            "uid": item["uid"],
            "image_id": item["image_id"],
            "image_size": item["image_size"],
            "prompt": prompt,
            "label": label,
            "parse_format": parse_format,
            "position_format": position_format
        })
    return instructions


if __name__ == "__main__":
    # convert guienv data to QA instructions
    data_name = "ocr_grounding"
    for tag in ["train_stage1", "train_stage2", 'test']: # "train_stage1", "train_stage2", 'test'
        base_path = "./data/"
        path = f"{base_path}/{data_name}_{tag}_data.json"
        out_path = f"{base_path}/{data_name}_{tag}_sft_instructions.json"
        data = read_json(path)
        print(len(data))
        insturctions = convert_guienv_data_to_instructions(
            data, 
            position_format = "related_version1"
        )
        write_json(insturctions, out_path)


    # convert guiact data to QA instructions
    for data_name in ["smartphone", "web-single", "web-multi"]:
        for tag in ["train", "test"]:  # "train", "test" 
            base_path = "./data/"
            path = f"{base_path}/{data_name}_{tag}_data.json"
            out_path = f"{base_path}/{data_name}_{tag}_sft_instructions.json"
            data = read_json(path)
            print(len(data))
            insturctions = convert_guiact_data_to_instructions(
                data, 
                data_name, 
                parse_format = "CSV_String", 
                position_format = "related_version1"
            )
            write_json(insturctions, out_path)