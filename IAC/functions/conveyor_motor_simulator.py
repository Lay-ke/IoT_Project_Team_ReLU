import json, os, io, time, random
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
REFERENCE_KEY    = os.getenv("REFERENCE_DATA_KEY", "raw_dataset/final_conveyor_fault_dataset.csv")
N_SAMPLES        = int(os.getenv("N_SAMPLES", "60"))
TRAINING_MODE    = os.getenv("TRAINING_MODE", "True").lower() == "true"

iot = boto3.client("iot-data")
s3  = boto3.client("s3")

# ==========================================================
# LOAD AND CLEAN REFERENCE DATA
# ==========================================================
def load_reference_data_from_s3(bucket: str, key: str) -> pd.DataFrame | None:
    """Load reference dataset from S3 safely and clean it for numeric consistency."""
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(io.BytesIO(obj["Body"].read()))
        print(f"✅ Loaded reference dataset from s3://{bucket}/{key} ({len(df)} rows)")
    except Exception as e:
        print(f"⚠️ Could not load reference dataset: {e}")
        return None

    # --- basic cleanup ---
    df.columns = [c.strip() for c in df.columns]  # strip spaces from headers
    if "Fault" in df.columns:
        df["Fault"] = df["Fault"].astype(str).str.strip().str.lower()

    numeric_cols = ["Load (kg)", "Speed (rpm)", "Current (A)", "Vibration (m/s²)", "Temperature (℃)"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # drop rows missing numeric data
    df = df.dropna(subset=numeric_cols)

    print(f"🧹 Cleaned dataset: {len(df)} valid numeric rows remain.")
    return df


# ==========================================================
# COMPUTE FEATURE BASELINES
# ==========================================================
def compute_feature_baselines(df: pd.DataFrame) -> dict:
    """Compute mean/std/correlation per fault class."""
    numeric_cols = ["Load (kg)", "Speed (rpm)", "Current (A)", "Vibration (m/s²)", "Temperature (℃)"]
    baselines = {}

    for fault, group in df.groupby("Fault"):
        baselines[fault] = {
            "mean": group[numeric_cols].mean().to_dict(),
            "std": group[numeric_cols].std().to_dict(),
            "corr": group[numeric_cols].corr().to_dict(),
        }

    print(f"✅ Computed baselines for {len(baselines)} fault classes: {list(baselines.keys())}")
    return baselines


# ==========================================================
# FAULT MODE SELECTOR
# ==========================================================
def generate_fault_mode() -> str:
    faults = ["normal", "ball_bearing", "central_shaft", "pulley", "drive_motor", "idler_roller", "belt_slippage"]
    return random.choices(faults, weights=[0.55, 0.1, 0.08, 0.08, 0.07, 0.06, 0.06], k=1)[0]


# ==========================================================
# SIMULATION LOGIC
# ==========================================================
def simulate_conveyor_batch(device_id: str, fault: str, baselines: dict, n: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng()

    base = baselines.get(fault, baselines["normal"])  # fallback to normal if fault missing
    mu, sigma = base["mean"], base["std"]

    load = rng.normal(mu["Load (kg)"], sigma["Load (kg)"], n)
    speed = rng.normal(mu["Speed (rpm)"], sigma["Speed (rpm)"], n)
    current = rng.normal(mu["Current (A)"], sigma["Current (A)"], n)
    vibration = rng.normal(mu["Vibration (m/s²)"], sigma["Vibration (m/s²)"], n)
    temperature = rng.normal(mu["Temperature (℃)"], sigma["Temperature (℃)"], n)

    # ===== Fault-specific modifiers =====
    if fault == "ball_bearing":
        vibration += np.linspace(0, 0.8, n) + rng.normal(0, 0.15, n)
        temperature += np.linspace(0, 3.0, n)

    elif fault == "central_shaft":
        vibration += np.sin(np.linspace(0, 4*np.pi, n)) * 0.25
        temperature += np.linspace(0, 1.5, n)
        
        speed += np.sin(np.linspace(0, 2*np.pi, n)) * 0.6

    elif fault == "pulley":
        vibration += np.sin(np.linspace(0, 8*np.pi, n)) * 0.3
        current += np.random.choice([0, 0.3], size=n, p=[0.9, 0.1])
        speed -= np.random.choice([0, 0.5], size=n, p=[0.95, 0.05])

    elif fault == "drive_motor":
        current += np.linspace(0.2, 0.6, n)
        temperature += np.linspace(1.0, 4.0, n)
        vibration += rng.normal(0, 0.05, n)

    elif fault == "idler_roller":
        vibration += np.linspace(0, 0.3, n) + rng.normal(0, 0.05, n)
        current += rng.normal(0, 0.02, n)

    elif fault == "belt_slippage":
        speed -= np.sin(np.linspace(0, 6*np.pi, n)) * 0.8
        vibration += np.sin(np.linspace(0, 6*np.pi, n)) * 0.2
        current -= np.sin(np.linspace(0, 6*np.pi, n)) * 0.1

    timestamps = [datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ") for _ in range(n)]

    df = pd.DataFrame({
        "timestamp": timestamps,
        "device_id": device_id,
        "Speed (rpm)": speed,
        "Load (kg)": load,
        "Temperature (℃)": temperature,
        "Vibration (m/s²)": vibration,
        "Current (A)": current,
        "Fault": fault,
    })

    if not TRAINING_MODE:
        df.drop(columns=["Fault"], inplace=True)

    return df


# ==========================================================
# AWS PUBLISH HELPERS
# ==========================================================
def batch_publish_to_iot(df: pd.DataFrame):
    """Publish data to IoT Core in a batch."""
    topic = IOT_TOPIC_BASE
    messages = [json.dumps(row.to_dict()) for _, row in df.iterrows()]
    try:
        iot.publish(topic=topic, qos=0, payload="[" + ",".join(messages) + "]")
        print(f"✅ Published {len(messages)} messages to {topic}")
    except Exception as e:
        print(f"⚠️ IoT Core publish failed: {e}")


def upload_to_s3_batch(df: pd.DataFrame):
    """Upload batch JSON to S3."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    key = f"conveyor_batches/{timestamp}_{DEVICE_ID}.json"
    json_data = df.to_json(orient="records", lines=False)
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json_data)
        print(f"✅ Uploaded batch to s3://{S3_BUCKET}/{key}")
    except Exception as e:
        print(f"⚠️ Upload to s3 failed: {e}")


# ==========================================================
# MAIN LAMBDA HANDLER
# ==========================================================
def lambda_handler(event=None, context=None):
    ref_df = load_reference_data_from_s3(REFERENCE_BUCKET, REFERENCE_KEY)
    if ref_df is None:
        print("❌ No reference dataset available. Exiting.")
        return {"statusCode": 500, "body": json.dumps({"error": "Reference dataset missing"})}

    baselines = compute_feature_baselines(ref_df)
    fault = generate_fault_mode()
    df = simulate_conveyor_batch(DEVICE_ID, fault, baselines, N_SAMPLES)

    print(f"🚧 Simulated {N_SAMPLES} samples from {DEVICE_ID} (fault: {fault})")
    print(df.head(3))
    print("Correlation matrix:\n", df[["Load (kg)", "Current (A)", "Vibration (m/s²)", "Temperature (℃)"]].corr().round(2))

    batch_publish_to_iot(df)
    upload_to_s3_batch(df)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "device_id": DEVICE_ID,
            "samples_generated": len(df),
            "fault_simulated": fault,
            "avg_vibration": round(df["Vibration (m/s²)"].mean(), 3),
            "avg_current": round(df["Current (A)"].mean(), 3)
        }),
    }
