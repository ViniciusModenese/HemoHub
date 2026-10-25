# 🧪 Roteiro de Testes Manuais — HemoHub

Este roteiro cobre os principais cenários do sistema, para validar o funcionamento antes de uma demonstração ou entrega. Os testes automatizados (`python manage.py test`) cobrem as mesmas regras; aqui o foco é o que a pessoa vê e faz na tela.

Marque cada item (☐ → ☑) conforme for executando.

---

## Preparação

1. Ambiente pronto, como descrito no [README](README.md): dependências instaladas e `python manage.py migrate` executado.
2. Dados de demonstração carregados:
   ```bash
   python manage.py popular_hemocentros
   python manage.py popular_doadores --quantidade 50
   python manage.py popular_estoque
   ```
3. Servidor no ar: `python manage.py runserver` (acesso em `http://127.0.0.1:8000`).
4. Use **uma janela anônima por perfil**, para que as sessões não se misturem.

### Usuários de demonstração
Senha de todos: `HemoHub2026!`.

| Perfil | Usuário |
|---|---|
| Hemocentro | `colsan_jundiai`, `banco_de_sangue_bioclinica_jun`, `banco_de_sangue_beneficencia_p` |
| Doador | `doador_0001` até `doador_0050` (idade, peso e tipo são aleatórios; o painel mostra se está apto) |

### Dados válidos para preencher formulários
| Campo | Valores válidos |
|---|---|
| CPF | `529.982.247-25`, `111.444.777-35`, `935.411.347-80` |
| CNPJ | `11.222.333/0001-81`, `11.444.777/0001-61`, `45.997.418/0001-53` |

### Como criar doadores para cada situação (cadastro, cenário **A**)
| Situação | Como cadastrar |
|---|---|
| Apto | Nascimento em 1990, peso 75 kg |
| Inapto por peso | Peso 45 kg |
| Inapto por idade (62 anos) | Nascimento há 62 anos, sem doação anterior |
| Inapto por idade (acima de 70) | Nascimento há 73 anos, sem doação anterior |

### Regras para ter em mente
- **Intervalo entre doações:** 60 dias para homens e 90 dias para mulheres.
- **Um agendamento confirmado por doador** de cada vez.
- **Horários de agendamento:** de 08:00 a 17:00. Para agendar hoje, o horário precisa ainda não ter passado.
- **Raio de alerta de urgência:** 30 km do hemocentro.
- **Níveis do estoque:** Crítico (abaixo de 10 bolsas), Baixo (10 a 24), Normal (25 ou mais).
- **E-mail:** só é enviado com o `.env` configurado. Sem ele, o envio falha em silêncio e **apenas o sino de notificações funciona**.

---

## A. Cadastro de doador

| # | Faça | Esperado | OK |
|---|---|---|---|
| A1 | Cadastre com CPF `123.456.789-00` | "CPF inválido. Confira os números digitados." | ☐ |
| A2 | Preencha senhas diferentes | "As senhas não coincidem." | ☐ |
| A3 | Cadastre um doador apto com CPF `529.982.247-25` | Cadastro feito, entra no painel como **apto** | ☐ |
| A4 | Cadastre outro usuário com o **mesmo CPF** (com ou sem pontuação) | "Este CPF já está cadastrado." | ☐ |
| A5 | Cadastre um doador com peso 45 kg | Painel "não apto", motivo: peso mínimo de 50 kg | ☐ |

## B. Cadastro de hemocentro

| # | Faça | Esperado | OK |
|---|---|---|---|
| B1 | CNPJ `11.222.333/0001-99` | "CNPJ inválido. Confira os números digitados." | ☐ |
| B2 | CNPJ `11.222.333/0001-81` | Cadastro feito | ☐ |
| B3 | CNPJ em branco | Aceito (campo opcional) | ☐ |
| B4 | CNPJ já usado por outro hemocentro | "Este CNPJ já está cadastrado." | ☐ |

## C. Login e controle de acesso

| # | Faça | Esperado | OK |
|---|---|---|---|
| C1 | Usuário ou senha errados | Aviso de erro | ☐ |
| C2 | Logado como doador, abra `/hemocentros/painel/` | Página não encontrada (404) | ☐ |
| C3 | Logado como hemocentro, abra `/doadores/painel/` | Página não encontrada (404) | ☐ |
| C4 | Sem login, abra qualquer painel | Redireciona para o login | ☐ |

