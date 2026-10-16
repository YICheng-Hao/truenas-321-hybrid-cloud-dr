#!/usr/bin/env python3
import subprocess, os, time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

BUCKET = "truenas-backup-myhome-2026"
CRED_FILE = "/etc/cloudwatch_exporter/credentials"
COST_PER_GB_USD = 0.025  # AWS S3 亞太台北區 Standard 約 $0.025 USD / GB / 月

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            start_time = time.time()
            env = os.environ.copy()
            env["AWS_SHARED_CREDENTIALS_FILE"] = CRED_FILE
            env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin"
            cmd = ["aws", "s3", "ls", f"s3://{BUCKET}", "--recursive", "--summarize"]
            res = subprocess.run(cmd, env=env, capture_output=True, text=True)
            duration = time.time() - start_time

            objs, size, latest_ts = 0, 0, 0
            health = 1 if res.returncode == 0 else 0

            for line in res.stdout.splitlines():
                line_s = line.strip()
                if "Total Objects:" in line_s:
                    objs = int(line_s.split(":")[1].strip())
                elif "Total Size:" in line_s:
                    size = int(line_s.split(":")[1].strip())
                elif len(line_s) > 19 and line_s[4] == '-' and line_s[7] == '-':
                    try:
                        dt_str = line_s[:19]
                        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                        ts = dt.timestamp()
                        if ts > latest_ts:
                            latest_ts = ts
                    except Exception:
                        pass

            size_gb = size / (1024 ** 3)
            est_cost_usd = size_gb * COST_PER_GB_USD
            age_seconds = max(0, time.time() - latest_ts) if latest_ts > 0 else 0

            out = (
                f'# HELP aws_s3_bucket_size_bytes_average Realtime S3 bucket size in bytes\n'
                f'# TYPE aws_s3_bucket_size_bytes_average gauge\n'
                f'aws_s3_bucket_size_bytes_average{{bucket_name="{BUCKET}",storage_type="StandardStorage"}} {size}\n'
                f'# HELP aws_s3_number_of_objects_average Realtime S3 number of objects\n'
                f'# TYPE aws_s3_number_of_objects_average gauge\n'
                f'aws_s3_number_of_objects_average{{bucket_name="{BUCKET}",storage_type="AllStorageTypes"}} {objs}\n'
                f'# HELP aws_s3_estimated_monthly_cost_usd Estimated monthly storage cost in USD\n'
                f'# TYPE aws_s3_estimated_monthly_cost_usd gauge\n'
                f'aws_s3_estimated_monthly_cost_usd{{bucket_name="{BUCKET}"}} {est_cost_usd:.4f}\n'
                f'# HELP aws_s3_last_backup_age_seconds Seconds since the newest object was uploaded\n'
                f'# TYPE aws_s3_last_backup_age_seconds gauge\n'
                f'aws_s3_last_backup_age_seconds{{bucket_name="{BUCKET}"}} {age_seconds:.0f}\n'
                f'# HELP aws_s3_bucket_health_status S3 bucket connectivity health (1=OK, 0=Error)\n'
                f'# TYPE aws_s3_bucket_health_status gauge\n'
                f'aws_s3_bucket_health_status{{bucket_name="{BUCKET}"}} {health}\n'
                f'# HELP aws_s3_api_latency_seconds S3 ls API response latency in seconds\n'
                f'# TYPE aws_s3_api_latency_seconds gauge\n'
                f'aws_s3_api_latency_seconds{{bucket_name="{BUCKET}"}} {duration:.3f}\n'
            )
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(out.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    HTTPServer(('127.0.0.1', 9107), MetricsHandler).serve_forever()
