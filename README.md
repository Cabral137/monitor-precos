# Monitor de Preços 

### - Estrutura dos arquivos
```
scrapfly/
│
├── requirements.txt                    
│
└── src/                
    ├── config.py                           
    ├── integrations.py                   
    ├── main.py                 
    ├── scrapper.py                         
    └── tracker.py                            
```

### - Pré-requisitos

Para configurar este projeto, é necessário configurar três serviços externos: 
- ScrapFly
- Google Cloud Platform
- Planilha modelo no Google Sheets

### - Configuração

- ##### ScrapFly
O ScrapFly é o serviço que executa a raspagem de dados evitando bloqueios.

```
Crie uma conta no ScrapFly.

Após o login, navegue até o Dashboard.

Copie a sua API Key.
```

- ##### API do Google

Crie um Projeto no Google Cloud:

```
Acesse o Console do Google Cloud Platform.

No topo da página, clique no seletor de projetos e em "NOVO PROJETO".

Dê um nome ao projeto e clique em "CRIAR".`
```

Ative as APIs:

```
Google Drive API

Google Sheets API
```
Crie a Conta de Serviço:

```
Na barra de busca, procure por "Contas de serviço".

Clique em "+ CRIAR CONTA DE SERVIÇO".

Dê um nome a ela e clique em "CRIAR E CONTINUAR".

Na seção "Papel", atribua a função de editor.
```

Gere a Chave JSON:

```
Na lista de contas de serviço, clique no e-mail da conta que você acabou de criar.

Vá para a aba "CHAVES".

Clique em "ADICIONAR CHAVE" > "Criar nova chave".

Selecione o formato JSON e clique em "CRIAR".

Um arquivo .json será baixado.
```

- ##### Planilha do Google Sheets
Crie e Configure a Planilha:

```
Vá para o Google Sheets e crie uma nova planilha.

Renomeie a planilha para Historico Precos.

Crie uma primeira guia e renomeie-a para Produtos.

Na célula A1 da guia Produtos, escreva o cabeçalho URL do Produto.

Adicione os links dos produtos que você quer monitorar a partir da célula A2.
```

Compartilhe a Planilha com o bot:

```
Abra o arquivo .json que você baixou do Google Cloud.

Copie o valor da chave "client_email"

Compartilhe a planilha com o email com a função de editor.
```

- ##### Secrets no Repositório do GitHub

```
No seu repositório no GitHub, vá para Settings > Secrets and variables > Actions.

Clique em New repository secret e crie os dois secrets a seguir:

Nome: SCRAPFLY_API_KEY
Valor: Cole a chave de API que você copiou do ScrapFly.


Nome: GOOGLE_CREDENTIALS
Valor: Copie todo o conteúdo do .json e cole aqui.
```

### - Uso

- ##### Automação via GitHub Actions

O projeto está configurado para rodar automaticamente conforme o cronograma definido em .github/workflows/price_tracker.yml. Atualmente a configuração está para que ele seja executado duas vezes no dia, as 6:00 e as 18:00.

```
  schedule:
    - cron: '0 9,21 * * *'
```