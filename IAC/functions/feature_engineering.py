import json, os, io, boto3
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# AWS Clients
s3 = boto3.client("s3")
sm_runtime = boto3.client("sagemaker-runtime")
ssm = boto3.client("ssm")

FEATURE_BUCKET = os.getenv("FEATURE_BUCKET", "predictive-maintenance-feature-store")

# Function to get endpoint name from Parameter Store
def get_sagemaker_endpoint_name():
    """
    Retrieve the SageMaker endpoint name from Parameter Store
    Returns the endpoint name or falls back to environment variable
    """
    try:
        parameter_name = "/relu/sagemaker/inference-endpoint-name"
        response = ssm.get_parameter(Name=parameter_name)
        endpoint_name = response['Parameter']['Value']
        print(f"✅ Retrieved endpoint name from Parameter Store: {endpoint_name}")
        return endpoint_name
    except ssm.exceptions.ParameterNotFound:
        print("⚠️  Parameter not found in Parameter Store, using fallback")
        fallback = os.getenv("SAGEMAKER_ENDPOINT", "pytorch-inference-2025-10-19-21-03-20-506")
        print(f"📋 Using fallback endpoint: {fallback}")
        return fallback
    except Exception as e:
        print(f"❌ Error retrieving parameter: {str(e)}, using fallback")
        fallback = os.getenv("SAGEMAKER_ENDPOINT", "pytorch-inference-2025-10-19-21-03-20-506")
        print(f"📋 Using fallback endpoint: {fallback}")
        return fallback

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

    # Correlations and derived features
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
        # Get the SageMaker endpoint name from Parameter Store
        endpoint_name = get_sagemaker_endpoint_name()
        
        record = event["Records"][0]
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        print(f"📥 Processing new raw batch: s3://{bucket}/{key}")
        print(f"🎯 Using SageMaker endpoint: {endpoint_name}")

        # Load raw data from S3
        raw_obj = s3.get_object(Bucket=bucket, Key=key)
        raw_data = raw_obj["Body"].read().decode("utf-8")
        df = pd.read_json(io.StringIO(raw_data))

        if df.empty:
            raise ValueError("Raw data is empty.")

        # ---- Compute features for batch ----
        features = compute_features(df)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        device_id = features["device_id"]

        # Save engineered features to feature store
        feature_key = f"features/{device_id}/{timestamp}.json"
        s3.put_object(Bucket=FEATURE_BUCKET, Key=feature_key, Body=json.dumps(features))
        print(f"✅ Features saved to s3://{FEATURE_BUCKET}/{feature_key}")

        # ---- Prepare payload for inference (first data point only, raw column names) ----
        first_point = df.iloc[0]
        model_input = {
            "Speed (rpm)": first_point["Speed (rpm)"],
            "Load (kg)": first_point["Load (kg)"],
            "Temperature (℃)": first_point["Temperature (℃)"],
            "Vibration (m/s²)": first_point["Vibration (m/s²)"],
            "Current (A)": first_point["Current (A)"]
        }

        payload = {"instances": [model_input]}
        print(f"📦 Sending input to model:\n{json.dumps(payload, indent=2)}")

        # ---- Send to SageMaker endpoint ----
        response = sm_runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=json.dumps(payload)
        )

        result = json.loads(response["Body"].read().decode("utf-8"))
        print(f"🧠 Raw Model Response: {json.dumps(result, indent=2)}")

        # ---- Parse inference results ----
        predictions = result.get("predictions", [])
        main_pred = predictions[0] if predictions else {}

        predicted_class = main_pred.get("predicted_class", "unknown")
        confidence = main_pred.get("confidence", 0.0)
        top_k = main_pred.get("top_k", {})
        model_timestamp = main_pred.get("timestamp", datetime.now(timezone.utc).isoformat())

        # ---- Save inference outputs ----
        inference_key_json = f"inference/{device_id}/{timestamp}.json"
        inference_key_txt = f"knowledge-base-inference/{device_id}/{timestamp}.txt"

        # Save full JSON response
        s3.put_object(
            Bucket=FEATURE_BUCKET,
            Key=inference_key_json,
            Body=json.dumps(result, indent=2)
        )

        # Build a well-formatted TXT summary
        txt_summary = [
            "--- Predictive Maintenance Inference Report ---",
            f"Device ID: {device_id}",
            f"Batch Source: {key}",
            f"Time Window: {features['window_start']} → {features['window_end']}",
            f"Inference Timestamp (UTC): {timestamp}",
            "",
            "🧠 Model Prediction Summary:",
            f"  - Predicted Fault: {predicted_class}",
            f"  - Confidence: {confidence:.3f}",
            f"  - Model Timestamp: {model_timestamp}",
            "",
            "Top Class Probabilities:"
        ]
        for cls, prob in top_k.items():
            txt_summary.append(f"  • {cls}: {prob:.3f}")

        txt_summary += [
            "",
            "Operational Feature Snapshot:",
            f"  - Mean Speed (rpm): {features.get('Speed_rpm_mean', 'N/A'):.2f}",
            f"  - Mean Load (kg): {features.get('Load_kg_mean', 'N/A'):.2f}",
            f"  - Mean Temperature (°C): {features.get('Temperature_C_mean', 'N/A'):.2f}",
            f"  - Mean Vibration (m/s²): {features.get('Vibration_m_s2_mean', 'N/A'):.2f}",
            f"  - Mean Current (A): {features.get('Current_A_mean', 'N/A'):.2f}",
            f"  - Stress Index: {features.get('stress_index', 'N/A'):.4f}",
            f"  - Thermal Ratio: {features.get('thermal_ratio', 'N/A'):.4f}",
            f"  - Power Mean: {features.get('power_mean', 'N/A'):.2f}",
            f"  - Corr(Vibration, Load): {features.get('corr_vibration_load', 'N/A'):.3f}",
            f"  - Corr(Temp, Current): {features.get('corr_temp_current', 'N/A'):.3f}",
        ]

        # Include true label if available
        if "fault_label" in features:
            txt_summary.append(f"  - True Fault Label: {features['fault_label']}")

        txt_summary += [
            "",
            "🧾 Interpretation:",
            f"The model suggests that device '{device_id}' shows behavior consistent with '{predicted_class}',",
            "based on current operational parameters and recent feature patterns."
        ]

        s3.put_object(
            Bucket=FEATURE_BUCKET,
            Key=inference_key_txt,
            Body="\n".join(txt_summary)
        )

        print(f"💾 Inference saved to S3 (JSON + TXT)")

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
