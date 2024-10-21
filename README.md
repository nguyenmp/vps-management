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

* Ubuntu 22
* 2 GB RAM minimum to run archivebox, otherwise pick the smallest one you can get.
* 4 GB SWAP cause archivebox launches like 10 chrome instances at once (https://itsfoss.com/swap-size/) and 2x RAM seems reasonable at low RAM usages. `sudo fallocate -l 4G /swapfile && ` (https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-ubuntu-20-04)
* 1 Volumes Block Storage (`/mnt/volume_sfo3_01/`) for hikariita

Domains:
* archivebox.href.cat
* changes.href.cat
* hikariita.href.cat

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

```bash
docker compose run archivebox manage createsuperuser
docker compose run archivebox config --set USE_CHROME=false
docker compose run archivebox config --set SAVE_WGET=false
docker compose run archivebox config --set SAVE_WARC=false
docker compose run archivebox config --set SAVE_PDF=false
docker compose run archivebox config --set SAVE_SCREENSHOT=false
docker compose run archivebox config --set SAVE_SINGLEFILE=false
docker compose run archivebox config --set SAVE_GIT=false
# Keep DOM enabled, even though it uses chrome.  One chrome at a time seems fine, not great but it gets past some paywalls.  Also the size is pretty minimal compared to WARC or singlefile which saves all the assets (images) too.
# docker compose run archivebox config --set SAVE_DOM=false

# Trigger an OAUTH login flow for yt-dlp to save tokens in the cache
docker compose exec -it --user archivebox archivebox yt-dlp --cache-dir=/data/yt-dlp-cache/ --write-description --skip-download --write-subs  --username=oauth2 --password= --proxy=socks5://tor-socks-proxy:9150 --write-info-json https://www.youtube.com/watch?v=GYIBYZuwQh4

# Pick up the new config changes and verify via the admin panel
docker compose restart archivebox
```

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
docker compose down && HIKARIITA_DB_FILE=~/code/hikariita/example.db docker compose up -d --wait`
```

Visit http://hikariita.docker.localhost/ for hikariita
Visit http://changes.docker.localhost/ for changedetector.io
Visit http://archivebox.docker.localhost/ for archivebox

Visit http://localhost:8080/dashboard/#/ for traefik dashboard

Finish with the configuration from "How To Use".

## Logs

```
ssh -i ~/.ssh/id_ed25519.digital_ocean root@147.182.236.144
docker container logs hikariita
```

## To rebuild a specific container image (like if you're updating local ArchiveBox)

```
cd ArchiveBox
docker build .
```

If it builds, then commit and push.

https://stackoverflow.com/questions/36884991/how-to-rebuild-docker-container-in-docker-compose-yml

```
docker compose up -d --wait --no-deps --build <service_name>
```

## Updating the server

ssh in, then:

```
docker compose down changedetection
docker pull ghcr.io/dgtlmoon/changedetection.io
docker compose up -d --wait
```

## Cronicle fork

I had to fork docker-cronicle because I was encountering a race condiiton:
https://github.com/soulteary/docker-cronicle/pull/27

The fork works by cloning https://github.com/nguyenmp/docker-cronicle and:

```
docker build --platform linux/amd64 .
docker image list
docker image tag <Image_ID> markerz/cronicle:latest
docker image push markerz/cronicle:latest
```