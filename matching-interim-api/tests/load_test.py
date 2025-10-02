# tests/load_test.py
"""
Script de test de charge basique pour valider les performances
Utilise locust ou des requêtes asyncio simples
"""
import asyncio
import aiohttp
import time
import json
import random
import statistics
from datetime import datetime
from typing import List, Dict, Any
import argparse
from dataclasses import dataclass
import sys

@dataclass
class TestResult:
    """Résultat d'un test"""
    endpoint: str
    method: str
    status: int
    response_time: float
    timestamp: float
    success: bool
    error: str = None

class LoadTester:
    """Testeur de charge basique"""
    
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.results: List[TestResult] = []
        self.headers = {}
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
    
    async def login(self, email: str, password: str) -> str:
        """Se connecter et récupérer un token"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/auth/login",
                data={"username": email, "password": password}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data['access_token']
                    self.headers['Authorization'] = f'Bearer {self.token}'
                    return self.token
                else:
                    raise Exception(f"Login failed: {response.status}")
    
    async def make_request(self, method: str, endpoint: str, 
                          data: Dict = None, params: Dict = None) -> TestResult:
        """Faire une requête et mesurer le temps"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = (time.time() - start_time) * 1000  # ms
                    
                    result = TestResult(
                        endpoint=endpoint,
                        method=method,
                        status=response.status,
                        response_time=response_time,
                        timestamp=start_time,
                        success=200 <= response.status < 400
                    )
                    
                    return result
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            return TestResult(
                endpoint=endpoint,
                method=method,
                status=0,
                response_time=response_time,
                timestamp=start_time,
                success=False,
                error=str(e)
            )
    
    async def test_endpoint_concurrent(self, method: str, endpoint: str, 
                                      concurrency: int, requests_per_user: int,
                                      data: Dict = None, params: Dict = None) -> List[TestResult]:
        """Tester un endpoint avec plusieurs utilisateurs concurrents"""
        tasks = []
        
        for _ in range(concurrency):
            for _ in range(requests_per_user):
                task = self.make_request(method, endpoint, data, params)
                tasks.append(task)
                # Petit délai pour étaler les requêtes
                await asyncio.sleep(random.uniform(0.01, 0.1))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrer les exceptions et convertir en TestResult
        valid_results = []
        for r in results:
            if isinstance(r, TestResult):
                valid_results.append(r)
            elif isinstance(r, Exception):
                valid_results.append(TestResult(
                    endpoint=endpoint,
                    method=method,
                    status=0,
                    response_time=0,
                    timestamp=time.time(),
                    success=False,
                    error=str(r)
                ))
        
        return valid_results
    
    def print_stats(self, results: List[TestResult], test_name: str = "Test"):
        """Afficher les statistiques des résultats"""
        if not results:
            print(f"\n❌ {test_name}: Aucun résultat")
            return
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        response_times = [r.response_time for r in successful if r.response_time > 0]
        
        print(f"\n📊 {test_name} - Statistiques:")
        print(f"  Total requêtes: {len(results)}")
        print(f"  ✅ Succès: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"  ❌ Échecs: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
        
        if response_times:
            print(f"\n  Temps de réponse (ms):")
            print(f"    Min: {min(response_times):.2f}")
            print(f"    Max: {max(response_times):.2f}")
            print(f"    Moyenne: {statistics.mean(response_times):.2f}")
            print(f"    Médiane: {statistics.median(response_times):.2f}")
            
            if len(response_times) > 1:
                print(f"    P95: {statistics.quantiles(response_times, n=20)[18]:.2f}")
                print(f"    P99: {statistics.quantiles(response_times, n=100)[98]:.2f}")
        
        # Statuts HTTP
        status_counts = {}
        for r in results:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1
        
        print(f"\n  Codes de statut:")
        for status, count in sorted(status_counts.items()):
            print(f"    {status}: {count}")
        
        # Erreurs
        if failed:
            print(f"\n  Erreurs rencontrées:")
            error_counts = {}
            for r in failed:
                if r.error:
                    error_type = r.error.split(':')[0]
                    error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            for error, count in error_counts.items():
                print(f"    {error}: {count}")

class ScenarioRunner:
    """Exécute des scénarios de test"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.tester = LoadTester(base_url)
    
    async def run_basic_load_test(self, users: int = 10, requests_per_user: int = 5):
        """Test de charge basique sur les endpoints principaux"""
        print(f"\n🚀 Démarrage du test de charge")
        print(f"   URL: {self.base_url}")
        print(f"   Utilisateurs: {users}")
        print(f"   Requêtes/utilisateur: {requests_per_user}")
        print(f"   Total requêtes: {users * requests_per_user}")
        
        all_results = []
        
        # 1. Test health check (sans auth)
        print("\n1️⃣ Test Health Check...")
        results = await self.tester.test_endpoint_concurrent(
            "GET", "/health", users, requests_per_user
        )
        self.tester.print_stats(results, "Health Check")
        all_results.extend(results)
        
        # 2. Login pour avoir un token
        print("\n2️⃣ Test Login...")
        login_data = {"username": "test@client1.com", "password": "Test123!"}
        
        # D'abord un login pour récupérer le token
        try:
            await self.tester.login("test@client1.com", "Test123!")
            print("   ✅ Login réussi")
        except Exception as e:
            print(f"   ❌ Login échoué: {e}")
            print("   Utilisation de token de test...")
            self.tester.token = "test_token"
        
        # 3. Test endpoints authentifiés
        print("\n3️⃣ Test Endpoints Métier...")
        
        # Test GET candidats
        print("\n   • GET /api/candidats")
        results = await self.tester.test_endpoint_concurrent(
            "GET", "/api/candidats", users, requests_per_user
        )
        self.tester.print_stats(results, "GET Candidats")
        all_results.extend(results)
        
        # Test GET besoins
        print("\n   • GET /api/besoins")
        results = await self.tester.test_endpoint_concurrent(
            "GET", "/api/besoins", users, requests_per_user
        )
        self.tester.print_stats(results, "GET Besoins")
        all_results.extend(results)
        
        # Résumé global
        print("\n" + "="*60)
        self.tester.print_stats(all_results, "RÉSUMÉ GLOBAL")
        
        return all_results
    
    async def run_stress_test(self, max_users: int = 100, step: int = 10):
        """Test de montée en charge progressive"""
        print(f"\n🔥 Test de Stress - Montée en charge progressive")
        print(f"   De 1 à {max_users} utilisateurs par paliers de {step}")
        
        results_by_level = {}
        
        for users in range(step, max_users + 1, step):
            print(f"\n📈 Niveau {users} utilisateurs...")
            
            results = await self.tester.test_endpoint_concurrent(
                "GET", "/health", users, 1
            )
            
            success_rate = sum(1 for r in results if r.success) / len(results) * 100
            avg_time = statistics.mean([r.response_time for r in results if r.success])
            
            results_by_level[users] = {
                'success_rate': success_rate,
                'avg_response_time': avg_time
            }
            
            print(f"   Taux de succès: {success_rate:.1f}%")
            print(f"   Temps moyen: {avg_time:.2f}ms")
            
            # Arrêter si trop d'échecs
            if success_rate < 50:
                print(f"\n⚠️ Arrêt du test: taux de succès < 50%")
                break
            
            # Pause entre les niveaux
            await asyncio.sleep(2)
        
        # Afficher le graphique ASCII
        print("\n📊 Évolution des performances:")
        print("Users | Success % | Avg Time (ms)")
        print("------|-----------|---------------")
        for users, metrics in results_by_level.items():
            bar = '█' * int(metrics['success_rate'] / 10)
            print(f"{users:5d} | {metrics['success_rate']:8.1f}% | {metrics['avg_response_time']:8.2f} {bar}")
    
    async def run_spike_test(self, spike_users: int = 50):
        """Test de pic soudain de charge"""
        print(f"\n⚡ Test de Spike - Pic soudain de {spike_users} utilisateurs")
        
        # Charge normale
        print("\n1. Charge normale (5 utilisateurs)...")
        normal_results = await self.tester.test_endpoint_concurrent(
            "GET", "/health", 5, 2
        )
        normal_avg = statistics.mean([r.response_time for r in normal_results if r.success])
        print(f"   Temps moyen normal: {normal_avg:.2f}ms")
        
        # Pic soudain
        print(f"\n2. Pic soudain ({spike_users} utilisateurs)...")
        spike_results = await self.tester.test_endpoint_concurrent(
            "GET", "/health", spike_users, 2
        )
        spike_avg = statistics.mean([r.response_time for r in spike_results if r.success or 0])
        print(f"   Temps moyen pic: {spike_avg:.2f}ms")
        
        # Retour à la normale
        await asyncio.sleep(5)
        print("\n3. Retour à la normale (5 utilisateurs)...")
        recovery_results = await self.tester.test_endpoint_concurrent(
            "GET", "/health", 5, 2
        )
        recovery_avg = statistics.mean([r.response_time for r in recovery_results if r.success])
        print(f"   Temps moyen récupération: {recovery_avg:.2f}ms")
        
        # Analyse
        print("\n📊 Analyse du Spike Test:")
        print(f"   Dégradation pendant pic: {(spike_avg/normal_avg - 1)*100:.1f}%")
        print(f"   Temps de récupération: {'✅ OK' if recovery_avg < normal_avg * 1.2 else '⚠️ Lent'}")

async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Test de charge API Matching Intérim')
    parser.add_argument('--url', default='http://localhost:8000', help='URL de base de l\'API')
    parser.add_argument('--test', default='basic', choices=['basic', 'stress', 'spike', 'all'],
                       help='Type de test à exécuter')
    parser.add_argument('--users', type=int, default=10, help='Nombre d\'utilisateurs simultanés')
    parser.add_argument('--requests', type=int, default=5, help='Requêtes par utilisateur')
    
    args = parser.parse_args()
    
    runner = ScenarioRunner(args.url)
    
    start_time = time.time()
    
    try:
        if args.test == 'basic' or args.test == 'all':
            await runner.run_basic_load_test(args.users, args.requests)
        
        if args.test == 'stress' or args.test == 'all':
            await runner.run_stress_test()
        
        if args.test == 'spike' or args.test == 'all':
            await runner.run_spike_test()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
    
    duration = time.time() - start_time
    print(f"\n\n✅ Test terminé en {duration:.1f} secondes")

if __name__ == "__main__":
    asyncio.run(main())

"""
Utilisation:

# Test basique
python tests/load_test.py --url http://localhost:8000 --test basic

# Test de stress
python tests/load_test.py --url http://localhost:8000 --test stress

# Test de spike
python tests/load_test.py --url http://localhost:8000 --test spike

# Tous les tests
python tests/load_test.py --url http://localhost:8000 --test all

# Personnalisé
python tests/load_test.py --url https://api.matching-interim.com --users 50 --requests 10
"""