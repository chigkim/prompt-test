base_url = "http://localhost:8080/v1/"
api_key = "api_key"
model = "Qwen3-30B-A3B-q8_0"
temperature = 0.7
top_p = 0.8
max_tokens = 2000
seed = 1000
prompt_file = "prompt.txt"
n_prompts = 10
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
from glob import glob
import openai
import re
import math
from pathlib import Path

def generate_prompts(file, n_prompts=10, reverse=False):
    text = Path("prompt.txt").read_text(encoding="utf-8")
    words = re.findall(r"\S+\s*", text)
    Path("prompts").mkdir(exist_ok=True)
    phi = (1 + 5 ** 0.5) / 2
    total = len(words)
    
    lengths = [max(1, int(round(total / (phi ** (n_prompts - i - 1))))) for i in range(n_prompts)]
    lengths[-1] = total  # Ensure last prompt includes all words
    
    for i in range(1, n_prompts):
        lengths[i] = max(lengths[i], lengths[i-1] + 1)
    
    prompts = []
    direction = "suffix" if reverse else "prefix"
    
    for idx, length in enumerate(lengths, start=1):
        snippet = words[-length:] if reverse else words[:length]
        prompt_text = "".join(snippet)
        prompts.append(prompt_text)
        
        path = Path("prompts") / f"{idx}.txt"
        path.write_text(prompt_text, encoding="utf-8")
        
        print(f"Prompt {idx} ({direction} {length} words), → {path}")

    print(f"Generated {len(prompts)} prompts. Delete prompts folder to regenerate.")
    return prompts


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    return [atoi(c) for c in re.split(r"(\d+)", text)]


def get_prompts():
    if Path("prompts").exists():
        files = glob("prompts/*.txt")
        files.sort(key=natural_keys)
        prompts = [Path(file).read_text(encoding="utf-8") for file in files]
    else:
        prompts = generate_prompts(prompt_file, n_prompts=n_prompts, reverse=True)
    print(f"Retrieved {len(prompts)} prompts.")
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
prompts = get_prompts()
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
    if cooling and i + 1 < len(prompts):
        print(f"Coolling down for {cooling} seconds.")
        time.sleep(cooling)


msg = f"\nTotal duration: {elapsed(start)}"
print(msg)
log(msg)
