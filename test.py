base_url = "http://localhost:8080/v1"
api_key = "api_key"
model = "qwen3:30b-a3b-q8_0"
# model = "mlx-community/Qwen3-30B-A3B-8bit"
# model = "Qwen/Qwen3-30B-A3B-FP8"
temperature = 0.7
top_p = 0.8
max_tokens = 2000
seed = 1000
prompt_file = "prompt.txt"
cooling = 10
setup = ["RTX3090", "LCPP"]
# Provides two system prompts to alternate in order to avoid prompt caching.
system_prompts = [
    "You are a helpful assistant. Provide a summary as well as a detail analysis of the following. /no_think",
    "Provide a summary as well as a detail analysis of the following. You are a helpful assistant. /no_think",
]
headers = [
    "Machine",
    "Engine",
    "Prompt Tokens",
    "PP/s",
    "TTFT",
    "Generated Tokens",
    "TG/s",
    "Duration",
]

import time
from datetime import datetime, timedelta
import os
from glob import glob
import openai
import codecs
import re
import math
import shutil


def generate_prompts(file, initial_ratio=0.02, reverse=False):
    text = codecs.open(file, "r", "utf-8").read()
    words = re.findall(r"\S+\s*", text)
    phi = (1 + math.sqrt(5)) / 2
    ratio = 1 / (1 + phi)
    prompts = []
    total = len(words)
    take = int(total * initial_ratio)

    while words:
        if take > len(words):
            if reverse:
                prompts[-1] = words + prompts[-1]
            else:
                prompts[-1] = prompts[-1] + words
            break
        if prompts:
            if reverse:
                prompt = words[-take:] + prompts[-1]
            else:
                prompt = prompts[-1] + words[:take]
        else:
            if reverse:
                prompt = words[-take:]
            else:
                prompt = words[:take]
        prompts.append(prompt)
        if reverse:
            words = words[:-take]
        else:
            words = words[take:]
        take = int(len(prompt) * ratio)
    prompts = ["".join(prompt) for prompt in prompts]
    try:
        shutil.rmtree("prompts")
    except:
        pass
    try:
        os.mkdir("prompts")
    except:
        pass
    for prompt in prompts:
        file = f"prompts/{len(re.findall(r"\S+\s*", prompt))}.txt"
        codecs.open(file, "w", "utf-8").write(prompt)
    print(f"Generated {len(prompts)} prompts.")
    return prompts


def send(messages, change_system_prompt=True):
    if change_system_prompt:
        # Flip system prompt to avoid prompt caching.
        messages[0]["content"] = (
            system_prompts[0]
            if messages[0]["content"] != system_prompts[0]
            else system_prompts[1]
        )
    ttf = 0
    start_time = time.time()
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        seed=seed,
        stream=True,
        stream_options={"include_usage": True},
    )
    for event in stream:
        if ttf == 0:
            ttf = time.time() - start_time
    duration = time.time() - start_time
    prompt_tokens = event.usage.prompt_tokens
    prompt_speed = prompt_tokens / ttf
    completion_tokens = event.usage.completion_tokens
    completion_speed = completion_tokens / (duration - ttf)
    return (
        prompt_tokens,
        prompt_speed,
        ttf,
        completion_tokens,
        completion_speed,
        duration,
    )


def report(
    prompt_tokens,
    prompt_speed,
    ttf,
    completion_tokens,
    completion_speed,
    duration,
    write_log=True,
):
    res = setup.copy()
    res.append(f"{prompt_tokens}")
    res.append(f"{prompt_speed:.2f}")
    res.append(f"{ttf:.2f}")
    res.append(f"{completion_tokens}")
    res.append(f"{completion_speed:.2f}")
    res.append(f"{duration:.2f}")
    msg = "| " + " | ".join(res) + " |"
    print(msg)
    if write_log:
        log(msg)


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


client = openai.Client(base_url=base_url, api_key=api_key)
model_name = re.sub(r"\W", "_", model)
report_file = f"report-{model_name}.txt"
try:
    os.remove(report_file)
except:
    pass
log(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
log(f"Model: {model_name}")

headers_text = "| " + " | ".join(headers) + " |"
log(headers_text)
header_line = [re.sub(r".", "-", header) for header in headers]
header_line = "| " + " | ".join(header_line) + " |"
log(header_line)

prompts = generate_prompts(prompt_file, reverse=True)
messages = [
    {"role": "system", "content": "Act as a system admin."},
    {"role": "user", "content": "This is test."},
]
print("Sending a warm up test.")
send(messages, change_system_prompt=False)
start = time.time()
for i, prompt in enumerate(prompts):
    print("Sending prompt ", i + 1)
    messages[-1]["content"] = prompt
    try:
        stats = send(messages, change_system_prompt=True)
        report(*stats)
    except Exception as e:
        print(e)
    if cooling:
        print(f"Coolling down for {cooling} seconds.")
        time.sleep(cooling)


msg = f"\nTotal duration: {elapsed(start)}"
print(msg)
log(msg)
