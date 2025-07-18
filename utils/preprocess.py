from StableDiffusionXLColabUI.utils import save_file_converter, downloader
from transformers import pipeline as pipe, set_seed
from transformers.utils import logging
import requests
import shutil
import time
import json
import os

# Load the save file
def load_param(filename):
    try:
        with open(filename, 'r') as f:
            params = json.load(f)
        return params
    except FileNotFoundError:
        return []

def import_mod_real_esrgan():
    os.chdir("/content/RealESRGAN")
    from modified_inference_realesrgan import ESRGANWidget, VariableHandlerESRGAN, run_upscaling
    os.chdir("/content")

# Adding the modified_inference_realesrgan.py to Real-ESRGAN
def add_mod_real_esrgan():
    shutil.copy(
        "/content/StableDiffusionXLColabUI/utils/modified_inference_realesrgan.py", 
        "/content/RealESRGAN/modified_inference_realesrgan.py"
    )
    import_mod_real_esrgan()

#Function to save parameters config (had to make separate JSON def to avoid confusion)
def save_param(path, data):
    with open(path, 'w') as file:
        json.dump(data, file)

# Return the default values for the parameters
def default_params():
  return {
        "text2img": ["", "", "", 1024, 1024, 12, 6, 2, "Default (defaulting to the model)", 
                     False, False, False, False, "", "", 1
                    ],
        "img2img": ["", "", "", 1024, 1024, 12, 6, 2, "Default (defaulting to the model)", 
                    False, False, False, False, "", "", "", 0.3, 1
                   ],
        "controlnet": ["", "", "", 1024, 1024, 12, 6, 2, "Default (defaulting to the model)", 
                      False, False, False, False, "", "", "", 100, 240, False, 
                      0.7, "", False, 0.7, "", False, 0.7, 1
                      ],
        "inpaint": ["", "", "", 1024, 1024, 12, 6, 2, "Default (defaulting to the model)", 
                     False, False, False, False, "", "", "", "", False, 0.9, 1
                   ],
        "ip": ["", 0.8, "None"],
        "lora": ["", ""],
        "embeddings": ["", ""],
    }

# Checking and validating the save file
def list_or_dict(cfg, path):
    new_cfg = cfg
    if isinstance(cfg, list):
        # Converting the save format from a list to a dictionary
        new_cfg = save_file_converter.old_to_new(cfg)
        
    if len(new_cfg["inpaint"]) < 19:
        new_cfg = save_file_converter.new_inpaint(new_cfg)
                
    if len(new_cfg["text2img"]) < 16:
        new_cfg = save_file_converter.add_batch_size(new_cfg)

    save_param(path, new_cfg)   
    return new_cfg

def run():
    # Minimizing the Transformers' output
    logging.set_verbosity_error()
    
    # Adding the modified Real-ESRGAN's inference Python script
    add_mod_real_esrgan()
    
    # Loading the saved config for the IPyWidgets
    os.makedirs("/content", exist_ok=True)
    if not os.path.exists("/content/gdrive/MyDrive"):
        try:
            from google.colab import drive
            drive.mount('/content/gdrive', force_remount=True)
            google_drive_use = True
        except Exception as e:
            print("Excluding Google Drive storage...")
            google_drive_use = False
            time.sleep(1.5)
    else:
        google_drive_use = True

    if google_drive_use:
        base_path = "/content/gdrive/MyDrive"
    else:
        base_path = "/content"

    os.makedirs(f"{base_path}/Saved Parameters", exist_ok=True)

    # Loading the save file
    cfg = None
    if os.path.exists(f"{base_path}/parameters.json"):
        cfg = load_param(os.path.join(f"{base_path}", "parameters.json"))
        os.makedirs(f"{base_path}/Saved Parameters", exist_ok=True)
        save_param(os.path.join(f"{base_path}/Saved Parameters/", "main_parameters.json"), cfg)
        main_parameter_path = os.path.join(f"{base_path}/Saved Parameters/", "main_parameters.json")
        print(f"Found a config at {base_path}/parameters.json.")
    elif os.path.exists(f"{base_path}/Saved Parameters/main_parameters.json"):
        cfg = load_param(os.path.join(f"{base_path}/Saved Parameters/", "main_parameters.json"))
        main_parameter_path = os.path.join(f"{base_path}/Saved Parameters/", "main_parameters.json")
        print(f"Found a config at {base_path}/Saved Parameters/main_parameters.json.")
    else:
        print("No saved config found. Defaulting...")

    # Validating the save file's content
    if cfg:
        cfg = list_or_dict(cfg, main_parameter_path)
    else:
        cfg = default_params()
        time.sleep(1)

    # Downloading ideas.txt from GitHub for prompt generation
    if not os.path.exists("/content/ideas.txt"):
        ideas_response = requests.get("https://raw.githubusercontent.com/ZicoDiegoRR/stable_diffusion_xl_colab_ui/refs/heads/main/ideas.txt")
        if ideas_response.status_code == 200:
            with open("/content/ideas.txt", "w") as ideas_file:
                ideas_file.write(ideas_response.text)
            with open("/content/ideas.txt", "r") as ideas_file:
                ideas_line = ideas_file.readlines()
            print("Loading GPT-2 prompt generator...")
            gpt2_pipe = pipe('text-generation', model='Gustavosta/MagicPrompt-Stable-Diffusion', tokenizer='gpt2')
            
        else:
            print("Failed to download ideas.txt from GitHub.")
            ideas_line = []
            gpt2_pipe = None
            
    else:
        with open("/content/ideas.txt", "r") as ideas_file:
            ideas_line = ideas_file.readlines()
        print("Loading GPT-2 prompt generator...")
        gpt2_pipe = pipe('text-generation', model='Gustavosta/MagicPrompt-Stable-Diffusion', tokenizer='gpt2')

    # Moving the last_generation.json to the Saved Parameters folder from previous versions
    if os.path.exists(os.path.join(base_path, "last_generation.json")):
        os.makedirs(f"{base_path}/Saved Parameters", exist_ok=True)
        os.rename(
            os.path.join(base_path, "last_generation.json"), 
            os.path.join(f"{base_path}/Saved Parameters", "last_generation.json"),
        )

    # Update the model selection
    model = downloader.download_file(base_path=base_path, update=True)

    return cfg, ideas_line, gpt2_pipe, base_path
