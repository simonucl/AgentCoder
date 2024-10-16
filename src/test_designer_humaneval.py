import argparse
import os
import json
from tqdm import tqdm
import copy
from openai import OpenAI
from constant_value import API_KEY

client = OpenAI(api_key=API_KEY)
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
from datasets import load_dataset
from constant_value import parse_args, preprocess_data
# Setting API parameters

dataset = load_dataset("openai_humaneval",split="test")
dataset = [entry for entry in dataset]

prompt_path = "prompts/test_designer_humaneval_prompt.txt"
with open(prompt_path, "r") as f:
    construct_few_shot_prompt = f.read()

# def preprocess_data(test_case_string):
#     if f"```python" in test_case_string:
#         test_case_string = test_case_string[test_case_string.find(f"```python")+len(f"```python"):]
#         test_case_string = test_case_string[:test_case_string.find("```")]
#     elif f"```" in test_case_string:
#         test_case_string = test_case_string[test_case_string.find("```")+len("```"):]
#         test_case_string = test_case_string[:test_case_string.find("```")]
#     else:
#         print("Error: No code block found")
#     return test_case_string

# Function to fetch completion
def fetch_completion(data_entry, model, lg,times=1, api_dict=None):
    global construct_few_shot_prompt
    if "need_reproduce" in data_entry.keys() and data_entry["need_reproduce"]==False:
        return data_entry
    prompt = data_entry["prompt"]
    entry_point = data_entry["entry_point"]

    text = f"""
{construct_few_shot_prompt}

**Input Code Snippet**:
```python
{prompt}
```
"""
    test_case_list = []
    if api_dict:
        client = OpenAI(api_key=api_dict["api_key"], base_url=api_dict["base_url"])
    else:
        client = OpenAI(api_key=API_KEY)

    for i in range(times):
        while True:
            try:
                completions = client.chat.completions.create(
                    model=model,
                stream=False,
                messages=[
                                {"role": "system", "content": "You are a code developer assistant."},
                                {"role": "user", "content":text},
                ],
                timeout=100,
                temperature=0)
                test_case = completions.choices[0].message.content
                test_case = preprocess_data(test_case)
            except Exception as e:
                time.sleep(20)
                print(e)
                test_case = ""
            if test_case!="":
                break
        test_case_list.append(test_case)
    data_entry["test_case_list"] = test_case_list
    return data_entry

def call_fetch_test_completion_helper(dataset, model,lg, api_dict=None):
    print("Fixing bug...")
    with ThreadPoolExecutor(max_workers=32) as executor:
        future_to_entry = {executor.submit(fetch_completion, copy.deepcopy(entry), model, lg, api_dict=api_dict): entry for entry in tqdm(dataset)}
        for future in tqdm(concurrent.futures.as_completed(future_to_entry), total=len(dataset)):
            entry = future_to_entry[future]
            try:
                updated_entry = future.result()
                idx = dataset.index(entry)
                dataset[idx] = updated_entry
            except Exception as e:
                print(repr(e))
    return dataset


if __name__ == "__main__":
    args = parse_args()
    model = args.model
    lg = args.language
    base_url = args.base_url
    api_key = args.api_key
    exp_name = args.exp_name
    times = args.times
    if base_url and api_key:
        api_dict = {"base_url": base_url, "api_key": api_key}
    else:
        api_dict = None
    from datasets import load_dataset
    # with open(f"./dataset/{model}_{lg}.json", "r") as f:
    with open(f"dataset/{exp_name}.json", "r") as f:
        dataset = json.load(f)
    dataset = [entry for entry in dataset]
    with ThreadPoolExecutor(max_workers=32) as executor:
        future_to_entry = {executor.submit(fetch_completion, copy.deepcopy(entry), model, lg, times, api_dict=api_dict): entry for entry in tqdm(dataset)}
        for future in tqdm(concurrent.futures.as_completed(future_to_entry), total=len(dataset), desc="Generating test cases"):
            entry = future_to_entry[future]
            try:
                updated_entry = future.result()
                idx = dataset.index(entry)
                dataset[idx] = updated_entry
            except Exception as e:
                print(repr(e))

    # with open(f"./dataset/{model}_{lg}.json", "w") as f:
    with open(f"dataset/{exp_name}.json", "w") as f:
        json.dump(dataset, f, indent=4)
