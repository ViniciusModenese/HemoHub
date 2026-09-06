# HemoHub 🩸

> **Projeto Integrador II — Universidade Virtual do Estado de São Paulo (UNIVESP)**  
> *Plataforma web de geolocalização e agendamento para hemocentros e doadores de sangue.*

---

## 🎓 Contexto Acadêmico

Este projeto foi desenvolvido como requisito para a disciplina de **Projeto Integrador II (PI II)** dos cursos de tecnologia da **UNIVESP (Universidade Virtual do Estado de São Paulo)**.

O objetivo do Projeto Integrador é aplicar conhecimentos práticos de engenharia de software, bancos de dados, desenvolvimento web e design centrado no usuário para resolver um problema real da sociedade. O **HemoHub** foca diretamente no fortalecimento da rede pública e privada de captação de sangue no Estado de São Paulo e no Brasil.

---

## 🎯 O Problema Abordado

No Brasil, menos de **1,8% da população doa sangue regularmente**, abaixo da faixa ideal de 3% a 5% estipulada pela Organização Mundial da Saúde (OMS). 

Durante a pesquisa exploratória do projeto, identificamos três grandes dores:
1. **Descompasso de estoques:** Bancos de sangue frequentemente enfrentam escassez crítica de tipos específicos (como O- ou plaquetas) enquanto outros tipos estão com estoque suficiente, sem um canal direto para convocar quem pode doar naquele momento.
2. **Falta de transparência e centralização:** O cidadão que quer doar não sabe quais hospitais próximos estão com demandas urgentes para o seu tipo de sangue.
3. **Atrito no atendimento:** Longas esperas, falta de previsão e dúvidas sobre intervalos mínimos e regras de aptidão desestimulam doadores voluntários.

---

## 💡 A Solução Proposta

O **HemoHub** é uma ponte tecnológica direta entre o hemocentro e o doador voluntário:

### 🩸 Para o Doador
- **Mapa Interativo em Tempo Real:** Visualização geoespacial das unidades com marcadores coloridos conforme a necessidade:
  - 🟢 **Verde:** Demanda normal
  - 🟠 **Âmbar:** Demanda alta
  - 🔴 **Vermelho Pulsante:** Demanda urgente ou crítica
- **Matriz de Compatibilidade Sanguínea:** Ferramenta educativa e interativa que indica quem doa e quem recebe para cada tipo.
- **Agendamento Inteligente:** Escolha de data e horário com validação automática de intervalos obrigatórios (60 dias para homens e 90 dias para mulheres).
- **Painel Pessoal:** Acompanhamento de agendamentos, cancelamentos e histórico de doações.

### 🏥 Para o Hemocentro
- **Painel de Gestão Hospitalar:** Monitoramento instantâneo do nível de estoque dos 8 tipos sanguíneos.
- **Alertas de Emergência:** Disparo de notificações automáticas para doadores compatíveis em um raio de até 10 km.
- **Agenda de Atendimento:** Lista diária de doadores agendados com confirmação de presença em 1 clique, integrando automaticamente com o histórico do doador.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem & Framework:** Python 3.13 / Django 6.0
- **Frontend:** HTML5 semântico, Bootstrap 5 customizado e CSS3 moderno
- **Geolocalização & Mapas:** Leaflet.js e API OpenStreetMap Nominatim
- **Banco de Dados:** SQLite (ambiente acadêmico/desenvolvimento) / compatível com PostgreSQL
- **Conformidade Legal:** Arquitetura pensada sob as diretrizes da LGPD para dados de saúde

---

## 📦 Como Executar o Projeto Localmente

### Pré-requisitos
- Python 3.12 ou superior instalado
- Git instalado

### 1. Clonar o Repositório
\\ash
git clone https://github.com/SEU_USUARIO/HemoHub.git
cd HemoHub
\
### 2. Criar e Ativar o Ambiente Virtual
**No Windows:**
\\ash
python -m venv venv
.\venv\Scripts\activate
\
**No Linux / macOS:**
\\ash
python3 -m venv venv
source venv/bin/activate
\
### 3. Instalar as Dependências
\\ash
pip install -r requirements.txt
\
### 4. Configurar as Variáveis de Ambiente
\\ash
cp .env.example .env
\*(No Windows PowerShell: Copy-Item .env.example .env)*

### 5. Executar as Migrações
\\ash
python manage.py migrate
\
### 6. Popular Dados de Demonstração
O projeto inclui comandos com dados de hemocentros reais do Estado de SP e geração de doadores para teste:
\\ash
python manage.py popular_hemocentros
python manage.py popular_doadores --quantidade 50
\
### 7. Iniciar a Aplicação
\\ash
python manage.py runserver
\
Acesse no navegador: **http://127.0.0.1:8000**

---

## 🔑 Credenciais para Avaliação e Demonstração

| Perfil | Usuário | E-mail | Senha |
|---|---|---|---|
| **Doador** | doador1 | doador1@teste.com | 	este123 |
| **Hemocentro** | hemocentro1 | hemocentro1@teste.com | 	este123 |

---

## 🧪 Testes Automatizados

O sistema conta com 14 testes unitários automatizados cobrindo autenticação, restrição de acesso por perfil, regras de aptidão, agendamento e API do mapa:

\\ash
python manage.py test
\
---

## 📂 Estrutura do Repositório

\\	ext
HemoHub/
├── doadores/          # Perfil do doador, cálculo de aptidão e agendamentos
├── hemocentros/       # Cadastro hospitalar, unidades e dados semente de SP
├── necessidades/      # Gestão de estoques sanguíneos e disparos de urgência
├── paginas/           # Página inicial institucional e API REST do mapa
├── usuarios/          # Autenticação unificada e controle de perfis
├── hemoconecta/       # Configurações centrais do Django (settings, urls)
├── static/            # Estilos (CSS), identidade visual e assets
├── templates/         # Templates HTML (Bootstrap 5)
├── media/             # Uploads locais de fotos (ignorado pelo git)
├── .env.example       # Template de variáveis de ambiente
├── .gitignore         # Regras de exclusão do controle de versão
├── manage.py          # Utilitário de linha de comando Django
├── requirements.txt   # Dependências do projeto travadas
└── README.md          # Documentação do Projeto Integrador
\
---

## 👥 Autoria e Agradecimentos

Projeto desenvolvido pelos estudantes da **UNIVESP (Universidade Virtual do Estado de São Paulo)** para o **Projeto Integrador II**.

Agradecemos aos docentes, orientadores de polo e profissionais da área da saúde e hemoterapia que contribuíram com dados e relatos sobre o processo de doação de sangue no Brasil.
