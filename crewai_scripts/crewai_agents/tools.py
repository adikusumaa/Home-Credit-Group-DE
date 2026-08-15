import git
import requests
import os
from datetime import datetime
from typing import Type
from opensearchpy import OpenSearch
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

AIRFLOW_USER = os.getenv("AIRFLOW_API_USER", "airflow")
AIRFLOW_PASS = os.getenv("AIRFLOW_API_PASSWORD", "airflow")
auth = (AIRFLOW_USER, AIRFLOW_PASS)

class OpenSearchLogInput(BaseModel):
    dag_id: str = Field(description="Nama DAG yang gagal, misal: dag_silver_processing")

class OpenSearchLogTool(BaseTool):
    name: str = "Fetch Airflow Error Logs"
    description: str = "Mengambil 20 baris log terakhir dari Airflow REST API berdasarkan DAG ID yang gagal."
    args_schema: Type[BaseModel] = OpenSearchLogInput

    def _run(self, dag_id: str) -> str:
        import requests
        import os
        import re

        base_url = "http://airflow-webserver:8080/api/v1"
        user = os.getenv("AIRFLOW_API_USER", "airflow")
        password = os.getenv("AIRFLOW_API_PASSWORD", "airflow")
        auth = (user, password)

        try:
            runs_url = f"{base_url}/dags/{dag_id}/dagRuns?order_by=-execution_date&limit=1"
            runs_resp = requests.get(runs_url, auth=auth, timeout=15)
            if runs_resp.status_code != 200:
                return f"[AirflowLog] Gagal ambil DAG runs: {runs_resp.status_code}"

            runs = runs_resp.json().get("dag_runs", [])
            if not runs:
                return f"[AirflowLog] Tidak ada DAG run untuk {dag_id}"

            run_id = runs[0]["dag_run_id"]

            tis_url = f"{base_url}/dags/{dag_id}/dagRuns/{run_id}/taskInstances?state=failed"
            tis_resp = requests.get(tis_url, auth=auth, timeout=15)
            if tis_resp.status_code != 200:
                return f"[AirflowLog] Gagal ambil task instances: {tis_resp.status_code}"

            task_instances = tis_resp.json().get("task_instances", [])
            logs = []

            for ti in task_instances[:3]:
                task_id = ti["task_id"]
                try_number = ti["try_number"]
                log_url = f"{base_url}/dags/{dag_id}/dagRuns/{run_id}/taskInstances/{task_id}/logs/{try_number}?full_content=true"
                log_resp = requests.get(log_url, auth=auth, timeout=60)

                if log_resp.status_code != 200:
                    logs.append(f"=== {task_id} (try {try_number}) ===\n[Gagal ambil log: {log_resp.status_code}]")
                    continue

                full_text = log_resp.text

                output_match = re.search(r"Output:\s*", full_text)
                if output_match:
                    start = output_match.end()
                    excerpt = full_text[start:start+5000]
                else:
                    error_pattern = r"(SyntaxError|File \"|Traceback)"
                    match = re.search(error_pattern, full_text, re.IGNORECASE)
                    if match:
                        start = max(0, match.start() - 500)
                        end = min(len(full_text), match.start() + 3000)
                        excerpt = full_text[start:end]
                    else:
                        excerpt = full_text[-4000:]

                logs.append(f"=== {task_id} (try {try_number}) ===\n{excerpt}")

            if logs:
                return "\n\n".join(logs)
            return f"[AirflowLog] Tidak ada task gagal untuk DAG {dag_id}."
        except requests.exceptions.Timeout:
            return "[AirflowLog] Timeout saat mengambil data dari Airflow API."
        except Exception as e:
            return f"[AirflowLog] Gagal ambil log dari Airflow: {str(e)}"

class GitPatchInput(BaseModel):
    file_path: str = Field(description="Path file yang akan di-patch, misal: dags/silver_cleaning.py")
    patch_content: str = Field(description="Isi kode perbaikan yang baru")

class ReadFileInput(BaseModel):
    file_path: str = Field(description="Path file di repo yang akan dibaca, contoh: jobs/pyspark/application_s.py atau dags/dag_silver_processing.py")

