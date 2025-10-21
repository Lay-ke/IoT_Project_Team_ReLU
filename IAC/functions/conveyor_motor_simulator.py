import json, os, io, random
from datetime import datetime, timezone
import boto3
import numpy as np
import pandas as pd

# ==========================================================
# CONFIGURATION
# ==========================================================
DEVICE_ID        = os.getenv("DEVICE_ID", "conveyor-A001")
IOT_TOPIC_BASE   = os.getenv("IOT_TOPIC_BASE", "predictive-maintenance/sensor-data-1")
S3_BUCKET        = os.getenv("S3_BUCKET", "predictive-maintenance-data-1")
REFERENCE_BUCKET = os.getenv("REFERENCE_BUCKET", "predictive-maintenance-data-1")
REFERENCE_KEY    = os.getenv("REFERENCE_DATA_KEY", "raw_dataset/conveyor_fault_dataset.csv")
N_SAMPLES        = int(os.getenv("N_SAMPLES", "60"))
TRAINING_MODE    = os.getenv("TRAINING_MODE", "True").lower() == "true"

iot = boto3.client("iot-data")
s3  = boto3.client("s3")

# ==========================================================
# LOAD AND CLEAN REFERENCE DATA
# ==========================================================
def load_reference_data_from_s3(bucket: str, key: str) -> pd.DataFrame | None:
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(io.BytesIO(obj["Body"].read()))
        print(f"✅ Loaded reference dataset from s3://{bucket}/{key} ({len(df)} rows)")
    except Exception as e:
        print(f"⚠️ Could not load reference dataset: {e}")
        return None

    df.columns = [c.strip() for c in df.columns]
    if "Fault" in df.columns:
        df["Fault"] = df["Fault"].astype(str).str.strip().str.lower()

    numeric_cols = ["Load (kg)", "Speed (rpm)", "Current (A)", "Vibration (m/s²)", "Temperature (℃)"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=numeric_cols)
    print(f"🧹 Cleaned dataset: {len(df)} valid numeric rows remain.")
    return df


# ==========================================================
# COMPUTE FEATURE BASELINES
# ==========================================================
def compute_feature_baselines(df: pd.DataFrame) -> dict:
    numeric_cols = ["Load (kg)", "Speed (rpm)", "Current (A)", "Vibration (m/s²)", "Temperature (℃)"]
    baselines = {}
    for fault, group in df.groupby("Fault"):
        baselines[fault] = {
            "mean": group[numeric_cols].mean().to_dict(),
            "std": group[numeric_cols].std().to_dict(),
        }
    print(f"✅ Computed baselines for {len(baselines)} fault classes: {list(baselines.keys())}")
    return baselines


# ==========================================================
# RANDOM SAMPLE PICKER
# ==========================================================
def pick_random_sample(df: pd.DataFrame) -> pd.Series:
    """Pick a random sample row (entire data) from the dataset."""
    sample_row = df.sample(1).iloc[0]
    fault = str(sample_row["Fault"]).lower()
    print(f"Sample data: {sample_row}")
    print(f"🎯 Picked random sample for fault class: {fault}")
    return sample_row


