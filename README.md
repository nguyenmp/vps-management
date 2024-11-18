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
docker compose --env-file ./envs/local.env run archivebox manage createsuperuser
docker compose --env-file ./envs/local.env run archivebox config --set USE_CHROME=false
docker compose --env-file ./envs/local.env run archivebox config --set SAVE_WGET=false
docker compose --env-file ./envs/local.env run archivebox config --set SAVE_WARC=false
docker compose --env-file ./envs/local.env run archivebox config --set SAVE_PDF=false
docker compose --env-file ./envs/local.env run archivebox config --set SAVE_SCREENSHOT=false
docker compose --env-file ./envs/local.env run archivebox config --set SAVE_SINGLEFILE=false
docker compose --env-file ./envs/local.env run archivebox config --set SAVE_GIT=false
# Keep DOM enabled, even though it uses chrome.  One chrome at a time seems fine, not great but it gets past some paywalls.  Also the size is pretty minimal compared to WARC or singlefile which saves all the assets (images) too.
# docker compose --env-file ./envs/local.env run archivebox config --set SAVE_DOM=false

# Follow the following url to create a cookies.txt file
https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies
# I used the following Firefox extension:
https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
"YT_DLP_COOKIES_FILE=./envs/cookies.txt" >> local.env

# Pick up the new config changes and verify via the admin panel
docker compose --env-file ./envs/local.env restart archivebox
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
docker compose --env-file ./envs/local.env down && docker compose --env-file ./envs/local.env up -d --wait
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

Based on https://docs.archivebox.io/dev/README.html#setup-the-dev-environment

Rebase onto latest released version: https://hub.docker.com/r/archivebox/archivebox/tags

```
cd ArchiveBox
git submodule update --init --recursive
# git pull --recurse-submodules
docker build --platform linux/amd64 -t markerz/archivebox:latest -t markerz/archivebox:v0.8.5rc51 .
```

If it builds, then commit and push.

https://stackoverflow.com/questions/36884991/how-to-rebuild-docker-container-in-docker-compose-yml

```
docker compose --env-file ./envs/local.env up -d --wait
docker image push markerz/archivebox:v0.8.5rc51
docker image push markerz/archivebox:latest
ansible ...
```

Note: Sometimes upgrading (or downgrading) will break chromium because the persona version is wrong.  In this case, just delete personal directory in the /data/ folder.  You'll find out when you run a chromium command and get:

```
The profile appears to be in use by another Chromium process (531) on another computer (f6a12c579e02). Chromium has locked the profile so that it doesn't get corrupted. If you are sure no other processes are using this profile, you can unlock the profile and relaunch Chromium
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
git merge upstream/dev

# Update version reference to latest 0.9.59 -> 0.9.61 https://github.com/jhuckaby/Cronicle/releases
sed -i '.bak' 's/0.9.59/0.9.61/g' # but do it in vscode instead

git commit
git push

cd docker
docker build --platform linux/amd64 .
docker image list
docker image tag <Image_ID> markerz/cronicle:latest
docker image push markerz/cronicle:latest
```

ssh in, then:

```

# Save these outputs in case things go wrong
docker container list
docker image ls

# Try updating!
docker compose --env-file ./envs/local.env pull
docker compose --env-file ./envs/local.env down  # Optional downtime to force restart all containers
docker compose --env-file ./envs/local.env up -d --remove-orphans --wait --build hikariita archivebox # Needs to be rebuilt from source cause git doesn't automatically update
docker compose --env-file ./envs/local.env up -d --wait

# Clean up?
docker system prune
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
docker image push markerz/recipes:latest

# VPS-Management local
docker compose --env-file ./envs/local.env pull recipes
docker compose --env-file ./envs/local.env up -d --wait --no-deps recipes
docker compose --env-file ./envs/local.env exec -it recipes /bin/sh -c "pnpm migrate"

# Production run ansible playbook
ansible ...
docker compose --env-file ./envs/production.env exec -it recipes /bin/sh -c "pnpm migrate"
```