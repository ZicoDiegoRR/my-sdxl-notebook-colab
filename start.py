from StableDiffusionXLColabUI.UI.mask_canvas import MaskCanvas
from IPython.display import display, clear_output
import ipywidgets as widgets
from PIL import Image
import subprocess
import os

# To subtitute the output method from Google Colab
class OutputSubstitute:
    def disable_custom_widget_manager(self):
        pass

    def enable_custom_widget_manager(self):
        pass

# Initialize Real-ESRGAN
def initialize_realesrgan():
    os.chdir("/content/RealESRGAN")
    subprocess.run(["python", "setup.py", "develop"])
    os.chdir("/content")

# Generate
def generate(args, instances):
    instances[1].reset_preview()
    instances[0].generate_value(**args)

# Plugging the inputted image into the canvas
def create_mask(mask, colab_ui):
    try:
        image = Image.open(colab_ui.inpaint.inpainting_image_dropdown.value)
        mask.create(image)
        colab_ui.draw = True
        colab_ui.reset_generate.submit_button_widget.disabled = True
        colab_ui.inpaint.mask_create_button.disabled = True
    except Exception as e:
        with colab_ui.inpaint_output:
            print(e)

# Enabling the button after finished drawing
def submit(colab_ui):
    colab_ui.inpaint.mask_image_widget.value = "/content/mask/temp.png"
    colab_ui.draw = False
    colab_ui.reset_generate.submit_button_widget.disabled = False
    colab_ui.inpaint.mask_create_button.disabled = False

# Doing everything
def start():
    initialize_realesrgan()

    # Import the preprocess module and UI
    from StableDiffusionXLColabUI.utils import preprocess
    from StableDiffusionXLColabUI.UI.ui_wrapper import UIWrapper

    # Import the widget manager (if exist)
    try:
        from google.colab import output
    except Exception as e:
        print("It seems like the output module from Google Colab doesn't exist. Are you using this repository somewhere else?\nAborting custom widget manager...")
        output = OutputSubstitute()

    # Setting the environment
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

    # Disable the custom widget manager
    output.disable_custom_widget_manager()

    # Preprocess the save file, ideas.txt, and GPT-2
    cfg, ideas_line, gpt2_pipe, base_path = preprocess.run()

    # Initialize the UI
    colab_ui = UIWrapper(cfg, ideas_line, gpt2_pipe, base_path)

    # Display (first)
    clear_output()
    display(colab_ui.ui)

    # Enable IPyCanvas widget
    output.enable_custom_widget_manager()

    # Initialize the IPyCanvas
    mask = MaskCanvas()
    mask.create(mask.black_image(256, 256))
    colab_ui.inpaint.mask_create_button.on_click(lambda b: create_mask(mask, colab_ui))
    mask.get_submit_button().on_click(lambda b: submit(colab_ui))

    # Display (second)
    display(mask.wrap_settings())
    display(colab_ui.generation_output)

    # Assign a click event
    colab_ui.reset_generate.submit_button_widget.on_click(
        lambda b: generate(
            {
                "index": colab_ui.ui_tab.selected_index, 
                "text2img": colab_ui.text2img,
                "img2img": colab_ui.img2img,
                "controlnet": colab_ui.controlnet,
                "inpaint": colab_ui.inpaint,
                "ip": colab_ui.ip,
                "lora": colab_ui.lora,
                "embeddings": colab_ui.embeddings,
            },
            (colab_ui, mask),
        )
    )
