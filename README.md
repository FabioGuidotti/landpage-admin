# DashX Landpage SaaS

Plataforma SaaS ultra rápida para publicação de Landing Pages baseadas em HTML geradas por IA (como Lovable), focada em alta performance e integração dinâmica com WhatsApp.

## 🚀 Como Funciona

- **Multi-Tenant via Subdomínios:** Publica as landing pages no formato `cliente.ai.dashx.com.br` automaticamente.
- **Backend Inteligente:** O FastAPI identifica o subdomínio da URL (via header `Host`), busca o HTML no PostgreSQL e o serve instantaneamente.
- **WhatsApp Dinâmico:** Você insere `{{WHATSAPP_LINK}}` no seu HTML estático. O backend cuida de substituir isso pelo link oficial da API do WhatsApp com o número e mensagem configurados no painel.
- **Hospedagem 100% VPS:** Tudo encapsulado em Docker (Nginx, PostgreSQL, FastAPI).
- **Sem Complexidade:** Nada de construtores de arrastar e soltar lentos. Foque na conversão com código limpo.

---

## 💻 Como Rodar via Portainer

### 1. Configuração do DNS
No seu painel de DNS (Cloudflare, Hostinger, etc), crie um registro *Wildcard* (Coringa):

- **Tipo:** `A`
- **Nome:** `*.ai.dashx.com.br`
- **Valor:** `IP_DA_SUA_VPS`

*Se você for usar o domínio principal para acessar algo, adicione também `ai.dashx.com.br` apontando para o mesmo IP.*

### 2. Deploy no Portainer (Stacks)
Certifique-se de que você já possui o [Portainer](https://www.portainer.io/) instalado e configurado na sua VPS.

1. Acesse o painel do seu **Portainer**.
2. Selecione o seu ambiente (geralmente `local`).
3. No menu lateral, clique em **Stacks** e depois no botão **Add stack**.
4. Dê um nome para a sua stack (exemplo: `landpage-admin`).
5. Na seção **Build method**, escolha a opção **Repository**.
6. Preencha os detalhes do repositório:
   - **Repository URL:** Coloque a URL deste repositório Git.
   - **Repository reference:** Deixe em branco (ou `refs/heads/main` dependendo da sua branch).
   - **Compose path:** Deixe como `docker-compose.yml`.
7. Na seção **Environment variables**, clique em **Advanced mode** ou adicione manualmente as seguintes variáveis baseadas no `.env.example`:
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD` (use uma senha forte)
   - `POSTGRES_DB`
   - `FASTAPI_ADMIN_USER`
   - `FASTAPI_ADMIN_PASS`
8. Role até o final da página e clique em **Deploy the stack**.

> **Nota para usuários do Traefik:** O `docker-compose.yml` nativo já vem configurado para ingressar na rede `proxy` e buscar os certificados SSL via Let's Encrypt para `*.ai.dashx.com.br` e `ai.dashx.com.br` no entrypoint `websecure`. Certifique-se de que a rede no seu Portainer chama-se `proxy`.

O Portainer fará o clone do projeto, realizará o build da imagem do FastAPI e subirá todos os containers (Nginx, FastAPI, PostgreSQL) automaticamente.

### 4. Acessando o Painel Admin
Acesse qualquer subdomínio do seu app com a rota `/admin`. 
Exemplo: `http://admin.ai.dashx.com.br/admin`

- **Login Padrão:** `admin`
- **Senha Padrão:** `admin`
*(Lembre-se de mudar isso no `docker-compose.yml` em produção)*

---

## 🎨 Como Cadastrar e Publicar uma Landing Page

1. **Faça o Login** no seu painel Admin.
2. Clique em **+ New Landing**.
3. Escreva o subdomínio desejado (exemplo: `promocao-vip`).
   - *A página ficará acessível em `http://promocao-vip.ai.dashx.com.br`*
4. Informe o **Número do WhatsApp** e a **Mensagem Padrão**.
   - *Exemplo: `5511999999999` e `Oi, quero aproveitar a oferta VIP!`*
5. Cole o **HTML** perfeito gerado pelo seu Lovable no campo `HTML Content`.
6. **IMPORTANTE:** Dentro do HTML, onde estiver o *href* do seu botão de WhatsApp, substitua o link inteiro por `{{WHATSAPP_LINK}}`.
7. Salve e teste acessando o subdomínio.

### Exemplo de Botão no HTML
```html
<a href="{{WHATSAPP_LINK}}" class="btn-whatsapp">
    Comprar Agora no WhatsApp
</a>
```

---

## 🔐 Configurando SSL (HTTPS)
Recomendamos colocar a VPS atrás do **Cloudflare** com SSL configurado como "Full" ou "Flexible". Não será necessário configurar certificados dentro da VPS; o Cloudflare cuidará do HTTPS publicamente e encaminhará porta 80 para sua máquina.
Caso queira SSL direto no Nginx, substitua o bloco Nginx por uma configuração gerenciada pelo *Certbot/Let's Encrypt*.

---

## 🛡️ Segurança Recomendada: Tailscale & Firewall (UFW)

Se você utiliza **Tailscale** na sua VPS para gerenciamento interno seguro, você pode configurar a sua máquina para que o SaaS das Landing Pages fique acessível **publicamente** para seus clientes na internet, enquanto os acessos administrativos da VPS (como o SSH) fiquem blindados apenas para a sua rede privada.

### Como funciona essa arquitetura?
1. **O DNS Wildcard** (`*.ai.dashx.com.br`) no Cloudflare ou Hostinger deve apontar para o **IP Público da Internet** da sua VPS (e não para o IP 100.x.x.x do Tailscale).
2. O Tailscale rodará normalmente em background para o seu acesso pessoal à VPS.
3. O Nginx no Docker (porta 80/443) responderá requisições de qualquer origem, servindo as páginas.

### Configurando o Firewall (UFW)
Para isolar a segurança da máquina de forma que a internet veja apenas suas Landing Pages, execute estes comandos na sua VPS:

```bash
# 1. Permite conexões totais apenas de quem vem pela rede do Tailscale (seu acesso de admin)
sudo ufw allow in on tailscale0

# 2. Abre a porta 80 e 443 para a internet pública ver o SaaS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 3. (Opcional) Fecha o SSH para a internet pública - CUIDADO: Faça isso apenas se você já acessa o SSH pelo IP do Tailscale!
# sudo ufw delete allow 22/tcp

# 4. Ativa o firewall
sudo ufw enable
```

Com essa configuração, seu servidor ganha as vantagens da rede Mesh do Tailscale e a resiliência desse SaaS que projetamos para o tráfego da internet!
