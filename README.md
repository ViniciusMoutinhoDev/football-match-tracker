# Football Match Tracker

Este projeto é um sistema simples de registro e acompanhamento de partidas de futebol, desenvolvido com foco em organização de dados, consumo de API externa e persistência local. O objetivo principal é permitir o registro de jogos assistidos, armazenando informações como data, times, placar e demais dados relevantes, servindo como base para análises futuras.

O projeto foi pensado como item de portfólio para desenvolvimento back-end, demonstrando boas práticas iniciais de versionamento, separação de responsabilidades e integração com serviços externos.

## Tecnologias utilizadas

A aplicação foi desenvolvida em Python, utilizando SQLite como banco de dados local para persistência das informações. O consumo de dados é feito por meio de uma API de futebol, centralizado em um cliente dedicado, mantendo o código organizado e de fácil manutenção.

## Estrutura do projeto

O arquivo main.py é o ponto de entrada da aplicação e responsável pela inicialização do sistema. O arquivo api_client.py concentra a lógica de comunicação com a API externa de futebol. O arquivo database.py é responsável pela criação e manipulação do banco de dados SQLite. O arquivo service.py contém a lógica de negócio que conecta a API com a camada de persistência. O arquivo requirements.txt lista as dependências necessárias para execução do projeto.

Arquivos sensíveis, banco de dados local, variáveis de ambiente e cache de execução são ignorados pelo controle de versão, seguindo boas práticas de segurança.

## Como executar o projeto

Após clonar o repositório, recomenda-se a criação de um ambiente virtual Python. Em seguida, instale as dependências listadas no arquivo requirements.txt. Com o ambiente configurado, a aplicação pode ser executada diretamente pelo terminal utilizando o comando python main.py. Ao iniciar, o sistema criará automaticamente o banco de dados local e estará pronto para registrar partidas.

## Objetivo educacional

Este projeto tem caráter educacional e evolutivo. Ele foi desenvolvido para consolidar conhecimentos em Python, integração com APIs, persistência de dados e uso correto do Git e GitHub. A estrutura foi pensada para permitir expansões futuras, como geração de estatísticas, filtros por temporada, times ou estádios e eventual exposição via API REST.

## Autor

Projeto desenvolvido por Vinicius Moutinho, com foco em aprendizado prático e construção de portfólio na área de desenvolvimento back-end.
