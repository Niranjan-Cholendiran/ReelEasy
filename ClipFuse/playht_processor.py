import requests
import json
import os
import time
from pydub import AudioSegment


# playht_userid= "TrMcrhz1qYSvLS6o0ef41lCCu7x2"
# playth_authorization="ak-ac83577260944420b1a9e313c11ebdf1" # Secret Key
# Funtion to create PlayHt custom voice
def custom_voice_creation (file_path, playth_authorization, playht_userid, voice_name='custom_voice-1'):
    """ Takes custom voice input path and creates a plyht voice instantly. Returns a dictionary of the created voice information."""
    url = "https://api.play.ht/api/v2/cloned-voices/instant"
    
    # Create a dictionary with the file details
    files = {
        "sample_file": (
            file_path.split("//")[-1],  # Extracts the file name from the path
            open(file_path, "rb"),     # Opens the file in read-binary mode
            "audio/x-m4a"              # Specifies the MIME type for the file
        )}

    # Post request 
    payload = { "voice_name": voice_name}

    headers = {"accept": "application/json",
        "AUTHORIZATION": playth_authorization,
        "X-USER-ID": playht_userid}

    response = requests.post(url, data=payload, files=files, headers=headers)

    # Extract the created voice information and return
    if (response.status_code in [200, 201]):
        print("Custom voice speech generated")
        custom_speech_info = json.loads(response.text)
        return custom_speech_info
    else:
        print("Custom voice speech generation failed")
        print(response.text)
        response.raise_for_status()
        return None
    
# Function to convert text to audio
def text_to_audio (playth_authorization, playht_userid, story_text, voice_id= "s3://voice-cloning-zero-shot/3cdb9c6c-547b-4935-9a50-d920a014874c/navya-cloned-01/manifest.json", voiceover_save_path= "../03. Intermediate Outputs//custom_speech_voiceover.mp3"):
    """ Convert text to speech audio using playht requests and saves it. This function text-to-speech playht job ID"""
    # Configure Plyht
    url = "https://api.play.ht/api/v2/tts"
    payload = {
        "text": story_text,
        "voice": voice_id,
        "output_format": "mp3",
        "voice_engine": "PlayHT2.0",
        #"voice_engine": "Play3.0-mini",
        #"speed": 0.8,
        #"quality": "medium",
        #"voice_guidance": 6, # Important Metric: Determines how close the generated voice should match the custom voice.
        #"seed": 7,
        #"temperature": 0.2,
        #"emotion": "male_happy", # Could also be "female_happy", but the gender doesn't impact the speech much.
        #"style_guidance": 5 # Important Metric: Determines how strong the chosen emotion will be. Keep it between 0-10, number more than that is too strong for a vlog video.
    }

    headers = {
        "accept": "text/event-stream",
        "content-type": "application/json",
        "AUTHORIZATION": playth_authorization,
        "X-USER-ID": playht_userid
    }

    # Generate and download custom voiceover 
    print("Generating Voiceover...")
    print(headers)
    print(payload)
    response = requests.post(url, json=payload, headers=headers)

    #print(response.text)
    #print(response.__dict__)

    if (response.status_code in [200, 201]):
        print("Voiceover Generated")
    else:
        print("Voiceover Generation Failed")
        print(response)
        print(json.loads(response.__dict__['_content'])['error_message'])
        response.raise_for_status()


    # Extract voiceover job information
    str_find= 'event: completed\r\ndata: '
    str_find_index= response.text.find(str_find)
    str_find_index
    voiceover_job_info= json.loads(response.text[str_find_index+len(str_find):].replace("\n",'').replace("\r",''))

    # Download voiceover
    response_url=  voiceover_job_info['url']
    print("Extracted URL:", response_url)

    try:
        response_audio = requests.get(response_url)
        if response_audio.status_code == 200:
            file_path = voiceover_save_path 
            
            with open(file_path, 'wb') as f:
                f.write(response_audio.content)
            
            print(f"Audio file downloaded successfully and saved in '{file_path}'.")
        else:
            print(f"Failed to download the audio file. Status code: {response_audio.status_code}")
    except requests.RequestException as e:
        print(f"Error downloading the audio file: {e}")

    job_id= voiceover_job_info['id']
    return job_id

# Function to generate transcript with timestamps
def transcript_timestamp(job_id, playth_authorization,playht_userid):
    """ Generates a sentence level timestamp using playht TTS job ID. Returns a list of dictionaries with sentence level transcript, start time, end time, and more informations."""

    # Create timestamp job
    print("Creating Transcript Job...")
    url = "https://api.play.ht/api/v2/transcriptions"
    payload = {
        "tts_job_id": job_id,
        "format": "JSON",
        "timestamp_level": "SENTENCE"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "AUTHORIZATION": playth_authorization,
        "X-USER-ID": playht_userid
    }
    response_timestamp_job = requests.post(url, json=payload, headers=headers)
    #print(response_timestamp_job.text)
    print("Transcript Job Created")
    
    # Download transcript
    print("\nDownloading Transcript...")
    url = f"https://api.play.ht/api/v2/transcriptions/{job_id}"
    headers = {
        "accept": "application/json",
        "AUTHORIZATION": playth_authorization,
        "X-USER-ID": playht_userid
    }
    response_timestamp = requests.get(url, headers=headers)

    # Wait for the job to complete
    attempt_id= 1
    while(True):
        if (attempt_id>10): return None
        print(f"    Attempt {attempt_id}")
        response_timestamp = requests.get(url, headers=headers)
        if(response_timestamp.status_code in [200,201]):
            break
        else:
            time.sleep(3)
            attempt_id+=1
            continue
        
    print("Transcript Downloaded")
    
    transcription_segments= json.loads(response_timestamp.text)['transcription']['segments']
    #print("\n\Transcript with timestamps (secs):") 
    #for segment in transcription_segments:
    #    print(segment['id'],':',segment['start'],"->", segment['end'],":", segment['text'])

    return transcription_segments