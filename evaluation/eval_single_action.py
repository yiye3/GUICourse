import sys
sys.path.append('..')

import math

import transformers.data.metrics.squad_metrics as squad_metrics

from utils import iou, parse_box, parse_point

# ocr
def eval_bbox2text(pred_text, label_text):
    """
    predict the text in one box
    """
   
    em = 1.0 if pred_text == label_text else 0.0
    f1 = squad_metrics.compute_f1(pred_text, label_text)
    return em, f1

# grounding
def eval_text2bbox(pred_boxes, label_boxes):
    """
    predict all the boxes including some text
    """
    if pred_boxes == None or len(pred_boxes) == 0:
        print("prediction is None")
        return 0.0

    score_mean = 0
    for single_pred in pred_boxes:
        score_max = 0.0
        for single_ans in label_boxes:
            score_max = max(score_max, iou(single_pred, single_ans))
        score_mean += score_max
        
    score_mean /= len(pred_boxes)

    return score_mean

def check_click_action(pred_action, label_action):
    """
    action = {
        "name": click / hover,
        "element": <box>x1, y1, x2, y2</box>
        "element_id": number
    }
    """
    is_finish_function = False
    score = 0.0

    def _process(element):
        x1, y1, x2, y2 = parse_box(element)
        return (x1, y1, max(0, x2-x1), max(0, y2-y1))

    if pred_action["name"] == label_action["name"]:
        if int(pred_action["element_id"]) == int(label_action["element_id"]):
            is_finish_function = True

        score = iou(_process(pred_action["element"]), _process(label_action["element"]))
    # breakpoint()

    return is_finish_function, score

def check_tap_action(pred_action, label_action):
    """
    action = {
        "name": tap,
        "point": <point>0.368, 0.856</point>
    }
    """
    is_finish_function = False
    score = 0.0
    _TAP_DISTANCE_THRESHOLD = 0.14

    def _process(point1, point2):
        x1, y1 = parse_point(point1, keep_float=True)
        x2, y2 = parse_point(point2, keep_float=True)
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    if pred_action["name"] == label_action["name"]:
        distance = _process(pred_action["point"], label_action["point"])

        if distance <= _TAP_DISTANCE_THRESHOLD:
            is_finish_function = True
            score = 1.0 - distance / _TAP_DISTANCE_THRESHOLD
    # breakpoint()
    return is_finish_function, score

def check_input_action(pred_action, label_action):
    """
    action = {
        "name": input,
        "element": <box>x1, y1, x2, y2</box>
        "element_id": number,
        "text": string
    }
    """
    is_finish_function = False
    score = 0.0

    if pred_action["name"] == label_action["name"]:
        score = squad_metrics.compute_f1(pred_action["text"], label_action["text"])

        if score > 0.5:
            is_finish_function = True
    
    return is_finish_function, score

def check_select_value_action(pred_action, label_action):
    """
    action = {
        "name": select,
        "element": <box>x1, y1, x2, y2</box>
        "element_id": number,
        "text": string
    }
    """
    is_finish_function = False
    score = 0.0

    def _process(element):
        x1, y1, x2, y2 = parse_box(element)
        return (x1, y1, max(0, x2-x1), max(0, y2-y1))

    if pred_action["name"] == label_action["name"]:
        score1 = squad_metrics.compute_f1(pred_action["text"], label_action["text"])

        score2 = iou(_process(pred_action["element"]), _process(label_action["element"]))

        if score1 > 0.5 and int(pred_action["element_id"]) == int(label_action["element_id"]):
            is_finish_function = True
        score = (score1 + score2) / 2
    
    return is_finish_function, score

def check_select_region_action(pred_action, label_action):
    """
    action = {
        "name": select,
        "dual_point": {
            "from": <point>284, 820</point>,
            "to": <point>284, 560</point>
        },
    }
    """
    is_finish_function = False
    score = 0.0

    def _process(dual_point):
        x1, y1 = parse_point(dual_point["from"])
        x2, y2 = parse_point(dual_point["to"])
        if x1 > x2:
            x1, y1, x2, y2 = x2, y2, x1, y1
        return (x1, y1, max(0, x2-x1), max(0, y2-y1))

    if pred_action["name"] == label_action["name"]:
        # breakpoint()
        score = iou(_process(pred_action["dual_point"]), _process(label_action["dual_point"]))

        if score > 0.5:
            is_finish_function = True
    
    return is_finish_function, score

