# CHECKLIST_RELEASE_VALORIS.md

# Checklist de Release — Valoris

Versão: v3.8.42  
Objetivo: evitar que o projeto cresça de forma desorganizada e reduzir erros antes de fechar cada versão.

---

## 1. Antes de mexer em arquivos

Confirme que está na pasta certa:

```powershell
cd C:\Users\user\Documents\maquina-preco-teto
```

Veja o estado do Git:

```powershell
git status
```

Se houver arquivos modificados que você não entende, pare e revise antes de substituir qualquer arquivo.

---

## 2. Regra de ouro dos nomes

Dentro do projeto, os arquivos finais devem ficar com nomes simples:

```text
app.py
style.py
experiencia_beta.py
explicabilidade_valoris.py
lista_espera_beta.py
oferta_beta.py
oferta_beta_pago.py
landing_page_beta.py
convite_beta_publico.py
```

Evite manter arquivos assim na raiz:

```text
experiencia_beta_v3_8_39.py
oferta_beta_v3_8_40.py
style_v3_8_38.py
Código colado.py
```

Esses nomes servem apenas para download/substituição, não para permanecer no projeto.

---

## 3. Arquivos locais que não devem ir para o Git

Não adicione ao Git:

```text
lista_espera_beta.csv
ofertas_beta_pago.csv
feedback_beta.csv
logs_motor_valuation.csv
metricas_fase3.csv
decisoes_fase3.csv
clientes_beta.csv
crm_beta.csv
watchlist_multiativos.csv
```

Eles são dados locais, não código-fonte.

---

## 4. Testes antes de abrir o app

Rode:

```powershell
python -m py_compile app.py
python -m py_compile experiencia_beta.py
python -m py_compile explicabilidade_valoris.py
python -m py_compile lista_espera_beta.py
python -m py_compile oferta_beta.py
python -m py_compile oferta_beta_pago.py
python -m py_compile landing_page_beta.py
python -m py_compile convite_beta_publico.py
```

Depois rode:

```powershell
python -m streamlit run app.py
```

---

## 5. Guardião de Release

A partir da v3.8.42, rode:

```powershell
python release_guard.py
```

Modo mais rígido:

```powershell
python release_guard.py --strict
```

O script verifica:

- arquivos Python que não compilam;
- arquivos temporários/versionados na raiz;
- CSVs locais no `.gitignore`;
- CSVs locais rastreados pelo Git;
- funções críticas de import;
- estado básico do Git.

---

## 6. Fechamento de versão

Quando tudo estiver certo:

```powershell
git status
git add ARQUIVOS_ALTERADOS.py
git commit -m "Mensagem clara da versão"
git push
git status
```

Exemplo:

```powershell
git add release_guard.py CHECKLIST_RELEASE_VALORIS.md
git commit -m "Adiciona guardiao de release e checklist v3.8.42"
git push
git status
```

---

## 7. Regra estratégica

A Valoris deve evoluir em duas frentes:

1. Produto público vendável:
   - experiência beta;
   - landing page;
   - lista de espera;
   - oferta beta;
   - relatório premium.

2. Plataforma robusta:
   - arquitetura limpa;
   - testes;
   - guardião de release;
   - dados fora do Git;
   - separação futura entre público, produto, negócio e fundador.

Não refatore tudo de uma vez.  
Organize por camadas, sem quebrar o app.
