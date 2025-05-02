llama_cli_path = "../llama.cpp/build/bin/llama-cli"
model_path = "../models/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
parameters = "--n-predict 2000 --temp 0.0 --top_p 0.9 --seed 1000 --batch-size 4096 --ubatch-size 4096 --flash-attn"
# For Cuda, You may need to assign buff_context to same as --n-predict.
buffer_context_size = 0

import time

start = time.time()
import subprocess
import shlex
import re
from datetime import datetime, timedelta
import os
from glob import glob


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r"(\d+)", text)]


def elapsed(start):
    duration = time.time() - start
    duration_td = timedelta(seconds=duration)
    days = duration_td.days
    hours, remainder = divmod(duration_td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    dur_str = ""
    if days:
        dur_str = f"{days}d"
    if hours:
        dur_str += f"{hours}h"
    if minutes:
        dur_str += f"{minutes}m"
    if seconds:
        dur_str += f"{seconds}s"
    return dur_str


def log(msg):
    with open(report_file, "a") as file:
        file.write(msg + "\n")


def run(command):
    print(command)
    command_args = shlex.split(command)
    start = time.time()
    process = subprocess.Popen(
        command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate()
    return stderr, elapsed(start)


r = r"(\d+\.\d+) tokens per second"
files = glob("steps/*")
files.sort(key=natural_keys)
cmd = f"{llama_cli_path} -v"
out, dur = run(cmd)
build = re.search(r"build: (.*?) with", out)[1]
model_name = os.path.basename(model_path)
report_file = f"report-{model_name} b{build}.txt"
try:
    os.remove(report_file)
except:
    pass
log(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
log(f"Model: {model_name}")
log(f"Build: {build}\n")
log(
    "| Prompt Tokens | Prompt Processing Speed | Generated Tokens | Token Generation Speed | Total Execution Time |"
)
log("| --- | --- | --- | --- | --- |")

init_out = ""
for file in files:
    count = int(re.search(r"(\d+)", file)[1])
    cmd = f"{llama_cli_path} -m {model_path} --ctx-size {count+buffer_context_size} {parameters} --file '{file}'"
    out, dur = run(cmd)
    speeds = re.findall(r, out)
    for line in out.split("\n"):
        if not init_out:
            init_out = out
            print(out)
            break
        if line not in init_out:
            print(line)
    runs = re.findall(r" (\d+) runs", out)
    tokens = re.findall(r" (\d+) tokens", out)
    res = [tokens[-2]]
    res.append(speeds[1])
    res.append(runs[-1])
    res.append(speeds[2])
    res.append(dur)
    msg = "| " + " | ".join(res) + " |"
    print(msg)
    log(msg)

msg = f"\nTotal duration: {elapsed(start)}"
print(msg)
log(msg)
