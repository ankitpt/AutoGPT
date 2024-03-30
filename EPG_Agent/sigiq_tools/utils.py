import json
from typing import List

PYQS_PATH = "EPG_Agent/data/mar25_pyqs.json"
with open(PYQS_PATH, "r") as f:
    PYQS: List[dict] = json.load(f)
    
ID_TO_PYQ = {pyq["id"]: pyq for pyq in PYQS}
IDX_2_ANS = ["(a)", "(b)", "(c)", "(d)", "(e)", "(f)", "(g)", "(h)", "(i)", "(j)"]

def pyqs_to_xml(questions: List[dict]) -> str:
    xml_string = '<questions>\n'

    for i, question_dict in enumerate(questions):
        xml_string += '  <question id={}>\n'.format(i)
        xml_string += '    <text>{}</text>\n'.format(question_dict["question"])
        xml_string += '    <options>\n'
        
        for i, option in enumerate(question_dict['options']):
            xml_string += '      <option>{}</option>\n'.format(IDX_2_ANS[i] + " " + option)
        
        xml_string += '    </options>\n'
        xml_string += '  </question>\n'

    xml_string += '</questions>'
    return xml_string