## D. Agendamento pela tela própria (doador apto)

| # | Faça | Esperado | OK |
|---|---|---|---|
| D1 | No painel, **Agendar nova doação** | Hemocentros do mais próximo ao mais distante, com o selo de demanda | ☐ |
| D2 | **Agendar aqui**, escolha data e horário, **Confirmar** | Abre o modal de requisitos para doação | ☐ |
| D3 | No modal, antes de marcar a caixa | Botão de confirmar desativado | ☐ |
| D4 | Marque a caixa e confirme | Agendamento aparece como **Confirmado** no painel | ☐ |
| D5 | Volte em **Agendar nova doação** | Aviso azul "você já tem um agendamento" e botões desativados | ☐ |
| D6 | Com outro doador apto, tente agendar **hoje** em horário que já passou | Aviso vermelho: "Esse horário já passou" | ☐ |
| D7 | (Técnico) Envie um agendamento com horário fora da grade, como `9:00` ou `03:00` | Recusado: "Horário inválido. Escolha um dos horários oferecidos." | ☐ |

## E. Agendamento pelo mapa (use um segundo doador apto)

| # | Faça | Esperado | OK |
|---|---|---|---|
| E1 | No mapa, clique em um hemocentro e em **Quero doar aqui** | Formulário com o quadro de requisitos e a caixa de aceite | ☐ |
| E2 | Tente enviar sem marcar a caixa | O navegador não deixa enviar | ☐ |
| E3 | Marque e confirme | "Agendamento confirmado" | ☐ |
| E4 | Abra o agendamento de novo | Aviso "você já tem um agendamento confirmado" | ☐ |

## F. Doadores inaptos

| # | Faça | Esperado | OK |
|---|---|---|---|
| F1 | Entre com o doador inapto por peso | Painel mostra o motivo. Tentar agendar é recusado, com mensagem | ☐ |
| F2 | Entre com o doador de 62 anos sem doação anterior | "Após os 60 anos, só pode doar quem já doou antes dessa idade." Agendar é recusado | ☐ |
| F3 | Entre com o doador de 73 anos sem doação anterior | Motivo: acima de 69 anos só doadores regulares, após avaliação médica. Agendar é recusado | ☐ |

## G. Cancelamento (doador)

| # | Faça | Esperado | OK |
|---|---|---|---|
| G1 | Cancele um agendamento confirmado | Fica **Cancelado** | ☐ |
| G2 | Tente agendar de novo | Permitido | ☐ |
| G3 | Olhe uma linha concluída, cancelada ou ausente | Sem botão de cancelar | ☐ |

## H. Agenda do hemocentro

| # | Faça | Esperado | OK |
|---|---|---|---|
| H1 | Entre no hemocentro em que houve agendamento | Pendentes no topo, depois concluídos, depois cancelados e ausentes | ☐ |
| H2 | Filtre por status e por período; use **Limpar** | A lista muda, e o filtro some ao limpar | ☐ |
| H3 | Agendamento de data futura | Botão **Concluir** desativado | ☐ |
| H4 | Agendamento de hoje, **Concluir** | Vira "Doação Concluída", avisa "Estoque de X: +1 bolsa", e o filtro continua aplicado | ☐ |
| H5 | Entre como o mesmo doador e tente agendar | Recusado, pois está dentro do intervalo de 60 ou 90 dias | ☐ |
| H6 | Com mais de 20 agendamentos | Aparece a paginação, mantendo os filtros | ☐ |

## I. Registrar doação (cadastro em rede)

| # | Faça | Esperado | OK |
|---|---|---|---|
| I1 | Buscar por nome com 2 letras | Nenhum resultado | ☐ |
| I2 | Buscar por 3 letras, ou pelo CPF completo (com ou sem pontuação) | Acha doadores de **qualquer** hemocentro, mostrando só nome, tipo e cidade/UF | ☐ |
| I3 | Registrar com data futura | Recusado, com erro no campo da data | ☐ |
| I4 | Registrar para doador que doou há menos de 60 ou 90 dias, em qualquer hemocentro | Recusado, citando a data da doação anterior | ☐ |
| I5 | Registro válido | Cria a linha "Doação Concluída" na agenda e soma 1 bolsa no estoque | ☐ |
| I6 | Registrar doação de quem tinha agendamento em **outro** hemocentro dentro do intervalo | O agendamento do outro hemocentro é cancelado, com aviso | ☐ |
| I7 | Selecionar um doador com peso abaixo de 50 kg (ou gestante) | Aviso vermelho com os motivos, e o botão **Confirmar doação** fica desativado | ☐ |
| I8 | Selecionar um doador com mais de 70 anos | Mostra a idade e "a avaliação por idade é feita pela triagem". A confirmação **não** é bloqueada por idade | ☐ |
| I9 | Em **Concluir** (agenda), um agendamento de hoje de doador inapto por peso | Recusado, com a mensagem do motivo, e o agendamento continua pendente | ☐ |

