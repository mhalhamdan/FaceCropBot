import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from quickselect_dl import find_faces
from quickselect_dl import face_utils
from quickselect_dl import inference

class FaceCrop(object):
    current_image = None
    to_be_cropped = {}

    def __init__(self, current_image=None, to_be_cropped=[]):

        self.current_image = None
        self.to_be_cropped = {}

    def fig2img(self, fig):
    # """Convert a Matplotlib figure to a PIL Image and return it"""
        import io
        buf = io.BytesIO()
        fig.savefig(buf)
        buf.seek(0)
        img = Image.open(buf)
        return img

    # Input: list of images
    # Output: PIL image
    def prompt_plot(self, image_list):
        f, axarr = plt.subplots(1,len(image_list))
        for idx, image in enumerate(image_list):
            axarr[idx].get_yaxis().set_visible(False)
            axarr[idx].get_xaxis().set_visible(False)
            axarr[idx].title.set_text(f"{idx+1}")
            axarr[idx].imshow(image)

        plot_image = self.fig2img(f)
        # plot_image.show()
        return plot_image
    
    # Input: PIL
    # Output: PIL after segmentation
    def face_crop_and_segment(self, image):
            result_after_cropping = face_utils.find_face(image)
            result_after_segmentation = inference.run(result_after_cropping)
            return result_after_segmentation

    # Input: PIL Image
    # Output: 
    # 1. if one face detected, return segmentation of face
    # 2. if multiple, return prompt
    def detect(self, image, message_id):

        result = find_faces.find_instances(image)
        # Multiple faces
        if len(result) > 1:

            prompt = self.prompt_plot(result)
            # Update dict to preserve for after user choice
            if message_id not in self.to_be_cropped.keys():
                self.to_be_cropped[message_id] = result
            return prompt, len(result)

        elif len(result) == 1:
            result_after_segmentation = self.face_crop_and_segment(result[0])
            return result_after_segmentation, 0


   

    
