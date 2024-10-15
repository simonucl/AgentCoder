# python programmer_[humaneval/mbpp].py
# python test_designer_[humaneval/mbpp].py
# python test_executor_[humaneval/mbpp].py

MODEL_PATH="meta-llama/Meta-Llama-3-8B-Instruct"
NUM_GPUS=1
EXP_NAME="gen-llama-3-8b-test-gpt-4o-mini"
wait_for_server() {
  # wait for vllm server to start
  # return 1 if vllm server crashes
  local api_key=token-abc123
  timeout 1200 bash -c '
    until curl -X POST -H "Authorization: Bearer '"$api_key"'" localhost:8000/v1/completions; do
      sleep 1
    done' && return 0 || return 1
}

# python3 -m vllm.entrypoints.openai.api_server --model $MODEL_PATH --dtype auto --api-key token-abc123 --port 8000 --tensor-parallel-size $NUM_GPUS > vllm.log 2>&1 &

python3 -m sglang.launch_server --model-path $MODEL_PATH --api-key token-abc123 --port 8000 --dp $NUM_GPUS > sglang.log 2>&1 &

# Wait for the server to be ready
if ! wait_for_server; then
    echo "VLLM server failed to start or crashed. Exiting."
    pkill -f multiprocessing
    pkill -f $INFERENCE
    exit 1
echo "VLLM server started successfully for $MODEL_NAME"
fi

python3 src/programmer_humaneval.py \
  --model $MODEL_PATH \
  --language python \
  --base_url http://0.0.0.0:8000/v1 \
  --api_key token-abc123 \
  --exp_name $EXP_NAME

python3 src/test_designer_humaneval.py \
  --model gpt-4o-mini \
  --language python \
  --exp_name $EXP_NAME

python3 src/test_executor_humaneval.py \
  --model $MODEL_PATH \
  --language python \
  --base_url http://0.0.0.0:8000/v1 \
  --api_key token-abc123 \
  --exp_name $EXP_NAME

# pkill -f sglang
# pkill -f multiprocessing
# pkill -f vllm
