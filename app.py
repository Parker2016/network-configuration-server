from flask import Flask, render_template, request
import os,re
import yaml, subprocess, time
app = Flask(__name__)

def check_internet_connection():
    try:
        result = subprocess.run(['ping', '-c', '1', 'google.com'], capture_output=True, text=True)
        if result.returncode == 0:
            print("System is connected to the internet.")
            return 1
        else:
            print("System is not connected to the internet.")
            return 0
    except Exception as e:
        print("An error occurred:", e)
        return 0

def is_valid_ipv4(ip):
    ipv4_pattern = r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    
    if re.match(ipv4_pattern, ip):
        return True
    else:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_network_settings', methods=['POST'])
def update_network_settings():
    ip = request.form['ip']
    subnet_mask = request.form['subnet_mask']
    gateway = request.form['gateway']
    if not is_valid_ipv4(ip):
        return "Wrong IP format"
    try:
        if not 1<= int(subnet_mask) <= 32:
            return "Wrong subnet mask format"
    except:
        return "Wrong subnet mask format"
    if not is_valid_ipv4(gateway):
        return "Wrong gateway format"
    interface_command = "ip a | grep 10.10.10.10 | awk '{print $7}'"
    interface = subprocess.check_output(interface_command, shell=True)
    interface = interface.decode('utf-8')
    interface = interface.strip('\n')
    network = {
        "network": {
            "ethernets": {
                interface: {
                    "dhcp4": False,
                    "dhcp6": False,
                    "addresses": ["10.10.10.10/16", "{0}/{1}".format(ip, subnet_mask), "2001:aaaa::1/64"],
                    "nameservers": {
                        "addresses": ["192.168.123.10", "8.8.8.8"]
                    },
                    "routes": [{"to": "default", "via": gateway}]
                }
            },
            "version": 2
        }
    }
    with open('00-installer-config.yaml', 'w') as file:
        yaml.dump(network, file)
    SUDO_COMMAND = "sudo -S cp 00-installer-config.yaml /etc/netplan"
    PASSWORD = "admin12345"
    os.system("echo {0} | {1}".format(PASSWORD, SUDO_COMMAND))
    os.system("sudo netplan apply")
    time.sleep(3)
    ret = check_internet_connection()
    if ret == 1:
        print("Install OAM")
        # os.system("bash check_k8s.sh")
        return 'Network settings updated successfully!'
    else:
        print("No internet")
        return 'The configured network cannot connect to the internet.'


if __name__ == '__main__':
    app.run(debug=True, host="10.10.10.10", port=8380)