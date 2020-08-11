# Python 3 script to check cpu load, cpu temperature and free space,
# on a Raspberry Pi computer and publish the data to a MQTT server.
# RUN pip install paho-mqtt
# RUN sudo apt-get install python-pip

import subprocess, time, socket, os
import paho.mqtt.client as paho
import json
import config

# get device info - may be used in mqtt topic
hostname = socket.gethostname()
serial = subprocess.check_output('cat /proc/cpuinfo|grep Serial', shell=True).split(':')[1].strip()
json_string = {'hostname': hostname, 'serial' : serial}

def check_used_space(path):
	return int(''.join(filter(str.isdigit, subprocess.Popen("df -h "+path+" |tail +2| awk '{print $5}'", shell=True, stdout=subprocess.PIPE).communicate()[0])))

def check_cpu_info():
	# bash command to get cpu load from uptime command
	avr = subprocess.Popen("uptime", shell=True, stdout=subprocess.PIPE).communicate()[0]
	avr = avr.split("average:")[1].split(",")
	cores = int(subprocess.Popen("nproc", shell=True, stdout=subprocess.PIPE).communicate()[0])
	avr1 = float(avr[0])
	avr5 = float(avr[1])
	avr15 = float(avr[2])
	cpu_load = float(avr1)/cores*100
	cpu_load = round(float(cpu_load), 1)
	return [cpu_load, cores, avr1, avr5, avr15]

def check_uptime():
	# bash command to get cpu load from uptime command
	uptime = subprocess.Popen("uptime -p", shell=True, stdout=subprocess.PIPE).communicate()[0]
	uptime = uptime.split("up ")[1].strip("\n")
	uptime = uptime.replace("hour", "heure")
	uptime = uptime.replace("day", "jour")
	uptime = uptime.replace("year", "ann\xc3e")
	#print uptime
	return uptime

def check_voltage():
	full_cmd = "vcgencmd measure_volts | cut -f2 -d= | sed 's/000//'"
	voltage = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
	voltage = voltage.strip()[:-1]
	return voltage

def check_swap():
	full_cmd = "free -t | awk 'NR == 3 {print $3/$2*100}'"
	swap = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
	swap = round(float(swap), 1)
	return swap

def check_memory():
	full_cmd = "free -t | awk 'NR == 2 {print $3/$2*100}'"
	memory = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
	memory = round(float(memory), 1)
	return memory		

def check_cpu_temp():
	full_cmd = "vcgencmd measure_temp"
	p = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
	cpu_temp = p.replace('\n', ' ').replace('\r', '').split("=")[1].split("'")[0]
	return cpu_temp

def check_sys_clock_speed():
	full_cmd = "awk '{printf (\"%0.0f\",$1/1000); }' </sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
	return subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]

def check_throttled():
	MESSAGES = {
		0: 'Under-voltage!',
		1: 'ARM frequency capped!',
		2: 'Currently throttled!',
		3: 'Soft temperature limit active',
		16: 'Under-voltage has occurred since last reboot.',
		17: 'Throttling has occurred since last reboot.',
		18: 'ARM frequency capped has occurred since last reboot.',
		19: 'Soft temperature limit has occurred'
	}
	throttled_output = subprocess.check_output('vcgencmd get_throttled', shell=True)
	throttled_binary = bin(int(throttled_output.split('=')[1], 0))
	warnings = 0
	messages = []
	for position, message in MESSAGES.iteritems():
	# Check for the binary digits to be "on" for each warning message
		if len(throttled_binary) > position and throttled_binary[0 - position - 1] == '1':
			#print(message)
			messages.append(message)
			warnings += 1
	return [warnings, messages]

def build_json():
	cpu_info = check_cpu_info()
	if config.cpu_load:
		json_string['cpuload'] = cpu_info[0]
	if config.cpu_average:
		json_string['cpu1m'] = cpu_info[2]
		json_string['cpu5m'] = cpu_info[3]
		json_string['cpu15m'] = cpu_info[4]
	if config.cores:
		json_string['cores'] = cpu_info[1]
	if config.uptime:
		json_string['uptime'] = check_uptime()
	if config.cpu_temp:
		json_string['cputemp'] = check_cpu_temp()
	if config.used_space:
		json_string['diskusage'] = check_used_space('/')
	if config.sys_clock_speed:
		json_string['clockspeed'] = check_sys_clock_speed()
	if config.voltage:
		json_string['voltage'] = check_voltage()
	if config.swap:
		json_string['swap'] = check_swap()
	if config.memory:
		json_string['memory'] = check_memory()
	if config.throttled:
		throttled = check_throttled()
		if throttled[0] == 0:
			json_string['throttled'] = throttled[0]
		else:
			json_string['throttled'] = throttled[1]


if __name__ == '__main__':
	# delay the execution of the script
	time.sleep(config.random_delay)
	#print config.mqtt_topic_prefix
	# connect to mqtt server
	client = paho.Client(serial)
	client.username_pw_set(config.mqtt_user, config.mqtt_password)
	client.connect(config.mqtt_host, config.mqtt_port)
	# Publish messages to MQTT
	build_json()
	client.publish(config.mqtt_topic_prefix+"/"+hostname, json.dumps(json_string), 1)
	time.sleep(config.sleep_time)
	# disconnect from mqtt server
	client.disconnect()
	#print json_string
