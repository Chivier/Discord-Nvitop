import os
import random
import json
import discord
import asyncio
from discord.ext import commands, tasks
import time

from nvitop import Device, GpuProcess, NA, colored

with open('./config.json') as data_file:
    config = json.load(data_file)

def GPUStatusStr():
    # Return a string of GPU status
    fire = "🔥"
    work = "🤖"
    result_str = ""
    devices = Device.all()  # or `Device.cuda.all()` to use CUDA ordinal instead
    for device in devices:
        processes = device.processes()  # type: Dict[int, GpuProcess]
        sorted_pids = sorted(processes.keys())

        result_str += "### " + str(device.name()) + "\n"
        if device.fan_speed() >= 85:
            result_str += (f'- Fan speed:       {device.fan_speed()}%  {fire}') + "\n"
        else:
            result_str += (f'- Fan speed:       {device.fan_speed()}%') + "\n"

        if device.temperature() >= 80:
            result_str += (f'- Temperature:     {device.temperature()}C  {fire}') + "\n"
        else:
            result_str += (f'- Temperature:     {device.temperature()}C') + "\n"

        if device.gpu_utilization() >= 5:
            result_str += (f'- GPU utilization: {device.gpu_utilization()}%{work}') + "\n"
        else:
            result_str += (f'- GPU utilization: {device.gpu_utilization()}%') + "\n"

        result_str += (f'- Memory:          {device.memory_used_human()}/{device.memory_total_human()}') + "\n"
        result_str += (f'- Processes ({len(processes)}):') + "\n"
        for pid in sorted_pids:
            result_str += (f'  - {processes[pid].username()} ({pid})') + "\n"
    return result_str

def GPUStatus():
    # Return a dict of GPU status
    devices = Device.all()
    status = {}
    available_devices = []
    available_devices_count = 0
    for index, device in enumerate(devices):
        processes = device.processes()
        device_name = "GPU" + str(index)
        status[device_name] = dict(processes)
        if len(processes) == 0:
            available_devices_count += 1
            available_devices.append(device_name)
    status['available_devices'] = available_devices
    status['available_devices_count'] = available_devices_count
    return status

def StatusDelta(old_status, new_status):
    global config
    old_process = []
    new_process = []
    # find old process that ends
    devices = Device.all()
    for index, device in enumerate(devices):
        device_name = "GPU" + str(index)
        old_process_pid_on_current_device = [process for process in old_status[device_name].keys()]
        new_process_pid_on_current_device = [process for process in new_status[device_name].keys()]
        for pid, process in old_status[device_name].items():
            if pid not in new_process_pid_on_current_device:
                old_process.append(process)
        for pid, process in new_status[device_name].items():
            if pid not in old_process_pid_on_current_device:
                new_process.append(process)
    if len(old_process) == 0 and len(new_process) == 0:
        return ""
    result_str = f"# {time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))} Device report on {config['machine']}\n"
    result_str += f"- Available devices number: 🤖 {new_status['available_devices_count']}\n"
    result_str += f"- Available devices: {new_status['available_devices']}\n"
    result_str += f"## Logs\n"
    for process in old_process:
        username = process.username()
        pid = process.pid
        result_str += f"- ⛔ {username} process {pid} terminates\n"
    for process in new_process:
        username = process.username()
        pid = process.pid
        result_str += f"- 🆕 {username} process {pid} starts\n"
    return result_str


def GetHelp():
    help_str = "## Help\n"
    help_str += "- help: get help\n"
    help_str += "- gala: get gala gpu status\n"
    help_str += "- jazz: get jazz gpu status\n"
    help_str += "- num: get number of gpu\n"
    return help_str

# Bot main
intents = discord.Intents.default()
# client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    watch_machine.start()

@bot.event
async def on_message(message):
    if message.content == 'help':
        await message.channel.send(GetHelp())
    elif message.content == config['machine']:
        await message.channel.send(GPUStatusStr())
    elif message.content == "num":
        GPU_status = GPUStatus()
        result_str = f"Available devices number on {config['machine']}: {GPU_status['available_devices_count']}"
        await message.channel.send(result_str)
    

@tasks.loop(seconds=1800)
async def watch_machine():
    global GPU_status
    # GPU_status = GPUStatus()
    # while not bot.is_closed():
    current_status = GPUStatus()

    result_str = StatusDelta(GPU_status, current_status)
    GPU_status = current_status
    if result_str == "":
        return

    channel = bot.get_channel(config['channel_id'])
    if channel is not None:
        await channel.send(result_str)
    else:
        print("channel not found")

@watch_machine.before_loop
async def before_watch_machine():
    global GPU_status
    GPU_status = GPUStatus()
    channel = bot.get_channel(config['channel_id'])
    await channel.send(f"{config['machine']} is ready!")

GPU_status = GPUStatus()
bot.run(config['token'])
