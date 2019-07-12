# NGINX PATTERN - <IP_ADDRRESS> - - [<TIMESTAMP>] - "<API_ENDPOINT> <PROTOCAL>" <STATUS> <NUMBER> " "<HTTP_REFRER> - <USER_AGENT>"
import re
import os
import json
import glob
from flask import Flask, request
import multiprocessing as mp

app = Flask(__name__)

def get_logs(filename,chunkStart, chunkSize):
    with open(filename) as f:
        # f = open(filename)
        f.seek(chunkStart)
        log_lines = f.read(chunkSize).splitlines()
    pattern = (r''
           '(\d+.\d+.\d+.\d+)\s-\s-\s'
           '\[(.+)\]\s'
           '"GET\s(.+)\s\w+/.+"\s'
           '(\d+)\s'
           '(\d+)\s'
           '"(.+)"\s'
           '"(.+)"'
        )
    logs = re.findall(pattern, '\n'.join(log_lines))
    return logs

def chunkify(file,size=1024*1024):
    fileEnd = os.path.getsize(file)
    with open(file,'r') as f:
        chunkEnd = f.tell()
        while True:
            chunkStart = chunkEnd
            f.seek(size,1)
            f.readline()
            chunkEnd = f.tell()
            yield chunkStart, chunkEnd - chunkStart
            if chunkEnd > fileEnd:
                break

@app.route('/')
def extract_logs_from_all_files():
    pool = mp.Pool()
    jobs = []
    logs_dict = []
    for f in glob.iglob("*.txt"):
        print f
        for chunkStart, chunkSize in chunkify(f):
            jobs.append(pool.apply_async(get_logs, args=(f, chunkStart, chunkSize)))
    for job in jobs:
        logs = job.get()
        headers = ["ip_addr", "timestamp", "endpoint", "status", "bytes", "referer", "user_agent"]
        logs_dict += [ dict(zip(headers, list(log))) for log in logs ]
    return json.dumps(logs_dict)

@app.route('/find')
def find():
    logs = extract_logs_from_all_files()
    ips_found = filter(lambda log: request.args['pattern'] in log[request.args['key']], json.loads(logs))
    return json.dumps(ips_found)

if __name__ == '__main__':
    app.run()
