API_KEY = ''

model = "gpt-3.5-turbo-1106"
MBPP_PATH = f"../dataset/{model}_mbpp_temp01.json"
MBPP_PATH_WITH_SUFFIX = MBPP_PATH.replace(".json", "_test.json")

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo-1106")
    parser.add_argument("--language", type=str, default="python")
    parser.add_argument("--base_url", type=str, default=None)
    parser.add_argument("--api_key", type=str, default=None)
    return parser.parse_args()