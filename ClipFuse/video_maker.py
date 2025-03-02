import os
import json
from ASR import audio_format_converter, ASR_audio_description, concatenate_audio_files
from dotenv import load_dotenv
from language_model import story_text_generator, subtitle_matcher
from playht_processor import custom_voice_creation, text_to_audio, transcript_timestamp
from video_editor import *
from moviepy.config import change_settings

load_dotenv()

# Set imagepath path for moviepy
imagemagick_path = os.environ['IMAGEMAGICK_PATH']  
change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})

import time
import logging

# Configure logging for video_maker.py
logger = logging.getLogger(__name__)

# Example configuration: Log to a file named video_maker.log
logging.basicConfig(filename='video_maker.log', level=logging.INFO)

concatenated_descr_video_save_loc= r"02. Scripts\static\uploads\descriptions\Description_Combined.wav"
final_video_save_loc= r"02. Scripts\static\uploads\final_video\final_video.mp4"
voiceover_save_path= r"02. Scripts\static\uploads\final_video\Custom Video Voiceover.mp3"

def video_maker(media_information, progress_queue):

    # Transcribe all the description audio one by one
    for segment_num in range (media_information['STARTER']['number_of_segments']):
        print("segment_num:",segment_num)

        # Convert description media format to WAV (if not)
        if (media_information['MEDIA_INFO'][segment_num]['description_audio_format'] not in ['wav', "WAV"]):
            # Prepare output file location
            audio_ip_path= media_information['MEDIA_INFO'][segment_num]['description_audio_loc']
            file_dir = os.path.dirname(audio_ip_path)
            file_name_with_ext = os.path.basename(audio_ip_path)
            file_name, file_extension = os.path.splitext(file_name_with_ext)
            audio_op_path = os.path.join(file_dir, file_name+".wav")
            audio_op_path= audio_op_path.replace("\\", "//")
            #print(audio_ip_path, "-> ", audio_op_path)
            audio_format_converter(audio_ip_path= audio_ip_path, audio_op_path= audio_op_path, format="wav")

            # Save the updated description audio location and format
            media_information['MEDIA_INFO'][segment_num]['description_audio_format']= "wav"
            media_information['MEDIA_INFO'][segment_num]['description_audio_loc']= audio_op_path

        # Transcribe the audio
        audio_file_path= media_information['MEDIA_INFO'][segment_num]['description_audio_loc']
        print("audio_file_path:", audio_file_path)
        description_text= ASR_audio_description(audio_file_path)
        media_information['MEDIA_INFO'][segment_num]['description_text']= description_text
        print(description_text)
    logger.info("Description Transcribed!")
    progress_queue.put("Description Transcribed!")

    # Create story text with the description text using a LLM
    story_dict= story_text_generator(media_information) # Will contain "Tile" to display as video starter, "Starter" as the welcome story text, "Segment_n" as each segment's text.
    logger.info("Story Generated!")
    progress_queue.put("Story Generated!")

    # Create custom voice with the description audio
    # Concatenate description audio files to use it as custom voice creation input
    file_loc_list=[]
    for segment_num in range (media_information['STARTER']['number_of_segments']):
        file_loc_list.append(media_information['MEDIA_INFO'][segment_num]['description_audio_loc'])
    output_location= concatenated_descr_video_save_loc
    concatenate_audio_files(file_loc_list, output_location)
    media_information['STARTER']["combined_description_audio_loc"]= output_location

    # Create custom voice with the concatenated description audio
    
    file_path= media_information['STARTER']["combined_description_audio_loc"]
    voice_name= "custom_voice"
    playth_authorization= os.environ['PLAYHT_SECRET_KEY']
    playht_userid= os.environ['PLAYHT_USER_ID']
    custom_voice_info= custom_voice_creation (file_path= file_path, playth_authorization= playth_authorization, playht_userid= playht_userid, voice_name= voice_name)
    voice_id= custom_voice_info['id']   # Cloned voice ID 
    logger.info("Custom Voice Created!")
    progress_queue.put("Custom Voice Created!")

    # Create video voiceover with the story text and cloned voice
    story_text= story_dict['Starter']
    for segment_num in range (media_information['STARTER']['number_of_segments']): 
        story_text= " " + story_text+ story_dict[f'Section_{segment_num+1}']
    
    voiceover_job_id= text_to_audio (playth_authorization= playth_authorization, playht_userid= playht_userid, story_text= story_text, voice_id= voice_id, voiceover_save_path= voiceover_save_path)
    media_information['STARTER']['final_voiceover_loc']= voiceover_save_path
    logger.info("Voiceover Generated!")
    progress_queue.put("Voiceover Generated!")

    # Generate timestamps & subtitles from the custom voiceover and Match the actual and ideal subtitle
    logger.info("Generating Video...")
    progress_queue.put("Generating Video...")
    subtitle_segments= transcript_timestamp(job_id= voiceover_job_id, playth_authorization= playth_authorization, playht_userid= playht_userid)
    actual_sub_list=[]
    for segment in subtitle_segments:
        actual_sub_list.append([segment['start'], segment['end'], segment['text']])

    subs_dict= subtitle_matcher (ideal_sub_dict= story_dict, actual_sub_list= actual_sub_list)

    # Prepare video cut timings
    video_cut_timer= []
    # Collect all the start and end time in a list
    for section,info in subs_dict.items():
        if(section=="Title"): continue
        video_cut_timer.append([info['start'], info['end']])
    # Hard code the start timer as 0 and add 2 seconds at the end 
    video_cut_timer[0][0]= 0
    video_cut_timer[-1][1]+= 2
    # Normalize the cut time as the center of current clip end and next clip start
    for time_index in range (len(video_cut_timer)-1):
        cut_time_normalized= round((video_cut_timer[time_index][1] + video_cut_timer[time_index+1][0])/2, 3)
        video_cut_timer[time_index][1] = cut_time_normalized
        video_cut_timer[time_index+1][0] = cut_time_normalized


    # Prepare final video
    # Prepare starter video with text 
    generated_clips=[]
    video_cut_timings= video_cut_timer[0]
    clip= text_clip_generator(duration= video_cut_timings[1]-video_cut_timings[0], text= subs_dict['Title']['story_text'])
    generated_clips.append(clip)
    # Iteratively prepare segment clips: Read the media format and call the respective clip generator
    for video_index in range (1, len(video_cut_timer)):
        video_cut_timings= video_cut_timer[video_index]
        media_info= media_information['MEDIA_INFO'][video_index-1]

        if (media_info['media_format'] == "IMAGE"):
            clip= image_clip_generator(duration= video_cut_timings[1]-video_cut_timings[0], media_loc= media_info['media_loc'])
            generated_clips.append(clip)
        elif (media_info['media_format'] == "VIDEO"):
            clip= video_clip_generator(duration= video_cut_timings[1]-video_cut_timings[0], media_loc= media_info['media_loc'])
            generated_clips.append(clip)
    # Combine the clips and add fade effects
    final_clip_without_audio= concatenate_videoclips(generated_clips, method="compose")
    final_clip_without_audio= final_clip_without_audio.fadein(3).fadeout(3)
    logger.info("    Merged Media!")
    progress_queue.put("    Merged Media!")
    logger.info("    Added Video Effects!")
    progress_queue.put("    Added Video Effects!")

    # Add voiceover and background music
    video_duration= final_clip_without_audio.duration
    # Load the background voiceover
    music_path = media_information['STARTER']['final_voiceover_loc']
    vo_music = AudioFileClip(music_path)
    # Load the background music and adjust duration
    music_path = media_information['STARTER']['bg_music_loc']
    bg_music = AudioFileClip(music_path)
    bg_music_duration= bg_music.duration
    if (bg_music_duration > video_duration):
        # Trimming the audio if it is long
        bg_music= bg_music.subclip(0, video_duration)
    elif (bg_music_duration < video_duration):
        # Looping the audio if it is short
        bg_music= bg_music.loop(duration= video_duration)
    # Match volume, reduce bg volumne to 60% and add fade effects
    vo_music, bg_music_path = match_volume(vo_music, bg_music)
    bg_music= bg_music.volumex(0.5)
    bg_music= bg_music.audio_fadein(2)
    bg_music= bg_music.audio_fadeout(2)
    # Set the new background music to the video
    final_audio = CompositeAudioClip([vo_music, bg_music])
    final_cip_with_audio = final_clip_without_audio.set_audio(final_audio)#.set_audio(bg_music)
    #final_cip_with_audio.ipython_display(width= 300)
    logger.info("    Added Voiceover!")
    progress_queue.put("    Added Background Music!")


    # Create subtitle list with timestamps
    subtitles = []
    for section,info in subs_dict.items():
        if(section=="Title"): continue
        for sub in info['subtitle']:
            subtitles.append((sub['start'], sub['end'], sub['text']))
    # Add subtitles to the video clip
    subtitled_clip = add_subtitles(final_cip_with_audio, subtitles)
    logger.info("    Added Subtitles!")
    progress_queue.put("    Added Subtitles!")

    logger.info("Final Video Rendering...")
    progress_queue.put("Final Video Rendering...")

    subtitled_clip.write_videofile(final_video_save_loc, codec='libx264', audio_codec='aac', ffmpeg_params=['-movflags', '+faststart'], fps=30)

    # Delete all the user files
    return
