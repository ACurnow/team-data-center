# Deploying the app: OVH VPS + Cloudflare Tunnel + Cloudflare Access

The Streamlit app runs in Docker on the VPS. A `cloudflared` container holds an outbound tunnel to
Cloudflare; `live.heatx.jp.net` routes through it to the app. Cloudflare Access sits in front of the
hostname, so nobody reaches the app without logging in, and the VPS publishes no port at all.

```
browser ── live.heatx.jp.net ── Cloudflare Access (login) ── Tunnel ──▶ cloudflared ──▶ app:8501
                                                                        └──── VPS, docker network "internal" ────┘
```

| File | What it does |
|---|---|
| `Dockerfile` (repo root) | The app image: Python 3.12, `uv sync --locked --no-dev`, Streamlit on port 8501, non-root |
| `deploy/compose.yaml` | `app`, `cloudflared`, and the one-off `build-data` job; three volumes for the generated data |
| `deploy/build-data.sh` | Downloads the map data and writes `out/` and `results/` for every page |
| `deploy/.env.example` | Tunnel token, the (empty) LLM key for the what-if panel, resource caps |

## Sizing (4 cores, 8 GB)

Pages solve MILPs with HiGHS while the page runs. The app container is capped at 3 CPUs and 6 GB,
and each solve at 2 threads (`DCOPT_THREADS`), which leaves a core for the OS and the tunnel. The
`build-data` job may use all 4 cores and 7 GB, so run it while the app is quiet, and pause other
services on the box (e.g. agent-office) for the first build. Change the caps in `deploy/.env`.

## 1. Cloudflare (once)

Account: *Adam Domains*, Zero Trust org `karasusec.cloudflareaccess.com`.

1. **Tunnel.** Zero Trust → Networks → Tunnels → Create a tunnel → Cloudflared, name
   `team-data-center`. Copy the token (the `--token` value) for `deploy/.env`.
2. **Route.** In the tunnel, add a published application route: `live.heatx.jp.net` → `http://app:8501`.
   This creates the proxied DNS record. (`app` is the compose service name.)
3. **Access application.** Zero Trust → Access → Applications → Self-hosted, domain
   `live.heatx.jp.net`, name *Team Data Center — live.heatx.jp.net*. Login methods: one-time PIN and
   Google Workspace. Policy *Allow* → Include → Emails → the owner's address. Session duration 24 h.
   To invite the team later, add their emails (or an email domain) to this policy; nothing on the VPS changes.
4. **Check the token at the origin too.** In the tunnel route → Access, turn on *Protect with Access*
   (required), team `karasusec`, and the application's AUD tag. cloudflared then drops any request
   without a valid Access token, as a second gate behind the one at the edge.

The health endpoint `/_stcore/health` is behind Access as well. The container checks it locally
(Docker `HEALTHCHECK`), and `docker compose ps` shows the result.

## 2. VPS (once)

Ubuntu's Docker packages, the user in the `docker` group, and a firewall that allows SSH only (the
tunnel is outbound):

```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2 docker-buildx
sudo usermod -aG docker "$USER"                                       # log in again afterwards
sudo ufw allow OpenSSH && sudo ufw default deny incoming && sudo ufw --force enable
git clone -b deploy/vps https://github.com/ACurnow/team-data-center.git ~/team-data-center
cd ~/team-data-center && cp deploy/.env.example deploy/.env && chmod 600 deploy/.env
nano deploy/.env                                                      # TUNNEL_TOKEN
```

Docker publishes no host port here, so its own iptables rules do not open anything past ufw.

## 3. First start

```bash
cd ~/team-data-center
export GIT_COMMIT=$(git rev-parse --short HEAD)
docker compose -f deploy/compose.yaml build
mkdir -p ~/logs && nohup docker compose -f deploy/compose.yaml run --rm build-data > ~/logs/build-data.log 2>&1 &   # long; the app can run meanwhile
docker compose -f deploy/compose.yaml up -d
docker compose -f deploy/compose.yaml ps                      # app "healthy", cloudflared running
```

Then open https://live.heatx.jp.net, log in, and check every page renders. The app starts before the
data is complete, too: pages without their data show the project's own "missing data" notice.

`build-data` skips any step whose output already exists; `run --rm build-data --force` redoes all of
them. The data lives in the volumes `team-data-center_cache`, `_out` and `_results`, so it survives
rebuilds of the image.

## 4. Updating

The fork follows `upstream/main`. On the VPS:

```bash
cd ~/team-data-center && git pull --ff-only
export GIT_COMMIT=$(git rev-parse --short HEAD)
docker compose -f deploy/compose.yaml up -d --build
docker compose -f deploy/compose.yaml run --rm build-data --force   # only when models or exports changed
```

## The what-if panel (off for now)

The Warm Ishikari page has a live what-if panel that turns plain-language requests into model
settings through an OpenAI-compatible endpoint (`dcopt.common.llm`). It is off while `CF_API_KEY` is
empty. To turn it on, set `CF_API_KEY` (and if needed `CARBONFORGE_BASE_URL`, `LLM_MODEL`) in
`deploy/.env` and run `docker compose -f deploy/compose.yaml up -d`.

## Pausing other services on the VPS

To give the first data build the whole box, stop what else runs there, then start it again after.
For a compose project: `docker compose -p <project> stop` / `start`; for a systemd unit:
`sudo systemctl stop <unit>` / `start`. The *agent-office-updates* tunnel shows as down in Cloudflare
while it is stopped.
