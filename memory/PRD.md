# DeployVPS - Product Requirements Document

## Problem Statement
Sistema de deploy automático que permite aos usuários hospedar projetos do GitHub em suas VPS pessoais, fornecendo apenas o link do repositório e credenciais de acesso SSH da VPS.

## User Personas
1. **Desenvolvedor Individual** - Quer deploy fácil sem configurar CI/CD complexo
2. **Pequenas Equipes** - Precisam gerenciar múltiplos projetos em VPS existentes
3. **Freelancers** - Querem deploy rápido para projetos de clientes

## Core Requirements
- Autenticação JWT (registro/login)
- Gerenciamento de VPS (CRUD)
- Suporte a autenticação SSH por senha ou chave
- Deploy via Docker (isolamento)
- Suporte a repositórios públicos e privados (GitHub token)
- Configuração de domínio com Nginx reverse proxy
- Logs de deploy em tempo real
- Monitoramento de status

## Architecture
- **Backend**: FastAPI + MongoDB + Paramiko (SSH)
- **Frontend**: React + Tailwind + Shadcn/UI
- **Deploy**: Docker containers na VPS do usuário
- **Proxy**: Nginx para domínios personalizados

## What's Been Implemented (Jan 2026)
- [x] Autenticação JWT completa (registro/login)
- [x] CRUD de VPS com criptografia de credenciais
- [x] Teste de conexão SSH
- [x] Criação de deployments com Docker
- [x] Geração automática de Dockerfile (Node.js, Python, Static)
- [x] Logs de deploy em tempo real
- [x] Configuração de domínio com Nginx
- [x] UI completa com design terminal/dark mode
- [x] Dashboard com estatísticas
- [x] Gerenciamento de servidores VPS
- [x] Detalhes de deployment com logs

## Prioritized Backlog

### P0 (Critical)
- N/A - MVP completo

### P1 (High)
- [ ] SSL/HTTPS automático com Certbot
- [ ] Webhooks para auto-deploy em push
- [ ] Notificações de status (email/webhook)

### P2 (Medium)
- [ ] Multi-branch deployments
- [ ] Rollback para versões anteriores
- [ ] Métricas de uso (CPU, memória)
- [ ] Suporte a GitLab/Bitbucket

### P3 (Low)
- [ ] Interface CLI
- [ ] API pública documentada
- [ ] Integração com Cloudflare DNS

## Next Tasks
1. Testar com VPS real
2. Implementar webhooks GitHub
3. Adicionar SSL automático
