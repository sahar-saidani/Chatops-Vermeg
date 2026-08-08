# logs-agent

> **[REGENERATED]** Ce README a été reconstruit à partir du code source
> (`config.py`, `parser.py`, `collector.py`, `utils.py`, `config.yaml`,
> `filebeat.yml`) et non récupéré tel quel depuis la session précédente.
> Vérifie les sections "Prérequis" et "Dépannage" par rapport à ton
> environnement réel avant de le considérer comme définitif.

Agent de collecte et de normalisation de logs, en mode **logs uniquement**
(pas de métriques Prometheus/Node Exporter — ce périmètre appartient à
l'Infrastructure Agent). Il reçoit des événements normalisés depuis
Logstash en TCP/NDJSON, les normalise (host Linux ou Windows), déduplique,
et publie chaque événement vers RabbitMQ.

## Architecture

```
[Filebeat]  --winlog/file/journald-->  [Logstash]  --TCP:5000 (json_lines)-->  [logs-agent]  --> [RabbitMQ]
```

- **Filebeat** collecte les logs bruts :
  - Linux (CentOS) : `filebeat.yml` — fichiers syslog (`/var/log/messages`,
    `/var/log/secure`, `/var/log/cron`, `/var/log/maillog`,
    `/var/log/boot.log`, `/var/log/dmesg`) + journal systemd.
  - Windows : `filebeat.windows.yml` — Event Log natif (`System`,
    `Application`, `Security`, `Setup`) via l'input `winlog`.
  - Dans les deux cas, Filebeat tague chaque événement avec l'identité de
    la machine (`tenant_name`, `environment_name`, `environment_type`,
    `machine_reference`), lue depuis les variables d'environnement — rien
    n'est codé en dur dans les fichiers de config, qui sont donc identiques
    d'une machine à l'autre.

- **Logstash** (`etc/logstash/conf.d/logs-agent.conf`) normalise les champs
  hétérogènes (ECS Linux vs `winlog.*` Windows) en un schéma commun
  (`source`, `service`, `process`, `severity`, `hostname`, `tags`), puis
  envoie chaque événement en TCP NDJSON vers `127.0.0.1:5000`.

- **logs-agent** (`logs-agent/`) :
  - `main.py` démarre le serveur TCP asyncio et résout l'identité machine.
  - `collector.py` lit chaque ligne JSON, déduplique (fenêtre glissante),
    parse/normalise via `parser.py`, puis publie sur RabbitMQ via
    `rabbitmq_publisher.RabbitMqPublisher` (si activé dans `config.yaml`).
  - `parser.py` normalise un événement Logstash brut en `NormalizedLogEvent`
    (hostname, service, level, process, source, message, tags), en tolérant
    aussi bien les champs Linux/ECS (`log.file.path`, `syslog.appname`,
    `systemd.unit`, `host.name`...) que les champs Windows (`winlog.channel`,
    `winlog.provider_name`, `winlog.level`, `host.hostname`).
  - `utils.py` fournit les helpers de bas niveau (lookup imbriqué,
    normalisation du niveau de log, parsing de timestamp, dédoublonnage).

## Variables d'environnement (identité machine)

Ces variables doivent être définies **avant** de démarrer `logs-agent`,
`Filebeat` et `Logstash` sur chaque machine :

| Variable            | Exemple (CentOS)  | Exemple (Windows) |
|----------------------|--------------------|--------------------|
| `TENANT_NAME`         | `NNBE`             | `MAIF`             |
| `ENVIRONMENT_NAME`    | `DEV`               | `DEV`               |
| `ENVIRONMENT_TYPE`    | `STANDALONE`        | `STANDALONE`        |
| `MACHINE_REFERENCE`   | `NNBE-DEV-01`       | `MAIF-DEV-01`       |

`config.yaml` ne contient volontairement **aucune** valeur en dur pour ces
champs — ils sont résolus au démarrage via
`machine.with_env_overrides()` puis validés (`validate_complete()`).

## Installation — CentOS

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r logs-agent/requirements.txt

sudo cp filebeat.yml /etc/filebeat/filebeat.yml
sudo cp etc/logstash/conf.d/logs-agent.conf /etc/logstash/conf.d/logs-agent.conf

export TENANT_NAME=NNBE ENVIRONMENT_NAME=DEV ENVIRONMENT_TYPE=STANDALONE MACHINE_REFERENCE=NNBE-DEV-01
python logs-agent/main.py &

sudo systemctl enable --now logstash
sudo systemctl enable --now filebeat
```

## Installation — Windows

```powershell
py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r logs-agent\requirements.txt

Copy-Item filebeat.windows.yml "C:\Program Files\Filebeat\filebeat.yml"
Copy-Item etc\logstash\conf.d\logs-agent.conf "C:\logstash\config\logs-agent.conf"

$Env:TENANT_NAME="MAIF"; $Env:ENVIRONMENT_NAME="DEV"; $Env:ENVIRONMENT_TYPE="STANDALONE"; $Env:MACHINE_REFERENCE="MAIF-DEV-01"
Start-Process python -ArgumentList "logs-agent\main.py"

Start-Service logstash
Start-Service filebeat
```

## Configuration RabbitMQ

Dans `config.yaml` :

```yaml
rabbitmq:
  enabled: true
  url: "amqp://guest:guest@localhost:5672/"
```

Si `enabled: false`, `logs-agent` fonctionne normalement (réception,
dédoublonnage, normalisation, logs) mais ne tente aucune publication —
utile pour du debug local sans broker.

## Tests

```bash
cd log-agent
pip install -r logs-agent/requirements.txt pytest

TENANT_NAME=NNBE ENVIRONMENT_NAME=DEV ENVIRONMENT_TYPE=STANDALONE MACHINE_REFERENCE=NNBE-DEV-01 \
  python -m pytest tests/ -v
```

- `tests/test_parser.py` — normalisation Linux (secure/cron) et Windows
  (System/Security), priorité process explicite > inférence par source.
- `tests/test_collector_publish.py` — publication RabbitMQ (mockée),
  dédoublonnage dans la fenêtre glissante, comportement quand RabbitMQ est
  désactivé, gestion d'un broker injoignable (ne doit pas crasher l'agent).

### Test manuel end-to-end (sans Filebeat/Logstash)

```bash
export TENANT_NAME=NNBE ENVIRONMENT_NAME=DEV ENVIRONMENT_TYPE=STANDALONE MACHINE_REFERENCE=NNBE-DEV-01
python logs-agent/main.py &

echo '{"message":"Failed password for invalid user demo from 127.0.0.1 port 2222 ssh2","host":{"name":"NNBE-DEV-01"},"log":{"file":{"path":"/var/log/secure"}},"process":{"name":"sshd"}}' \
  | nc 127.0.0.1 5000
```

Vérifie ensuite dans RabbitMQ (management UI ou `rabbitmqctl list_queues`)
qu'un message avec l'enveloppe suivante est bien arrivé :

```json
{
  "tenant": "NNBE", "environment": "DEV", "environmentName": "DEV",
  "environmentType": "STANDALONE", "machineReference": "NNBE-DEV-01",
  "agent": "log",
  "data": {
    "hostname": "NNBE-DEV-01", "service": "auth", "level": "WARN",
    "process": "sshd", "source": "/var/log/secure",
    "message": "Failed password for invalid user demo from 127.0.0.1 port 2222 ssh2",
    "tags": ["logs-agent", "auth", "secure"]
  }
}
```

### Test avec la vraie chaîne Filebeat → Logstash (CentOS)

```bash
sudo systemctl restart logstash
sudo systemctl restart filebeat
bash log-agent/tests/generate_logs.sh
journalctl -u filebeat -f
tail -f /var/log/logstash/logstash-plain.log
```

### Vérifier la config Logstash avant déploiement

```bash
sudo /usr/share/logstash/bin/logstash --config.test_and_exit \
  -f /etc/logstash/conf.d/logs-agent.conf
```

## Dépannage

| Symptôme | Piste |
|---|---|
| Aucun message dans RabbitMQ | Vérifier `rabbitmq.enabled: true` dans `config.yaml` et que l'URL du broker est joignable (`rabbitmqctl status`). |
| `logs-agent` démarre puis crashe immédiatement | Vérifier que les 4 variables d'environnement d'identité machine sont bien définies (`validate_complete()` lève une erreur sinon). |
| Champs Windows vides (`service`, `process`) | Vérifier que Filebeat utilise bien l'input `winlog` (pas `filestream`) et que `winlog.channel` / `winlog.provider_name` remontent jusqu'à Logstash sans être supprimés par un filtre. |
| Logstash ne transmet rien à `logs-agent` | Vérifier que `logs-agent` écoute bien sur le port 5000 (`ss -tlnp | grep 5000`) et que le output TCP de `logs-agent.conf` pointe vers `127.0.0.1:5000`. |
| Doublons publiés | La fenêtre de dédoublonnage (`normalization.dedup_window_seconds`) est peut-être trop courte pour ton volume de logs — l'augmenter dans `config.yaml`. |

## Périmètre explicitement hors scope

- Toute collecte Prometheus / Node Exporter (retirée de cet agent —
  gérée indépendamment par l'Infrastructure Agent).
- Écriture de fichiers de sortie locaux (`output_writer.py` a été
  supprimé ; la seule sortie est RabbitMQ).