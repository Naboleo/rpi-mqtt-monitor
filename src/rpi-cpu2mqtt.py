# Python 2 script to check cpu load, cpu temperature and free space,
# on a Raspberry Pi computer and publish the data to a MQTT server.
# RUN pip install paho-mqtt
# RUN sudo apt-get install python-pip

from __future__ import division
import subprocess, time, socket, os
import paho.mqtt.client as paho
import json
import config

# get device host name - used in mqtt topic
hostname = socket.gethostname()


def check_used_space(path):
		used_space= subprocess.Popen("df -h / |tail +2| awk '{print $5}'", shell=True, stdout=subprocess.PIPE).communicate()[0]
		used_space = used_space[:-1]
		return used_space

def check_cpu_info():
		# bash command to get cpu load from uptime command
		p = subprocess.Popen("uptime", shell=True, stdout=subprocess.PIPE).communicate()[0]
		cores = int(subprocess.Popen("nproc", shell=True, stdout=subprocess.PIPE).communicate()[0])
		cpu_load = p.split("average:")[1].split(",")[0].replace(' ', '')
		cpu_load = float(cpu_load)/cores*100
		cpu_load = round(float(cpu_load), 1)
		p=p.split(",")
		avr=p[2].split(": ")
		avr1=float(avr[1])
		avr5=float(p[3])
		avr15=float(p[4])
		up=p[0].split("up")
		print up
		uptime=up[1].strip()
		return [cpu_load,cores,avr1,avr5,avr15,uptime]

def check_cpu_average():
		full_cmd = "cat /proc/loadavg|cut -d' ' -f1-3"
		cpu_average = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]
		return cpu_average
		
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

	
def publish_to_mqtt (cpu_info = [0,0,0,0,0,0], cpu_temp = 0, used_space = 0, voltage = 0, sys_clock_speed = 0, swap = 0, memory = 0):
		# connect to mqtt server
		client = paho.Client()
		client.username_pw_set(config.mqtt_user, config.mqtt_password)
		client.connect(config.mqtt_host, config.mqtt_port)

		# publish monitored values to MQTT
		if config.cpu_load:
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/cpuload", cpu_info[0], qos=1)
			time.sleep(config.sleep_time)
		if config.cores:
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/cores", cpu_info[1], qos=1)
			time.sleep(config.sleep_time)
		if config.cpu_average:
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/cpu1m", cpu_info[2], qos=1)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/cpu5m", cpu_info[3], qos=1)
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/cpu15m", cpu_info[4], qos=1)
			time.sleep(config.sleep_time)
		if config.uptime:
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/uptime", cpu_info[5], qos=1)
			time.sleep(config.sleep_time)
		if config.cpu_temp:
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/cputemp", cpu_temp, qos=1)
			time.sleep(config.sleep_time)
		if config.used_space:
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/diskusage", used_space, qos=1)
			time.sleep(config.sleep_time)
		if config.voltage:
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/voltage", voltage, qos=1)
			time.sleep(config.sleep_time)
		if config.swap:
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/swap", swap, qos=1)
			time.sleep(config.sleep_time)
		if config.memory:
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/memory", memory, qos=1)
			time.sleep(config.sleep_time)
		if config.sys_clock_speed:
			client.publish(config.mqtt_topic_prefix+"/"+hostname+"/sys_clock_speed", sys_clock_speed, qos=1)
			time.sleep(config.sleep_time)
		# disconect from mqtt server
		client.disconnect()

def bulk_publish_to_mqtt (cpu_info = [0,0,0,0,0,0], cpu_temp = 0, used_space = 0, voltage = 0, sys_clock_speed = 0, swap = 0, memory = 0):
		# compose the CSV message containing the measured values
		
		values = cpu_info, float(cpu_temp), used_space, float(voltage), int(sys_clock_speed), swap, memory
		values = str(values)[1:-1]

		# connect to mqtt server
		client = paho.Client()
		client.username_pw_set(config.mqtt_user, config.mqtt_password)
		client.connect(config.mqtt_host, config.mqtt_port)
		
		# publish monitored values to MQTT
		client.publish(config.mqtt_topic_prefix+"/"+hostname, values, qos=1)
		
		# disconect from mqtt server
		client.disconnect()



if __name__ == '__main__':
		# set all monitored values to False in case they are turned off in the config
		cpu_load = cores = cpu_average = cpu_temp = used_space = voltage = sys_clock_speed = swap = memory = False
		
		# delay the execution of the script
		time.sleep(config.random_delay)
		
		# collect the monitored values		
		if config.cpu_load or config.uptime or config.cpu_average or config.uptime:
			cpu_info = check_cpu_info()
		if config.cpu_temp:
			cpu_temp = check_cpu_temp()
		if config.used_space:
			used_space = check_used_space('/')
		if config.voltage:
			voltage = check_voltage() 
		if config.sys_clock_speed:
			sys_clock_speed = check_sys_clock_speed()
		if config.swap:
			swap = check_swap()
		if config.memory:
			memory = check_memory()

		# Publish messages to MQTT
		if config.group_messages:
			bulk_publish_to_mqtt(cpu_info, cpu_temp, used_space, voltage, sys_clock_speed, swap, memory)
		else:
			publish_to_mqtt(cpu_info, cpu_temp, used_space, voltage, sys_clock_speed, swap, memory)