## J. Cadastro presencial

| # | Faça | Esperado | OK |
|---|---|---|---|
| J1 | Em **Registrar doação**, clique em **Cadastrar doador presencial** | O modal abre e **rola** até o fim | ☐ |
| J2 | Observe usuário e senha | Campos vazios (o navegador não deve preencher sozinho) | ☐ |
| J3 | Envie com CPF inválido | O modal reabre, mostrando o erro | ☐ |
| J4 | Envie com o CPF de quem já tem cadastro | "Este CPF já está cadastrado." (a busca por nome ou CPF resolve) | ☐ |
| J5 | Envie um cadastro válido | Vai para a tela com o doador selecionado e o botão **Confirmar doação** | ☐ |
| J6 | Clique em **Confirmar doação** | Linha concluída na agenda e +1 bolsa no estoque | ☐ |
| J7 | Cadastre outro doador e **não confirme** | Fica "Agendado" para hoje, e o estoque não muda | ☐ |

## K. Ausente

| # | Faça | Esperado | OK |
|---|---|---|---|
| K1 | **Hoje**, agende em um horário que ainda não passou | Confirmado | ☐ |
| K2 | **No dia seguinte**, abra qualquer painel (doador, hemocentro ou tela de agendar) | O agendamento vira **Ausente**, sem botões | ☐ |
| K3 | Filtro **Ausente** na agenda do hemocentro | Mostra só os ausentes | ☐ |
| K4 | O doador tenta agendar de novo | Permitido | ☐ |

## L. Estoque e alerta de urgência

| # | Faça | Esperado | OK |
|---|---|---|---|
| L1 | Veja os 8 cartões do estoque | Selo de nível e barra por tipo (Crítico, Baixo, Normal) | ☐ |
| L2 | **Atualizar estoque** com valor negativo | Recusado | ☐ |
| L3 | Em **Atualizar estoque**, deixe um tipo com menos de 10 bolsas | O cartão fica **Crítico** e ganha o botão **Emitir alerta** | ☐ |
| L4 | Clique em **Emitir alerta** | Pede confirmação. A mensagem informa quantos doadores foram notificados, ou avisa que não há doadores compatíveis em 30 km | ☐ |
| L5 | Entre como um doador compatível que mora a até 30 km do hemocentro | O **sino** mostra a notificação, que leva ao mapa | ☐ |
| L6 | Volte ao painel do hemocentro | O cartão mostra "Último alerta: data e hora", e o mapa mostra o hemocentro em vermelho | ☐ |
| L7 | Faça uma doação concluída de um doador do tipo em falta | O estoque do tipo sobe 1 bolsa | ☐ |

## M. Necessidades de sangue

| # | Faça | Esperado | OK |
|---|---|---|---|
| M1 | **Registrar necessidade** com urgência Alta ou Crítica | Notifica os doadores compatíveis no raio de 30 km (sino), e a coluna "Notificação" mostra "Enviada" | ☐ |
| M2 | **Encerrar** a necessidade | Vira "Encerrada", o mapa volta ao normal, e nenhum e-mail é reenviado | ☐ |

## N. Testes automatizados

| # | Faça | Esperado | OK |
|---|---|---|---|
| N1 | `python manage.py test` | Todos os testes passam, terminando em `OK` | ☐ |

---

## Observações
- Os testes automatizados usam um banco temporário e **não alteram** os dados do `db.sqlite3`.
- Para reiniciar o estoque com valores novos: `python manage.py popular_estoque` (use `--todos` para todos os hemocentros). Isso **substitui** as quantidades atuais por valores aleatórios, e o comando só roda com `DEBUG` ligado (ou com `--forcar`).
- Se o resultado de algum item divergir do esperado, anote o item, o que foi feito e a mensagem exibida.
