# DeployVPS - Product Requirements Document

## Original Problem Statement
Sistema para automatizar o deploy de aplicações web de repositórios GitHub para VPS do usuário. O sistema deve suportar tanto Nginx quanto Apache2, preservar dados MongoDB durante redeploys, e oferecer configuração de domínio customizado com SSL.

## User Personas
- **Desenvolvedor Individual**: Quer fazer deploy rápido de projetos Emergent/GitHub para seu VPS
- **Admin de Sistema**: Gerencia múltiplos VPS e deploys com necessidade de monitoramento de segurança

## Core Requirements (Implemented)
1. ✅ Autenticação de usuários (JWT)
2. ✅ Gerenciamento de VPS (CRUD)
3. ✅ Deploy de projetos GitHub (frontend, backend, full-stack)
4. ✅ Redeploy preservando dados MongoDB
5. ✅ Suporte a Apache2 e Nginx
6. ✅ Configuração de domínio customizado
7. ✅ SSL via Let's Encrypt
8. ✅ Visualizador de logs estilo Emergent
9. ✅ Verificação e hardening de segurança VPS
10. ✅ Landing page otimizada para SEO
11. ✅ Sistema de Backup MongoDB (manual + automático)
12. ✅ Cancelar deploy em andamento
13. ✅ Aviso ao sair durante deploy ativo

## Tech Stack
- **Frontend**: React + TailwindCSS + Shadcn/UI
- **Backend**: FastAPI + Python
- **Database**: MongoDB
- **Remote Execution**: Paramiko (SSH)
- **Containerization**: Docker

## Architecture
```
/app
├── backend/
│   ├── .env          # MONGO_URL, JWT_SECRET
│   └── server.py     # API monolítica (2700+ linhas - precisa refatorar)
├── frontend/
│   ├── public/       # index.html, robots.txt, sitemap.xml
│   └── src/
│       ├── pages/    # LandingPage, Dashboard, VPSManagement, DeploymentDetails
│       └── components/
```

## Key API Endpoints
- `POST /api/auth/login` - Login
- `POST /api/deployments` - Criar deploy
- `POST /api/deployments/{id}/redeploy` - Redeploy
- `POST /api/deployments/{id}/cancel` - Cancelar deploy em andamento
- `DELETE /api/deployments/{id}` - Deletar deploy
- `GET /api/deployments/{id}/logs` - Logs
- `POST /api/deployments/{id}/domain` - Configurar domínio
- `POST /api/deployments/{id}/ssl` - Ativar SSL
- `GET /api/vps/{id}/security` - Check segurança
- `POST /api/vps/{id}/security/harden` - Hardening

### Backup Endpoints (NEW)
- `GET /api/deployments/{id}/backups` - Listar backups
- `POST /api/deployments/{id}/backups` - Criar backup
- `POST /api/deployments/{id}/backups/{backup_id}/restore` - Restaurar
- `GET /api/deployments/{id}/backups/{backup_id}/download` - Baixar
- `DELETE /api/deployments/{id}/backups/{backup_id}` - Excluir
- `PUT /api/deployments/{id}/backups/settings` - Configurações

## Prioritized Backlog

### P0 (Critical)
- (none)

### P1 (High)
- [ ] Finalizar SEO com domínio definitivo (substituir `deployvps.com`)
- [ ] Implementar cronjob para backups automáticos no VPS

### P2 (Medium)
- [ ] Criar imagem Open Graph (1200x630px)
- [ ] Refatorar server.py em módulos (routers/, services/)
- [ ] Notificações por email para falhas de backup

### P3 (Low)
- [ ] Desabilitar login root SSH automaticamente (com confirmação)
- [ ] Suporte a múltiplos repositórios por deploy

## Completed This Session (Jan 31, 2026)
- ✅ Bug fix: "Reforçar Segurança" não reinstala Fail2ban/UFW se já ativos
- ✅ Aviso ao sair da página durante deploy ativo
- ✅ Botão "Cancelar Deploy" quando status é building/deploying
- ✅ Sistema completo de Backup MongoDB:
  - Criar backup manual
  - Configurações de backup automático (intervalo + max backups)
  - Listar, restaurar, baixar e excluir backups
  - **Importar backup** de arquivo externo
  - Backups salvos no VPS em /var/backups/deployvps/{projeto}/
- ✅ Bug fix: Conflito de portas no deploy saasv6 (MongoDB na porta errada)
- ✅ Melhoria no formulário de novo deploy:
  - 3 campos de porta separados (Frontend, Backend, MongoDB)
  - Dica de ranges de portas sugeridas
- ✅ Limpeza de recursos não utilizados no VPS (2.43GB liberados)

## Credentials (Test)
- **App**: admin@admin.com / Admin@123
- **VPS**: 174.138.178.243 / root / Ba4_Paf6=Mi5

## Known Issues
- VPS tem recursos limitados (2GB RAM) - builds Docker podem travar
- Projeto `saasv6` precisa patch especial para admin panel via IP
- Backup automático salva configuração mas não executa cronjob ainda
