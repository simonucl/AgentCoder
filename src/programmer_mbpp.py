import argparse
import os
import json
from tqdm import tqdm
import copy
import openai
from openai import OpenAI
from constant_value import API_KEY, MBPP_PATH, parse_args

client = OpenAI(api_key=API_KEY)
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

# Setting API parameters
# TODO: The 'openai.api_base' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(base_url="https://api.aiohub.org/v1")'
# openai.api_base = "https://api.aiohub.org/v1"

prompt_path = "prompts/mbpp_prompt_update.txt"
with open(prompt_path, "r") as f:
    construct_few_shot_prompt = f.read()

def preprocess_data(data,lg):
    if f"```{lg}" in data["completion"]:
        data["completion"] = data["completion"][data["completion"].find(f"```{lg}")+len(f"```{lg}"):]
        data["completion"] = data["completion"][:data["completion"].find("```")]
    else:
        print(data["task_id"])
    return data

# Function to fetch completion
def fetch_completion(data_entry, model,lg):
    global construct_few_shot_prompt
    if "passed" in data_entry.keys() and data_entry["passed"] == True:
        return data_entry
    prompt = data_entry["prompt"]
    test_case = data_entry["test_list"]
    # code = data_entry["completion"]
    tests = ""
    for test in test_case:
        tests+="\n"+test
    text = f"""
construct_few_shot_prompt

**Task**:
```python
{prompt}
```
Your code should pass these tests:
```python
{tests}
```
"""
    try:
        completions = client.chat.completions.create(model = model,
        stream=False,
        messages=[
                {"role": "system", "content": "You are a code developer."},
                {"role": "user", "content":text},
        ],
        timeout=100)
        data_entry["completion"] = completions.choices[0].message.content
        # print("completion===============", data_entry["completion"], "\n", "\n")
        data_entry = preprocess_data(data_entry,lg)
        return data_entry
    except Exception as e:
        print(repr(e))
        data_entry["completion"] = ""
        return data_entry

def fix_bug(data_entry, model,lg,preprocess_data = preprocess_data):
    if "passed" in data_entry.keys() and data_entry["passed"] == True:
        return data_entry
    else:
        gpt_prompt = (
            "Please re-completion the code to fix the error message. "+
            f"\nHere is the previous version:\n```{lg}\n" + 
            data_entry['completion'] + f"\n```\nWhen we use this test cases: ```{lg}\n"+data_entry["test_case"]+f"\n``` to evaluate the code. It raise the error:\n```{lg}\n" + data_entry["result"] +
            f"\n```\nPlease fix the bug and return the code. The re-completion code should in triple backticks format(i.e., in ```{lg} ```)."
        )
        try:
            completions = client.chat.completions.create(model = model,
            stream=False,
            messages=[
                        {"role": "system", "content": "You are a code developer assistant."},
                        {"role": "user", "content":gpt_prompt},
            ],
            timeout=100)
            data_entry["completion"] = completions.choices[0].message.content
            data_entry = preprocess_data(data_entry,"py")
        except Exception as e:
            print(repr(e))
    return data_entry

def call_fix_bug(dataset, model,lg):
    print("Fixing bug...")
    with ThreadPoolExecutor() as executor:
        future_to_entry = {executor.submit(fetch_completion, copy.deepcopy(entry), model, lg): entry for entry in tqdm(dataset)}
        for future in tqdm(concurrent.futures.as_completed(future_to_entry)):
            entry = future_to_entry[future]
            try:
                updated_entry = future.result()
                idx = dataset.index(entry)
                dataset[idx] = updated_entry
            except Exception as e:
                print(repr(e))
    return dataset

def call_completion(dataset, model,lg):
    print("Fixing bug...")
    with ThreadPoolExecutor() as executor:
        future_to_entry = {executor.submit(fetch_completion, copy.deepcopy(entry), model, lg): entry for entry in tqdm(dataset)}
        for future in tqdm(concurrent.futures.as_completed(future_to_entry)):
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
    if base_url and api_key:
        api_dict = {"base_url": base_url, "api_key": api_key}
    else:
        api_dict = None
    from datasets import load_dataset
    dataset = load_dataset("mbpp",name="sanitized",split="test")
    dataset = [entry for entry in dataset]
    # with open(path, "r") as f:
    #     dataset = json.load(f)
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_entry = {executor.submit(fetch_completion, copy.deepcopy(entry), model, lg): entry for entry in dataset}
        # data_entry = fetch_completion(copy.deepcopy(dataset[0]), model, lg)
        # print(data_entry)
        # print(data_entry)
        # future_to_entry = {executor.submit(fetch_completion, copy.deepcopy(dataset[0]), model, lg)}
        # print(type(future_to_entry))
        for future in tqdm(concurrent.futures.as_completed(future_to_entry)):
            # print(type(future_to_entry))
            entry = future_to_entry[future]
            # print(entry)
            try:
                updated_entry = future.result()
                # print(updated_entry)
                idx = dataset.index(entry)
                dataset[idx] = updated_entry
            except Exception as e:
                print(repr(e))

    with open(MBPP_PATH, "w") as f:
        json.dump(dataset, f, indent=4)
