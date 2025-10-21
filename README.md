# 🌧️ RecifeSafe

<p align="center"> <img width="1913" height="674" alt="Banner RecifeSafe" src="https://github.com/Thomazrlima/RecifeSafe/blob/main/img/banner.png" /> </p><p align="center"> </p><p align="center"> <a href="#-sobre-o-projeto">Sobre</a> • <a href="#-funcionalidades-principais">Funcionalidades</a> • <a href="#-metodologia">Metodologia</a> • <a href="#-tecnologias-utilizadas">Tecnologias</a> • <a href="#-estrutura-do-projeto">Estrutura</a> • <a href="#-instalação-e-uso">Instalação</a> • <a href="#-nossa-equipe">Equipe</a> • <a href="#-próximos-passos">Próximos Passos</a> </p>

## 🚀 Sobre o Projeto

O **RecifeSafe** é um sistema inteligente de análise e visualização de riscos ambientais desenvolvido para apoiar a **Defesa Civil** e a **Prefeitura do Recife** na **prevenção e resposta a deslizamentos e alagamentos**.  

A solução integra **dados meteorológicos, oceânicos, geoespaciais e sociais**, aplicando **modelos preditivos** e **visualizações interativas** que permitem antecipar pontos críticos, planejar ações preventivas e comunicar alertas de forma clara e acessível à população.

---

## ⭐ Funcionalidades Principais

### 🌦️ **Integração de Dados Multifonte**
- Unificação de dados de **chuva**, **maré**, **ocorrências históricas** e **vulnerabilidade urbana**
- Padronização e limpeza automática das bases (tratamento de outliers, fusos horários e coordenadas)
- Pipeline ETL (Extract, Transform, Load) automatizado

### 📊 **Análise e Modelagem Preditiva**
- Análises exploratórias com identificação de **padrões, distribuições e correlações**
- Aplicação de **modelos de regressão** para estimar tendências e limites críticos
- Avaliação de classificadores com **matriz de confusão, curva ROC e métricas de desempenho**
- Cálculo do **Índice de Risco de Deslizamento (IRD)**

### 🗺️ **Dashboard Interativo**
- Visualizações dinâmicas e filtros por **bairro**, **período** e **tipo de evento**
- **Mapas de calor**, **gráficos temporais**, **boxplots** e **indicadores de risco**
- Interface intuitiva, responsiva e focada na usabilidade para tomada de decisão

### ⚡ **Sistema de Alerta em Tempo Real**
- Monitoramento contínuo de condições de risco
- Exibição em tempo real de áreas críticas e bairros sob alerta
- Comunicação proativa para órgãos públicos e população

---

## 🧠 Metodologia

### 1. **Coleta e Integração de Dados**
   - Fontes: **APAC, INMET, Defesa Civil, GeoRecife e IBGE**
   - APIs e web scraping para dados em tempo real

### 2. **Pré-processamento e Engenharia de Features**
   - Padronização temporal (UTC-3)
   - Normalização de variáveis e correção geoespacial (WGS84)
   - Tratamento de valores missing e outliers

### 3. **Análise Exploratória de Dados**
   - Identificação de padrões sazonais e espaciais de risco
   - Análise de correlação entre variáveis preditoras
   - Estudo de séries históricas de eventos

### 4. **Modelagem Preditiva**
   - **Regressão linear** para previsão de intensidade de eventos
   - **Classificação binária** (risco alto/baixo) com múltiplos algoritmos
   - Validação cruzada e tuning de hiperparâmetros

### 5. **Visualização e Dashboard**
   - Desenvolvimento de interface em **Streamlit**
   - Integração de métricas, gráficos interativos e mapas
   - Design centrado no usuário final

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Ferramentas |
|-----------|-------------|
| **Linguagem Principal** | Python 3.9+ |
| **Análise de Dados** | Pandas, NumPy, SciPy |
| **Modelagem Preditiva** | Scikit-learn, XGBoost |
| **Visualização** | Matplotlib, Seaborn, Plotly |
| **Dashboard** | Streamlit |
| **Geolocalização** | GeoPandas, Folium, Geopy |
| **Desenvolvimento** | Jupyter Notebook, VS Code |
| **Versionamento** | Git, GitHub |
| **Gerenciamento** | Poetry, Pip |

