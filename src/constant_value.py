API_KEY = ''

model = "gpt-3.5-turbo-1106"
MBPP_PATH = f"dataset/{model}_mbpp_temp01.json"
MBPP_PATH_WITH_SUFFIX = MBPP_PATH.replace(".json", "_test.json")

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo-1106")
    parser.add_argument("--language", type=str, default="python")
    parser.add_argument("--base_url", type=str, default=None)
    parser.add_argument("--api_key", type=str, default=None)
    parser.add_argument("--exp_name", type=str, required=True)
    return parser.parse_args()

def preprocess_data(test_case_string):
    if f"```python" in test_case_string:
        test_case_string = test_case_string[test_case_string.find(f"```python")+len(f"```python"):]
        test_case_string = test_case_string[:test_case_string.find("```")]
    elif f"```" in test_case_string:
        test_case_string = test_case_string[test_case_string.find("```")+len("```"):]
        test_case_string = test_case_string[:test_case_string.find("```")]
    else:
        print("Error: No code block found")
    return test_case_string