import json
import yaml
import math

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

def iou(box1, box2):
    """
    计算两个边界框的IOU（Intersection over Union）
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    # 计算相交区域的坐标
    x_left = max(x1, x2)
    y_top = max(y1, y2)
    x_right = min(x1 + w1, x2 + w2)
    y_bottom = min(y1 + h1, y2 + h2)

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # 计算相交区域的面积
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # 计算并集区域的面积
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - intersection_area
    iou = intersection_area / union_area
    return iou

def distance_to_rectangle(point, rectangle):
    """计算点到矩形的距离"""
    x, y, width, height = rectangle
    px, py = point

    """判断点是否在矩形内部"""
    if x <= px <= x + width and y <= py <= y + height:
        return 0.0
    
    point_to_x_side = min(abs(x-px), abs(x+width-px))
    point_to_y_side = min(abs(y-py), abs(y+height-py))

    """判断点是否在矩形侧面"""
    if x <= px <= x + width:
        return point_to_y_side
    
    if y <= py <= y + height:
        return point_to_x_side

    """点距离矩形四角最近"""
    point_to_point = math.sqrt(point_to_x_side**2 + point_to_y_side**2)
    return point_to_point

def attach_min_distance_element(pred_element, elements):
    try:
        box = parse_box(pred_element)
    except:
        print("error pred_element", pred_element)
        return -1

    max_iou, min_dis = 0, 9999999
    max_iou_id, min_dis_id = -1, -1
    for e in elements:
        candidate_rectangle = (e["rect"]["x"], e["rect"]["y"], e["rect"]["width"], e["rect"]["height"])
        pred_center_point = ((box[0] + box[2])/2, (box[1] + box[3])/2)
        x_iou = iou((box[0], box[1], box[2]-box[0], box[3]-box[1]), candidate_rectangle)
        if x_iou > max_iou:
            max_iou = x_iou
            max_iou_id = e["uid"]
        x_dis = distance_to_rectangle(pred_center_point, candidate_rectangle)
        if x_dis < min_dis:
            min_dis = x_dis
            min_dis_id = e["uid"]
    
    if max_iou > 0.1:
        return max_iou_id
    else:
        return min_dis_id

def parse_action_json(action_str):
    """
    input: ```json\n{}\n```
    output: [dict, dict, ..., dict]
    """
    action_str = action_str.split("```json")[-1].split("```")[0].strip()
    actions = json.loads(action_str)
    if isinstance(actions, dict):
        actions = [actions]

    return actions

def parse_action_yaml(action_str):
    """
    input: yaml-format
    output: [dict, dict, ..., dict]
    """
    actions = yaml.safe_load(action_str)
    if isinstance(actions, dict):
        actions = [actions]
    return actions

def parse_action_csv_string(csv_string):
    actions_csv = csv_string.strip().split("\n")
    actions = []

    for line in actions_csv:
        if line.startswith("click,"):
            action = {
                "name": "click",
                "element": line.split("click,")[-1].strip(),
            }
        elif line.startswith("hover,"):
            action = {
                "name": "hover",
                "element": line.split("hover,")[-1].strip(),
            }
        elif line.startswith("input,"):
            action = {
                "name": "input",
                "text": line.split("input,")[-1].strip(),
            }
        elif line.startswith("enter"):
            action = {
                "name": "enter"
            }
        elif line.startswith("scroll,"):
            x, y = line.split("scroll,")[-1].strip().split("down")[-1].split("right")
            action = {
                "name": "scroll",
                "scroll": {
                    "down": x.strip(),
                    "right": y.strip()
                }
            }
        elif line.startswith("select_text,"):
            x, y = line.split("select_text,")[-1].strip().split("from")[-1].split("to")
            action = {
                "name": "select_text",
                "dual_point": {
                    "from": x.strip(),
                    "to": y.strip()
                }
            }
        elif line.startswith("copy"):
            action = {
                "name": "copy",
            }
        elif line.startswith("answer,"):
            action = {
                "name": "answer",
                "text": line.split("answer,")[-1].strip(),
            }
        elif line.startswith("select,"):
            x, y = line.split("select,")[-1].strip().split(",", 1)
            action = {
                "name": "select",
                "element": x.strip(),
                "text": y.strip()
            }
        elif line.startswith("tap,"):
            action = {
                "name": "tap",
                "point": line.split("tap,")[-1].strip(),
            }
        elif line.startswith("swipe,"):
            x, y = line.split("swipe,")[-1].strip().split("from")[-1].split("to")
            action = {
                "name": "swipe",
                "dual_point": {
                    "from": x.strip(),
                    "to": y.strip()
                }
            }
        else:
            action = {
                "name": "answer",
                "text": line.strip(),
            }
            # print(line)
            # print("unsupported action name")
            # continue
        actions.append(action)
    
    return actions

def scale_box_format_by_rate(box_format, scale_rate_w, scale_rate_h, parse_keep_float=False):
    x1, y1, x2, y2 = parse_box(box_format, parse_keep_float)
    x1, y1, x2, y2 = int(x1 * scale_rate_w), int(y1 * scale_rate_h), int(x2 * scale_rate_w), int(y2 * scale_rate_h)
    return f"<box>{x1}, {y1}, {x2}, {y2}</box>"

def scale_point_format_by_rate(point_format, scale_rate_w, scale_rate_h, parse_keep_float=False):
    x, y = parse_point(point_format, parse_keep_float)
    x, y = int(x * scale_rate_w), int(y * scale_rate_h)
    return f"<point>{x}, {y}</point>"

def scale_box_format_by_rate_float(box_format, scale_rate_w, scale_rate_h):
    x1, y1, x2, y2 = parse_box(box_format)
    x1, y1, x2, y2 = x1 * scale_rate_w, y1 * scale_rate_h, x2 * scale_rate_w, y2 * scale_rate_h
    return "<box>%.3f, %.3f, %.3f, %.3f</box>"%(x1, y1, x2, y2)

def scale_point_format_by_rate_float(point_format, scale_rate_w, scale_rate_h):
    x, y = parse_point(point_format)
    x, y = x * scale_rate_w, y * scale_rate_h
    return "<point>%.3f, %.3f</point>"%(x, y)

def generate_box_format(rect, view_port=None):
    """
    input: rect = {
        "top": y1,
        "left: x1,
        "bottom": y2,
        "right": x2
    }
    output: <box>x1, y1, x2, y2</box>
    """
    x1, y1, x2, y2 = int(rect["left"]), int(rect["top"]), int(rect["right"]), int(rect["bottom"])

    if x1 < 0:
        print("warning: box pixel x1 must > 0")
        x1 = 0
    if y1 < 0:
        print("warning: box pixel y1 must > 0")
        y1 = 0
    if x2 < 0:
        print("warning: box pixel x2 must > 0")
        x2 = 0
    if y2 < 0:
        print("warning: box pixel y2 must > 0")
        y2 = 0

    if view_port is not None:
        w, h = view_port["width"], view_port["height"]
        if x1 > w:
            print("warning: box pixel x1 must < image width")
            x1 = w
        if x2 > w:
            print("warning: box pixel x2 must < image width")
            x2 = w
        if y1 > h:
            print("warning: box pixel y1 must < image height")
            y1 = h
        if y2 > h:
            print("warning: box pixel y2 must < image height")
            y2 = h
    return f"<box>{x1}, {y1}, {x2}, {y2}</box>"

def convert_list_to_dict(results):
    new_res = {}
    for res in results:
        new_res[res['uid']] = res
    return new_res