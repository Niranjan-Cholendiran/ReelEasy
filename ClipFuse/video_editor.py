import os
from moviepy.editor import concatenate_videoclips
from moviepy.video.VideoClip import ImageClip
from moviepy.video.fx.resize import resize
#from moviepy.video.fx import crop, resize

import moviepy.editor as mp
from moviepy.video.fx.all import crop
from moviepy.editor import VideoFileClip, AudioFileClip, ColorClip, CompositeAudioClip, CompositeVideoClip, concatenate_audioclips
from moviepy.audio.fx.all import audio_fadein, audio_fadeout
from moviepy.editor import TextClip, CompositeVideoClip
import math
from PIL import Image
import numpy as np
from dotenv import load_dotenv
load_dotenv()

from moviepy.config import change_settings

# Set imagepath path for moviepy
# imagemagick_path = os.environ['IMAGEMAGICK_PATH']  
# change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})

# from moviepy.config import change_settings

# #change_settings({"IMAGEMAGICK_BINARY": "/mnt/c/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"})
# change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

# Set imagepath path for moviepy
imagemagick_path = os.environ['IMAGEMAGICK_PATH']  
change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})

# Function to crop
def crop_clip_9_16(clip_object):
    """Crop image to 9:16 ratio from center and resize to (1080, 1920)"""
    # Desired aspect ratio
    aspect_ratio = 9 / 16
    target_width, target_height = 720, 1280

    # Original dimensions
    image_width, image_height = clip_object.size

    # Determine new width and height based on the desired aspect ratio
    if image_width / image_height > aspect_ratio:
        new_width = image_height * aspect_ratio
        new_height = image_height
    else:
        new_width = image_width
        new_height = image_width / aspect_ratio

    # Center crop
    crop_x_center = (image_width - new_width) / 2
    crop_y_center = (image_height - new_height) / 2

    # Perform the crop
    cropped_clip = crop(clip_object, x_center=image_width / 2, y_center=image_height / 2, width=new_width, height=new_height)

    # Resize the cropped clip to the target dimensions
    resized_clip = resize(cropped_clip, newsize=(target_width, target_height))
    
    return resized_clip

# Function to zoom
def zoom_in_effect(clip, zoom_ratio=0.05):
    '''Add zoom effect to the image clips. Credits to https://gist.github.com/mowshon/2a0664fab0ae799734594a5e91e518d5'''
    def effect(get_frame, t):
        img = Image.fromarray(get_frame(t))
        base_size = img.size

        new_size = [
            math.ceil(img.size[0] * (1 + (zoom_ratio * t))),
            math.ceil(img.size[1] * (1 + (zoom_ratio * t)))
        ]

        # The new dimensions must be even.
        new_size[0] = new_size[0] + (new_size[0] % 2)
        new_size[1] = new_size[1] + (new_size[1] % 2)

        img = img.resize(new_size, Image.LANCZOS)

        x = math.ceil((new_size[0] - base_size[0]) / 2)
        y = math.ceil((new_size[1] - base_size[1]) / 2)

        img = img.crop([
            x, y, new_size[0] - x, new_size[1] - y
        ]).resize(base_size, Image.LANCZOS)

        result = np.array(img)
        img.close()

        return result

    return clip.fl(effect)

def text_clip_generator(duration, text):
    # Set the video dimensions (9:16 aspect ratio)
    width, height = 720, 1280

    # Create the background clip
    background_clip = ColorClip(size=(width, height), color=(0, 0, 0), duration=duration)
    background_clip = crop_clip_9_16(background_clip)

    # Create the text clip with a fancy font
    text_clip = TextClip(text, fontsize=70, color='gold', font='Arial', size=(width * 0.8, None))
    text_clip = text_clip.set_position(('center', 'center')).set_duration(duration)

    # Overlay the text clip on the background
    final_clip = CompositeVideoClip([background_clip, text_clip])

    return final_clip

# Function to create image clip
def image_clip_generator(media_loc, duration):
    # Create the ImageClip
    image_clip = ImageClip(media_loc).set_duration(duration)

    # Crop image in 9:16 ratio
    cropped_image_clip = crop_clip_9_16(image_clip)

    # Add zoom effect
    zoomed_image_clip= zoom_in_effect(cropped_image_clip)

    # Create as video 
    final_clip= concatenate_videoclips([zoomed_image_clip], method="compose")
    #final_clip.ipython_display(width= 300, fps=30)

    return final_clip


# Function to create video clip
def video_clip_generator(media_loc, duration):
    video_clip= VideoFileClip(media_loc).without_audio()
    video_duration= video_clip.duration

    # Crop the video 
    video_clip= crop_clip_9_16(video_clip)

    if (video_duration > duration):
        # Trimming if the video is long
        video_clip= video_clip.subclip(0, duration) 

    elif (video_duration < duration):
        # Freezing the last frame with zoom effect if the video is short
        last_frame_time = video_duration - 2 / video_clip.fps # Collect the last frame and subtract a small epsilon to ensure the frame is within bounds 
        last_frame = video_clip.get_frame(last_frame_time)
        remaining_duration = duration - video_duration
        last_frame_clip = ImageClip(last_frame).set_duration(remaining_duration)
        last_frame_clip= zoom_in_effect(last_frame_clip)
        video_clip = concatenate_videoclips([video_clip, last_frame_clip])
    return video_clip

# Function to match volumne of audio clips and reduce the background music volume
# def calculate_rms(audio_clip):
#     # Get the audio data as a numpy array
#     audio_data = audio_clip.to_soundarray()
    
#     # Calculate RMS amplitude
#     rms_amplitude = np.sqrt(np.mean(audio_data**2))
    
#     return rms_amplitude
def calculate_rms(audio_clip):
    print(f"Type of audio_clip: {type(audio_clip)}")  # Debugging line
    audio_data = audio_clip.to_soundarray()
    rms_amplitude = np.sqrt(np.mean(audio_data**2))
    return rms_amplitude

def match_volume(vo_music, bg_music):   
    # Calculate average amplitude (RMS) of both clips and the adjustment factor vo_music to match bg_music
    vo_rms = calculate_rms(vo_music)
    bg_rms = calculate_rms(bg_music)
    volume_adjustment = bg_rms / vo_rms
    
    # Adjust volume of vo_music to match bg_music
    adjusted_vo_music = vo_music.volumex(volume_adjustment)
    
    return adjusted_vo_music, bg_music

def add_subtitles(video_clip, subtitles, max_width=None):
    subtitle_clips = []

    # Set seubs height relative to the video's height
    if max_width is None:
        max_width = video_clip.w * 0.9

    # Create TextClip objects for each subtitle
    for subtitle in subtitles:
        start_time, end_time, text = subtitle
        duration = end_time - start_time
        subtitle_clip = TextClip(text, fontsize=40, color='white', font='Arial', method='caption', size=(max_width, None))
        subtitle_clip = subtitle_clip.set_duration(duration).set_position(('center', video_clip.h * 0.7)).set_start(start_time)
        subtitle_clips.append(subtitle_clip)

    # Overlay the subtitle clips onto the video clip
    subtitled_clip = CompositeVideoClip([video_clip] + subtitle_clips)

    return subtitled_clip