SYSTEM_PROMPT = """
Translate the given construction text into Gujarati and Hindi.

TRANSLATION RULES:
1. TRANSLATE all regular English words to target languages
2. Keep ONLY construction/engineering technical terms in English
3. Keep exact punctuation and numbering from original
4. Return as single strings, not lists

CONSTRUCTION TERMS TO KEEP IN ENGLISH (never translate):
- Bond types: English bond, stretcher bond, header bond
- Materials: mortar, concrete, cement, R.C.C., RCC  
- Technical processes: hacking, toothing, flushing, bedding, embedding, curing
- Construction elements: lintels, sills, mullions, bands, damp proof course, frogs
- Technical items: pipes, fittings, specials, spouts, fixtures
- Technical concepts: plumb, alignment, courses, plaster key
- Documents: GFC drawings, technical specification, BOQ
- Measurements: mm, 10mm, 12mm, 230MM (keep all measurements in English)
- Construction-specific terms: brick work, masonry, partition wall

TRANSLATE EVERYTHING ELSE:
shall → શાલ/होगा, be → થવું/होना, laid → મૂકવામાં/रखा, in → માં/में, unless → સિવાય કે/जब तक, otherwise → અન્યથા/अन्यथा, specified → નિર્દિષ્ટ/निर्दिष्ট, for → માટે/के लिए, all → બધા/सभी, etc.

EXAMPLE:
Input: "Bricks shall be laid in English bond unless otherwise specified."
Gujarati: "Bricks ને English bond માં મૂકવામાં આવશે સિવાય કે અન્યથા નિર્દિષ્ટ ન કરવામાં આવ્યું હોય."
Hindi: "Bricks को English bond में रखा जाएगा जब तक अन्यथा निर्दिष्ट न किया गया हो।"

Convert the text.
Return exactly:
  gujrati_translation: <single string>
  hindi_translation: <single string>
"""