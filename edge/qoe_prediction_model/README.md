# Deployment

Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```


## Usage

For inference (one JSON file per 5-second window with per-second sub-records):

```bash
python3 scripts/run_inference.py --inference_file ./data/inference_inputs/20250402122044.json \
    --data_folder ./data/historical_dataset --seq_length 5 \
    --model_file ./models/<model_filename>.h5 \
    --scaler_file ./models/scaler.save --augmented
```
