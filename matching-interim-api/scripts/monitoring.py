# scripts/monitoring.py
"""
Script de monitoring pour production
Vérifie l'état de l'API et envoie des alertes si nécessaire
Compatible avec Render.com et autres plateformes cloud
"""
import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from dataclasses import dataclass, field
from enum import Enum

class HealthStatus(Enum):
    """Statuts de santé possibles"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class Check:
    """Résultat d'un check"""
    name: str
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict = field(default_factory=dict)

@dataclass
class Alert:
    """Alerte à envoyer"""
    level: str  # critical, warning, info
    service: str
    message: str
    details: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class Monitor:
    """Moniteur principal de l'application"""
    
    def __init__(self, config: Dict):
        self.base_url = config.get('base_url', 'http://localhost:8000')
        self.check_interval = config.get('check_interval', 60)  # secondes
        self.alert_config = config.get('alerts', {})
        self.checks_history: List[Check] = []
        self.consecutive_failures = {}
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes entre alertes similaires
        
    async def check_health(self) -> Check:
        """Vérifier le health endpoint basique"""
        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = (time.time() - start) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        return Check(
                            name="health",
                            status=HealthStatus.HEALTHY,
                            message="API is responsive",
                            response_time_ms=response_time,
                            details=data
                        )
                    else:
                        return Check(
                            name="health",
                            status=HealthStatus.UNHEALTHY,
                            message=f"HTTP {response.status}",
                            response_time_ms=response_time
                        )
        except asyncio.TimeoutError:
            return Check(
                name="health",
                status=HealthStatus.UNHEALTHY,
                message="Timeout after 10s"
            )
        except Exception as e:
            return Check(
                name="health",
                status=HealthStatus.UNHEALTHY,
                message=str(e)
            )
    
    async def check_database(self) -> Check:
        """Vérifier la connexion base de données"""
        start = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health/db",
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    response_time = (time.time() - start) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Analyser le statut
                        db_status = data.get('status', 'unknown')
                        if db_status == 'healthy':
                            status = HealthStatus.HEALTHY
                        elif db_status == 'degraded':
                            status = HealthStatus.DEGRADED
                        else:
                            status = HealthStatus.UNHEALTHY
                        
                        return Check(
                            name="database",
                            status=status,
                            message=f"Database {db_status}",
                            response_time_ms=response_time,
                            details=data
                        )
                    else:
                        return Check(
                            name="database",
                            status=HealthStatus.UNHEALTHY,
                            message=f"HTTP {response.status}"
                        )
        except Exception as e:
            return Check(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=str(e)
            )
    
    async def check_api_endpoint(self, token: Optional[str] = None) -> Check:
        """Vérifier un endpoint API métier"""
        if not token:
            return Check(
                name="api_endpoints",
                status=HealthStatus.UNKNOWN,
                message="No auth token configured"
            )
        
        headers = {"Authorization": f"Bearer {token}"}
        start = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test simple: récupérer la liste des besoins
                async with session.get(
                    f"{self.base_url}/api/besoins/",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    response_time = (time.time() - start) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        return Check(
                            name="api_endpoints",
                            status=HealthStatus.HEALTHY,
                            message="API endpoints accessible",
                            response_time_ms=response_time,
                            details={"besoins_count": len(data)}
                        )
                    elif response.status == 401:
                        return Check(
                            name="api_endpoints",
                            status=HealthStatus.UNHEALTHY,
                            message="Authentication failed"
                        )
                    else:
                        return Check(
                            name="api_endpoints",
                            status=HealthStatus.UNHEALTHY,
                            message=f"HTTP {response.status}"
                        )
        except Exception as e:
            return Check(
                name="api_endpoints",
                status=HealthStatus.UNHEALTHY,
                message=str(e)
            )
    
    async def check_performance(self) -> Check:
        """Vérifier les performances globales"""
        # Analyser l'historique des checks
        if len(self.checks_history) < 5:
            return Check(
                name="performance",
                status=HealthStatus.UNKNOWN,
                message="Not enough history"
            )
        
        recent_checks = self.checks_history[-10:]
        avg_response_time = sum(c.response_time_ms for c in recent_checks if c.response_time_ms > 0) / len(recent_checks)
        
        if avg_response_time < 500:
            status = HealthStatus.HEALTHY
            message = f"Good performance (avg {avg_response_time:.0f}ms)"
        elif avg_response_time < 1000:
            status = HealthStatus.DEGRADED
            message = f"Degraded performance (avg {avg_response_time:.0f}ms)"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Poor performance (avg {avg_response_time:.0f}ms)"
        
        return Check(
            name="performance",
            status=status,
            message=message,
            details={"avg_response_time_ms": avg_response_time}
        )
    
    def should_alert(self, check: Check) -> bool:
        """Déterminer si une alerte doit être envoyée"""
        # Ne pas alerter pour UNKNOWN
        if check.status == HealthStatus.UNKNOWN:
            return False
        
        # Incrémenter le compteur d'échecs
        if check.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]:
            self.consecutive_failures[check.name] = self.consecutive_failures.get(check.name, 0) + 1
        else:
            self.consecutive_failures[check.name] = 0
        
        # Alerter après 3 échecs consécutifs
        if self.consecutive_failures.get(check.name, 0) < 3:
            return False
        
        # Vérifier le cooldown
        last_alert = self.last_alert_time.get(check.name)
        if last_alert and (datetime.utcnow() - last_alert).seconds < self.alert_cooldown:
            return False
        
        return True
    
    def create_alert(self, check: Check) -> Alert:
        """Créer une alerte basée sur un check"""
        if check.status == HealthStatus.UNHEALTHY:
            level = "critical"
        elif check.status == HealthStatus.DEGRADED:
            level = "warning"
        else:
            level = "info"
        
        return Alert(
            level=level,
            service=check.name,
            message=f"{check.name}: {check.message}",
            details=check.details
        )
    
    async def send_alert(self, alert: Alert):
        """Envoyer une alerte (email, webhook, etc.)"""
        print(f"🚨 ALERT [{alert.level.upper()}] {alert.service}: {alert.message}")
        
        # Email alert (si configuré)
        if self.alert_config.get('email_enabled'):
            await self.send_email_alert(alert)
        
        # Webhook alert (si configuré)
        if self.alert_config.get('webhook_url'):
            await self.send_webhook_alert(alert)
        
        # Enregistrer l'heure de l'alerte
        self.last_alert_time[alert.service] = datetime.utcnow()
    
    async def send_email_alert(self, alert: Alert):
        """Envoyer une alerte par email"""
        try:
            smtp_config = self.alert_config.get('smtp', {})
            
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('from', 'monitoring@matching-interim.com')
            msg['To'] = smtp_config.get('to', 'admin@matching-interim.com')
            msg['Subject'] = f"[{alert.level.upper()}] Matching Interim API - {alert.service}"
            
            body = f"""
            Alert Level: {alert.level.upper()}
            Service: {alert.service}
            Time: {alert.timestamp.isoformat()}
            
            Message: {alert.message}
            
            Details:
            {json.dumps(alert.details, indent=2)}
            
            ---
            Matching Interim Monitoring System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Envoyer l'email
            # (implémenter avec les vraies configs SMTP)
            print(f"📧 Email alert would be sent to {msg['To']}")
            
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
    
    async def send_webhook_alert(self, alert: Alert):
        """Envoyer une alerte via webhook (Slack, Discord, etc.)"""
        webhook_url = self.alert_config.get('webhook_url')
        
        payload = {
            "text": f"🚨 [{alert.level.upper()}] {alert.service}",
            "attachments": [{
                "color": "danger" if alert.level == "critical" else "warning",
                "fields": [
                    {"title": "Service", "value": alert.service, "short": True},
                    {"title": "Level", "value": alert.level, "short": True},
                    {"title": "Message", "value": alert.message},
                    {"title": "Time", "value": alert.timestamp.isoformat(), "short": True}
                ]
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        print(f"🔔 Webhook alert sent successfully")
                    else:
                        print(f"❌ Webhook alert failed: HTTP {response.status}")
        except Exception as e:
            print(f"❌ Failed to send webhook alert: {e}")
    
    async def run_checks(self, token: Optional[str] = None):
        """Exécuter tous les checks"""
        checks = []
        
        # 1. Health check
        health_check = await self.check_health()
        checks.append(health_check)
        
        # 2. Database check
        db_check = await self.check_database()
        checks.append(db_check)
        
        # 3. API check (si token disponible)
        if token:
            api_check = await self.check_api_endpoint(token)
            checks.append(api_check)
        
        # 4. Performance check
        perf_check = await self.check_performance()
        checks.append(perf_check)
        
        # Enregistrer dans l'historique
        for check in checks:
            self.checks_history.append(check)
            
            # Alerter si nécessaire
            if self.should_alert(check):
                alert = self.create_alert(check)
                await self.send_alert(alert)
        
        # Nettoyer l'historique (garder les 100 derniers)
        if len(self.checks_history) > 100:
            self.checks_history = self.checks_history[-100:]
        
        return checks
    
    def print_status(self, checks: List[Check]):
        """Afficher le statut actuel"""
        print(f"\n📊 Monitoring Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 60)
        
        for check in checks:
            emoji = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.UNHEALTHY: "❌",
                HealthStatus.UNKNOWN: "❓"
            }[check.status]
            
            time_str = f"({check.response_time_ms:.0f}ms)" if check.response_time_ms > 0 else ""
            print(f"{emoji} {check.name:15} {check.status.value:10} {time_str} - {check.message}")
        
        print("-" * 60)
    
    async def monitor_loop(self, token: Optional[str] = None):
        """Boucle principale de monitoring"""
        print(f"🔍 Starting monitoring for {self.base_url}")
        print(f"⏱️ Check interval: {self.check_interval}s")
        
        while True:
            try:
                checks = await self.run_checks(token)
                self.print_status(checks)
                
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                await asyncio.sleep(self.check_interval)

async def main():
    """Point d'entrée principal"""
    # Configuration depuis variables d'environnement
    config = {
        'base_url': os.getenv('MONITOR_API_URL', 'http://localhost:8000'),
        'check_interval': int(os.getenv('MONITOR_INTERVAL', '60')),
        'alerts': {
            'email_enabled': os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true',
            'webhook_url': os.getenv('ALERT_WEBHOOK_URL'),
            'smtp': {
                'from': os.getenv('SMTP_FROM', 'monitoring@matching-interim.com'),
                'to': os.getenv('SMTP_TO', 'admin@matching-interim.com'),
                'host': os.getenv('SMTP_HOST'),
                'port': int(os.getenv('SMTP_PORT', '587')),
                'username': os.getenv('SMTP_USERNAME'),
                'password': os.getenv('SMTP_PASSWORD')
            }
        }
    }
    
    # Token pour tester les endpoints (optionnel)
    auth_token = os.getenv('MONITOR_AUTH_TOKEN')
    
    monitor = Monitor(config)
    await monitor.monitor_loop(auth_token)

if __name__ == "__main__":
    asyncio.run(main())

"""
Utilisation:

1. Configuration basique:
   python scripts/monitoring.py

2. Avec variables d'environnement:
   export MONITOR_API_URL=https://api.matching-interim.com
   export MONITOR_INTERVAL=30
   export ALERT_WEBHOOK_URL=https://hooks.slack.com/services/xxx
   python scripts/monitoring.py

3. Avec Docker:
   docker run -e MONITOR_API_URL=... monitoring:latest

4. Avec systemd (production):
   Créer /etc/systemd/system/matching-monitor.service
"""