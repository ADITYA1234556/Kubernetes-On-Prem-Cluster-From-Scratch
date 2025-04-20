#

- Create a new User 
```bash
sudo useradd --system --no-create-home --shell /bin/false prometheus
```
- Get the latest version of prometheus from the <a href="https://prometheus.io/download/">downloads page</a>
```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.53.4/prometheus-2.53.4.linux-amd64.tar.gz
tar -xvzf prometheus-2.53.4.linux-amd64.tar.gz
mv prometheus-2.53.4.linux-amd64 prometheus
sudo mkdir -p /data /etc/prometheus
cd prometheus/
sudo mv prometheus promtool /usr/local/bin/ 
sudo mv consoles/ console_libraries/ /etc/prometheus/
sudo mv prometheus.yml /etc/prometheus/
sudo chown -R prometheus:prometheus /etc/prometheus/ /data/
prometheus --version
```
- Create systemd configuration file for prometheus service
```bash
cat <<-EOF | sudo tee /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus Monitoring System
Documentation=https://prometheus.io/docs/introduction/overview/
Wants=network-online.target #Specifies that the Prometheus service wants the network to be online before it starts
After=network-online.target #Specifies that the Prometheus service should start after the network-online.target is reached
StartLimitIntervalSec=500
StartLimitBurst=5 #Systemd Attempts to restart prometheus 5 times if it fails it will wait for 500 seconds, before retrying another 5 times.

[Service]
User=prometheus
Group=prometheus
Type=simple 
Restart=on-failure
RestartSec=5
StandardOutput=journal #Sends the standard output of the Prometheus process to the systemd journal. You can view these logs using journalctl -u prometheus
StandardError=inherit
LimitNOFILE=65535 #Sets the maximum number of open files that the Prometheus process can have. This is often necessary for database-heavy applications.
ExecStart=/usr/local/bin/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/data \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries \
    --web.listen-address=0.0.0.0:9090 \
    --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable prometheus
sudo systemctl start prometheus
sudo systemctl status prometheus
journalctl -u prometheus -f
```
- Access the prometheus at "http:serverIP:9090"
- To view the targets -> status -> Targets

## We will set up Node Exporter To collect OS Metrics
- Similar process to install node exporter, Create a user
```bash
sudo useradd --system --no-create-home --shell /bin/false node_exporter
```
- Install Node Exporter 
```bash
wget https://github.com/prometheus/node_exporter/releases/download/v1.9.1/node_exporter-1.9.1.linux-amd64.tar.gz
tar -xvzf node_exporter-1.9.1.linux-amd64.tar.gz
cd node_exporter-1.9.1.linux-amd64/
sudo mv node_exporter /usr/local/bin/
node_exporter --help
cat <<-EOF | sudo tee /etc/systemd/system/node_exporter.service
[Unit]
Description=Node Exporter Monitoring System
Documentation=https://prometheus.io/docs/introduction/overview/
Wants=network-online.target 
After=network-online.target 
StartLimitIntervalSec=500
StartLimitBurst=5 

[Service]
User=node_exporter
Group=node_exporter
Type=simple
Restart=on-failure
RestartSec=5
ExecStart=/usr/local/bin/node_exporter \
    --collector.logind

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable node_exporter
sudo systemctl start node_exporter
sudo systemctl status node_exporter
journalctl -u node_exporter -f
``` 

