from gtts import gTTS
import os

text = "1. my name is Ashish. \n2 i'm working as software engineer \n3. i'm from gujarat"
tts = gTTS(text=text, lang='hi', slow=False, tld="co.in") 
tts.save("test.mp3")
tts = gTTS(text=text, lang='en', slow=False, tld="co.in") 
tts.save("test_2.mp3") 