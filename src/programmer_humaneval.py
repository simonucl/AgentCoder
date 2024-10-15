import argparse
import os
import json
from tqdm import tqdm
import copy
import openai
from openai import OpenAI
from constant_value import API_KEY, parse_args
import argparse

# client = OpenAI(api_key=API_KEY)
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
from datasets import load_dataset
# Setting API parameters
# TODO: The 'openai.api_base' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(base_url="https://api.aiohub.org/v1")'
# openai.api_base = "https://api.aiohub.org/v1"

dataset = load_dataset("openai_humaneval",split="test")
dataset = [entry for entry in dataset]

prompt_path = "prompts/humaneval_prompt_update.txt"
with open(prompt_path, "r") as f:
    construct_few_shot_prompt = f.read()

def preprocess_data(completion_string):
    # print(completion_string)
    if f"```python" in completion_string:
        completion_string = completion_string[completion_string.find(f"```python")+len(f"```python"):]
        completion_string = completion_string[:completion_string.find("```")]
    else:
        print("Error: No code block found")
    return completion_string

# Function to fetch completion
def fetch_completion(data_entry, model,lg,times = 1, api_dict=None):
    global construct_few_shot_prompt
    if "need_reproduce" in data_entry.keys() and data_entry["need_reproduce"]==False:
        return data_entry
    prompt = data_entry["prompt"]
    text = f"""
{construct_few_shot_prompt}

**Input Code Snippet**:
```python
{prompt}
```
## Completion 3:
"""
    completions_code = []
    if api_dict:
        client = OpenAI(
            base_url=api_dict['base_url'],
            api_key=api_dict['api_key']
        )
    else:
        client = OpenAI(
            api_key=API_KEY
        )
    for i in range(times):
        while True:
            try:
                completions = client.chat.completions.create(model=model,
                messages=[
                                {"role": "system", "content": "You are a software programmer."},
                                {"role": "user", "content":text},
                ])
                completion = completions.choices[0].message.content
                completion = preprocess_data(completion)

            except Exception as e:
                print(e)
                time.sleep(10)
                completion = ""
            if completion!="":
                break
        completions_code.append(completion)
    data_entry["completion_list"] = completions_code
    return data_entry


def call_fetch_completion_helper(dataset, model,lg, api_dict=None):
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
    if base_url and api_key:
        api_dict = {"base_url": base_url, "api_key": api_key}
    else:
        api_dict = None
    from datasets import load_dataset
    dataset = load_dataset("openai_humaneval",split="test")
    dataset = [entry for entry in dataset]
    with ThreadPoolExecutor(max_workers=32) as executor:
        future_to_entry = {executor.submit(fetch_completion, copy.deepcopy(entry), model, lg, api_dict=api_dict): entry for entry in tqdm(dataset)}
        for future in tqdm(concurrent.futures.as_completed(future_to_entry), total=len(dataset)):
            entry = future_to_entry[future]
            try:
                updated_entry = future.result()
                if updated_entry is not None:
                    idx = dataset.index(entry)
                    dataset[idx] = updated_entry
                else:
                    print(f"Warning: fetch_completion returned None for entry: {entry}")
            except TypeError as e:
                print(f"TypeError occurred: {repr(e)}")
                print(f"Entry causing the error: {entry}")
            except Exception as e:
                print(f"An unexpected error occurred: {repr(e)}")
    # with open(f"./dataset/{model}_{lg}.json", "w") as f:
    with open(f"dataset/{exp_name}.json", "w") as f:
        json.dump(dataset, f, indent=4)