## Setup BlackBox Exporter
- Create a user
```bash
sudo useradd --system --no-create-home --shell /bin/false blackbox_exporter
```
- Download the binaries and install
```bash
wget https://github.com/prometheus/blackbox_exporter/releases/download/v0.26.0/blackbox_exporter-0.26.0.linux-amd64.tar.gz
tar -xvzf blackbox_exporter-0.26.0.linux-amd64.tar.gz
cd blackbox_exporter-0.26.0.linux-amd64/
sudo mv blackbox_exporter /usr/local/bin/
blackbox_exporter --help
sudo mkdir -p /etc/blackbox
sudo mv blackbox.yml /etc/blackbox/
cat <<-EOF | sudo tee /etc/systemd/system/blackbox_exporter.service
[Unit]
Description=Blackbox Exporter
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=500
StartLimitBurst=5 

[Service]
User=blackbox_exporter 
Group=blackbox_exporter 
Type=simple
ExecStart=/usr/local/bin/blackbox_exporter \
 --config.file=/etc/blackbox/blackbox.yml \
 --web.listen-address=:9115
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=inherit


[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable blackbox_exporter
sudo systemctl start blackbox_exporter
sudo systemctl status blackbox_exporter
```

## Setup PushGateway
- Used to push metrics from jobs that allows us to monitor jobs and cron jobs
- Create user
```bash
sudo useradd --system --no-create-home --shell /bin/false pushgateway
```
- Install push gateway
```bash
wget https://github.com/prometheus/pushgateway/releases/download/v1.11.1/pushgateway-1.11.1.linux-amd64.tar.gz
tar -xvzf pushgateway-1.11.1.linux-amd64.tar.gz
cd pushgateway-1.11.1.linux-amd64/
sudo mv pushgateway /usr/local/bin
cat <<-EOF | sudo tee /etc/systemd/system/pushgateway.service
[Unit]
Description=Blackbox Exporter
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=500
StartLimitBurst=5 

[Service]
User=pushgateway 
Group=pushgateway 
Type=simple
ExecStart=/usr/local/bin/pushgateway
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=inherit


[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable pushgateway
sudo systemctl start pushgateway
sudo systemctl status pushgateway
```
- Send metrics to pushgateway
- Create a script, to constantly send this data for testing. Imagining we will have a jenkins job that ran for 10.24 seconds
```bash
cat <<-EOF | sudo tee /home/ubuntu/bash.sh
#!/bin/bash
echo "jenkins_job_duration_seconds 10.24" | curl --data-binary @- http://localhost:9091/metrics/job/backup
EOF
cd $HOME
sudo chmod +x bash.sh
nohup /home/ubuntu/bash.sh &
```

## Alert Manager
- Used to send alerts metrics from jobs that allows us to monitor jobs and cron jobs
- Create user
```bash
sudo useradd --system --no-create-home --shell /bin/false alertmanager
```
- Install push gateway
```bash
wget https://github.com/prometheus/alertmanager/releases/download/v0.28.1/alertmanager-0.28.1.linux-amd64.tar.gz
tar -xvzf alertmanager-0.28.1.linux-amd64.tar.gz
cd alertmanager-0.28.1.linux-amd64/
sudo mkdir -p /alertmanager-data /etc/alertmanager
sudo mv alertmanager /usr/local/bin/
alertmanager --help
sudo mv alertmanager.yml /etc/alertmanager/
cat <<-EOF | sudo tee /etc/systemd/system/alertmanager.service
[Unit]
Description=alertmanager 
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=500
StartLimitBurst=5 

[Service]
User=alertmanager 
Group=alertmanager 
Type=simple
ExecStart=/usr/local/bin/alertmanager \
  --storage.path=/alertmanager-data \
  --config.file=/etc/alertmanager/alertmanager.yml
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=inherit


[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable alertmanager
sudo systemctl start alertmanager
sudo systemctl status alertmanager
```
- Create a simple alert
```bash
cat <<-EOF | sudo tee /etc/prometheus/simple-alert-rule.yml
groups:
- name: simple-alert
  rules:
  - alert: SimpleAlert
    annotations:
      message: This will be the alert message
    expr: vector(1)
EOF
```
- Update prometheus.yml
```bash
promtool check config /etc/prometheus/prometheus.yml
sudo systemctl restart prometheus
```
- Alerts from alert manager can be sent to slack, pagerduty, etc.
- Now lets try to send an aler to Slack
- Create a slack channel.
- Create an app from scratch using<a href="https://api.slack.com/apps">slack api</a>. Name=Anything Workspace=where the channel is created 
    1. Enable incoming webhooks 
    2. Add webhook to the workspace
    3. Copy the webhook URL and use it in **alertmanager.yml**
