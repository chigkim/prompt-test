prompt_path = "portugal.txt"
llama_cli_path = "../llama.cpp/build/bin/llama-cli"
model_path = "../models/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
step = 1000 # aprox tokens

prefix = """<|start_header_id|>system<|end_header_id|>

Cutting Knowledge Date: December 2023
Today Date: 23 July 2024

You are a helpful assistant<|eot_id|><|start_header_id|>user<|end_header_id|>

Provide a summary as well as a detail analysis of the following:
"""

suffix = "<|eot_id|><|start_header_id|>assistant<|end_header_id|>"


import subprocess
import shlex
import re
import time
from datetime import datetime, timedelta
import os
def run(command):
	print(command)
	command_args = shlex.split(command)
	start = time.time()
	process = subprocess.Popen(command_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	stdout, stderr = process.communicate()
	print(stderr)
	return stderr


try: os.mkdir("steps")
except: pass

prev = 0
prompt = prefix
text = open(prompt_path).read()
for line in open(prompt_path).readlines():
	prompt += line
	if len(line)<10: continue
	open("temp.txt", "w").write(prompt+suffix)
	cmd = f"{llama_cli_path} -m {model_path} -c 1 -n 1 -f ./temp.txt"
	out = run(cmd)
	m = re.search(r"(\d+) tokens", out)
	count = int(m[1])
	if count > prev+step or len(prompt) > len(text):
		os.rename("temp.txt", "steps/"+str(count)+".txt")
		prev += step