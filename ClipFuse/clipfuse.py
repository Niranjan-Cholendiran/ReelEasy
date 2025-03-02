import moviepy
import pandas as pd
import flask
import os
import json
from ASR import audio_format_converter, ASR_audio_description, concatenate_audio_files
from dotenv import load_dotenv
from language_model import story_text_generator, subtitle_matcher
from playht_processor import custom_voice_creation, text_to_audio, transcript_timestamp
from video_editor import *
from moviepy.config import change_settings


media_info_list=[
    {
            "media_loc": r"C:\Users\niran\OneDrive\Desktop\HackCU11\ClipFuse V2\input_image\01.jpg", # DYNAMIC
            "media_format": "IMAGE", # DYNAMIC
            "description_text": "Eating my free breakfast", # Converted voice to text DYNAMIC
            "transcript_text": None, # The story transcript for this media
            "transcript_start_sec": None, # 
            "transcript_end_sec": None
        },
    {
            "media_loc": r"C:\Users\niran\OneDrive\Desktop\HackCU11\ClipFuse V2\input_image\02.mov", # DYNAMIC
            "media_format": "VIDEO",
            "description_text": "Received my hackathon goodies", # Converted voice to text DYNAMIC
            "transcript_text": None, # The story transcript for this media
            "transcript_start_sec": None, # 
            "transcript_end_sec": None
        }
]

media_information = {
        "STARTER": {
            "title": "My Hackathon at Colorado", # Overall video title DYNAMIC
            "combined_description_audio_loc": None, # Combined (concatenated) spoken audio media to be used for voice cloning NOT_NEEDED
            "final_voiceover_loc": None, # The location of the final voiceover of explaining the story with cloned voice to be used as video voiceover
            "bg_music_loc": r'C:\Users\niran\OneDrive\Desktop\HackCU11\ClipFuse V2\bg_music\Standard BG Music.mp3', # Standard background music location DYNAMIC
            "transcript_text": None, # 
            "transcript_start_sec": None,
            "transcript_end_sec": None,
            "number_of_segments": 2
        },
        "MEDIA_INFO": media_info_list
    }


playth_authorization= os.environ['PLAYHT_SECRET_KEY']
playht_userid= os.environ['PLAYHT_USER_ID']
voice_id= "s3://voice-cloning-zero-shot/daa273d8-3210-4172-ba64-b2447c56ac85/navya-cloned-01/manifest.json"
voiceover_save_path= r"C:\Users\niran\OneDrive\Desktop\HackCU11\ClipFuse V2\output\Custom Video Voiceover.mp3"
final_video_save_loc= r"C:\Users\niran\OneDrive\Desktop\HackCU11\ClipFuse V2\final_video\final_video.mp4"

