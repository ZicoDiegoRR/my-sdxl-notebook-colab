import time
import os
import re

def save_image(image, prompt_for_name, prefix, base_path="/content/gdrive/MyDrive" if os.path.exists("/content/gdrive/MyDrive") else "/content"):
    current_time = time.localtime()
    formatted_time = time.strftime("[%H-%M-%S %B %d, %Y]", current_time)
    if prefix == "[Text-to-Image]":
        image_save_path = f"{base_path}/Text2Img"
    elif prefix == "[ControlNet]":
        image_save_path = f"{base_path}/ControlNet"
    elif prefix == "[Inpainting]":
        image_save_path = f"{base_path}/Inpainting"
    else:
        image_save_path = f"{base_path}/Img2Img"
    os.makedirs(image_save_path, exist_ok=True)
  
    sub_prompt = re.sub(r"[<>:\"/\\|?*]", "_", prompt_for_name)
    split_prompt = re.split(r"\s*,\s*", sub_prompt)
    prompt_name = " ".join(split_prompt)
    generated_image_raw_filename = f"{prefix} {formatted_time} {prompt_name}"
    generated_image_filename = generated_image_raw_filename[:251] if len(generated_image_raw_filename) > 255 else generated_image_raw_filename
    generated_image_savefile = f"{image_save_path}/{generated_image_filename}.png"
    image.save(generated_image_savefile)

    return generated_image_savefile
