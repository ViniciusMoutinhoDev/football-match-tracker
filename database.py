"""
Database Layer - Persistência e gerenciamento de dados
Utiliza SQLite para armazenamento local
"""
import sqlite3
from typing import List, Dict, Optional
from contextlib import contextmanager


class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "football_matches.db"):
        """
        Inicializa o gerenciador do banco de dados
        
        Args:
            db_path: Caminho para o arquivo do banco de dados
        """
        self.db_path = db_path
        self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager para gerenciar conexões com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def initialize_database(self):
        """Cria as tabelas do banco de dados se não existirem"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    team_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    country TEXT,
                    founded INTEGER,
                    logo_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leagues (
                    league_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    country TEXT,
                    season INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fixtures (
                    fixture_id INTEGER PRIMARY KEY,
                    date TIMESTAMP NOT NULL,
                    timestamp INTEGER,
                    venue TEXT,
                    venue_city TEXT,
                    status TEXT NOT NULL,
                    status_long TEXT,
                    league_id INTEGER,
                    season INTEGER,
                    round TEXT,
                    home_team_id INTEGER,
                    home_team_name TEXT NOT NULL,
                    away_team_id INTEGER,
                    away_team_name TEXT NOT NULL,
                    home_goals INTEGER,
                    away_goals INTEGER,
                    halftime_home INTEGER,
                    halftime_away INTEGER,
                    fulltime_home INTEGER,
                    fulltime_away INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (league_id) REFERENCES leagues(league_id),
                    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
                    FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attended_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fixture_id INTEGER NOT NULL,
                    attended_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (fixture_id) REFERENCES fixtures(fixture_id),
                    UNIQUE(fixture_id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fixtures_date 
                ON fixtures(date)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fixtures_teams 
                ON fixtures(home_team_id, away_team_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fixtures_status 
                ON fixtures(status)
            """)
    
    def insert_fixture(self, fixture_data: Dict) -> bool:
        """
        Insere ou atualiza uma partida
        
        Args:
            fixture_data: Dicionário com dados da partida
            
        Returns:
            True se operação foi bem-sucedida
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO fixtures 
                (fixture_id, date, timestamp, venue, venue_city, status, status_long,
                 league_id, season, round, home_team_id, home_team_name, 
                 away_team_id, away_team_name, home_goals, away_goals,
                 halftime_home, halftime_away, fulltime_home, fulltime_away,
                 updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                        CURRENT_TIMESTAMP)
            """, (
                fixture_data.get('fixture_id'),
                fixture_data.get('date'),
                fixture_data.get('timestamp'),
                fixture_data.get('venue'),
                fixture_data.get('venue_city'),
                fixture_data.get('status'),
                fixture_data.get('status_long'),
                fixture_data.get('league_id'),
                fixture_data.get('season'),
                fixture_data.get('round'),
                fixture_data.get('home_team_id'),
                fixture_data.get('home_team_name'),
                fixture_data.get('away_team_id'),
                fixture_data.get('away_team_name'),
                fixture_data.get('home_goals'),
                fixture_data.get('away_goals'),
                fixture_data.get('halftime_home'),
                fixture_data.get('halftime_away'),
                fixture_data.get('fulltime_home'),
                fixture_data.get('fulltime_away')
            ))
            
            return True
    
    def mark_attended(self, fixture_id: int, notes: Optional[str] = None) -> bool:
        """
        Marca uma partida como assistida
        
        Args:
            fixture_id: ID da partida
            notes: Notas opcionais sobre a experiência
            
        Returns:
            True se operação foi bem-sucedida
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO attended_matches (fixture_id, notes)
                    VALUES (?, ?)
                """, (fixture_id, notes))
                return True
            except sqlite3.IntegrityError:
                return False
    
    def unmark_attended(self, fixture_id: int) -> bool:
        """
        Remove marcação de partida assistida
        
        Args:
            fixture_id: ID da partida
            
        Returns:
            True se remoção foi bem-sucedida
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM attended_matches WHERE fixture_id = ?
            """, (fixture_id,))
            return cursor.rowcount > 0
    
    def get_fixtures(
        self, 
        team_id: Optional[int] = None,
        status: Optional[str] = None,
        attended_only: bool = False
    ) -> List[Dict]:
        """
        Consulta partidas com filtros opcionais
        
        Args:
            team_id: Filtrar por time específico
            status: Filtrar por status (finished, scheduled, in_progress)
            attended_only: Retornar apenas partidas assistidas
            
        Returns:
            Lista de partidas
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    f.*,
                    CASE WHEN am.fixture_id IS NOT NULL THEN 1 ELSE 0 END as attended,
                    am.attended_date,
                    am.notes
                FROM fixtures f
                LEFT JOIN attended_matches am ON f.fixture_id = am.fixture_id
                WHERE 1=1
            """
            params = []
            
            if team_id:
                query += " AND (f.home_team_id = ? OR f.away_team_id = ?)"
                params.extend([team_id, team_id])
            
            if status:
                query += " AND f.status = ?"
                params.append(status)
            
            if attended_only:
                query += " AND am.fixture_id IS NOT NULL"
            
            query += " ORDER BY f.date DESC"
            
            cursor.execute(query, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self, team_id: Optional[int] = None) -> Dict:
        """
        Obtém estatísticas de partidas assistidas
        
        Args:
            team_id: Calcular estatísticas para um time específico
            
        Returns:
            Dicionário com estatísticas
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT COUNT(*) as total
                FROM attended_matches am
                JOIN fixtures f ON am.fixture_id = f.fixture_id
            """
            params = []
            
            if team_id:
                query += " WHERE (f.home_team_id = ? OR f.away_team_id = ?)"
                params.extend([team_id, team_id])
            
            cursor.execute(query, params)
            total = cursor.fetchone()['total']
            
            stats = {'total_attended': total}
            
            if team_id:
                query = """
                    SELECT 
                        SUM(CASE 
                            WHEN (f.home_team_id = ? AND f.home_goals > f.away_goals) 
                                OR (f.away_team_id = ? AND f.away_goals > f.home_goals)
                            THEN 1 ELSE 0 
                        END) as wins,
                        SUM(CASE 
                            WHEN f.home_goals = f.away_goals AND f.status = 'finished'
                            THEN 1 ELSE 0 
                        END) as draws,
                        SUM(CASE 
                            WHEN (f.home_team_id = ? AND f.home_goals < f.away_goals) 
                                OR (f.away_team_id = ? AND f.away_goals < f.home_goals)
                            THEN 1 ELSE 0 
                        END) as losses
                    FROM attended_matches am
                    JOIN fixtures f ON am.fixture_id = f.fixture_id
                    WHERE (f.home_team_id = ? OR f.away_team_id = ?)
                        AND f.status = 'finished'
                """
                cursor.execute(query, [team_id] * 6)
                result = cursor.fetchone()
                
                stats.update({
                    'wins': result['wins'] or 0,
                    'draws': result['draws'] or 0,
                    'losses': result['losses'] or 0
                })
            
            query = """
                SELECT DISTINCT f.venue, f.venue_city, COUNT(*) as visits
                FROM attended_matches am
                JOIN fixtures f ON am.fixture_id = f.fixture_id
            """
            
            if team_id:
                query += " WHERE (f.home_team_id = ? OR f.away_team_id = ?)"
                params = [team_id, team_id]
            else:
                params = []
            
            query += " GROUP BY f.venue, f.venue_city ORDER BY visits DESC"
            
            cursor.execute(query, params)
            stats['stadiums'] = [dict(row) for row in cursor.fetchall()]
            
            return stats