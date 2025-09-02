import asyncio
import edge_tts
import os

# Texts
text = "This method statement describes the outline procedure to be followed for Brick Masonry Work to be executed at Proposed location of the project."
hindi_text = "यह पद्धति कथन प्रस्तावित स्थान पर ईंटों की चिनाई (Brick Masonry Work) के लिए पालन की जाने वाली रूपरेखा प्रक्रिया का वर्णन करता है।"
guj_text = "આ પદ્ધતિ નિવેદન પ્રસ્તાવિત સ્થળ પર ઈંટોની ચણાઈ (Brick Masonry Work) માટે અનુસરવાની રૂપરેખા પ્રક્રિયાનું વર્ણન કરે છે."

# Output folder
output_dir = "mitesh audio"
os.makedirs(output_dir, exist_ok=True)

async def main():
    # English Male Voice
    eng_voice = "en-IN-PrabhatNeural"
    await edge_tts.Communicate(text, eng_voice).save(os.path.join(output_dir, "english.mp3"))

    # Hindi Male Voice
    hindi_voice = "hi-IN-MadhurNeural"
    await edge_tts.Communicate(hindi_text, hindi_voice).save(os.path.join(output_dir, "hindi.mp3"))

    # Gujarati Male Voice
    guj_voice = "gu-IN-NiranjanNeural"
    await edge_tts.Communicate(guj_text, guj_voice).save(os.path.join(output_dir, "gujarati.mp3"))

asyncio.run(main())
