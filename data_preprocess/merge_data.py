import json
import re

def read_json(path):
    with open(path, 'r', encoding='utf8') as f:
        data = json.loads(f.read())
    return data

def write_json(data, path):
    with open(path, 'w', encoding='utf8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))


def convert_guienv_to_qwen_format(data, image2path):
    new_data = []
    for item in data:
        conversations = []

        question = item["prompt"]
        answer = item["label"]

        path = image2path[item["image_id"]]
        question = f"<img>{path}</img>" + question

        for pos in re.findall(r"<box>(.*?)</box>", question):
            x1, y1, x2, y2 = pos.strip().split()
            question = question.replace(f"<box>{pos}</box>", f"<box>({x1},{y1}),({x2},{y2})</box>")

        for pos in re.findall(r"<box>(.*?)</box>", answer):
            x1, y1, x2, y2 = pos.strip().split()
            answer = answer.replace(f"<box>{pos}</box>", f"<box>({x1},{y1}),({x2},{y2})</box>")

        conversations = [
            {
                "from": "user",
                "value": question
            },
            {
                "from": "assistant",
                "value": answer
            }
        ]

        new_data.append({
            "id": item["uid"],
            "conversations": conversations
        })
    return new_data

def convert_guiact_to_qwen_format(data, data_type, image2path):
    new_data = []
    for item in data:
        image_id = item["image_id"]
        path = image2path[image_id]

        question = f"<img>{path}</img>\n" + item["prompt"]
        answer = item["label"]

        for pos in re.findall(r"<point>(.*?)</point>", answer):
            x1, y1 = pos.strip().split()
            answer = answer.replace(f"<point>{pos}</point>", f"<point>({x1},{y1})</point>")
            
        for pos in re.findall(r"<box>(.*?)</box>", answer):
            x1, y1, x2, y2 = pos.strip().split()
            answer = answer.replace(f"<box>{pos}</box>", f"<box>({x1},{y1}),({x2},{y2})</box>")

        conversations = [
            {
                "from": "user",
                "value": question
            },
            {
                "from": "assistant",
                "value": answer
            }
        ]

        new_data.append({
            "id": item["uid"],
            "type": data_type,
            "conversations": conversations
        })
    return new_data

def convert_guichat_to_qwen_format(data, image_id2path):
    new_data = []
    for item in data:
        conversations = []
        for content in item["text"]:
            if content["from"] == "human":
                res_from = "user"
            elif content["from"] == "gpt":
                res_from = "assistant"
            else:
                print(content["from"])
            
            res_value = content["value"]
            for x in re.findall(r"<image>(.*?)</image>", res_value):
                path = image_id2path[x]
                res_value = res_value.replace(f"<image>{x}</image>", f"<img>{path}</img>")

            for pos in re.findall(r"<box>(.*?)</box>", res_value):
                x1, y1, x2, y2 = pos.strip().split()
                res_value = res_value.replace(f"<box>{pos}</box>", f"<box>({x1},{y1}),({x2},{y2})</box>")

            conversations.append({
                "from": res_from,
                "value": res_value
            })

        new_data.append({
            "id": item["uid"],
            "conversations": conversations
        })
    return new_data

if __name__ == "__main__":
    all_instructions = []

    # guienv
    tag = "train_stage2" 
    ins_data = read_json(f"./data/ocr_grounding_{tag}_sft_instructions.json")
    image2path = read_json(f"./images/guienv/image_id2path.json")
    new_data = convert_guienv_to_qwen_format(ins_data, image2path)
    all_instructions.extend(new_data)

    # guiact
    tag = "train" 
    for data_name in ["smartphone", "web-single", "web-multi"]:
        ins_data = read_json(f"./data/{data_name}_{tag}_sft_instructions.json")
        image2path = read_json(f"./images/guiact/{data_name}/image_id2path.json")
        new_data = convert_guiact_to_qwen_format(ins_data, data_name, image2path)
        all_instructions.extend(new_data)

    # guichat
    ins_data = read_json(f"./data/guichat_data.json")
    image2path = read_json(f"./images/guiact/image_id2path.json")
    new_data = convert_guichat_to_qwen_format(ins_data, image2path)
    all_instructions.extend(new_data)

    print(len(all_instructions))
    import random
    random.seed(0)
    random.shuffle(all_instructions)
    write_json(all_instructions, "training_data_qwen.json")
    
