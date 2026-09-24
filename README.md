# 🏢 Dell Storage Array Migration Assistant

> An AI storage architect and migration automation concierge built with Google ADK and Gemini 2.5 Flash.

The **Dell Storage Array Migration Assistant** helps enterprise IT storage administrators plan, assess, execute, and verify end-to-end data migrations across Dell EMC storage arrays (PowerStore, PowerMax, Unity XT, VNX, SC Series).

---

## 🚀 Key Capabilities

### 1. 🔍 Compatibility & Assessment
- **`assess_storage_array_compatibility`**: Evaluates migration paths, minimum required Operating Environments (OE/firmware), and array-native mechanisms (PowerStore Native Import, PowerMax Non-Disruptive Migration, Unity Replication).
- **`run_migration_prechecks`**: Automated readiness checks for array hardware health, host multipathing (PowerPath / ALUA MPIO), network latency/bandwidth, and target storage pool capacity.

### 2. 📋 Migration Planning & Playbooks
- **`generate_migration_plan`**: Generates a structured phase-by-phase migration execution plan (Pre-migration, Sync, Cutover window, Post-checks).
- **`get_manual_migration_playbook`**: Provides step-by-step CLI commands and scripts for host-based migrations (Storage vMotion, PowerPath PPME, Linux LVM live mirror).

### 3. ⚡ REST API Orchestration & Best Practices
- **`orchestrate_api_migration`**: Simulates or triggers Dell PowerStore/Unity/PowerMax REST API actions (`create_session`, `start_sync`, `cutover`, `commit`, `cancel`).
- **`recommend_migration_best_practices`**: Dell-validated architecture guidelines for IOPS throttling, queue depth tuning, and FC/iSCSI zoning.

### 4. 🩺 Post-Migration Health Verification
- **`verify_post_migration_health`**: Verifies volume online status, active multipath count, thin data compression efficiency, and IOPS/latency baseline comparisons.

---

## 🛠️ Installation & Local Usage

### Prerequisites
- Python 3.10+
- Google Cloud Project with Vertex AI enabled
- `agents-cli` installed (`uv tool install google-agents-cli`)

### Quick Start

```bash
# 1. Navigate to the project directory
cd dell-storage-migrator

# 2. Run the interactive CLI agent playground
agents-cli run

# 3. Example prompts to try:
# "Assess migration compatibility from Unity 500 to PowerStore 5000T over FC"
# "Run migration prechecks for Unity array 'unity-prod-01' attached to VMware ESXi 7.0"
# "Generate a migration plan for moving Oracle DB from VMAX 2000 to PowerMax 8000"
# "Get manual migration playbook for Linux LVM"
```

---

## 📁 Project Structure

```
dell-storage-migrator/
├── app/
│   ├── __init__.py
│   └── agent.py          # Main ADK Agent definition and 7 Dell migration tools
├── GEMINI.md             # Antigravity agent instructions
├── README.md             # Project documentation
├── pyproject.toml        # Dependencies and project metadata
└── agents-cli-manifest.yaml
```
