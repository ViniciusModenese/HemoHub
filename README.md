# HemoHub 🩸

> **Projeto Integrador II — Universidade Virtual do Estado de São Paulo (UNIVESP)**  
> *Plataforma web de geolocalização e agendamento para hemocentros e doadores de sangue.*

---

## 🎓 Contexto Acadêmico

Este projeto foi desenvolvido como requisito para a disciplina de **Projeto Integrador II (PI II)** do curso de Tecnologia da Informação da **UNIVESP (Universidade Virtual do Estado de São Paulo)**.

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
- **Agendamento Inteligente:** Tela própria que lista os hemocentros do mais próximo ao mais distante, com a situação de demanda de cada um, e também agendamento direto pelo mapa. As regras valem nos dois caminhos:
  - Validação de aptidão (idade, peso, gestação, pós-parto) e dos intervalos obrigatórios (60 dias para homens e 90 dias para mulheres).
  - Um agendamento confirmado por vez, e nenhum horário que já passou. Um agendamento confirmado cuja data passou sem comparecimento vira **Ausente** automaticamente e libera um novo agendamento.
  - Aviso com os requisitos para doação, que precisa ser confirmado antes de agendar. As regras seguem o [Ministério da Saúde](https://www.gov.br/saude/pt-br/composicao/saes/doacao-de-sangue) e a Fundação Pró-Sangue ([requisitos](https://www.portal.prosangue.sp.gov.br/fps/doacao_de_sangue__/requisitos_para_doacao___) e [quem não pode doar](https://www.portal.prosangue.sp.gov.br/fps/doacao_de_sangue__/quem_nao_pode_doar__)).
- **Painel Pessoal:** Acompanhamento de agendamentos, cancelamentos (apenas de agendamentos confirmados) e histórico de doações.
- **Cadastro com validação:** CPF validado pelos dígitos verificadores.

### 🏥 Para o Hemocentro
- **Painel de Gestão Hospitalar:** Monitoramento do estoque dos 8 tipos sanguíneos, com nível (crítico, baixo ou normal) e barra de progresso por tipo. Todos os tipos aparecem sempre (sem registro, contam como zero). O hemocentro informa o saldo pela própria tela, e cada doação concluída soma 1 bolsa ao tipo do doador automaticamente.
- **Alerta por tipo crítico:** nos tipos com estoque crítico (abaixo de 10 bolsas), o painel mostra o botão **Emitir alerta**, que notifica os doadores compatíveis no raio de 30 km, e exibe a data do último alerta emitido.
- **Alertas de Emergência:** Disparo de notificações automáticas para doadores compatíveis em um raio de até 30 km.
- **Agenda de Atendimento:** Lista de doadores agendados, com filtro por status e período e confirmação de presença em 1 clique, integrando automaticamente com o histórico do doador. A confirmação só é liberada a partir da data do agendamento.
- **Cadastro em Rede e Registro de Doação:** Os hemocentros compartilham o cadastro de doadores. A busca é por nome (mínimo 3 letras) ou CPF e mostra só nome, tipo sanguíneo e cidade. O registro valida a data e o intervalo considerando as doações feitas em **qualquer** hemocentro, e cancela agendamentos do doador em outros locais que ficariam dentro do intervalo. A confirmação ("Concluir" ou "Registrar doação") é bloqueada se o doador estiver inapto por peso, gestação, pós-parto, intervalo ou limite anual. A **idade fica a cargo da triagem** do hemocentro.
- **Cadastro Presencial:** Para quem chega sem cadastro, o hemocentro cadastra o doador num modal na própria tela de registro. O doador já entra na agenda de hoje, pronto para a doação ser confirmada.
- **Agenda Paginada:** A agenda lista os pendentes primeiro e identifica doadores acima de 70 anos, que passam por avaliação médica no local.
- **Cadastro com validação:** CNPJ validado pelos dígitos verificadores (quando informado).

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
```bash
git clone https://github.com/SEU_USUARIO/HemoHub.git
cd HemoHub
```

### 2. Criar e Ativar o Ambiente Virtual
**No Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**No Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente
```bash
cp .env.example .env
```
*(No Windows PowerShell: `Copy-Item .env.example .env`)*

### 5. Executar as Migrações
```bash
python manage.py migrate
```

### 6. Popular Dados de Demonstração
O projeto inclui comandos com dados de hemocentros reais do Estado de SP e geração de doadores para teste:
```bash
python manage.py popular_hemocentros
python manage.py popular_doadores --quantidade 50
python manage.py popular_estoque            # estoque aleatório do hemocentro de demonstração (colsan_jundiai); só roda com DEBUG ligado
```

### 7. Iniciar a Aplicação
```bash
python manage.py runserver
```

Acesse no navegador: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔑 Credenciais para Avaliação e Demonstração

Os comandos `popular_doadores` e `popular_hemocentros` criam todos os usuários com a mesma senha: `HemoHub2026!`.

| Perfil | Usuário | E-mail | Senha |
|---|---|---|---|
| **Doador** | doador_0001 (até doador_0050) | doador_0001@doadores.hemohub.local | HemoHub2026! |
| **Hemocentro** | banco_de_sangue_beneficencia_p | banco_de_sangue_beneficencia_p@hemocentros.hemohub.local | HemoHub2026! |
| **Hemocentro** | colsan_jundiai | colsan_jundiai@hemocentros.hemohub.local | HemoHub2026! |

No login, escolha a aba correspondente (**Sou Doador** ou **Sou Hemocentro**). Os demais hemocentros seguem o padrão `nome_da_unidade@hemocentros.hemohub.local`. Para listá-los, ou para acessar o `/admin/`, crie um administrador com `python manage.py createsuperuser`.

---

## 🧪 Testes Automatizados

O sistema conta com 111 testes automatizados cobrindo autenticação, restrição de acesso por perfil, regras de aptidão (inclusive por faixa de idade), agendamento (aptidão, um por vez, horário passado, aceite dos requisitos, cancelamento), validação de CPF e CNPJ, agenda e filtros do hemocentro, registro de doação (com bloqueio por aptidão), validação de horário, cadastro presencial, paginação da agenda, estoque de sangue, alerta por tipo crítico e API do mapa:

```bash
python manage.py test
```

Para validar o sistema pela tela, siga o [Roteiro de Testes Manuais](ROTEIRO_TESTES.md), que cobre cadastros, agendamentos, cancelamentos, cadastro presencial, estoque e alertas.

---

## ⚠️ Limitações Conhecidas e Melhorias Futuras

Este é um projeto acadêmico e algumas decisões foram deixadas de fora de propósito:

- **Sem limite de vagas por horário:** vários doadores podem agendar o mesmo horário, como é comum nos hemocentros.
- **Doador regular acima de 70 anos:** o sistema considera regular quem tem ao menos 2 doações registradas nos últimos 2 anos (critério adotado pelo projeto, já que as fontes oficiais não definem o número). Doações feitas fora do sistema só contam se o hemocentro as registrar. A avaliação médica é feita no local, e a agenda apenas sinaliza o doador. A idade vale para o agendamento feito pelo doador; na confirmação pelo hemocentro, ela é avaliada pela triagem.
- **Cadastro de hemocentro sem aprovação:** não há verificação por um administrador, e o CNPJ é opcional.
- **Configurações de desenvolvimento:** `SECRET_KEY` e `DEBUG` usam valores de desenvolvimento e devem ser trocados antes de qualquer publicação.
- **E-mail de urgência:** exige configuração do `.env`. Sem ela, o envio falha, mas as notificações dentro do sistema continuam funcionando.
- **Fuso horário único:** todo o sistema usa o horário de Brasília (`America/Sao_Paulo`). Hemocentros em estados com outro fuso (como Acre e Amazonas) teriam a checagem de "horário já passou" deslocada em 1 a 2 horas.
- **Estoque com baixa manual:** as doações concluídas somam 1 bolsa automaticamente, mas a saída de bolsas (transfusões, descarte, validade) deve ser ajustada pelo hemocentro na tela de estoque. Os níveis (crítico abaixo de 10 bolsas, baixo abaixo de 25) são valores de referência fixos.
- **Histórico de doações:** o hemocentro vê as doações concluídas na agenda, mas não há uma tela própria de histórico.
- **Lista de impedimentos:** o aviso de requisitos resume as fontes oficiais. A avaliação final é sempre da triagem clínica do hemocentro.

---

## 📂 Estrutura do Repositório

```text
HemoHub/
├── doadores/          # Perfil do doador, cálculo de aptidão e agendamentos
├── hemocentros/       # Cadastro hospitalar, unidades e dados semente de SP
├── necessidades/      # Necessidades de sangue e disparos de urgência
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
├── ROTEIRO_TESTES.md  # Roteiro de testes manuais, cenário por cenário
└── README.md          # Documentação do Projeto Integrador
```

---

## 👥 Autoria e Agradecimentos

Projeto desenvolvido pelos estudantes da **UNIVESP (Universidade Virtual do Estado de São Paulo)** para o **Projeto Integrador II**.

Agradecemos aos docentes, orientadores de polo e profissionais da área da saúde e hemoterapia que contribuíram com dados e relatos sobre o processo de doação de sangue no Brasil.
