"""
Business Logic Layer - Regras de negócio e orquestração
"""
from typing import Dict, List, Optional, Tuple
from api_client import APIFootballClient
from database import DatabaseManager


class FootballMatchService:
    """Serviço principal de gerenciamento de partidas"""
    
    COMPETITIONS = {
        'brasileirao_a': {'id': 71, 'name': 'Brasileirão Série A'},
        'brasileirao_b': {'id': 72, 'name': 'Brasileirão Série B'},
        'copa_do_brasil': {'id': 73, 'name': 'Copa do Brasil'},
        'libertadores': {'id': 13, 'name': 'Copa Libertadores'},
        'sul_americana': {'id': 11, 'name': 'Copa Sul-Americana'}
    }
    
    def __init__(self, api_key: Optional[str] = None, db_path: str = "football_matches.db"):
        """
        Inicializa o serviço
        
        Args:
            api_key: Chave da API-Football
            db_path: Caminho do banco de dados
        """
        self.api_client = APIFootballClient(api_key)
        self.db = DatabaseManager(db_path)
    
    def search_and_select_team(self, team_name: str, country: str = "Brazil") -> Optional[Dict]:
        """
        Busca times por nome e permite seleção
        
        Args:
            team_name: Nome do time para busca
            country: País do time
            
        Returns:
            Dados do time selecionado ou None
        """
        try:
            teams = self.api_client.search_team(team_name, country)
            
            if not teams:
                print(f"Nenhum time encontrado com o nome '{team_name}'")
                return None
            
            if len(teams) == 1:
                team = teams[0]['team']
                print(f"Time encontrado: {team['name']} (ID: {team['id']})")
                return team
            
            print(f"\n{len(teams)} times encontrados:")
            for idx, result in enumerate(teams, 1):
                team = result['team']
                print(f"{idx}. {team['name']} - {team.get('country', 'N/A')} (ID: {team['id']})")
            
            selected_team = teams[0]['team']
            print(f"\nSelecionado: {selected_team['name']}")
            
            return selected_team
            
        except Exception as e:
            print(f"Erro ao buscar time: {str(e)}")
            return None
    
    def sync_team_fixtures(
        self, 
        team_id: int,
        competition: str = 'brasileirao_a',
        season: int = 2024
    ) -> Tuple[int, int]:
        """
        Sincroniza partidas de um time com o banco de dados
        
        Args:
            team_id: ID do time
            competition: Competição (chave do dicionário COMPETITIONS)
            season: Temporada
            
        Returns:
            Tupla (total_fixtures, new_fixtures)
        """
        try:
            comp_data = self.COMPETITIONS.get(competition)
            if not comp_data:
                raise ValueError(f"Competição '{competition}' não encontrada")
            
            print(f"Buscando partidas do {comp_data['name']} {season}...")
            
            fixtures = self.api_client.get_team_fixtures(
                team_id=team_id,
                league_id=comp_data['id'],
                season=season
            )
            
            print(f"Total de {len(fixtures)} partidas encontradas. Sincronizando com banco de dados...")
            
            new_count = 0
            for fixture_raw in fixtures:
                fixture_data = self.api_client.parse_fixture(fixture_raw)
                
                if self.db.insert_fixture(fixture_data):
                    new_count += 1
            
            print(f"Sincronização concluída: {new_count} novas/atualizadas de {len(fixtures)} partidas")
            
            return len(fixtures), new_count
            
        except Exception as e:
            print(f"Erro ao sincronizar partidas: {str(e)}")
            return 0, 0
    
    def list_fixtures(
        self,
        team_id: Optional[int] = None,
        status: Optional[str] = None,
        attended_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Lista partidas com filtros
        
        Args:
            team_id: Filtrar por time
            status: Filtrar por status (finished, scheduled, in_progress)
            attended_only: Apenas partidas assistidas
            limit: Limitar número de resultados
            
        Returns:
            Lista de partidas
        """
        fixtures = self.db.get_fixtures(
            team_id=team_id,
            status=status,
            attended_only=attended_only
        )
        
        if limit:
            fixtures = fixtures[:limit]
        
        return fixtures
    
    def mark_match_attended(self, fixture_id: int, notes: Optional[str] = None) -> bool:
        """
        Marca uma partida como assistida
        
        Args:
            fixture_id: ID da partida
            notes: Notas opcionais
            
        Returns:
            True se marcação foi bem-sucedida
        """
        try:
            success = self.db.mark_attended(fixture_id, notes)
            
            if success:
                print(f"Partida {fixture_id} marcada como assistida!")
            else:
                print(f"Partida {fixture_id} já estava marcada como assistida")
            
            return success
            
        except Exception as e:
            print(f"Erro ao marcar partida: {str(e)}")
            return False
    
    def unmark_match_attended(self, fixture_id: int) -> bool:
        """
        Remove marcação de partida assistida
        
        Args:
            fixture_id: ID da partida
            
        Returns:
            True se remoção foi bem-sucedida
        """
        try:
            success = self.db.unmark_attended(fixture_id)
            
            if success:
                print(f"Marcação da partida {fixture_id} removida")
            else:
                print(f"Partida {fixture_id} não estava marcada como assistida")
            
            return success
            
        except Exception as e:
            print(f"Erro ao remover marcação: {str(e)}")
            return False
    
    def get_attendance_statistics(self, team_id: Optional[int] = None) -> Dict:
        """
        Obtém estatísticas de frequência em partidas
        
        Args:
            team_id: Calcular para um time específico
            
        Returns:
            Dicionário com estatísticas
        """
        return self.db.get_statistics(team_id)
    
    def format_fixture_summary(self, fixture: Dict) -> str:
        """
        Formata uma partida para exibição
        
        Args:
            fixture: Dicionário com dados da partida
            
        Returns:
            String formatada
        """
        home = fixture['home_team_name']
        away = fixture['away_team_name']
        
        if fixture['status'] == 'finished':
            score = f"{fixture['home_goals']} x {fixture['away_goals']}"
        elif fixture['status'] == 'in_progress':
            score = f"{fixture['home_goals'] or 0} x {fixture['away_goals'] or 0} (AO VIVO)"
        else:
            score = "vs"
        
        attended_mark = "✓ " if fixture.get('attended') else ""
        
        return (
            f"{attended_mark}[{fixture['fixture_id']}] "
            f"{home} {score} {away} | "
            f"{fixture.get('venue', 'N/A')} | "
            f"{fixture.get('date_formatted', fixture.get('date', 'N/A'))} | "
            f"Status: {fixture['status']}"
        )
    
    def display_fixtures(self, fixtures: List[Dict], title: str = "Partidas"):
        """
        Exibe lista de partidas formatada
        
        Args:
            fixtures: Lista de partidas
            title: Título da listagem
        """
        print(f"\n{'=' * 80}")
        print(f"{title} ({len(fixtures)} partidas)")
        print('=' * 80)
        
        if not fixtures:
            print("Nenhuma partida encontrada")
            return
        
        for fixture in fixtures:
            print(self.format_fixture_summary(fixture))
    
    def display_statistics(self, stats: Dict, team_name: Optional[str] = None):
        """
        Exibe estatísticas formatadas
        
        Args:
            stats: Dicionário com estatísticas
            team_name: Nome do time (para contexto)
        """
        print(f"\n{'=' * 80}")
        print(f"ESTATÍSTICAS DE FREQUÊNCIA" + (f" - {team_name}" if team_name else ""))
        print('=' * 80)
        
        print(f"\nTotal de partidas assistidas: {stats['total_attended']}")
        
        if 'wins' in stats:
            print(f"\nVitórias: {stats['wins']}")
            print(f"Empates: {stats['draws']}")
            print(f"Derrotas: {stats['losses']}")
            
            total_games = stats['wins'] + stats['draws'] + stats['losses']
            if total_games > 0:
                win_rate = (stats['wins'] / total_games) * 100
                print(f"Aproveitamento: {win_rate:.1f}%")
        
        if stats['stadiums']:
            print(f"\nEstádios visitados ({len(stats['stadiums'])}):")
            for stadium in stats['stadiums']:
                city = f" - {stadium['venue_city']}" if stadium['venue_city'] else ""
                print(f"  • {stadium['venue']}{city}: {stadium['visits']} visita(s)") 
