# 🚀 Apache Airflow Codespace Setup Guide

1. Create a **Cloud Codespace** on GitHub.
2. ⏳ *Wait 5–10 minutes* for the environment to finish building.
3. Run `cmd_1` in your terminal:
   ```bash
   airflow standalone
   ```

---

## ⚠️ Troubleshooting: If `cmd_1` says `"command not found"`

> **Note:** Sometimes the container doesn't build all dependencies on the first try. Follow these steps to refresh it:

1. Run `cmd_2` to pull the latest changes:
   ```bash
   git pull
   ```
2. Open the Command Palette by pressing <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd> *(or <kbd>Cmd</kbd> + <kbd>Shift</kbd> + <kbd>P</kbd> on Mac)*.
3. Input **"Codespace"** and click **`Codespaces: Rebuild Container`**.
4. Run `cmd_1` again:
   ```bash
   airflow standalone
   ```
5. *Wait again* 😂

---

## 🛠️ Manual Setup: If `cmd_1` *still* says `"command not found"`

> 💡 __*Looks like you are having a bad day!*__ Run these commands step-by-step in your terminal to set everything up manually:

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```
2. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```
3. **Upgrade `pip`:**
   ```bash
   python -m pip install --upgrade pip
   ```
4. **Install Apache Airflow and constraints:**
   ```bash
   pip install "apache-airflow==3.3.2" requests --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.2/constraints-3.12.txt"
   ```
5. **Set the `AIRFLOW_HOME` directory:**
   ```bash
   export AIRFLOW_HOME=/workspaces/airflow-class/.airflow
   ```
6. **Set the `DAGS_FOLDER` location:**
   ```bash
   export AIRFLOW__CORE__DAGS_FOLDER=/workspaces/airflow-class/dags
   ```
7. **Disable example DAGs:**
   ```bash
   export AIRFLOW__CORE__LOAD_EXAMPLES=false
   ```
8. **Start Airflow:**
   ```bash
   airflow standalone
   ```

---

<img width="500" height="281" alt="image" src="https://github.com/user-attachments/assets/e146812e-b686-4ebc-8146-97d6868b8e62" />