def video_editor(
        media_information
        ,bg_music_flag=True
        ,voice_over_flag=True
        ,starting_video_title_display_flag=True
        ,subtitle_flag=True
        ,transition_flag=True
        ,animation_flag=True 
        ,ratio="Instagram"
        , volume_level="Default"):
    
    # Create story
    print("Creating Story...")
    while True:
        try:
            story_dict= story_text_generator(media_information)
            break
        except:
            print("\n\n TRYING AGAIN \n\n")
            continue
    print("Story Created!\n")

    # Create video voiceover with the story text and cloned voice
    print("Creating Voiceover...")
    story_text= story_dict['Starter']
    for segment_num in range (media_information['STARTER']['number_of_segments']): 
        story_text= " " + story_text+ story_dict[f'Section_{segment_num+1}']


    voiceover_job_id= text_to_audio (playth_authorization= playth_authorization, playht_userid= playht_userid, story_text= story_text, voice_id= voice_id, voiceover_save_path= voiceover_save_path)
    media_information['STARTER']['final_voiceover_loc']= voiceover_save_path
    print("Created Voiceover!\n")

    # Generate timestamps & subtitles from the custom voiceover and Match the actual and ideal subtitle
    print("Generating Subtitles...")
    subtitle_segments= transcript_timestamp(job_id= voiceover_job_id, playth_authorization= playth_authorization, playht_userid= playht_userid)
    actual_sub_list=[]
    for segment in subtitle_segments:
        actual_sub_list.append([segment['start'], segment['end'], segment['text']])
    subs_dict= subtitle_matcher (ideal_sub_dict= story_dict, actual_sub_list= actual_sub_list)
    print("Generated Subtitles\n")

    # Prepare video cut timings
    print("Preparing Video Cuts...")
    video_cut_timer= []
    # Collect all the start and end time in a list
    for section,info in subs_dict.items():
        if(section=="Title"): continue
        video_cut_timer.append([info['start'], info['end']])
    # Hard code the start timer as 0 and add 2 seconds at the end 
    print("video_cut_timer:", video_cut_timer)
    video_cut_timer[0][0]= 0
    video_cut_timer[-1][1]+= 2
    # Normalize the cut time as the center of current clip end and next clip start
    for time_index in range (len(video_cut_timer)-1):
        cut_time_normalized= round((video_cut_timer[time_index][1] + video_cut_timer[time_index+1][0])/2, 3)
        video_cut_timer[time_index][1] = cut_time_normalized
        video_cut_timer[time_index+1][0] = cut_time_normalized
    print("Prepared Video Cuts\n")

    # Prepare final video

    # Prepare starter video with text 
    print("Preparing Starter Video...")
    generated_clips=[]
    video_cut_timings= video_cut_timer[0]
    clip= text_clip_generator(duration= video_cut_timings[1]-video_cut_timings[0], text= subs_dict['Title']['story_text'])
    generated_clips.append(clip)
    print("Prepared Starter Video!\n")

    # Iteratively prepare segment clips: Read the media format and call the respective clip generator
    print("Preparing Remaining Video Clips...")
    for video_index in range (1, len(video_cut_timer)):
        video_cut_timings= video_cut_timer[video_index]
        media_info= media_information['MEDIA_INFO'][video_index-1]

        if (media_info['media_format'] == "IMAGE"):
            clip= image_clip_generator(duration= video_cut_timings[1]-video_cut_timings[0], media_loc= media_info['media_loc'])
            generated_clips.append(clip)
        elif (media_info['media_format'] == "VIDEO"):
            clip= video_clip_generator(duration= video_cut_timings[1]-video_cut_timings[0], media_loc= media_info['media_loc'])
            generated_clips.append(clip)
    print("Prepared Remaining Video Clips!\n")

    # Combine the clips and add fade effects
    print("Merging Clips...")
    final_clip_without_audio= concatenate_videoclips(generated_clips, method="compose")
    final_clip_without_audio= final_clip_without_audio.fadein(3).fadeout(3)
    print("Merged Clips!\n")

    # Add voiceover and background music
    print("Adding Voiceover and BG Music...")
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
    #vo_music, bg_music_path = match_volume(vo_music, bg_music)
    bg_music= bg_music.volumex(0.5)
    bg_music= bg_music.audio_fadein(2)
    bg_music= bg_music.audio_fadeout(2)
    # Set the new background music to the video
    final_audio = CompositeAudioClip([vo_music, bg_music])
    final_cip_with_audio = final_clip_without_audio.set_audio(final_audio)#.set_audio(bg_music)
    #final_cip_with_audio.ipython_display(width= 300)
    print("Added Voiceover and BG Music!\n")


    # Create subtitle list with timestamps
    print("Adding Subtitles...")
    subtitles = []
    for section,info in subs_dict.items():
        if(section=="Title"): continue
        for sub in info['subtitle']:
            subtitles.append((sub['start'], sub['end'], sub['text']))
    # Add subtitles to the video clip
    subtitled_clip = add_subtitles(final_cip_with_audio, subtitles)
    subtitled_clip = final_cip_with_audio #add_subtitles(final_cip_with_audio, subtitles)
    print("Added Subtitles!\n")

    print("Rendering Final Video...")
    subtitled_clip.write_videofile(final_video_save_loc, codec='libx264', audio_codec='aac', ffmpeg_params=['-movflags', '+faststart'], fps=30)
    print("Video Ready!!")


video_editor(media_information)