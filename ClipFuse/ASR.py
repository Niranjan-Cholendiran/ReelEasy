from pydub import AudioSegment
#import speech_recognition as sr

# Function to convert audio format
def audio_format_converter(audio_ip_path, audio_op_path, format="wav"):
    sound = AudioSegment.from_file(audio_ip_path)
    sound.export(audio_op_path, format= format)
    print(f"Audio converted and saved in {format} format")

#audio_format_converter("Whisper_ip_test.mp3", "Whisper_ip_test.wav", format="wav")


# Function to perform ASR on input audio description
def ASR_audio_description(audio_file_path):
    """Takes the audio file path (make sure the audio is in WAV format for seemless transcription) and returns the transcript text"""
    recognizer = sr.Recognizer()
    print("recognizer ready")

    # Open the audio file and recognize speech using Google Web Speech API
    with sr.AudioFile(audio_file_path) as source:
        print("Audio Read")
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)  
            print("ASR Successful!")
            return text
            #print("Transcription:", text)
        except sr.UnknownValueError:
            print("ASR Failed")
            print("Google Web Speech API could not understand the audio")
            return
        except sr.RequestError as e:
            print("ASR Failed")
            print(f"Could not request results from Google Web Speech API; {e}")
            return

#ASR_audio_description("Whisper_ip_test.wav")

# Function to concatenate multiple adescription udio file and save
def concatenate_audio_files(file_loc_list, output_location):
    """Function that takes audio file location list, concatenate them and save in the output location."""
    combined = AudioSegment.empty()
    
    for file_loc in file_loc_list:
        audio = AudioSegment.from_file(file_loc)
        combined += audio
    
    combined.export(output_location, format="wav")
    print("Description audio concatenated!")

#concatenate_audio_files(["file1.wav", "file2.wav", "file3.wav"], "combined_audio.wav" )