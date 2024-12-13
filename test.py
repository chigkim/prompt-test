llama_cli_path = "../llama.cpp/build/bin/llama-cli"
model_path = "../models/Llama-3.2-1B-Instruct-Q4_K_M.gguf"

import subprocess
import shlex
import re
import time
from datetime import datetime, timedelta
import os
from glob import glob

def atoi(text):
	return int(text) if text.isdigit() else text

def natural_keys(text):
	return [ atoi(c) for c in re.split(r'(\d+)', text) ]

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

def run(command):
	print(command)
	command_args = shlex.split(command)
	start = time.time()
	process = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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
report = open(report_file, "w")
report.write(f"Model: {model_name}\n")
report.write(f"Build: {build}\n")
report.write("| Prompt Tokens | Prompt Processing Speed | Generated Tokens | Token Generation Speed | Total Execution Time |\n")
report.write("| --- | --- | --- | --- | --- |\n")

init_out = ""
for file in files:
	count = int(re.search(r"(\d+)", file)[1])
	cmd = f"{llama_cli_path} -m {model_path} -c {count+2000} -n 2000 --temp 0.0 --top_p 0.9 --seed 1000 -fa -f '{file}'"
	out, dur = run(cmd)
	speeds = re.findall(r, out)
	if not speeds:
		cmd = f"{llama_cli_path} -m {model_path} -c {count} -n 2000 --temp 0.0 --top_p 0.9 --seed 1000 -fa -f '{file}'"
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
	msg = "| "+" | ".join(res)+" |"
	print(msg)
	report.write(msg+"\n")