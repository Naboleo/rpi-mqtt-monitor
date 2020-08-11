from random import randrange

# MQTT server configuration
mqtt_host = "192.168.1.49"
mqtt_user = "jeedom"
mqtt_password = "cc2531"
mqtt_port = "1883"
# Messages configuration
mqtt_topic_prefix = "pi2mqtt"

# Random delay in seconds before measuring the values 
# - this is used for de-synchronizing message if you run this script on many hosts, set this to 0 for no delay.
# - if you want a fix delay you can remove the randarnge function and just set the needed delay.
random_delay = randrange(30)

# This is the time  between sending the indivudual messages
sleep_time = 1
cpu_load = True
cpu_temp = True
used_space = True
voltage = True
sys_clock_speed = True
swap = False
memory = True
cpu_average = True
cores = True
uptime = True
throttled = True
