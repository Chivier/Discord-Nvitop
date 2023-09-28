# bot.py
import os
import random
import json
import discord

import time

from nvitop import Device, GpuProcess, NA, colored

def GPUStatus():
    result_str = ""
    devices = Device.all()  # or `Device.cuda.all()` to use CUDA ordinal instead
    for device in devices:
        processes = device.processes()  # type: Dict[int, GpuProcess]
        sorted_pids = sorted(processes.keys())

        result_str += "## " + str(device.name()) + "\n"
        result_str += (f'- Fan speed:       {device.fan_speed()}%') + "\n"
        result_str += (f'- Temperature:     {device.temperature()}C') + "\n"
        result_str += (f'- GPU utilization: {device.gpu_utilization()}%') + "\n"
        result_str += (f'- Memory:          {device.memory_used_human()}/{device.memory_total_human()}') + "\n"
        result_str += (f'  - Processes ({len(processes)}): {sorted_pids}') + "\n"
        for pid in sorted_pids:
            result_str += (f'    - {processes[pid]}') + "\n"
    return result_str


with open('./config.json') as data_file:
    config = json.load(data_file)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.event
async def on_message(message):
    if message.content == 'help':
        await message.channel.send(GetHelp())
    if message.content == config['machine']:
        await message.channel.send(GPUStatus())

client.run(config['token'])
