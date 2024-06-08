from PIL import Image, ImageDraw, ImageFont
import math

from utils import parse_point, parse_box


def draw_rectangle(draw, box_coords, width=2, outline_color=(0, 255, 0), is_fill=False, bg_color=(0, 255, 0), transparency=50):  
    if is_fill:
        # Calculate the alpha value based on the transparency percentage
        alpha = int((1 - transparency / 100) * 255)

        # Set the fill color with the specified background color and transparency
        fill_color = tuple(bg_color) + (alpha,)

        draw.rectangle(box_coords, width=width, outline=outline_color, fill=fill_color)
    else:
        draw.rectangle(box_coords, width=width, outline=outline_color)

def draw_circle(draw, center, radius=10, width=2, outline_color=(0, 255, 0), is_fill=False, bg_color=(0, 255, 0), transparency=80):
    # Calculate the bounding box coordinates for the circle
    x1 = center[0] - radius
    y1 = center[1] - radius
    x2 = center[0] + radius
    y2 = center[1] + radius
    bbox = (x1, y1, x2, y2)

    # Draw the circle
    if is_fill:
        # Calculate the alpha value based on the transparency percentage
        alpha = int((1 - transparency / 100) * 255)

        # Set the fill color with the specified background color and transparency
        fill_color = tuple(bg_color) + (alpha,)

        draw.ellipse(bbox, width=width, outline=outline_color, fill=fill_color)
    else:
        draw.ellipse(bbox, width=width, outline=outline_color)

def draw_text_with_bg_box(draw, text, view_port, position, 
                          font_size=24, font_color=(0, 0, 0), 
                          bg_padding=10, bg_color=(179, 238, 58)):

    # Define the font and size for the text
    try:
        font = ImageFont.truetype("./NotoSerifSC-SemiBold.otf", font_size)
    except:
        font = ImageFont.truetype("../NotoSerifSC-SemiBold.otf", font_size)

    # Calculate the bounding box of the text
    text_bbox = draw.textbbox((0, 0), text, font=font)

    # Extract the width and height from the bounding box
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]


    # Define the position of the text based on the specified position parameter
    image_width, image_height = view_port
    if position == "top-left":
        text_x = 5
        text_y = 5
    elif position == "bottom-middle":
        text_x = (image_width - text_width) // 2
        text_y = image_height - text_height - 5
    elif position == "top-middle":
        text_x = (image_width - text_width) // 2
        text_y = 5
    elif position.startswith("point"):
        text_x, text_y = position.split("-")[1:]
        text_x, text_y = int(text_x), int(text_y)
    else:
        print("unsupported position")

    # Draw the background box
    draw_rectangle(
        draw,
        [(text_x, text_y), (text_x + text_width + bg_padding, text_y + text_height + bg_padding)],
        outline_color=(154, 205, 50), 
        is_fill=True, 
        bg_color=bg_color
    )


    # Draw the text on top of the background box
    draw.text((text_x + 2, text_y + 2), text, font=font, fill=font_color)

def draw_index_with_bg_box(draw, text, position, 
                          font_size=18, font_color=(255, 255, 255), 
                          bg_padding=10, bg_color=(66, 119, 56)):  
    # Define the font and size for the text
    try:
        font = ImageFont.truetype("./NotoSerifSC-SemiBold.otf", font_size)
    except:
        font = ImageFont.truetype("../NotoSerifSC-SemiBold.otf", font_size)

    # Calculate the bounding box of the text
    text_bbox = draw.textbbox((0, 0), text, font=font)

    # Extract the width and height from the bounding box
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Define the position of the text based on the specified position parameter
    text_x, text_y = position

    # Draw the background box
    draw_rectangle(
        draw,
        [(text_x, text_y), (text_x + text_width + bg_padding, text_y + text_height + bg_padding)],
        outline_color=bg_color, 
        is_fill=True, 
        bg_color=bg_color
    )

    # Draw the text on top of the background box
    draw.text((text_x + 2, text_y), text, font=font, fill=font_color)

def draw_point(draw, center, radius1=3, radius2=6, color=(0, 255, 0)):
    draw_circle(draw, center, radius=radius1, outline_color=color)
    draw_circle(draw, center, radius=radius2, outline_color=color)

def draw_line_with_arrow(draw, start_point, end_point, color=(0, 255, 0), width=3, arrow_size=10):   
    # Draw the line
    x1, y1 = start_point
    x2, y2 = end_point
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    
    # Compute the angle between the line and the x-axis
    angle = math.atan2(y2 - y1, x2 - x1)
    
    # Calculate coordinates for arrowhead
    x_arrow = x2 - arrow_size * math.cos(angle + math.pi/6)
    y_arrow = y2 - arrow_size * math.sin(angle + math.pi/6)
    x_arrow2 = x2 - arrow_size * math.cos(angle - math.pi/6)
    y_arrow2 = y2 - arrow_size * math.sin(angle - math.pi/6)
    
    # Draw arrowhead
    draw.polygon([(x2, y2), (x_arrow, y_arrow), (x_arrow2, y_arrow2)], fill=color) 


