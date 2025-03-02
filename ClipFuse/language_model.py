import os
import json
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# Initiate the LLM model
llm= ChatOpenAI(
        model= "gpt-3.5-turbo",
        openai_api_key= os.getenv("OPENAI_API_KEY"), 
        temperature=1, 
        )

# from PIL import Image as pil
# from pkg_resources import parse_version

# if parse_version(pil.__version__)>=parse_version('10.0.0'):
#     Image.ANTIALIAS=Image.LANCZOS

# Create story text with the description text
def story_text_generator (media_information):
    """Collects the media information that contains description text of many segments, builds the vlog story and returns a story dictionary with keys as segment name and values as story texts"""
        
    # Prepare llm's input prompt
    user_input= f"""
    Vacation Short Summary: {media_information['STARTER']['title']}
    Image Descriptions:
    """
    for segment_num in range (media_information['STARTER']['number_of_segments']):
        user_input += f"{segment_num+1} : {media_information['MEDIA_INFO'][segment_num]['description_text']}\n"

    input_prompt= """
    You are a story-creating assistant. Your task is to take a list of image/video descriptions from the user's recent vacation and combine them in the provided order to create a concise narrative. This narrative will be used as a background voiceover for the user's vlog video. Generate the story based on the descriptions below and return STRICTLY A JSON output. For instance, if the list contains three descriptions, return a JSON with 3 story segments with keys as Section_[number]. Make sure to be concise. Additionally, provide a video starter with the key "Starter" with value something like "Welcome to my vlog ____" and provide key "Title" with value of some short text to display in the video's starter.

    ENSURE EVERY SEGMENT's DESCRIPTION IS NOT MORE THAN 7 SECONDS OF LENGTH WHEN SPOKEN. KEEP IT CONCISE.

    Here's an example response:
    {
    "Title": "My Journey to the Great Taj Mahal",
    "Starter": "Welcome to my vlog of my unforgettable vacation to the Great Taj Mahal.",
    "Section_1": "It all began with my fully packed bag ready for the early morning flight to Delhi.",
    "Section_2": "After arriving in Agra, I strolled through the bustling shopping streets where vendors offered a variety of goods, from jewelry and toys to leather boots.",
    "Section_3": "The highlight of my trip was undoubtedly visiting the magnificent Taj Mahal. Here I am, standing in front of this breathtaking monument.",
    "Section_4": "As the day came to an end, I took a cab, known locally as an Auto Rickshaw, back to my hotel."
    }

    User:
    """ + user_input

    #print(input_prompt)

    # Generate voiceover story using LLM
    reply= llm.invoke(input_prompt).content
    print(reply)
    story_dict= json.loads(reply)
    print("Vlog Story Created")
    print(story_dict)
    return story_dict


# Match actual and ideal subtitle
def subtitle_matcher (ideal_sub_dict, actual_sub_list):
    """Collects the ideal subtitle dictionary and actual subtitle list, matches them, generates segment timestamps and returns a combined dictionary"""

    subtilte_matcher_prompt= """
    I will provide an ideal subtitle dictionary and actual subtitle list. The ideal subtitle text dictionary contains keys as different segments and values as the ideal subtitle text.
    The actual subtitle list consist of multiple lists inside with each each in format [start time seconds, end time seconds, actual text]. Remember the actual text and subtitle text will be almost same but might not be an exact match.Math

    Your goal is to create a json output with keys as segments and values as a dictionary with "story_text" as actual text, "start" and "end" as subtitle start and end time of the actual text in subtitle list generated 
    by matching the actual text with ideal text of that particular segment, "subtitle" as the list dictionaries of the subtitle corresponding to the story text with start, end and text keys where text shoudl be the ideal text but not actual text.text_to_audio

    Use the below example for better understanding. Make sure to strictly repond a JSON output as shown in the example below:
        
    EXAMPLE IDEAL SUBTITLE DICTIONARY:

    {
        'Starter': 'Welcome to my vlog of my exciting vacation at the Great Sand Dunes National Park.',
        'Section_1': 'The day began with a long drive of 400 miles to the national park, setting the stage for an adventure-filled day ahead.'
    }

    EXAMPLE ACTUAL SUBTITLE LIST:
    [
        [0.18, 1.22, "Welcome to"], 
        [2.1, 6.36, "my vlog of my ice-lighting vacation at the Grey Sand Dunes National Park."],
        [7.26, 10.3, "The day began with a long drive of 400 miles to the national park,"],
        [11, 11.82, "setting the stage for"]
        [11.84, 12.96, "an adventure field day ahead."]
    ]

    EXAMPLE RESPONSE:
    {
        "Starter": {
            "story_text": "Welcome to my vlog of my exciting vacation at the Great Sand Dunes National Park.",
            "start": 0.18,
            "end": 6.36,
            "subtitle": [{"start": 0.18, "end": 1.22, "text": "Welcome to"},
                        {"start": 2.1, "end": 6.36, "text": "my vlog of my exciting vacation at the Great Sand Dunes National Park."}]
                    },
        "Section_1": {
            "story_text": "The day began with a long drive of 400 miles to the national park, setting the stage for an adventure-filled day ahead.",
            "start": 7.26,
            "end": 10.3,
            "subtitle": [{"start": 7.26, "end": 10.3, "text": "The day began with a long drive of 400 miles to the national park,"},
                        {"start": 11, "end": 11.82, "text": "setting the stage for"},
                        {"start": 11.84, "end": 12.96, "text": "an adventure-filled day ahead."}]
                    }
    }

    STRICTLY ENSURE THE RESPONSE LENGTH IS EQUAL TO IDEAL SUBTITLE DICTIONARY LENGTH
    USER INPUT:
    """ + f"IDEAL SUBTITLE DICTIONARY:{ideal_sub_dict}" + f"ACTUAL SUBTITLE LIST: {actual_sub_list}"

    # Generate subtitle matched dictionary using LLM
    reply= llm.invoke(subtilte_matcher_prompt).content
    subs_dict= json.loads(reply)
    print("Subtitles Matched")
    return subs_dict
