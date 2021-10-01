import discord
import os
from quickselect_dl import face_utils
from quickselect_dl import inference
import io
import PIL
from PIL import Image

from face_crop import FaceCrop

TOKEN = 'TOKEN HERE'
IMAGE_TYPES = ["png", "jpeg", "jpg"]
ACTIONS = ['gender', 'race', 'emotion', 'age']
client = discord.Client()
fc = FaceCrop()

# Convert between PIL and Binary
def convert_image(image, original_type):
    if original_type == "PIL":
        image_binary = io.BytesIO()
        image.save(image_binary, 'PNG')
        image_binary.seek(0)
        return image_binary
    if original_type == "bytes":
        PIL_image = Image.open(image)
        return PIL_image

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.content[0:5] == '-crop':
        
        if message.reference is not None:
            message = await message.channel.fetch_message(message.reference.message_id) 

        attachment_size = len(message.attachments)
        if attachment_size == 0:
            response = "You have not attached an image."
            await message.channel.send(response) 
        elif attachment_size > 1:
            response = "Too many images. Please send one at a time."
            await message.channel.send(response) 
        else:
            content_type = message.attachments[0].content_type[6:]
            if content_type in IMAGE_TYPES:
                # TODO: multiple faces
                if message.content == '-crop face':
                    pass

                response = "Cropping..."
                response = await message.channel.send(response)  
                bot_response = await message.channel.fetch_message(response.id) # Preserve id of sent message for later use
                # Save image
                # image_path = f"./processing_images/{message.id}.{content_type}"
                image_path = io.BytesIO()
                await message.attachments[0].save(image_path)
                image_path.seek(0)
                image_path = convert_image(image_path, "bytes")
                
                # Cropping and sending image to channel
                # result_path = f"./processing_images/{message.id}-cropped.png"
                try:
                    result = inference.run(image_path, model_no=6)
                    binary_image = convert_image(result, "PIL")
                    await message.channel.send(file=discord.File(fp=binary_image, filename=f"{message.id}-cropped.png"))
                    await bot_response.edit(content="Done!")
                except RuntimeError:
                    await message.channel.send("Something went wrong. Please try a different image.")

    if message.content[1:len(message.content)] in ACTIONS and message.content[0] == '-':
        action = message.content[1:len(message.content)]

        if message.reference is not None:
            message = await message.channel.fetch_message(message.reference.message_id) 
        attachment_size = len(message.attachments)
        if attachment_size == 0:
            response = "There is no image attached."
            await message.channel.send(response)
        elif attachment_size > 1:
            response = "Too many images. Please send one at a time."
            await message.channel.send(response) 
        else:
            content_type = message.attachments[0].content_type[6:]
            if content_type in IMAGE_TYPES:
                response = "Analyzing..."
                response = await message.channel.send(response)  
                # Save image
                # image_path = f"./processing_images/{message.id}.{content_type}"
                image_path = io.BytesIO()
                await message.attachments[0].save(image_path)
                image_path.seek(0)
                image_path = convert_image(image_path, "bytes")
                # fix png problem
                image_path = image_path.convert('RGB')
        
                try:
                    result = face_utils.face_information(image_path, action)
                    await message.reply(f"Person's {action} is {result}.")
                    # Cleanup directory afterwards
                except RuntimeError:
                    await message.channel.send("Something went wrong. Please try a different image.")

        
client.run(TOKEN)