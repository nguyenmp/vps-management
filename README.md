# VPS Management

https://github.com/nguyenmp/vps-management

My old VPS is a mystery now.  It has an uptime of 7+ years and is running at 100% CPU because of a rogue script I kicked off into the background and I have no idea if it's necessary or what.  As such, I'm trying to get my VPS under version control and automation!

I use ansible to do initial setup of the main machine and then docker to run my specific projects and apps (like hikariita).

## Initial Access (SSH, SCP)

I run off Digital Ocean droplets.  At a high level: use digital ocean to get a console, and curl append your SSH keys to the authorized host to get ssh and scp access.

0. `ssh-keygen` to generate a key-pair (name it something specific to digital ocean like id_ed25519.digital_ocean)
1. Upload your `id_*.pub` key to a public github gist (must contain `*.pub` or else it's a private key)
2. On the droplet in the Console through the web UI, `curl raw_url >> ~/.ssh/authorized_keys` to permit this key

Now you should have SSH access:
```
scp -i ~/.ssh/id_ed25519.digital_ocean ./example.db root@147.182.236.144:/mnt/volume_sfo3_01/hikariita/
ssh -i ~/.ssh/id_ed25519.digital_ocean root@147.182.236.144
```

## Config

Anything weird I might need to know:

* Ubuntu 26
* 2 GB RAM minimum, otherwise pick the smallest one you can get.
* 2 GB buffer file `fallocate -l 2G ~/buffer_file.2G.txt` to delete if we run out of disk space
* 8 GB SWAP (https://itsfoss.com/swap-size/). `sudo fallocate -l 8G /swapfile && ` (https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-ubuntu-20-04)
* Transfer to new host using `rsync -avz --partial --delete --progress root@vps.href.cat:~/vps-management/ ~/vps-management/`
* Install docker-ce https://community.hetzner.com/tutorials/howto-docker-install#step-1---installing-docker-engine
* 1 Volumes Block Storage (`/mnt/HC_Volume_106261021/`) for docker images so that they don't take up unnecessary backup space. https://stackoverflow.com/questions/24309526/how-to-change-the-docker-image-installation-directory
```
cat /etc/docker/daemon.json 
{
  "data-root": "/mnt/HC_Volume_106261021/docker"
}

# Also update containerd https://docs.docker.com/engine/storage/containerd/
# https://docs.docker.com/engine/daemon/#configure-the-data-directory-location
cat /etc/containerd/config.toml
root = "/mnt/HC_Volume_106261021/containerd"

systemctl daemon-reload
systemctl restart docker containerd
docker run hello-world # should create in the mount/docker/containers
```
* Backup snapshots via n8n via API
* When changing hosts, you should update inventory.ini with the new host IP
* You should also update the hostname under `GCLOUD_FM_COLLECTOR_ID` in `envs/production.env` to support alloy (grafana) and redeploy alloy

Domains:
* changes.href.cat
* hikariita.href.cat

## Monitoring

I use [the basic system monitoring provided by DigitalOcean](https://cloud.digitalocean.com/droplets/448047765/graphs) with alerts on sustained high CPU and disk (85%).

These metrics are [duplicated in Grafana Cloud](https://hrefcat.grafana.net/d/mgzd8tw/os-metrics) for more history and better granularity and detail.

I also have [container level metrics in Grafana Cloud](https://hrefcat.grafana.net/d/mglw6wx/new-dashboard) to diagnose specific container issues.

I use [Portainer to manage individual containers (logs, stats, recreating, updating/pulling)](https://portainer.href.cat/).  Anything that wouldn't require a change to the compose.yaml.  New services I stand up through ansible.  Ansible also handles system upgrades whereas portainer only handles containers.

## How to Use

Install `ansible` on your local dev machine:

```
pip3 install ansible

# force was necessary cause of https://github.com/geerlingguy/internet-pi/issues/577
ansible-galaxy collection install community.docker community.crypto --force
```

Make sure new host is defined in `inventory.ini` and that we have SSH access (see https://github.com/nguyenmp/hikariita for details on SSH)

Ping hosts defined in `inventory.ini`

```
ansible myhosts -m ping -i inventory.ini -u root --key-file ~/.ssh/id_ed25519.digital_ocean
```

Run playbook to set up VPS:

```
ansible-playbook -i inventory.ini playbook.yaml --key-file ~/.ssh/id_ed25519.digital_ocean -u root
```

Set up specific services if first run (via SSH on remote machine):

Add password to changes.href.cat (under Settings in web UI)

Set poll interval to 1 minute (instead of 3 hours)

Add base email notifications for changes.href.cat (Settings > Notifications) w/ email account configured on my mail server:
mailtos://password@href.cat:587?user=changedetection@href.cat&smtp=banshee.mxlogin.com&to=personal_email@gmail.com

## Setup docker locally

Install Docker Desktop: https://www.docker.com/products/docker-desktop/

Do the initial SSH access above.

Fetch a seeded DB:

```bash
scp -i ~/.ssh/id_ed25519.digital_ocean root@147.182.236.144:/mnt/volume_sfo3_01/hikariita/ ~/code/hikariita/example.db
```

Then run compose up:
```bash
docker compose --env-file ./envs/local.env down && docker compose --env-file ./envs/local.env up -d --wait
```

Visit http://hikariita.docker.localhost/ for hikariita
Visit http://changes.docker.localhost/ for changedetector.io

Visit http://localhost:8080/dashboard/#/ for traefik dashboard

Finish with the configuration from "How To Use".

## Logs

```
ssh -i ~/.ssh/id_ed25519.digital_ocean root@147.182.236.144
docker container logs hikariita
```

## Updating the server

Consider updating traefik while you're at it, it's a hardcoded version whereas everything else is "latest".

Sync https://github.com/nguyenmp/ArchiveBox#dev with upstream (might take a while get back on mainline, it's pretty hacked):
```
git clone https://github.com/nguyenmp/ArchiveBox.git
git remote add upstream https://github.com/ArchiveBox/ArchiveBox.git
git fetch upstream
git merge upstream/dev
git push
```

Sync https://github.com/nguyenmp/docker-cronicle/ (see if we're behind first) with upstream (https://github.com/jhuckaby/Cronicle/releases) (should be removed after the https://github.com/soulteary/docker-cronicle/pull/27 race condition fix is merged or addressed):
```
git clone https://github.com/nguyenmp/docker-cronicle.git
git remote add upstream https://github.com/soulteary/docker-cronicle.git
git fetch upstream
git merge upstream/main

# Update version reference to latest 0.9.59 -> 0.9.61 https://github.com/jhuckaby/Cronicle/releases
sed -i '.bak' 's/0.9.59/0.9.61/g' # but do it in vscode instead

git commit

cd docker
docker build --platform linux/amd64 . -t markerz/cronicle:latest
docker image push markerz/cronicle:latest
git push
```

ssh in, then:

```

# Save these outputs in case things go wrong
docker container list
docker image ls

# Try updating!
docker compose --env-file ./envs/local.env pull
docker compose --env-file ./envs/local.env down  # Optional downtime to force restart all containers
docker compose --env-file ./envs/local.env up -d --remove-orphans --wait --build hikariita # Needs to be rebuilt from source cause git doesn't automatically update
docker compose --env-file ./envs/local.env up -d --wait

# Clean up
docker system prune -a

# Also update the OS and packages
aptitude update
aptitude upgrade

# And do a reboot to clear out temp (don't run docker down, it'll prevent containers from restarting)
reboot
```

## Adding packages to n8n

In Dockerfile, add the package.

```
docker compose --env-file envs/local.env build  --no-cache n8n
docker compose --env-file envs/local.env up --detach --wait n8n
```

## Manually backup postgres

```
docker compose --env-file ./envs/local.env exec -it pgbackups3 /bin/sh backup.sh
```

And how to restore from backup:

```
pg_restore -h localhost -p 5432 -U postgres -d postgres postgres_2024-10-28T19_26_17.dump
```

## Run migrations for recipes

```bash
# Local
docker build --platform linux/amd64 -t markerz/recipes:latest .

# VPS-Management local
docker compose --env-file ./envs/local.env up -d --wait --no-deps recipes
docker compose --env-file ./envs/local.env exec -it recipes /bin/sh -c "pnpm migrate"

# Production run ansible playbook
docker image push markerz/recipes:latest
ansible ...
docker compose --env-file ./envs/production.env exec -it recipes /bin/sh -c "pnpm migrate"
```

## Reconquer deploy

```
cd frontend
docker build . -t markerz/reconquer.online.cli --platform linux/amd64
docker push markerz/reconquer.online.cli

cd backend
docker build . -t markerz/reconquer.online.backend --platform linux/amd64
docker push markerz/reconquer.online.backend

ansible ...

docker container logs -f --since 1m ...
```
