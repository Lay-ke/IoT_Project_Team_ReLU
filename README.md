# Predictive Maintenance Forecaster (PMF) - Hackathon Documentation

## 1\. Project Overview

The **Predictive Maintenance Forecaster (PMF)** project is an **AI-driven solution** designed to eliminate costly, unplanned downtime in industrial conveyor systems. By transforming reactive maintenance into **proactive, scheduled optimization**, PMF delivers real-time visibility and forecasts component failure before it occurs.

| Feature | Detail | Impact |
| :--- | :--- | :--- |
| **Core Problem** | Unplanned conveyor failure causes **$5,000–$30,000 per hour** in losses. | Reduces production costs and enhances operational reliability. |
| **Key Innovation** | **Synthetic IoT Data Simulation** combined with **AI Agents (AWS Bedrock + SageMaker)**. | Enables scalable, low-cost development and rapid model validation without heavy initial hardware investment. |
| **Goal** | Detect anomalies, classify faults, and estimate **Remaining Useful Life (RUL)**. | **Reduces Mean Time To Repair (MTTR)** and improves asset longevity. |

-----

## 2\. Problem Statement & Motivation

### The Challenge: Visibility Gap ⚠️

Traditional maintenance relies on **reactive** (fix after failure) or **preventive** (time-based) methods, which are inherently inefficient. Maintenance teams lack **real-time visibility** into component health, meaning issues like bearing degradation, motor overheating, or belt wear are detected too late.

### Why Predictive Maintenance (PdM)?

PdM leverages data-driven insights to anticipate failures. It shifts the operational focus from **"When will it fail?"** to **"How can we prevent it?"**

  * **Key Benefits:**
      * ⏱️ **Reduced MTTR** (Mean Time To Repair).
      * 💰 **Lower Operational Costs** and fewer catastrophic breakdowns.
      * 📈 **Improved Asset Utilization** and lifespan.
      * 🧠 **Intelligent Resource Planning** based on AI forecasts.

-----

## 3\. Architecture & End-to-End Flow

The PMF system utilizes a **scalable, five-layer pipeline** that leverages cloud-native services for data simulation, intelligence, and action.

### 3.1. Data Simulation Layer

The foundation is a **digital twin** created via simulated data, crucial for low-cost, high-volume model training and validation.

  * **Method:** AWS Lambda functions and EventBridge generate synthetic IoT readings (Vibration (Hz), Temperature (°C), Motor Current (A)) every minute.
  * **Simulation:** Controlled injection of data anomalies (e.g., a rising temperature trend or a vibration spike) simulates mechanical wear and different failure modes.
  * **Data Path:** Readings are published through **AWS IoT Core** to Amazon S3.

### 3.2. Feature Extraction Layer

Raw time-series data is processed into features that models can interpret.

  * **Method:** Lambda functions or SageMaker processing jobs compute signal features over a 1-minute data window.
  * **Features:** **Statistical** (e.g., Root Mean Square (RMS), Mean, Kurtosis) and **Spectral** (e.g., FFT amplitudes, frequency-domain energy).

### 3.3. Model Training & Inference Layer

The core ML logic is applied here to predict component health.

  * **Service:** Hosted on **Amazon SageMaker Endpoints**.
  * **Models:**
      * **Anomaly Detection:** Supervised/unsupervised models detect deviations from normal operation.
      * **Fault Classification:** Predicts the specific failure type (e.g., bearing, pulley, motor fault).
  * **Maintenance:** Models are scheduled for retraining or triggered on drift detection to maintain accuracy.

### 3.4. AI Reasoning & Decision Layer (Agentic Core) 🧠

**AWS Bedrock AgentCore** orchestrates specialized AI agents, providing the human-like reasoning layer.

  * **Orchestration:** AgentCore interprets raw model scores, applies reasoning logic (e.g., *if anomaly score \> 0.8*), and generates coherent insights.
  * **Agents:**
      * **Diagnosis Agent:** Queries inference results for fault analysis.
      * **Explanation Agent:** Provides human-readable reasoning for the prediction.
      * **Recommendation Agent:** Formulates the final decision/action.
      * **Scheduler Agent:** Triggers maintenance action.

### 3.5. Smart Scheduling & Visualization Layer

The final actionable output for the end-user.

  * **Action:** The Recommendation Agent triggers automatic scheduling via an integrated system, generating a **high-priority maintenance ticket** when RUL hits a critical threshold.
  * **Visualization:** A deployed application (via **AWS Amplify/Streamlit**) displays:
      * Current equipment health status.
      * Anomaly/fault predictions and confidence scores.
      * Maintenance timelines and RUL estimates.

-----

## 4\. Predictive Maintenance Forecaster Deployment

The entire system is designed for **Infrastructure as Code (IaC)** using Terraform.

### 4.1. Prerequisites & Requirements

| Category | Requirement | Notes |
| :--- | :--- | :--- |
| **Cloud** | **AWS Account** | Permissions for Lambda, IoT Core, Bedrock, S3, DynamoDB/RDS. |
| **Tools** | **Terraform CLI, AWS CLI, Git** | For provisioning and management. |
| **Code** | **Python 3.12+** | For Lambda functions and the Streamlit application. |
| **Artifacts** | **Inference Models, Agent Definitions** | Pre-trained models and configuration (YAML/JSON) for the four Bedrock Agents. |

### 4.2. System Architecture Components

| Component Name | AWS Service | Purpose |
| :--- | :--- | :--- |
| **Sensor Simulation** | AWS Lambda (L1) & EventBridge | Periodically generates and pushes synthetic data. |
| **Data Ingestion** | AWS IoT Core & IoT Rule | Routes stream data and triggers the processing pipeline. |
| **Stream Processing** | AWS Lambda (L4, L6) | Handles data transfer, orchestrates model invocation, and stores results. |
| **Anomaly/Rule Logic** | Packaged in L6 / SageMaker Endpoint | Executes the core predictive maintenance models. |
| **Multi-Agent System** | **Amazon Bedrock AgentCore** | Orchestrates specialized agents for reasoning, decision, and action. |
| **Visualization Layer** | Streamlit App & AWS Lambda (L8) | Provides the user interface; L8 acts as an API for data display. |

### 4.3. Deployment Workflow

1.  **Repository Setup:** Clone the repository and ensure all code artifacts (Lambda zips, models) are placed in the designated locations referenced by the Terraform files.

    ```bash
    git clone https://github.com/Lay-ke/IoT_Project_Team_ReLU
    cd IoT_Project_Team_ReLU/terraform
    ```

2.  **Terraform Provisioning:** The entire infrastructure is provisioned by the launch script.

    ```bash
    chmod +x launch.sh    
    ./lauch.sh
    ```

3.  **Bedrock Agent Configuration (Post-Provisioning):** Due to the complexity of Agent definitions, this step often requires manual or scripted configuration within the AWS Bedrock Console.

      * **Define Agent Schemas:** Specify the **Action Groups** (APIs) the agents can call (e.g., an API endpoint to update a schedule database).
      * **Configure AgentCore:** Create the primary Bedrock Agent and define the four sub-agents: **Scheduler, Diagnosis, Explanation, and Recommendation Agents**.
      * **Orchestration Logic:** Provide clear instructions to AgentCore on the workflow (e.g., "Diagnosis first, then Explanation, then Recommendation, concluding with the Scheduler updating the database.").