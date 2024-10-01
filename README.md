# VPS Management

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
* Smallest config @ $4/mo
* 1 Volumes Block Storage (`/mnt/volume_sfo3_01/`) for hikariita

## How to Use

Install `ansible` on your local dev machine:

```
pip3 install ansible
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

## Logs

```
ssh -i ~/.ssh/id_ed25519.digital_ocean root@147.182.236.144
docker container logs hikariita
```