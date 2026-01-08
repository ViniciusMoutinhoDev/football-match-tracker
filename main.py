"""
Aplicação Principal - Interface de linha de comando
"""
import os
import sys
from dotenv import load_dotenv
from service import FootballMatchService

# Carrega variáveis do arquivo .env
load_dotenv()


def print_menu():
    """Exibe menu principal"""
    print("\n" + "=" * 80)
    print("SISTEMA DE REGISTRO DE PARTIDAS DE FUTEBOL")
    print("=" * 80)
    print("\n1. Buscar time e sincronizar partidas")
    print("2. Listar todas as partidas (banco local)")
    print("3. Listar partidas finalizadas")
    print("4. Listar próximas partidas")
    print("5. Listar partidas assistidas")
    print("6. Marcar partida como assistida")
    print("7. Remover marcação de partida assistida")
    print("8. Ver estatísticas de frequência")
    print("9. Sair")
    print("\nEscolha uma opção: ", end="")


def main():
    """Função principal"""
    
    api_key = os.getenv('API_FOOTBALL_KEY')
    if not api_key:
        print("ERRO: Variável de ambiente API_FOOTBALL_KEY não configurada")
        print("\nVerifique se o arquivo .env existe e contém:")
        print("API_FOOTBALL_KEY=sua_chave_aqui")
        sys.exit(1)
    
    try:
        service = FootballMatchService(api_key=api_key)
        print("Sistema inicializado com sucesso!")
    except Exception as e:
        print(f"Erro ao inicializar sistema: {str(e)}")
        sys.exit(1)
    
    current_team = None
    
    while True:
        print_menu()
        
        try:
            choice = input().strip()
            
            if choice == '1':
                team_name = input("\nDigite o nome do time: ").strip()
                if not team_name:
                    print("Nome do time não pode ser vazio")
                    continue
                
                team = service.search_and_select_team(team_name)
                if team:
                    current_team = team
                    
                    print("\nCompetições disponíveis:")
                    for idx, (key, comp) in enumerate(service.COMPETITIONS.items(), 1):
                        print(f"{idx}. {comp['name']}")
                    
                    comp_choice = input("\nEscolha a competição (1-5) [padrão: 1]: ").strip()
                    comp_key = list(service.COMPETITIONS.keys())[
                        int(comp_choice) - 1 if comp_choice.isdigit() and 1 <= int(comp_choice) <= 5 else 0
                    ]
                    
                    season = input("Digite o ano da temporada [padrão: 2024]: ").strip()
                    season = int(season) if season.isdigit() else 2024
                    
                    service.sync_team_fixtures(
                        team_id=team['id'],
                        competition=comp_key,
                        season=season
                    )
            
            elif choice == '2':
                if not current_team:
                    print("\nNenhum time selecionado. Use a opção 1 primeiro.")
                    continue
                
                fixtures = service.list_fixtures(team_id=current_team['id'])
                service.display_fixtures(fixtures, f"Todas as partidas - {current_team['name']}")
            
            elif choice == '3':
                if not current_team:
                    print("\nNenhum time selecionado. Use a opção 1 primeiro.")
                    continue
                
                fixtures = service.list_fixtures(
                    team_id=current_team['id'],
                    status='finished'
                )
                service.display_fixtures(fixtures, f"Partidas finalizadas - {current_team['name']}")
            
            elif choice == '4':
                if not current_team:
                    print("\nNenhum time selecionado. Use a opção 1 primeiro.")
                    continue
                
                fixtures = service.list_fixtures(
                    team_id=current_team['id'],
                    status='scheduled',
                    limit=10
                )
                service.display_fixtures(fixtures, f"Próximas partidas - {current_team['name']}")
            
            elif choice == '5':
                if not current_team:
                    print("\nNenhum time selecionado. Use a opção 1 primeiro.")
                    continue
                
                fixtures = service.list_fixtures(
                    team_id=current_team['id'],
                    attended_only=True
                )
                service.display_fixtures(fixtures, f"Partidas assistidas - {current_team['name']}")
            
            elif choice == '6':
                fixture_id = input("\nDigite o ID da partida: ").strip()
                if not fixture_id.isdigit():
                    print("ID inválido")
                    continue
                
                notes = input("Notas opcionais (Enter para pular): ").strip()
                notes = notes if notes else None
                
                service.mark_match_attended(int(fixture_id), notes)
            
            elif choice == '7':
                fixture_id = input("\nDigite o ID da partida: ").strip()
                if not fixture_id.isdigit():
                    print("ID inválido")
                    continue
                
                service.unmark_match_attended(int(fixture_id))
            
            elif choice == '8':
                if not current_team:
                    print("\nNenhum time selecionado. Use a opção 1 primeiro.")
                    continue
                
                stats = service.get_attendance_statistics(team_id=current_team['id'])
                service.display_statistics(stats, current_team['name'])
            
            elif choice == '9':
                print("\nEncerrando sistema...")
                break
            
            else:
                print("\nOpção inválida. Tente novamente.")
        
        except KeyboardInterrupt:
            print("\n\nEncerrando sistema...")
            break
        except Exception as e:
            print(f"\nErro: {str(e)}")
    
    print("Até logo!")


if __name__ == "__main__":
    main()