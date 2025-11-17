"""
Data Simulation Utilities for FaultCast Development

This module provides utilities for simulating sensor data and equipment states
for development and testing purposes.
"""

import random
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional


class ConveyorDataSimulator:
    """
    Simulates realistic conveyor belt sensor data for FaultCast system testing.
    
    Features:
    - Realistic vibration, temperature, current, and speed readings
    - Configurable anomaly injection for testing scenarios
    - Multiple machine configurations
    - Time series data generation
    - Anomaly scenario management
    """
    
    def __init__(self, custom_configs: Optional[Dict[str, Any]] = None):
        # Use custom configs if provided, otherwise use defaults
        default_configs = {
            "CONV_001": {
                "location": "Production Line A",
                "belt_width": 1200,  # mm
                "normal_ranges": {
                    "vibration": {"min": 1.5, "max": 2.5, "unit": "mm/s"},
                    "temperature": {"min": 65, "max": 75, "unit": "°C"},
                    "current": {"min": 10, "max": 14, "unit": "A"},
                    "speed": {"min": 1150, "max": 1250, "unit": "rpm"}
                }
            },
            "CONV_002": {
                "location": "Production Line B", 
                "belt_width": 800,
                "normal_ranges": {
                    "vibration": {"min": 1.0, "max": 2.0, "unit": "mm/s"},
                    "temperature": {"min": 60, "max": 70, "unit": "°C"},
                    "current": {"min": 8, "max": 12, "unit": "A"},
                    "speed": {"min": 950, "max": 1050, "unit": "rpm"}
                }
            }
        }
        
        self.machine_configs = custom_configs if custom_configs else default_configs
        
        self.anomaly_scenarios = {
            "bearing_wear": {
                "affected_sensors": ["vibration", "temperature"],
                "vibration_multiplier": 1.8,
                "temperature_increase": 15
            },
            "belt_misalignment": {
                "affected_sensors": ["vibration", "current"],
                "vibration_multiplier": 1.5,
                "current_multiplier": 1.3
            },
            "motor_overload": {
                "affected_sensors": ["current", "temperature"],
                "current_multiplier": 1.6,
                "temperature_increase": 20
            },
            "belt_slippage": {
                "affected_sensors": ["speed", "current"],
                "speed_multiplier": 0.8,
                "current_multiplier": 1.4
            }
        }
    
    def generate_sensor_reading(self, machine_id: str = "CONV_001", 
                              anomaly_type: str = None, 
                              anomaly_severity: float = 1.0) -> Dict[str, Any]:
        """
        Generate a single sensor reading
        
        Args:
            machine_id: Machine identifier
            anomaly_type: Type of anomaly to inject (optional)
            anomaly_severity: Severity multiplier for anomaly (1.0 = normal, >1.0 = more severe)
            
        Returns:
            Sensor reading data
        """
        if machine_id not in self.machine_configs:
            machine_id = "CONV_001"
        
        config = self.machine_configs[machine_id]
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Generate base readings within normal ranges
        sensors = {}
        for sensor_type, ranges in config["normal_ranges"].items():
            base_value = random.uniform(ranges["min"], ranges["max"])
            
            # Add small random variation
            variation = random.uniform(-0.05, 0.05)
            value = base_value * (1 + variation)
            
            sensors[sensor_type] = {
                "value": round(value, 2),
                "unit": ranges["unit"],
                "timestamp": timestamp,
                "quality": "good"
            }
        
        # Apply anomaly if specified
        if anomaly_type and anomaly_type in self.anomaly_scenarios:
            sensors = self._apply_anomaly(sensors, anomaly_type, anomaly_severity)
        
        return {
            "machine_id": machine_id,
            "location": config["location"],
            "timestamp": timestamp,
            "sensors": sensors,
            "anomaly_injected": anomaly_type,
            "data_source": "simulator"
        }
    
    def generate_time_series(self, machine_id: str = "CONV_001", 
                           duration_hours: int = 24, 
                           interval_minutes: int = 5,
                           anomaly_events: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Generate time series sensor data
        
        Args:
            machine_id: Machine identifier
            duration_hours: Duration of data to generate
            interval_minutes: Interval between readings
            anomaly_events: List of anomaly events to inject
            
        Returns:
            List of sensor readings over time
        """
        readings = []
        start_time = datetime.now(timezone.utc) - timedelta(hours=duration_hours)
        current_time = start_time
        end_time = datetime.now(timezone.utc)
        
        anomaly_events = anomaly_events or []
        
        while current_time <= end_time:
            # Check if any anomaly should be active at this time
            active_anomaly = None
            anomaly_severity = 1.0
            
            for event in anomaly_events:
                event_start = datetime.fromisoformat(event["start_time"].replace("Z", "+00:00"))
                event_end = datetime.fromisoformat(event["end_time"].replace("Z", "+00:00"))
                
                if event_start <= current_time <= event_end:
                    active_anomaly = event["anomaly_type"]
                    anomaly_severity = event.get("severity", 1.0)
                    break
            
            # Generate reading
            reading = self.generate_sensor_reading(
                machine_id=machine_id,
                anomaly_type=active_anomaly,
                anomaly_severity=anomaly_severity
            )
            
            # Update timestamp to current iteration time
            reading["timestamp"] = current_time.isoformat().replace('+00:00', 'Z')
            for sensor_data in reading["sensors"].values():
                sensor_data["timestamp"] = reading["timestamp"]
            
            readings.append(reading)
            current_time += timedelta(minutes=interval_minutes)
        
        return readings
    
    def _apply_anomaly(self, sensors: Dict[str, Any], 
                      anomaly_type: str, 
                      severity: float) -> Dict[str, Any]:
        """Apply anomaly effects to sensor readings"""
        scenario = self.anomaly_scenarios[anomaly_type]
        
        for sensor_type in scenario["affected_sensors"]:
            if sensor_type in sensors:
                if f"{sensor_type}_multiplier" in scenario:
                    multiplier = scenario[f"{sensor_type}_multiplier"]
                    # Apply severity scaling
                    adjusted_multiplier = 1 + (multiplier - 1) * severity
                    sensors[sensor_type]["value"] *= adjusted_multiplier
                    sensors[sensor_type]["value"] = round(sensors[sensor_type]["value"], 2)
                
                if f"{sensor_type}_increase" in scenario:
                    increase = scenario[f"{sensor_type}_increase"] * severity
                    sensors[sensor_type]["value"] += increase
                    sensors[sensor_type]["value"] = round(sensors[sensor_type]["value"], 2)
                
                # Mark sensor as affected by anomaly
                sensors[sensor_type]["anomaly_affected"] = True
        
        return sensors
    
    def create_anomaly_scenario(self, anomaly_type: str, 
                               start_offset_hours: int = -2,
                               duration_hours: int = 1,
                               severity: float = 1.5) -> Dict[str, Any]:
        """
        Create an anomaly scenario for time series generation
        
        Args:
            anomaly_type: Type of anomaly
            start_offset_hours: Hours before now when anomaly starts (negative = past)
            duration_hours: Duration of anomaly
            severity: Severity multiplier
            
        Returns:
            Anomaly event dictionary
        """
        start_time = datetime.now(timezone.utc) + timedelta(hours=start_offset_hours)
        end_time = start_time + timedelta(hours=duration_hours)
        
        return {
            "anomaly_type": anomaly_type,
            "start_time": start_time.isoformat().replace('+00:00', 'Z'),
            "end_time": end_time.isoformat().replace('+00:00', 'Z'),
            "severity": severity,
            "description": f"{anomaly_type.replace('_', ' ').title()} event"
        }
    
    def save_sample_data(self, filename: str = "sample_sensor_data.json"):
        """Generate and save sample data for testing"""
        
        # Create some anomaly scenarios
        anomaly_events = [
            self.create_anomaly_scenario("bearing_wear", -6, 2, 1.8),
            self.create_anomaly_scenario("belt_misalignment", -1, 0.5, 1.3)
        ]
        
        # Generate time series data
        data = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "generator": "ConveyorDataSimulator",
                "description": "Sample conveyor sensor data with injected anomalies"
            },
            "machines": {}
        }
        
        for machine_id in self.machine_configs.keys():
            readings = self.generate_time_series(
                machine_id=machine_id,
                duration_hours=24,
                interval_minutes=5,
                anomaly_events=anomaly_events
            )
            
            data["machines"][machine_id] = {
                "config": self.machine_configs[machine_id],
                "readings": readings,
                "anomaly_events": anomaly_events
            }
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Sample data saved to {filename}")
        print(f"   Generated {len(data['machines'])} machines")
        print(f"   Each with {len(readings)} readings over 24 hours")
        print(f"   Includes {len(anomaly_events)} anomaly scenarios")
        
        return data
    
    def get_available_anomaly_types(self) -> List[str]:
        """Get list of available anomaly types for injection"""
        return list(self.anomaly_scenarios.keys())
    
    def get_machine_ids(self) -> List[str]:
        """Get list of configured machine IDs"""
        return list(self.machine_configs.keys())
    
    def add_machine_config(self, machine_id: str, config: Dict[str, Any]) -> None:
        """
        Add a new machine configuration
        
        Args:
            machine_id: Unique machine identifier
            config: Machine configuration dictionary
        """
        self.machine_configs[machine_id] = config
        print(f"✅ Added machine configuration for {machine_id}")
    
    def add_anomaly_scenario(self, anomaly_name: str, scenario: Dict[str, Any]) -> None:
        """
        Add a new anomaly scenario
        
        Args:
            anomaly_name: Unique anomaly identifier
            scenario: Anomaly scenario configuration
        """
        self.anomaly_scenarios[anomaly_name] = scenario
        print(f"✅ Added anomaly scenario: {anomaly_name}")
    
    def generate_real_time_stream(self, machine_id: str = "CONV_001", 
                                 interval_seconds: int = 30,
                                 anomaly_probability: float = 0.05) -> Dict[str, Any]:
        """
        Generate a single real-time sensor reading with random anomaly injection
        
        Args:
            machine_id: Machine identifier
            interval_seconds: Seconds since last reading (for realistic timing)
            anomaly_probability: Probability of anomaly occurrence (0.0-1.0)
            
        Returns:
            Real-time sensor reading
        """
        # Randomly inject anomaly based on probability
        anomaly_type = None
        if random.random() < anomaly_probability:
            anomaly_type = random.choice(list(self.anomaly_scenarios.keys()))
            severity = random.uniform(1.2, 2.0)  # Random severity
        else:
            severity = 1.0
        
        reading = self.generate_sensor_reading(
            machine_id=machine_id,
            anomaly_type=anomaly_type,
            anomaly_severity=severity
        )
        
        # Add real-time metadata
        reading["real_time"] = True
        reading["interval_seconds"] = interval_seconds
        
        return reading
    
    def validate_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate sensor data structure and values
        
        Args:
            sensor_data: Sensor data to validate
            
        Returns:
            Validation results with any issues found
        """
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        required_fields = ["machine_id", "timestamp", "sensors"]
        for field in required_fields:
            if field not in sensor_data:
                validation_results["valid"] = False
                validation_results["issues"].append(f"Missing required field: {field}")
        
        if "sensors" in sensor_data:
            required_sensors = ["vibration", "temperature", "current", "speed"]
            for sensor in required_sensors:
                if sensor not in sensor_data["sensors"]:
                    validation_results["warnings"].append(f"Missing sensor: {sensor}")
                else:
                    sensor_info = sensor_data["sensors"][sensor]
                    if "value" not in sensor_info:
                        validation_results["issues"].append(f"Missing value for sensor: {sensor}")
                    if "unit" not in sensor_info:
                        validation_results["warnings"].append(f"Missing unit for sensor: {sensor}")
        
        return validation_results


if __name__ == "__main__":
    # Generate sample data when run directly
    simulator = ConveyorDataSimulator()
    simulator.save_sample_data()
    
    # Generate a single reading for testing
    reading = simulator.generate_sensor_reading("CONV_001", "bearing_wear", 1.5)
    print("\n📊 Sample sensor reading:")
    print(json.dumps(reading, indent=2))