def check_enter_action(pred_action, label_action):
    """
    action = {
        "name": enter,
    }
    """
    is_finish_function = False
    score = 0.0
        
    if pred_action["name"] == label_action["name"]:
        is_finish_function = True
        score = 1.0
    
    return is_finish_function, score

def check_scroll_action(pred_action, label_action):
    """
    action = {
        "name": scroll,
        "down": pixel,
        "right": pixel
    }
    """
    is_finish_function = False
    score = 0.0
    
    def _judge_direction(scroll_distance):
        down, right = float(scroll_distance["down"]), float(scroll_distance["right"])
        if abs(right) > abs(down):
            if right > 0:
                return "right"
            else:
                return "left"
        else:
            if down > 0:
                return "down"
            else:
                return "up"

    if pred_action["name"] == label_action["name"]:
        if _judge_direction(pred_action["scroll"]) == _judge_direction(label_action["scroll"]):
            is_finish_function = True
            score = 1.0
    
    return is_finish_function, score


def check_swipe_action(pred_action, label_action):
    """
    action = {
        "name": swipe,
        "dual_point": {
            "from": <point>284, 820</point>,
            "to": <point>284, 560</point>
        },
    }
    """
    is_finish_function = False
    score = 0.0

    def _judge_direction(dual_point):
        from_x1, from_y1 = parse_point(dual_point["from"], keep_float=True)
        to_x1, to_y1 = parse_point(dual_point["to"], keep_float=True)
        deltas_x = to_x1 - from_x1
        deltas_y = to_y1 - from_y1
        if abs(deltas_x) > abs(deltas_y):
            if deltas_x > 0:
                return "right"
            else:
                return "left"
        else:
            if deltas_y > 0:
                return "down"
            else:
                return "up"
        
    if pred_action["name"] == label_action["name"]:
        if _judge_direction(pred_action["dual_point"]) == _judge_direction(label_action["dual_point"]):
            is_finish_function = True
            score = 1.0
    
    return is_finish_function, score

def check_answer_action(pred_action, label_action):
    """
    action = {
        "name": answer,
        "text": string,
    }
    """
    is_finish_function = False
    score = 0.0

    if pred_action["name"] == label_action["name"]:
        score = squad_metrics.compute_f1(pred_action["text"], label_action["text"])
        if score > 0.5:
            is_finish_function = True

    return is_finish_function, score

def eval_action(pred_action, label_action):
    if label_action["name"] == "click" or label_action["name"] == "hover":
        is_finish_function, score = check_click_action(pred_action, label_action)

    elif label_action["name"] == "tap":
        is_finish_function, score = check_tap_action(pred_action, label_action)

    elif label_action["name"] == "input":
        is_finish_function, score = check_input_action(pred_action, label_action)

    elif label_action["name"] == "select":
        is_finish_function, score = check_select_value_action(pred_action, label_action)

    elif label_action["name"] == "select_text":
        is_finish_function, score = check_select_region_action(pred_action, label_action)

    elif label_action["name"] == "enter" or label_action["name"] == "copy" or label_action["name"] == "task_complete":
        is_finish_function, score = check_enter_action(pred_action, label_action)

    elif label_action["name"] == "scroll":
        is_finish_function, score = check_scroll_action(pred_action, label_action)
    
    elif label_action["name"] == "swipe":
        is_finish_function, score = check_swipe_action(pred_action, label_action)

    elif label_action["name"] == "answer":
        is_finish_function, score = check_answer_action(pred_action, label_action)

    else:
        print(label_action["name"])
        print("unsupported action label")
    return is_finish_function, score

def eval_action_group(pred_action_group, label_action_group):
    pred_act_list = [item["name"] for item in pred_action_group]
    label_act_list = [item["name"] for item in label_action_group]

    if str(pred_act_list) == str(label_act_list):
        name_em = 1.0
    else:
        name_em = 0.0
    
    is_finish_function, score = True, 0.0
    for i, item in enumerate(label_action_group):
        try:
            sub_function, sub_score = eval_action(pred_action_group[i], item)
            score += sub_score
            if not sub_function:
                is_finish_function = False
        except:
            score += 0.0
            is_finish_function = False

    score = score / len(label_act_list)

    return label_act_list, name_em, is_finish_function, score

