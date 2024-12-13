# Prompt Test Instructions

Modify `test.py` and update the following paths as needed:

```python
llama_cli_path = "../llama.cpp/build/bin/llama-cli"
model_path = "../models/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
```

### Optimize Performance on Mac

Some Mac models, offer High Power mode that prevents performance throttling. Without this, speed results may fluctuate significantly. To enable high-power mode:

1. Open System Settings > Battery.  
2. Under "Energy Mode" for "On Power Adapter," select High Power.

### Adjust GPU Memory Allocation

By default, macOS limits GPU memory usage to 2/3 or 3/4 of total system memory depending your model. To increase this limit, run the following command in the terminal before executing the script:

```bash
sudo sysctl iogpu.wired_limit_mb=57344
```

For a 64GB system, this allows the GPU to use up to 56GB, leaving 8GB for other processes.

Calculation: (64GB - 8GB) × 1024MB = **57344MB**  

The setting will be persistent until next reboot.

### Using Different Prompts

1. First, modify split.py as needed. You can supply your own prompt file and customize tokens, steps, and prompt template.
2. Delete all the files inside the steps folder.
3. Run split.py.

The script will generate new prompts with different number of tokens inside the steps folder. Review and delete the files as needed in order to reduce the steps. The number of tokens won't be exactly the same as what you specified in step, because the script will split at the closest new line.