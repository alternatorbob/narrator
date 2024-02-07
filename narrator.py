import os
from openai import OpenAI
import base64
import json
import time
import simpleaudio as sa
import errno
from elevenlabs import generate, play, set_api_key, voices

client = OpenAI()

set_api_key(os.environ.get("ELEVENLABS_API_KEY"))


def encode_image(image_path):
    while True:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except IOError as e:
            if e.errno != errno.EACCES:
                # Not a "file in use" error, re-raise
                raise
            # File is being written to, wait a bit and retry
            time.sleep(0.1)


def play_audio(text):
    audio = generate(text, voice=os.environ.get("ELEVENLABS_VOICE_ID"))

    unique_id = base64.urlsafe_b64encode(
        os.urandom(30)).decode("utf-8").rstrip("=")
    dir_path = os.path.join("narration", unique_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, "audio.wav")

    with open(file_path, "wb") as f:
        f.write(audio)

    play(audio)


def generate_new_line(base64_image):
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image"},
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ],
        },
    ]


def analyze_image(base64_image, script):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": """

                You Generate a dialogue between two characters based on the image provided. The conversation will alternate between the two, with each character providing their perspective in a distinct style.

                Character One will focus on the biological and behavioral aspects of the individual in the image. This character will comment on the person’s physical stance, facial expressions, and any implied characteristics or emotions, inferring depth and narrative behind the subject's natural traits.

                Character Two will concentrate on the visual and aesthetic details, critiquing the individual’s clothing, colors, patterns, and overall fashion sense. This character will bring in fashion terminology and a more critical, trend-focused lens to the discussion.

                The dialogue should be structured with clear line breaks and designated speaker labels for each line. Begin with an instruction for Character One to 'Wait' before launching into their analysis, signaling the start of the detailed examination. The conversation should flow as follows:

                Character One: will offer an observation or a comment, starting with 'Wait,' followed by a thoughtful analysis of the person’s primal traits.
                Character Two: will then respond, either agreeing, disagreeing, or adding a new observation about the individual's outfit and style.
                Continue the exchange, ensuring that each character sticks to their respective domain of analysis.
                Conclude the conversation with a directive or a rhetorical question that either character may pose, prompting a theoretical reaction of surprise or shock.
                Ensure the dialogue progresses logically, with each character’s comments informed by the previous lines. The exchange should capture a dynamic interplay between the two perspectives, with Character One's lines being more rhetorical and analytical and Character Two's lines being sassy, employing fashion lingo.

                For output, maintain the format with line breaks and character labels as follows:

                Character One: [Observation/Comment]
                Character Two: [Response/Addition]

                Adapt the length of the conversation as needed, providing a long, medium, and short version based on the depth and breadth of the analysis required.
                
                """,
            },
        ]
        + script
        + generate_new_line(base64_image),
        max_tokens=500,
    )
    response_text = response.choices[0].message.content
    return response_text


def main():
    script = []

    while True:
        # path to your image
        image_path = os.path.join(os.getcwd(), "./frames/frame.jpg")

        # getting the base64 encoding
        base64_image = encode_image(image_path)

        # analyze posture
        print("👀 David is watching...")
        analysis = analyze_image(base64_image, script=script)

        print("🎙️ David says:")
        print(analysis)

        play_audio(analysis)

        script = script + [{"role": "assistant", "content": analysis}]

        # wait for 5 seconds
        time.sleep(5)


if __name__ == "__main__":
    main()
