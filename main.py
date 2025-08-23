from src.doc_extractor import extract_json_from_doc
from pprint import pprint
import json 
if __name__ == "__main__":
    structure = extract_json_from_doc("data/demo.docx")
    pprint(structure)

    # with open('test.json','wb') as f:
    #     json.dump(structure,f,indent=2,ensure_ascii=False)