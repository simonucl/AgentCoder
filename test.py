from datasets import load_dataset
from tqdm import tqdm


dataset = load_dataset("mbpp",name="sanitized",split="test")

print(type(dataset))

# for entry in tqdm(dataset):
#     print(entry)

# print(dataset)

#     # features: ['source_file', 'task_id', 'prompt', 'code', 'test_imports', 'test_list'],
#     # num_rows: 257

# print(dataset[2])

# # print(dataset[0]['source_file'])

# # f = open("../dataset/demofile3.txt", "w")
# # f.write(dataset[0]['source_file'])
# # f.close()