---

## 📁 Estrutura do Projeto

```
RecifeSafe/
├── 📊 data/                   # Bases de dados (raw e processed)
│   ├── raw/                   # Dados brutos
│   ├── processed/             # Dados tratados
│   └── external/              # Dados de fontes externas
├── 📓 notebooks/              # Análises exploratórias e modelagens
│   ├── 01_eda.ipynb           # Análise exploratória
│   ├── 02_feature_engineering.ipynb
│   └── 03_modeling.ipynb      # Desenvolvimento de modelos
├── 🎯 src/                    # Código-fonte principal
│   ├── data/                  # Scripts de coleta e limpeza
│   ├── models/                # Modelos de ML
│   ├── visualization/         # Funções de visualização
│   ├── dashboard/             # Aplicação Streamlit
│   └── utils/                 # Utilitários e helpers
├── 📋 docs/                   # Documentação adicional
├── 🧪 tests/                  # Testes unitários e de integração
├── 📄 requirements.txt        # Dependências do projeto
├── 🐍 pyproject.toml          # Configuração Poetry
└── 📖 README.md              # Este arquivo
```

---

## 🌍 Objetivos

### 🎯 **Principais Metas**
- **Antecipar riscos** de deslizamentos e alagamentos com base em evidências científicas
- **Fornecer informações visuais e preditivas** para a tomada de decisão pública
- **Facilitar a comunicação de alertas** para a população de forma acessível
- **Apoiar o planejamento urbano preventivo** e a **gestão de emergências**

### 📊 **Métricas de Sucesso**
- Redução no tempo de resposta a eventos climáticos
- Aumento na precisão de alertas preventivos
- Melhoria na comunicação risco-população

---

## 👥 Nossa Equipe

<div align="center">

| [<img src="https://github.com/Thomazrlima.png" width="100" style="border-radius:50%"><br>Thomaz Lima](https://github.com/Thomazrlima) | [<img src="https://github.com/lovepxdro.png" width="100" style="border-radius:50%"><br>Pedro Antônio](https://github.com/lovepxdro) | [<img src="https://github.com/Ferraz27.png" width="100" style="border-radius:50%"><br>Lucas Ferraz](https://github.com/Ferraz27) | [<img src="https://github.com/Henrique-12345.png" width="100" style="border-radius:50%"><br>Henrique Magalhães](https://github.com/Henrique-12345) | [<img src="https://github.com/a-guy-and-his-computer.png" width="100" style="border-radius:50%"><br>João Marcelo](https://github.com/a-guy-and-his-computer) |
|:---:|:---:|:---:|:---:|:---:|
| Coordenador de Projeto | Cientista de Dados | Desenvolvedor Backend | Analista de Dados | Analista de Dados |

</div>

---

## 📈 Próximos Passos

### 🚀 **Fase 1** (Em Andamento)
- [ ] Finalizar análise exploratória e modelagem estatística
- [ ] Consolidar notebook de desenvolvimento

### 🎯 **Fase 2** (Próxima)
- [ ] Implementar dashboard interativo completo com Streamlit
- [ ] Integrar modelos preditivos em produção
- [ ] Desenvolver sistema de alertas automatizados

### 🔮 **Futuro**
- [ ] Refinar visualizações com base em feedback de usuários
- [ ] Expandir para outras cidades e tipos de desastres
- [ ] Implementar APIs para integração com sistemas municipais
- [ ] Desenvolver aplicativo móvel para alertas populacionais

---

## 📄 Licença

Este projeto é distribuído sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

### 🤝 Contribuições
Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar problemas e sugerir melhorias
- Enviar pull requests
- Compartilhar casos de uso e experiências

---

<div align="center">

**💙 Construindo uma Recife mais segura, um dado de cada vez**

</div>
