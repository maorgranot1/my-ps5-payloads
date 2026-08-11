# my-ps5-payloads

An automated repository and custom build system for managing PlayStation 5 payloads. 

This project serves two main purposes:
1. **Automated Payload Registry**: It maintains a constantly updated JSON registry (`P.json`) of popular PS5 payloads (like etaHEN, kstuff, and ShadowMountPlus) by scraping their official GitHub/GitLab releases.
2. **Custom Payload Manager Builder**: It automatically tracks, patches, and compiles a custom version of [itsPLK's Payload Manager](https://github.com/itsPLK/ps5-payload-manager), adding custom autoloader mirroring and hardcoding this repository as the default payload source.

---

## 🚀 Features

* **Zero-Maintenance Payload Updates**: A daily Python script checks for new releases of tracked payloads, verifies/calculates their SHA-256 checksums, and updates the registry automatically.
* **Custom Autoloader Integration**: The custom-built `pldmgr.elf` patches the official C code to automatically copy specific payloads (`kstuff.elf`, `shadowmountplus.elf`, and `pldmgr.elf`) directly to `/data/ps5_autoloader` upon installation.
* **GitHub Pages Hosted API**: The `P.json` registry is automatically deployed to GitHub Pages, acting as a live endpoint for the Payload Manager app.
* **Fully Dockerized Build**: The PS5 SDK compilation process runs cleanly within a GitHub Actions Ubuntu runner using Docker.

---

## 📦 Tracked Payloads

This repository automatically tracks and updates the following payloads in `P.json`:

* **ftpsrv**: Simple FTP server (port 2121)
* **PS5 Game Compressor**: Background service to compress installed games
* **Garlic SaveMgr**: Game save extraction and backup utility
* **kstuff-lite**: Kernel patcher for unsigned game packages
* **nanoDNS**: Lightweight DNS proxy to block Sony update servers
* **ShadowMountPlus**: Virtual directory mounter for game packages/disk images
* **Payload Manager (Custom)**: The web-based dashboard compiled by this repository
* **etaHEN**: All-in-one payload for unsigned games and debug settings
* **Elf Arsenal**: Centralized dashboard for managing payloads

---

## ⚙️ How It Works (GitHub Actions)

This repository relies heavily on GitHub Actions to fully automate the ecosystem:

1. **Daily Release Checker (`update-json.yml`)**
   Runs `update_releases.py` every day at 14:42 UTC. It queries the APIs of tracked payloads, detects version bumps, calculates missing SHA-256 hashes, and commits any changes to `P.json`.
   *(Note: Uses a `PAT_TOKEN` to ensure the resulting commit triggers the Pages deployment workflow).*

2. **Deploy Pages (`deploy-pages.yml`)**
   Listens for changes to `P.json`. When triggered, it securely deploys the updated JSON file to GitHub Pages, making it instantly available to the PS5 Payload Manager app.

3. **Auto-Build Custom pldmgr (`AutoBuildPldmgr.yml`)**
   Runs daily to check for new releases from the upstream `itsPLK/ps5-payload-manager`. If a new version is found:
   * Clones the upstream source.
   * Replaces the default payload URL with this repository's GitHub Pages URL.
   * Injects custom C code into `repository.c` and `payload_mgr.c` to mirror specific payloads to the `/data/ps5_autoloader` directory.
   * Compiles the web frontend via Node.js and the ELF via a PS5 SDK Docker image.
   * Publishes the compiled `pldmgr.elf` to this repository's Releases tab.

4. **Keep Alive (`keep-alive.yml`)**
   Runs monthly to create a dummy commit in `.github/keepalive.txt`. This prevents GitHub from disabling the repository's cron schedules due to inactivity.

---

## 🛠️ Setup (If Forking)

If you fork this repository to create your own payload ecosystem, you will need to configure the following in your repository settings (**Settings > Secrets and variables > Actions**):

1. **`PAT_TOKEN`**: Create a Personal Access Token (Classic) with `repo` and `workflow` permissions. Add it as a repository secret. This is required for `update-json.yml` to trigger the `deploy-pages.yml` workflow recursively.
2. **GitHub Pages**: Go to **Settings > Pages** and set the source to **GitHub Actions**.
3. **Write Permissions**: Ensure your Actions have Read and Write permissions under **Settings > Actions > General > Workflow permissions**.

## 📝 Modifying Tracked Payloads

To add or remove payloads, simply edit `P.json`. Ensure the URL format strictly follows standard GitHub or Gitea release structures, as `update_releases.py` uses Regex to extract the domain, owner, and repository to query the correct API.

## 🙏 Credits & Acknowledgments

* **[itsPLK](https://github.com/itsPLK)**: Massive credit for creating the original, incredible [PS5 Payload Manager](https://github.com/itsPLK/ps5-payload-manager) which this project forks and modifies. All frontend UI and core payload execution logic belongs to them.
* **[ps5-payload-dev team](https://github.com/ps5-payload-dev)** (John Törnblom, Specter, etc.) for `ftpsrv` and foundational PS5 SDK work.
* **[LightningMods / etaHEN team](https://github.com/etaHEN)** for `etaHEN`.
* **[EchoStretch](https://github.com/EchoStretch)** for `kstuff-lite`.
* **[drakmor](https://github.com/drakmor)** for `nanoDNS` and `ShadowMountPlus`.
* **[juma-sayeh](https://github.com/juma-sayeh)** for `PS5 Game Compressor`.
* **[earthonion](https://github.com/earthonion)** for `Garlic SaveMgr`.
* **[soniciso](https://git.etawen.dev/soniciso)** for `Elf Arsenal`.

## ⚖️ License & Open Source Compliance

This project automatically downloads, patches, and compiles [itsPLK's PS5 Payload Manager](https://github.com/itsPLK/ps5-payload-manager), which is licensed under the **GNU General Public License v3.0 (GPL-3.0)**. 

In compliance with the GPL-3.0:
* The distributed `pldmgr.elf` binaries in the Releases tab are licensed under GPL-3.0.
* The exact modifications made to the original C code are fully visible and open-source within the `patch_c_code.py` script located in `.github/workflows/AutoBuildPldmgr.yml`.
* No proprietary, closed-source code is injected into the application.