- Adding this entry to alertmanager.yml in /etc/alertmanager/alertmanager.yml
```yaml
  routes:
  - receiver: slack-notifications
    match:
      severity: warning
receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://127.0.0.1:5001/'
  - name: slack-notifications
    slack_configs:
    - channel: "alertmanager"
      send_resolved: true
      api_url: 'https://hooks.slack.com/services/<TOKENHERE>'
      title: "{{ .GroupLabels.alertname }}"
      text: "{{ range.Alerts}}{{ .Annotations.message}}\n{{end}}"
```
- Restart alert manager 
```bash
sudo systemctl restart alertmanager
```
- Now include batch job rules in prometheus at /etc/prometheus/job-rules.yml
```bash
cat <<-EOF | sudo tee /etc/prometheus/job-rules.yml
groups:
- name: job-rules-simple
  rules:
  - alert: JenkinsJobExceededThreshold
    annotations:
      message: Jenkins Job exceeded treshold of 30 seconds.
    expr: jenkins_job_duration_seconds{job="backup"} > 30
    for: 1m
    labels:
      severity: warning
EOF
```
- Add a new rule to prometheus
```bash
rule_files:
    - job-rules.yml
```
- Create alert to see if it gets received in slack. Send this request. If treshold crosses more than 30 as mentioned in job-rules.yml slack notification will be sent.
```bash
echo "jenkins_job_duration_seconds 40.24" | curl --data-binary @- http://localhost:9091/metrics/job/backup
```


## Set up targets on Prometheus
- Edit the prometheus.yaml configuration file to add targets
```bash
sudo vi /etc/prometheus/prometheus.yml
```
- Check if config is valid
```bash
promtool check config /etc/prometheus/prometheus.yml
#Checking /etc/prometheus/prometheus.yml
# SUCCESS: /etc/prometheus/prometheus.yml is valid prometheus config file syntax
```
- Reload the prometheus without restarting the service.
```bash
curl -X POST http://localhost:9090/-/reload
```


## To visualize metrics we will install grafana
- To install grafana <a href"https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/">Grafana</a>
```bash
sudo apt-get install -y apt-transport-https software-properties-common wget 
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
sudo systemctl status grafana-server
```
- Access the UI at http://IP:3000, uname:admin, password:admin
- Add datasource -> Grafana UI -> Connections -> Add new connection -> Prometheus. For the URL, private IP of prometheus http://IP:9090 Save and Test
- Another way through console
```bash
cat <<-EOF | sudo tee /etc/grafana/provisioning/datasources/datasources.yaml
apiVersion: 1
datasources: 
    - name: Prometheus
      type: prometheus
      url: http://172.31.25.232:9090
      isDefault: true
EOF
sudo systemctl restart grafana-server
sudo systemctl status grafana-server
```

## Dashboards.
- We can use grafana pre-build dashboards, that queries the metrics and visualizes. View the available <a href="https://grafana.com/grafana/dashboards/">grafana dashboards</a>
- We can also select custom queries from prometheus metric query and create our own dashboard.
- To create a custom dashboard, Go to http://promethues:9090/, Explore what metrics we have.
- Seacrh for "scrape_duration_seconds" and execute. It will show all the targets and scape duration in seconds
- We will use this query to create new dashboard
- Go to grafana UI -> dashboard -> new dashboard -> Add Visualization -> Select data source -> We added prometheus in /etc/grafana/provisioning/datasources/datasources.yaml that should show.
- We can give title and description -> Select datasource -> Metric -> Metric explorer ->Search "scrape_duration_seconds" SELECT -> reduce time interval
