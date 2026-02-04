#!/usr/bin/env python3
&quot;&quot;&quot;
BR AI OCR Monitoring Agent
- Checks /health every 5 minutes
- Logs response time &amp; status
- Alerts on 3 consecutive failures (prints analysis)
&quot;&quot;&quot;

import requests
import time
import logging
from datetime import datetime
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEALTH_URL = &quot;http://localhost:8000/health&quot;  # Update for prod
FAIL_COUNT = 0
MAX_FAILS = 3
LOG_FILE = &quot;ocr_service.log&quot;  # Update path

def health_check():
    try:
        start = time.time()
        resp = requests.get(HEALTH_URL, timeout=10)
        duration = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            logger.info(f&quot;Health OK: {data} (RT: {duration:.2f}s)&quot;)
            return True, duration
        else:
            logger.warning(f&quot;Health FAIL: {resp.status_code}&quot;)
            return False, duration
    except Exception as e:
        logger.error(f&quot;Health check error: {e}&quot;)
        return False, 0

def get_recent_logs(num_lines=50):
    try:
        result = subprocess.run([&quot;tail&quot;, &quot;-n&quot;, str(num_lines), LOG_FILE], 
                              capture_output=True, text=True, timeout=10)
        return result.stdout
    except:
        return &quot;Unable to read logs&quot;

def analyze_failure():
    logs = get_recent_logs()
    logger.critical(f&quot;🚨 CRITICAL ALERT: 3x failures! Recent logs:\\n{logs}&quot;)
    print(f&quot;🚨 OCR Service DOWN - Check logs: {logs}&quot;, file=sys.stderr)

def main():
    global FAIL_COUNT
    while True:
        success, rt = health_check()
        if not success:
            FAIL_COUNT += 1
            if FAIL_COUNT >= MAX_FAILS:
                analyze_failure()
                FAIL_COUNT = 0  # Reset after alert
        else:
            FAIL_COUNT = 0
        
        time.sleep(300)  # 5 minutes

if __name__ == &quot;__main__&quot;:
    main()