class ReadFileTool(BaseTool):
    name: str = "Read File from Repo"
    description: str = "Membaca isi file dari repo /opt/repo untuk melihat kode asli sebelum diubah."
    args_schema: Type[BaseModel] = ReadFileInput

    def _normalize_path(self, file_path: str) -> str:
        if file_path.startswith("/opt/airflow/dags/"):
            return "dags/" + file_path[len("/opt/airflow/dags/"):]
        elif file_path.startswith("/opt/jobs/"):
            return "jobs/" + file_path[len("/opt/jobs/"):]
        elif file_path.startswith("dags/") or file_path.startswith("jobs/"):
            return file_path
        else:
            return file_path

    def _run(self, file_path: str) -> str:
        import os
        repo_root = "/opt/repo"
        rel_path = self._normalize_path(file_path)
        abs_path = os.path.join(repo_root, rel_path)
        try:
            with open(abs_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"[ReadFile] Gagal baca {rel_path}: {str(e)}"

class GitPatchTool(BaseTool):
    name: str = "Create Git Branch with Patch and PR"
    description: str = "Membuat branch baru, push ke remote, dan membuka Pull Request ke main."
    args_schema: Type[BaseModel] = GitPatchInput

    def _normalize_path(self, file_path: str) -> str:
        if file_path.startswith("/opt/airflow/dags/"):
            return "dags/" + file_path[len("/opt/airflow/dags/"):]
        elif file_path.startswith("/opt/jobs/"):
            return "jobs/" + file_path[len("/opt/jobs/"):]
        elif file_path.startswith("dags/") or file_path.startswith("jobs/"):
            return file_path
        else:
            return file_path

    def _run(self, file_path: str, patch_content: str) -> str:
        import git
        import os
        import requests
        from datetime import datetime

        if not file_path or not patch_content:
            return "[GitPatch] Gagal: file_path dan patch_content wajib diisi."

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "[GitPatch] Gagal: GITHUB_TOKEN tidak ditemukan. Tidak bisa push/PR."

        repo_root = "/opt/repo"
        repo_owner = "adikusumaa"
        repo_name = "Home-Credit-Group-DE"

        try:
            repo = git.Repo(repo_root)
        except Exception as e:
            return f"[GitPatch] Gagal buka repo di {repo_root}: {str(e)}"

        rel_path = self._normalize_path(file_path)
        abs_path = os.path.join(repo_root, rel_path)

        try:
            # Baca file asli untuk validasi panjang
            original_content = ""
            if os.path.exists(abs_path):
                with open(abs_path, "r") as f:
                    original_content = f.read()

            # Validasi: patch harus ≥ 80% panjang file asli
            if original_content:
                original_len = len(original_content)
                patch_len = len(patch_content)
                min_required = int(original_len * 0.8)
                if patch_len < min_required:
                    return (
                        f"[GitPatch] ❌ Patch DITOLAK. patch_content terlalu pendek "
                        f"({patch_len} chars vs original {original_len} chars). "
                        f"Anda HARUS memanggil tool `read_file` terlebih dahulu untuk "
                        f"mendapatkan file asli, lalu kirim file lengkap dengan hanya "
                        f"menghapus/memperbaiki baris yang error."
                    )

            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            # Buat branch unik
            base = f"fix/incident-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            branch_name = base
            counter = 1
            while branch_name in repo.branches:
                branch_name = f"{base}-{counter}"
                counter += 1

            new_branch = repo.create_head(branch_name)
            new_branch.checkout()

            with open(abs_path, "w") as f:
                f.write(patch_content)

            repo.index.add([rel_path])
            repo.index.commit(f"AI Patch: Perbaikan otomatis untuk {rel_path}")

            origin = repo.remote(name="origin")
            remote_url = f"https://x-access-token:{github_token}@github.com/{repo_owner}/{repo_name}.git"
            origin.set_url(remote_url)

            origin.push(refspec=f"{branch_name}:{branch_name}")

            pr_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            pr_data = {
                "title": f"[AI Auto-Patch] Perbaikan untuk error di {rel_path}",
                "body": f"""## 🤖 Auto-Generated Pull Request

**Incident:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

**File yang diubah:** `{rel_path}`

**Perubahan:**
{patch_content[:500]}{'...' if len(patch_content) > 500 else ''}

**📌 Mohon review sebelum di-merge.**""",
                "head": branch_name,
                "base": "main",
            }
            response = requests.post(pr_url, json=pr_data, headers=headers)
            if response.status_code == 201:
                pr_result = response.json()
                return (
                    f"[GitPatch] ✅ Branch {branch_name} berhasil di-push "
                    f"dan PR #{pr_result.get('number')} dibuat: {pr_result.get('html_url')}"
                )
            else:
                return f"[GitPatch] ⚠️ Branch ter-push, tapi PR gagal: {response.text}"

        except Exception as e:
            return f"[GitPatch] Gagal total: {str(e)}"