# ==========================================================
# SIMULATION LOGIC
# ==========================================================
def simulate_conveyor_batch(device_id: str, sample_row: pd.Series, baselines: dict, n: int = 60) -> pd.DataFrame:
    fault = sample_row["Fault"]
    rng = np.random.default_rng()
    base = baselines.get(fault, baselines.get("normal", {}))
    mu, sigma = base["mean"], base["std"]

    # Generate synthetic samples
    load = rng.normal(mu["Load (kg)"], sigma["Load (kg)"], n-1)
    speed = rng.normal(mu["Speed (rpm)"], sigma["Speed (rpm)"], n-1)
    current = rng.normal(mu["Current (A)"], sigma["Current (A)"], n-1)
    vibration = rng.normal(mu["Vibration (m/s²)"], sigma["Vibration (m/s²)"], n-1)
    temperature = rng.normal(mu["Temperature (℃)"], sigma["Temperature (℃)"], n-1)

    t = np.linspace(0, 2*np.pi, n-1)

    # Amplified distinct patterns
    if fault == "ball_bearing":
        vibration += 0.8 * np.sin(3*t) + rng.normal(0, 0.3, n-1)
        temperature += np.linspace(0, 5, n-1)
        current += rng.normal(0.1, 0.05, n-1)
    elif fault == "central_shaft":
        vibration += 0.6 * np.sin(5*t) + rng.normal(0, 0.25, n-1)
        temperature += np.linspace(0, 4, n-1)
        speed += 0.8 * np.sin(2*t)
    elif fault == "pulley":
        vibration += np.sin(10*t) * 1.0
        current += rng.normal(0.4, 0.15, n-1)
        speed -= rng.normal(0.7, 0.2, n-1)
        temperature += np.linspace(0, 2.5, n-1)
    elif fault == "drive_motor":
        current += np.linspace(0.3, 1.0, n-1)
        vibration += rng.normal(0.2, 0.1, n-1)
        temperature += np.linspace(2.0, 6.0, n-1)
        load += rng.normal(0.3, 0.15, n-1)
    elif fault == "idler_roller":
        vibration += 0.5 * np.sin(4*t) + rng.normal(0, 0.2, n-1)
        current += rng.normal(0.1, 0.05, n-1)
        temperature += np.linspace(0, 2, n-1)
    elif fault == "belt_slippage":
        speed -= 1.5 * np.sin(3*t) + rng.normal(0, 0.4, n-1)
        vibration += 0.6 * np.sin(3*t + np.pi/4)
        current -= 0.3 * np.sin(3*t)
        load -= rng.normal(0.4, 0.15, n-1)
        temperature += rng.normal(0.5, 0.2, n-1)

    timestamps = [datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ") for _ in range(n-1)]

    sim_df = pd.DataFrame({
        "timestamp": timestamps,
        "device_id": device_id,
        "Speed (rpm)": speed,
        "Load (kg)": load,
        "Temperature (℃)": temperature,
        "Vibration (m/s²)": vibration,
        "Current (A)": current,
        "Fault": fault,
    })

    # Prepend the real sample as first row
    real_row = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "device_id": device_id,
        "Speed (rpm)": sample_row["Speed (rpm)"],
        "Load (kg)": sample_row["Load (kg)"],
        "Temperature (℃)": sample_row["Temperature (℃)"],
        "Vibration (m/s²)": sample_row["Vibration (m/s²)"],
        "Current (A)": sample_row["Current (A)"],
        "Fault": fault,
    }
    df = pd.concat([pd.DataFrame([real_row]), sim_df], ignore_index=True)

    if not TRAINING_MODE:
        df.drop(columns=["Fault"], inplace=True)

    return df


# ==========================================================
# AWS PUBLISH HELPERS
# ==========================================================
def batch_publish_to_iot(df: pd.DataFrame):
    topic = IOT_TOPIC_BASE
    messages = [json.dumps(row.to_dict()) for _, row in df.iterrows()]
    try:
        iot.publish(topic=topic, qos=0, payload="[" + ",".join(messages) + "]")
        print(f"✅ Published {len(messages)} messages to {topic}")
    except Exception as e:
        print(f"⚠️ IoT Core publish failed: {e}")


def upload_to_s3_batch(df: pd.DataFrame):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    key = f"conveyor_batches/{timestamp}_{DEVICE_ID}.json"
    json_data = df.to_json(orient="records", lines=False)
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json_data)
        print(f"✅ Uploaded batch to s3://{S3_BUCKET}/{key}")
    except Exception as e:
        print(f"⚠️ Upload to s3 failed: {e}")


# ==========================================================
# MAIN HANDLER
# ==========================================================
def lambda_handler(event=None, context=None):
    ref_df = load_reference_data_from_s3(REFERENCE_BUCKET, REFERENCE_KEY)
    if ref_df is None or ref_df.empty:
        print("❌ Reference dataset missing.")
        return {"statusCode": 500, "body": json.dumps({"error": "Reference dataset missing"})}

    baselines = compute_feature_baselines(ref_df)

    sample_row = pick_random_sample(ref_df)
    df = simulate_conveyor_batch(DEVICE_ID, sample_row, baselines, N_SAMPLES)

    print(f"🚧 Simulated {len(df)} samples (fault: {sample_row['Fault']})")
    print(df.head(3))

    batch_publish_to_iot(df)
    upload_to_s3_batch(df)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "device_id": DEVICE_ID,
            "samples_generated": len(df),
            "fault_simulated": sample_row["Fault"],
            "avg_vibration": round(df["Vibration (m/s²)"].mean(), 3),
            "avg_current": round(df["Current (A)"].mean(), 3)
        }),
    }
