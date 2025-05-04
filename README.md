# Prompt Test Instructions

```bash
git clone https://github.com/chigkim/prompt-test
cd prompt-test
pip install openai
```

1. Modify `test.py` for your setup.
2. Run `python test.py`

To test with the default prompt setup, launch your server with 36k context length. Otherwise, modify prompt.txt to fit your need.

## Metrics

Metrics are calculated as follows:

* Time to First Token (TTFT): Measured from the start of the streaming request to the first streaming event received.
* Prompt Processing Speed (PP): Number of prompt tokens divided by TTFT.
* Token Generation Speed (TG): Number of generated tokens divided by (total duration - TTFT).

The displayed results were truncated to two decimal places, but the calculations used full precision.

Some servers don't let you disable prompt caching. To work around this, I made the script to prepend 40% new material in the beginning of next longer prompt to avoid caching effect. Also it uses two system prompts with the same number of tokens to alternate every test.

### Optimize Performance on Mac

Some Mac models, offer High Power mode that prevents performance throttling. Without this, speed results may fluctuate significantly. To enable high-power mode:

1. Open System Settings > Battery.  
2. Under "Energy Mode" for "On Power Adapter," select High Power.

Even with this setting, I noticed there's some throttling. You might want to increase coolling to 120 in `test.py`.

### Adjust GPU Memory Allocation

By default, macOS limits GPU memory usage to 2/3 or 3/4 of total system memory depending your model. To increase this limit, run the following command in the terminal before executing the script:

```bash
sudo sysctl iogpu.wired_limit_mb=57344
```

The setting will be reset on next reboot. To make it persistent every reboot, you can add `iogpu.wired_limit_mb=57344` to `/etc/sysctl.conf` and reboot.

For a 64GB system, this allows the GPU to use up to 56GB, leaving 8GB for other processes.

Calculation: (64GB - 8GB) ?? 1024MB = **57344MB**  
