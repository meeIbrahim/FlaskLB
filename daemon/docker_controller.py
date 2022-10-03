import docker
import time
import re


BACKEND_PORT = 5000
BACKEND_SERVER_NAME = 'flask-{}'
DOCKER_BASE_URL = 'unix://var/run/docker.sock'
NETWORK = 'flask-lb'
CONTAINER_IMAGE = 'flask-image'
HAPROXY = 'ha_proxy'
CPU_THRESHOLD = 10



def main(client: docker.DockerClient):
    start_time = 0
    while True:
        running_containers = client.containers.list(filters={'network': NETWORK})
        flask_servers = [container for container in running_containers if container.name != HAPROXY]
        total_cpu = 0
        for server in flask_servers:
            total_cpu = total_cpu + getCPU(server)
        cpu = total_cpu / len(flask_servers)
        if cpu > CPU_THRESHOLD:
            start_time = 0
            startContainer(client,len(flask_servers))
        elif cpu < 5 and len(flask_servers) > 1:
            if start_time == 0:
                start_time = time.time()
            elif (time.time()-start_time) == 5:
                stopContainer(client,len(flask_servers))


def getCPU(server):
    metric =  server.stats(stream=False)
    cpu_percent = 0.0 
    cpu_delta = float(metric['cpu_stats']['cpu_usage']['total_usage']) - \
                float(metric['precpu_stats']['cpu_usage']['total_usage'])
    system_delta = float(metric['cpu_stats']['system_cpu_usage']) - \
                float(metric['precpu_stats']['system_cpu_usage'])
    
    if system_delta > 0.0:
        cpu_percent = cpu_delta / system_delta * 100.0 * metric['cpu_stats']['online_cpus']
    return cpu_percent

def startContainer(client: docker.DockerClient,count):
    print("START")
    server = BACKEND_SERVER_NAME.format(count+1)
    client.containers.run(CONTAINER_IMAGE,network=NETWORK,name=server,detach=True)
    AddServer(count+1)
    haproxy = client.containers.get(container_id=HAPROXY)
    haproxy.kill(signal='HUP')
    
def stopContainer(client: docker.DockerClient,count):
    print("STOP")
    server = client.containers.get(container_id=BACKEND_SERVER_NAME.format(count))
    RemoveServer(count)
    haproxy = client.containers.get(container_id=HAPROXY)
    haproxy.kill(signal='HUP')
    server.stop()
    server.remove()
    
    
def RemoveServer(count):
    server = BACKEND_SERVER_NAME.format(count)
    with open('.haproxy.cfg','r') as file:
        buf = file.readlines()
    with open('./haproxy.cfg','w') as file:
        for line in buf:
            if not server in line:
                file.write(line)
                
def AddServer(count):
    server = BACKEND_SERVER_NAME.format(count)
    last_server = BACKEND_SERVER_NAME.format(count-1)
    
    with open('./haproxy.cfg','r') as file:
        buf = file.readlines()
    with open('./haproxy.cfg','w') as file:
        for line in buf:
            file.write(line)
            if last_server in line:
                new_line = re.sub(fr'(server).*{last_server}(:.*)',rf'\1 {server} {server}\2',line)
                file.write(f'{new_line}')
            
            
if __name__=='__main__':
    main(client = docker.DockerClient(base_url=DOCKER_BASE_URL)) 