def element_visual(element: str, pil_img: Image, text: str):
    draw = ImageDraw.Draw(pil_img)
    image_h = pil_img.height
    image_w = pil_img.width

    if not isinstance(element["absolute"], list):
        elements = [element["absolute"]]
    else:
        elements = element["absolute"]
    
    for e in elements:
        box_coords = parse_box(e)
        draw_rectangle(draw, box_coords, outline_color='red')

    draw_text_with_bg_box(
        draw,
        text=text, 
        view_port=(image_w, image_h),
        position = "top-middle", 
        font_size=16)

    return pil_img

def elements_visual(elements: list, pil_img: Image, outline_color="red"):

    draw = ImageDraw.Draw(pil_img)

    for element in elements:
        # draw rectangle
        if "rect" in element:
            rect = element['rect']
            left = rect['left']
            top = rect['top']
            right = rect['right']
            bottom = rect['bottom'] 
        else:
            rect = element['position']
            left = rect['x']
            top = rect['y']
            right = rect['x'] + rect["width"]
            bottom = rect['y'] + rect["height"]

        box_coords = (left, top, right, bottom)
        draw_rectangle(draw, box_coords, outline_color=outline_color)
    
        # draw index 
        draw_index_with_bg_box(draw, 
            text=str(element["uid"] if "uid" in element else element["id"]), 
            position=((left + right - 16) // 2, (top + bottom - 16) // 2), 
            font_size=14, 
            font_color=(255, 255, 255), 
            bg_padding=6, 
            bg_color=(66, 119, 56))
        
    return pil_img

def actions_visual(action_group: list, pil_img: Image, ins_cmd: str, color=(255, 48, 48), from_eval=False):
    draw = ImageDraw.Draw(pil_img)

    image_h = pil_img.height
    image_w = pil_img.width

    if isinstance(action_group, dict):
        action_group = [action_group]

    name_group = ""
    text_group = ""
    for i, action in enumerate(action_group):
        name_group += "{}. {}\n".format(i+1, action["name"])

        # Draw element with index
        if "element" in action:
            if from_eval:
                box_coords = parse_box(action["element"])
            else:
                box_coords = parse_box(action["element"]["absolute"])
   
            if color is not None:
                draw_rectangle(draw, box_coords, outline_color=color)
            else:
                draw_rectangle(draw, box_coords)
            draw_index_with_bg_box(draw, str(i+1), (box_coords[0], box_coords[1]-10), font_size=10, bg_padding=2)
         
        
        # Draw point
        if "point" in action:
            if from_eval:
                center = parse_point(action["point"])
            else:
                center = parse_point(action["point"]["absolute"])

            if color is not None:
                draw_point(draw, center, color=color)
            else:
                draw_point(draw, center)
 
        # Draw dual_point with index
        if "dual_point" in action:
            if from_eval:
                start_point, end_point = parse_point(action["dual_point"]['from']), parse_point(action["dual_point"]['to'])
            else:
                start_point, end_point = parse_point(action["dual_point"]["absolute"]['from']), parse_point(action["dual_point"]["absolute"]['to'])

            if color is not None:
                draw_line_with_arrow(draw, start_point, end_point, color=color)
            else:
                draw_line_with_arrow(draw, start_point, end_point)
            draw_index_with_bg_box(draw, str(i+1), (start_point[0], start_point[1]-10), font_size=10, bg_padding=2)

        # Draw scroll
        if "scroll" in action:
            start_point = (image_w // 2, image_h // 2)
            if from_eval:
                end_point = (image_w // 2 + action["scroll"]['right'], image_h // 2 + action["scroll"]['down'])
            else:
                end_point = (image_w // 2 + action["scroll"]["absolute"]['right'], image_h // 2 + action["scroll"]["absolute"]['down'])

            if color is not None:
                draw_point(draw, start_point, color=color)
                draw_line_with_arrow(draw, start_point, end_point, color=color)
            else:
                draw_point(draw, start_point)
                draw_line_with_arrow(draw, start_point, end_point)
        
        # Draw select value
        if "value" in action:
            assert "element" in action
            if from_eval:
                box_coords = parse_box(action["element"])
            else:
                box_coords = parse_box(action["element"]["absolute"])

            x, y = box_coords[0], box_coords[1] + 30
            draw_text_with_bg_box(
                draw,
                text=action["value"], 
                view_port=(image_w, image_h),
                position = f"point-{x}-{y}", 
            )

        if "text" in action:
            text_group += "{}. {}\n".format(i+1, action["text"].replace("\n", "\t"))
            
    # Draw action_names
    draw_text_with_bg_box(
        draw,
        text=name_group, 
        view_port=(image_w, image_h),
        position = "top-left", 
        font_size=16
    )

    # Draw text
    if text_group != "":
        draw_text_with_bg_box(
            draw,
            text=text_group, 
            view_port=(image_w, image_h),
            position = "bottom-middle", 
            font_size=16
        )

    # Draw instruction
    draw_text_with_bg_box(
        draw,
        text=ins_cmd, 
        view_port=(image_w, image_h),
        position = "top-middle", 
        font_size=16
    )

    return pil_img
