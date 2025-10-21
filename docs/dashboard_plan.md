# Plano do Dashboard — Recife Risco (visão inicial)

Visão geral

Este documento descreve a estrutura inicial do dashboard interativo para monitorar risco de alagamento e deslizamento na região de Recife. O objetivo é oferecer uma visão em tempo quase real, permitir filtragem por bairro e ajudar equipes de resposta a priorizar áreas.

Ferramenta de publicação

- Streamlit (escolha inicial): simples, rápida para prototipação, integração com GitHub/Streamlit Cloud.
- Futuro: Power BI Web ou uma aplicação web custom (Dash/Flask + React) para requisitos corporativos.

Seções do painel

1. Cabeçalho
   - Título, data/hora da última atualização, contatos de emergência.
2. Filtros laterais (painel esquerdo)
   - Seleção de bairro (multi-select)
   - Intervalo de datas
   - Escolha de variável a exibir (chuva, maré, vulnerabilidade, índice de risco)
   - Thresholds para alertas (limiar de chuva X mm, maré Z cm, vulnerabilidade W)
3. Mapa principal
   - Mapa interativo (pydeck/folium) com bolhas/choropleth por bairro
   - Cores: escala de risco (verde->amarelo->vermelho)
4. Série temporal
   - Gráfico de linhas da variável selecionada por bairro
5. Painel de métricas
   - Número de bairros em risco alto, eventos nas últimas 24h, máxima chuva registrada
6. Tabelas e histórico de eventos
   - Lista de eventos de alagamento/deslizamento reportados com datas e notas

Filtros e interatividade

- Seleção de um bairro atualiza mapa, séries e tabela.
- Hover sobre mapa mostra resumo (chuva, maré, vulnerabilidade, índice).
- Filtro de intervalo de datas para análise histórica.

Decisões visuais iniciais

- Hierarquia: mapa grande no centro, filtros à esquerda, séries abaixo.
- Contraste: cores acessíveis; usar paletas colorblind-friendly (ex: ColorBrewer).
- Tipografia: títulos legíveis, legendas curtas.

Próximos passos de refinamento

- Integrar dados reais e estabelecer pipelines ETL (ex: Airflow, Prefect).
- Adicionar alertas em tempo real via WebSocket ou webhook.
- Validar modelos com dados históricos rotulados e melhorar o classificador.
- Adicionar testes automatizados e analisar performance.

Contato

- Projeto: RecifeSafe
- Proprietário inicial: equipe local / Thomazrlima
