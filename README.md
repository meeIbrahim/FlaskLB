# FlaskLB
## Getting Started
### Pre-requisites:
  - Docker Engine
  - Docker Compose
  - Linux OS

### Running the Application
  - Clone the main branch
  - CD into the directoy
  - Run "docker compose up -d"
  - To Stop: Run "docker compose down -v --remove-orphans"
  
## Application Working
  Multi Container App that includes one haproxy loadbalancer, one daemon to control child containers and one flask application container.
  When Stress is increased within the flask container, daemon container spins up a new container and configures haproxy to loadbalance between old flask
  and new flask container. If load is reduced below a certain threshold, and cerrtain time has elapsed since last cpu bottleneck, new containers are removed
  
## To do
 - Include Environment Variables for configuring the Application
