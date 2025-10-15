import json, os, io, boto3
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# AWS Clients
s3 = boto3.client("s3")
sm_runtime = boto3.client("sagemaker-runtime")

FEATURE_BUCKET = os.getenv("FEATURE_BUCKET", "predictive-maintenance-feature-store")
ENDPOINT_NAME = os.getenv("SAGEMAKER_ENDPOINT", "sagemaker-xgboost-2025-10-12-11-39-56-079")

# ---- Feature computation helpers ----
def compute_basic_stats(series: pd.Series):
    return {
        "mean": series.mean(),
        "std": series.std(),
        "min": series.min(),
        "max": series.max(),
        "rms": np.sqrt(np.mean(np.square(series))),
        "ptp": series.max() - series.min(),
    }

def compute_features(df: pd.DataFrame) -> dict:
    features = {}
    numeric_cols = ["Speed (rpm)", "Load (kg)", "Temperature (℃)", "Vibration (m/s²)", "Current (A)"]
    
    for col in numeric_cols:
        col_safe = (
            col.replace(" ", "_")
               .replace("(", "")
               .replace(")", "")
               .replace("℃", "C")
               .replace("/", "_")
               .replace("²", "2")
        )
        features.update({f"{col_safe}_{stat}": val for stat, val in compute_basic_stats(df[col]).items()})

    features["corr_vibration_load"] = df["Vibration (m/s²)"].corr(df["Load (kg)"])
    features["corr_temp_current"] = df["Temperature (℃)"].corr(df["Current (A)"])
    features["power_mean"] = (df["Speed (rpm)"] * df["Load (kg)"]).mean()
    features["stress_index"] = ((df["Load (kg)"] * df["Vibration (m/s²)"]) / df["Speed (rpm)"]).mean()
    features["thermal_ratio"] = (df["Temperature (℃)"] / df["Load (kg)"]).mean()

    # Metadata
    features["device_id"] = df["device_id"].iloc[0]
    features["window_start"] = df["timestamp"].iloc[0].strftime("%Y-%m-%d %H:%M:%S")
    features["window_end"] = df["timestamp"].iloc[-1].strftime("%Y-%m-%d %H:%M:%S")

    if "Fault" in df.columns:
        features["fault_label"] = df["Fault"].mode()[0]

    return features

# ---- Lambda entrypoint ----
def lambda_handler(event, context):
    try:
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        print(f"📥 Processing new raw batch: s3://{bucket}/{key}")

        # Load raw data from S3
        raw_obj = s3.get_object(Bucket=bucket, Key=key)
        raw_data = raw_obj["Body"].read().decode("utf-8")
        df = pd.read_json(io.StringIO(raw_data))

        if df.empty:
            raise ValueError("Raw data is empty.")

        # Compute features
        features = compute_features(df)

        # Persist to feature store
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        feature_key = f"features/{features['device_id']}/{timestamp}.json"
        s3.put_object(Bucket=FEATURE_BUCKET, Key=feature_key, Body=json.dumps(features))
        print(f"✅ Features saved to s3://{FEATURE_BUCKET}/{feature_key}")

        # Prepare payload for inference — drop extra fields
        model_features = {k: v for k, v in features.items() if k not in ["device_id", "window_start", "window_end", "fault_label"]}
        
        payload = {"instances": [model_features]}
        print(f"📦 Payload feature count: {len(model_features)}")

        # Send to SageMaker endpoint
        response = sm_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType="application/json",
            Body=json.dumps(payload)
        )

        result = json.loads(response["Body"].read().decode("utf-8"))
        print(f"🧠 Model inference result: {result}")

        device_id = features["device_id"]
        inference_key_json = f"inference/{device_id}/{timestamp}.json"
        inference_key_txt = f"knowledge-base-inference/{device_id}/{timestamp}.txt"

        # JSON output
        s3.put_object(
            Bucket=FEATURE_BUCKET,
            Key=inference_key_json,
            Body=json.dumps(result, indent=2)
        )

        # TXT summary (for knowledge base ingestion)
        txt_summary = (
            f"--- Predictive Maintenance Inference Report ---\n"
            f"Device ID: {device_id}\n"
            f"Time Window: {features['window_start']} → {features['window_end']}\n"
            f"Source Data: {features.get('source_key', key)}\n"
            f"Inference Timestamp (UTC): {timestamp}\n\n"

            f"🧠 Model Prediction Summary:\n"
            f"  - Predicted Fault Type: {result.get('predicted_class', 'unknown')}\n"
            f"  - Confidence Score: {result.get('confidence', 'N/A')}\n\n"

            f"Top Class Probabilities:\n" +
            "\n".join([f"  • {k}: {v:.3f}" for k, v in result.get('top_k', {}).items()]) +
            "\n\n"

            f"Operational Feature Snapshot (key stats):\n"
            f"  - Mean Speed (rpm): {features.get('Speed_rpm_mean', 'N/A'):.2f}\n"
            f"  - Mean Load (kg): {features.get('Load_kg_mean', 'N/A'):.2f}\n"
            f"  - Mean Temperature (°C): {features.get('Temperature_C_mean', 'N/A'):.2f}\n"
            f"  - Mean Vibration (m/s²): {features.get('Vibration_m_s2_mean', 'N/A'):.2f}\n"
            f"  - Mean Current (A): {features.get('Current_A_mean', 'N/A'):.2f}\n"
            f"  - Stress Index: {features.get('stress_index', 'N/A'):.4f}\n"
            f"  - Thermal Ratio: {features.get('thermal_ratio', 'N/A'):.4f}\n"
            f"  - Power Mean: {features.get('power_mean', 'N/A'):.2f}\n"
            f"  - Corr(Vibration, Load): {features.get('corr_vibration_load', 'N/A'):.3f}\n"
            f"  - Corr(Temp, Current): {features.get('corr_temp_current', 'N/A'):.3f}\n\n"

            f"🧾 Interpretation:\n"
            f"The model predicts that device {device_id} is exhibiting signs consistent with "
            f"'{result.get('predicted_class', 'unknown')}'. "
            f"This conclusion is based on the observed operational conditions above. "
        )

        # Text output
        s3.put_object(
            Bucket=FEATURE_BUCKET,
            Key=inference_key_txt,
            Body=txt_summary
        )

        print(f"💾 Inference saved to S3 as JSON and TXT")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Feature engineering & inference complete",
                "feature_file": feature_key,
                "inference_json": inference_key_json,
                "inference_txt": inference_key_txt
            })
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
