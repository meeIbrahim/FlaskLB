import docker
import time
import re


BACKEND_PORT = 5000
BACKEND_SERVER_NAME = 'flask-{}'
DOCKER_BASE_URL = 'unix://var/run/docker.sock'
NETWORK = 'flask-lb'
CONTAINER_IMAGE = 'flask-image'
HAPROXY = 'ha_proxy'
DAEMON  = 'lb-daemon'
CPU_THRESHOLD = 10
CFG_FILE = './haproxy/haproxy.cfg'


class Daemon:
    
    def __init__(self,client: docker.DockerClient):
        start_time = 0
        self.client = client
        while True:
            running_containers = self.client.containers.list(filters={'network': NETWORK})
            flask_servers = [container for container in running_containers if container.name != HAPROXY if container.name != DAEMON]
            total_cpu = 0
            server_count = len(flask_servers)
            print(f"Server Count: {server_count}")
            if server_count == 0:
                continue
            for server in flask_servers:
                total_cpu = total_cpu + self.getCPU(server)
            cpu = total_cpu / server_count
            if cpu > CPU_THRESHOLD:
                start_time = 0
                self.startContainer(server_count)
            elif cpu < 5 and server_count > 1:
                if start_time == 0:
                    start_time = time.time()
                elif (time.time()-start_time) == 5:
                    self.stopContainer(server_count)
                    
    def __del__(self):
        running_containers = self.client.containers.list(filters={'network': NETWORK})
        flask_servers = [container for container in running_containers if container.name != HAPROXY if container.name != DAEMON]
        for i in range(len(flask_servers),-1,-1):
            self.stopContainer(i)


    def getCPU(self,server):
        metric =  server.stats(stream=False)
        cpu_percent = 0.0 
        cpu_delta = float(metric['cpu_stats']['cpu_usage']['total_usage']) - \
                    float(metric['precpu_stats']['cpu_usage']['total_usage'])
        system_delta = float(metric['cpu_stats']['system_cpu_usage']) - \
                    float(metric['precpu_stats']['system_cpu_usage'])
        
        if system_delta > 0.0:
            cpu_percent = cpu_delta / system_delta * 100.0 * metric['cpu_stats']['online_cpus']
        return cpu_percent

    def startContainer(self,count):
        server = BACKEND_SERVER_NAME.format(count+1)
        client = self.client
        client.containers.run(CONTAINER_IMAGE,network=NETWORK,name=server,detach=True)
        self.AddServer(count+1)
        haproxy = client.containers.get(container_id=HAPROXY)
        haproxy.kill(signal='HUP')
        
    def stopContainer(self,count):
        client = self.client
        server = client.containers.get(container_id=BACKEND_SERVER_NAME.format(count))
        self.RemoveServer(count)
        haproxy = client.containers.get(container_id=HAPROXY)
        haproxy.kill(signal='HUP')
        server.stop()
        server.remove()
        
        
    def RemoveServer(self,count):
        server = BACKEND_SERVER_NAME.format(count)
        print(f"Removing {server}")
        with open(CFG_FILE,'r') as file:
            buf = file.readlines()
        with open(CFG_FILE,'w') as file:
            for line in buf:
                if not server in line:
                    file.write(line)
                    
    def AddServer(self,count):
        server = BACKEND_SERVER_NAME.format(count)
        last_server = BACKEND_SERVER_NAME.format(count-1)
        print(f"Adding {server}")
        with open(CFG_FILE,'r') as file:
            buf = file.readlines()
        with open(CFG_FILE,'w') as file:
            for line in buf:
                file.write(line)
                if last_server in line:
                    new_line = re.sub(fr'(server).*{last_server}(:.*)',rf'\1 {server} {server}\2',line)
                    file.write(f'{new_line}')
            
            
if __name__=='__main__':
    Daemon(client = docker.DockerClient(base_url=DOCKER_BASE_URL)) 