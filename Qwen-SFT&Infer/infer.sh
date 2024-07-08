MODEL_NAME="qwen_act_chat_ep3"
MODEL_PATH="./qwen_act_chat_ep3"

nohup python infer.py \
    --model_path $MODEL_PATH \
    --data_path ./data/smartphone_test_instructions_related.json \
    --img_path ./data/smartphone_test_images.parquet \
    --output_path ./infer_results/$MODEL_NAME/smartphone.json \
    --device cuda:0 \
    > logs/$MODEL_NAME-smartphone.log 2>&1 &

nohup python infer.py \
    --model_path $MODEL_PATH \
    --data_path ./data/web-single_test_instructions_related.json \
    --img_path ./data/web-single_test_images.parquet \
    --output_path ./infer_results/$MODEL_NAME/web-single.json \
    --device cuda:1 \
    > logs/$MODEL_NAME-web-single.log 2>&1 &

nohup python infer.py \
    --model_path $MODEL_PATH \
    --data_path ./data/web-multi_test_instructions_relatedjson \
    --img_path ./data/web-multi_test_images.parquet \
    --output_path ./infer_results/$MODEL_NAME/web-multi.json \
    --device cuda:2 \
    > logs/$MODEL_NAME-web-multi.log 2>&1 &