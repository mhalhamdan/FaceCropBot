import discord
import os
from quickselect_dl import face_utils
from quickselect_dl import inference
import io
import PIL
from PIL import Image

from face_crop import FaceCrop

TOKEN = 'token here'
IMAGE_TYPES = ["png", "jpeg", "jpg"]
ACTIONS = ['gender', 'race', 'emotion', 'age']
EMOJI_MAPPING = {
                        1: "1️⃣",
                        2: "2️⃣",
                        3: "3️⃣",
                        4: "4️⃣",
                        5: "5️⃣",
                        6: "6️⃣",
                        7: "7️⃣",
                        8: "8️⃣",
                        9: "9️⃣",
                        "1️⃣": 1, 
                        "2️⃣": 2,
                        "3️⃣": 3,
                        "4️⃣": 4,
                        "5️⃣": 5,
                        "6️⃣": 6,
                        "7️⃣": 7,
                        "8️⃣": 8,
                        "9️⃣": 9
                    }

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
async def on_reaction_add(reaction, user):

    # If reaction is to a message that references that id that is already inside fc.to_be_cropped
    if reaction.message.reference.message_id in fc.to_be_cropped.keys():
        to_be_cropped = fc.to_be_cropped[reaction.message.reference.message_id] # get list of PIL images to crop and send
        # If not bot who added reaction
        if (user.id != client.user.id):
            if reaction.emoji == "✂️":
                bot_response = await reaction.message.channel.send("Cropping...")
                for emoji in reaction.message.reactions:
                    if emoji.me == True: # Only if bot started reaction
                        if emoji.count > 1 and emoji.emoji != "✂️":
                            try:
                                result = fc.face_crop_and_segment(to_be_cropped[EMOJI_MAPPING[emoji.emoji] - 1])
                                binary_image = convert_image(result, "PIL")
                                await reaction.message.channel.send(file=discord.File(fp=binary_image, filename=f"{reaction.message.reference.message_id}.png"))
                            except:
                                await reaction.message.channel.send("An error occured with one of cropped images, will continue.")
                # After running inference on all images and sending them in the channel, remove instance from to_be_cropped
                fc.to_be_cropped.pop(reaction.message.reference.message_id)
                # And remove message
                await reaction.message.delete()
                await bot_response.edit(content="Done!")


@client.event
async def on_message(message):
    if message.content[0:5] == '-crop':
        # if full crop or face only
        face_crop = message.content == '-crop face'

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
                response = "Cropping..."
                response = await message.channel.send(response)  
                bot_response = await message.channel.fetch_message(response.id) # Preserve id of sent message for later use
                # Save image
                # image_path = f"./processing_images/{message.id}.{content_type}"
                image_path = io.BytesIO()
                await message.attachments[0].save(image_path)
                image_path.seek(0)
                image_path = convert_image(image_path, "bytes")

                # TODO: multiple faces
                faces_number = 0
                try:
                    if face_crop:
                        result, faces_number = fc.detect(image_path, message.id)
                        if faces_number > 9: 
                            return await message.channel.send("The bot does not support cropping for images with more than 9 people.")
                    else:
                        image_path = image_path.convert('RGB')
                        result = inference.run(image_path, model_no=6)
                except:
                    return await message.channel.send("Something went wrong. Please try a different image.")

                binary_image = convert_image(result, "PIL")
                
                # If multiple faces, reply with prompt
                if faces_number:
                    await bot_response.delete()
                    bot_response = await message.reply("Choose which of the following instances to crop. When done click on the scissors.", file=discord.File(fp=binary_image, filename=f"{message.id}.png"))
                    for n in range(1, faces_number+1):
                        await bot_response.add_reaction(EMOJI_MAPPING[n])
                    await bot_response.add_reaction("✂️")
                else:
                    await message.channel.send(file=discord.File(fp=binary_image, filename=f"{message.id}.png"))
                    await bot_response.edit(content="Done!")

                return
                
                

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