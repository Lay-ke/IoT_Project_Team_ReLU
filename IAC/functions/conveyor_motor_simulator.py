import json, os, time, random, io
from datetime import datetime, timezone
import boto3
import numpy as np
import pandas as pd

# ========== CONFIGURATION ==========
DEVICE_ID       = os.getenv("DEVICE_ID", "conveyor-A001")
IOT_TOPIC_BASE  = os.getenv("IOT_TOPIC_BASE", "predictive-maintenance/sensor-data-1")
S3_BUCKET       = os.getenv("S3_BUCKET", "predictive-maintenance-data-1")
N_SAMPLES       = int(os.getenv("N_SAMPLES", "60"))      # ≈1 sample/sec
TRAINING_MODE   = os.getenv("TRAINING_MODE", "True").lower() == "true"

iot = boto3.client("iot-data")
s3  = boto3.client("s3")

# ==================================
def generate_fault_mode() -> str:
    """Weighted random choice of fault mode."""
    faults = ["normal", "ball_bearing", "central_shaft", "pulley","drive_motor", "idler_roller", "belt_slippage"]
    return random.choices(
        faults,
        weights=[0.55, 0.1, 0.08, 0.08, 0.07, 0.06, 0.06],
        k=1
    )[0]



def simulate_conveyor_batch(device_id: str, fault: str, n: int = 60) -> pd.DataFrame:
    """Simulate correlated conveyor sensor readings."""
    rng = np.random.default_rng()

    load = rng.normal(500, 25, n)  # Load around 500kg with noise
    vibration = 0.6 + 0.001*(load - 500) + rng.normal(0, 0.05, n)  # Vibration increases with load
    current = 3.3 + 0.003*(load - 500) + 0.4*vibration + rng.normal(0, 0.05, n)  # Current increases with load

    speed = 120 - 0.05 * (load - 500) + rng.normal(0, 1, n)  # Speed decreases with load

    temperature = 38 + 0.25*current + 0.3*vibration + 0.05*load - 0.3*speed + rng.normal(0, 0.3, n)

    # Adjust for fault-specific behavior
    if fault == "ball_bearing":
        vibration += np.linspace(0, 0.8, n)  # Increase vibration slowly
        temperature += np.linspace(0, 3.0, n)  # Slow temperature rise
    elif fault == "central_shaft":
        vibration += np.sin(np.linspace(0, 4*np.pi, n)) * 0.25  # Shaft oscillation
        temperature += np.linspace(0, 1.5, n)  # Steady temperature rise
        speed += np.sin(np.linspace(0, 2*np.pi, n)) * 0.6  # Speed drops
    elif fault == "pulley":
        vibration += np.sin(np.linspace(0, 8*np.pi, n)) * 0.3  # Periodic vibration
        current += np.random.choice([0, 0.3], size=n, p=[0.9, 0.1])  # Small current spikes
        speed -= np.random.choice([0, 0.5], size=n, p=[0.95, 0.05])  # Slippage affects speed
    elif fault == "drive_motor":
        current += np.linspace(0.2, 0.6, n)  # Increased motor load
        temperature += np.linspace(1.0, 4.0, n)  # Significant temperature rise
        vibration += rng.normal(0, 0.05, n)  # Small random vibrations
    elif fault == "idler_roller":
        vibration += np.linspace(0, 0.3, n)  # Mild vibration increase
        vibration += rng.normal(0, 0.05, n)  # Random noise
        current += rng.normal(0, 0.02, n)  # Minor current increase
    elif fault == "belt_slippage":
        speed -= np.sin(np.linspace(0, 6*np.pi, n)) * 0.8  # Speed drop
        vibration += np.sin(np.linspace(0, 6*np.pi, n)) * 0.2  # Slippage-induced vibration
        current -= np.sin(np.linspace(0, 6*np.pi, n)) * 0.1  # Current drops during slippage

    timestamps = [
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        for _ in range(n)
    ]

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



def batch_publish_to_iot(df: pd.DataFrame):
    """Publish data to IoT Core in batches for efficiency."""
    topic = IOT_TOPIC_BASE
    
    # Collect all messages in a batch
    messages = []
    for _, row in df.iterrows():
        message = row.to_dict()
        messages.append(json.dumps(message))
    

    # Publish batch to IoT Core in one API call
    try:
        iot.publish(
            topic=topic,
            qos=0,
            payload="[" + ",".join(messages) + "]"  # JSON array of messages
        )
        print(f"✅ Published {len(messages)} messages to {topic}")
        return True
    except Exception as e:
        print(f"Iot Core publish failed")
        return e


def upload_to_s3_batch(df: pd.DataFrame):
    """Upload batch to S3 in a single call."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    key = f"conveyor_batches/{timestamp}_{DEVICE_ID}.json"

    # Convert entire DataFrame to JSON in memory
    json_data = df.to_json(orient="records", lines=False)

    try:
        # Upload the single JSON object to S3
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=json_data)
        print(f"✅ Uploaded batch to s3://{S3_BUCKET}/{key}")
    except Exception as e:
        print(f"Upload to s3 bucket failed")
        return e


def lambda_handler(event, context):
    """Main Lambda entrypoint."""
    fault = generate_fault_mode()
    df = simulate_conveyor_batch(DEVICE_ID, fault, N_SAMPLES)
    print(f"🚧 Simulated {N_SAMPLES} samples from {DEVICE_ID} with fault: {fault}")
    print(f"📊 {len(df)} samples generated.")
    print(df.head(3))

    mode = "TRAINING" if TRAINING_MODE else "INFERENCE"
    print(f"🌀 Running in {mode} mode — Fault label {'included' if TRAINING_MODE else 'excluded'}.")

    # Quick correlation check
    corr = df[["Load (kg)", "Current (A)", "Vibration (m/s²)", "Temperature (℃)"]].corr()
    print("Correlation matrix:\n", corr.round(2))

    batch_publish_to_iot(df)
    upload_to_s3_batch(df)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "device_id": DEVICE_ID,
            "mode": mode,
            "samples_generated": len(df),
            "avg_vibration": round(df["Vibration (m/s²)"].mean(), 3),
            "avg_current": round(df["Current (A)"].mean(), 3),
            "fault_simulated": fault if TRAINING_MODE else "N/A"
        })
    }
