"""
API-Football Integration Layer
Responsável pela comunicação com a API-Football (API-Sports)
"""
import os
import requests
from typing import Dict, List, Optional
from datetime import datetime
import time


class APIFootballClient:
    """Cliente para integração com API-Football"""
    
    BASE_URL = "https://v3.football.api-sports.io"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente da API
        
        Args:
            api_key: Chave de API. Se None, busca da variável de ambiente API_FOOTBALL_KEY
        """
        self.api_key = api_key or os.getenv('API_FOOTBALL_KEY')
        if not self.api_key:
            raise ValueError("API key não fornecida. Configure a variável API_FOOTBALL_KEY")
        
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """
        Realiza requisição HTTP com tratamento de erros
        
        Args:
            endpoint: Endpoint da API
            params: Parâmetros da requisição
            
        Returns:
            Dados da resposta em formato dict
            
        Raises:
            Exception: Em caso de erro na requisição
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Verifica se a API retornou erro
            if 'errors' in data and data['errors']:
                raise Exception(f"Erro na API: {data['errors']}")
            
            return data
            
        except requests.exceptions.Timeout:
            raise Exception("Timeout na requisição à API")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro na requisição: {str(e)}")
    
    def search_team(self, team_name: str, country: str = "Brazil") -> List[Dict]:
        """
        Busca times por nome
        
        Args:
            team_name: Nome do time para busca
            country: País do time (padrão: Brazil)
            
        Returns:
            Lista de times encontrados
        """
        params = {
            'name': team_name,
            'country': country
        }
        
        data = self._make_request('teams', params)
        return data.get('response', [])
    
    def get_team_fixtures(
        self, 
        team_id: int, 
        league_id: int = 71,
        season: int = 2024
    ) -> List[Dict]:
        """
        Obtém todas as partidas de um time em uma competição e temporada
        Versão corrigida sem paginação (API v3 free tier)
        
        Args:
            team_id: ID do time na API-Football
            league_id: ID da competição (71 = Brasileirão Série A)
            season: Ano da temporada
            
        Returns:
            Lista completa de partidas
        """
        params = {
            'team': team_id,
            'league': league_id,
            'season': season
        }
        
        print(f"Consultando API com parâmetros: team={team_id}, league={league_id}, season={season}")
        
        data = self._make_request('fixtures', params)
        fixtures = data.get('response', [])
        
        print(f"API retornou {len(fixtures)} partidas")
        
        return fixtures
    
    def get_fixture_details(self, fixture_id: int) -> Optional[Dict]:
        """
        Obtém detalhes completos de uma partida específica
        
        Args:
            fixture_id: ID da partida
            
        Returns:
            Detalhes da partida ou None se não encontrada
        """
        params = {'id': fixture_id}
        data = self._make_request('fixtures', params)
        
        response = data.get('response', [])
        return response[0] if response else None
    
    @staticmethod
    def parse_fixture(fixture_data: Dict) -> Dict:
        """
        Normaliza dados de uma partida para formato interno
        
        Args:
            fixture_data: Dados brutos da API
            
        Returns:
            Dados normalizados da partida
        """
        fixture = fixture_data.get('fixture', {})
        teams = fixture_data.get('teams', {})
        goals = fixture_data.get('goals', {})
        league = fixture_data.get('league', {})
        score = fixture_data.get('score', {})
        
        fixture_date = datetime.fromisoformat(
            fixture.get('date', '').replace('Z', '+00:00')
        )
        
        status_short = fixture.get('status', {}).get('short', '')
        if status_short in ['FT', 'AET', 'PEN']:
            match_status = 'finished'
        elif status_short in ['1H', '2H', 'HT', 'ET', 'P', 'LIVE']:
            match_status = 'in_progress'
        elif status_short in ['TBD', 'NS']:
            match_status = 'scheduled'
        else:
            match_status = 'postponed'
        
        return {
            'fixture_id': fixture.get('id'),
            'date': fixture_date,
            'date_formatted': fixture_date.strftime('%d/%m/%Y %H:%M'),
            'timestamp': fixture.get('timestamp'),
            'venue': fixture.get('venue', {}).get('name', 'N/A'),
            'venue_city': fixture.get('venue', {}).get('city', 'N/A'),
            'status': match_status,
            'status_long': fixture.get('status', {}).get('long', ''),
            'league_id': league.get('id'),
            'league_name': league.get('name', ''),
            'season': league.get('season'),
            'round': league.get('round', ''),
            'home_team_id': teams.get('home', {}).get('id'),
            'home_team_name': teams.get('home', {}).get('name', ''),
            'away_team_id': teams.get('away', {}).get('id'),
            'away_team_name': teams.get('away', {}).get('name', ''),
            'home_goals': goals.get('home'),
            'away_goals': goals.get('away'),
            'halftime_home': score.get('halftime', {}).get('home'),
            'halftime_away': score.get('halftime', {}).get('away'),
            'fulltime_home': score.get('fulltime', {}).get('home'),
            'fulltime_away': score.get('fulltime', {}).get('away')
        }