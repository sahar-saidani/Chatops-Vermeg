# Jenkins Agent

Jenkins Agent autonome pour collecte/analyse CI/CD Jenkins et production de rapport JSON compatible architecture multi-agents DevOps.

## Fonctionnalites

- Connexion Jenkins REST API avec auth username/token
- Collecte jobs, builds, pipelines, stages, logs, erreurs
- Correlation commit, branche, utilisateur declencheur
- Analyse repository cible (ToDoList)
- Calcul de metriques CI/CD
- Export rapport JSON dans reports/jenkins_report.json
- Payload multi-agents RabbitMQ-ready

## Architecture

- main.py
- agent/jenkins_agent.py
- jenkins/jenkins_client.py
- jenkins/api.py
- jenkins/parser.py
- models/schemas.py
- collectors/job_collector.py
- collectors/build_collector.py
- collectors/pipeline_collector.py
- collectors/log_collector.py
- utils/logger.py
- utils/exceptions.py
- message_sender.py
- tests/test_client.py
- tests/test_collectors.py

## Configuration

Creer un fichier .env:

JENKINS_URL=http://localhost:8080
JENKINS_USERNAME=user
JENKINS_TOKEN=token

Optionnel:

LOG_LEVEL=INFO

## Installation

```bash
python -m pip install -r requirements.txt
```

## Utilisation

Analyse Jenkins:

```bash
python main.py analyze --repo-path ToDoList
```

Generer rapport:

```bash
python main.py report --repo-path ToDoList
```

Lancer les tests:

```bash
pytest
```

## Sortie multi-agents

message_sender.py produit un payload standard:

{
  "agent": "jenkins-agent",
  "timestamp": "...",
  "data": { ... }
}
