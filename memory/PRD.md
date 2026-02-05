# DeployVPS - Product Requirements Document

## Original Problem Statement
O usuário quer finalizar uma aplicação "DeployVPS" - um sistema completo para fazer deploy automático de aplicações do GitHub (especialmente projetos do Emergent.sh) em VPS próprias.

## Product Overview
**DeployVPS** é uma plataforma web full-stack (React/FastAPI/MongoDB) que automatiza o deploy de aplicações web do GitHub para servidores VPS do usuário. Suporta projetos Node.js, React, Python/FastAPI com MongoDB, configuração automática de SSL e domínios personalizados.

## Core Features

### Authentication & Users
- [x] Registro de usuários com aprovação de admin
- [x] Login com JWT
- [x] Sistema de expiração de acesso
- [x] Painel administrativo para gerenciar usuários
- [x] Alterar senha

### VPS Management
- [x] Cadastro de servidores VPS (SSH com senha ou chave)
- [x] Teste de conexão
- [x] Verificação de segurança (Firewall, Fail2ban)
- [x] Reforçar segurança automaticamente
- [x] Suporte a múltiplas VPS por usuário

### Deployment System
- [x] Deploy automático de projetos GitHub
- [x] Suporte a Frontend Only, Backend Only, Fullstack
- [x] Suporte a Nginx e Apache2
- [x] Docker containerization
- [x] MongoDB automático para projetos fullstack
- [x] Seleção inteligente de portas (evita conflitos)
- [x] Redeploy preservando banco de dados
- [x] Cancelar deploy em andamento
- [x] Visualização de logs em tempo real

### Domain & SSL
- [x] Configuração de domínio personalizado
- [x] SSL gratuito com Let's Encrypt
- [x] Remoção de domínio

### Backup System
- [x] Criar backup manual do MongoDB
- [x] Listar backups
- [x] Download de backups
- [x] Restaurar backup
- [x] Deletar backup
- [x] Importar backup externo
- [x] Configurações de backup automático (UI implementada, cronjob pendente)

### Internationalization (i18n)
- [x] Suporte a 3 idiomas: Português, English, Español
- [x] Detecção automática de idioma por IP
- [x] Seletor de idioma no header
- [x] Todas as páginas traduzidas:
  - Landing Page
  - Login
  - Register
  - Dashboard
  - New Deployment
  - Deployment Details
  - VPS Management
  - Admin Users
  - Admin Analytics

### SEO Optimization
- [x] Meta tags otimizadas para deployvps.online
- [x] Open Graph tags para redes sociais
- [x] Sitemap.xml com hreflang para 3 idiomas
- [x] Schema.org structured data
- [x] Keywords para PT, EN, ES

### Admin Analytics Dashboard
- [x] Page views (total, hoje, semana, mês)
- [x] Visitantes únicos
- [x] Conversões (registros)
- [x] Taxa de conversão
- [x] Top páginas visitadas
- [x] Top países de visitantes
- [x] Gráfico de visualizações diárias (30 dias)
- [x] Atividade recente

## Tech Stack
- **Frontend**: React 18, TailwindCSS, Shadcn/UI, React Router
- **Backend**: FastAPI (Python), Motor (MongoDB async)
- **Database**: MongoDB
- **Deployment**: Docker, Nginx/Apache2
- **SSL**: Let's Encrypt (certbot)

## API Endpoints

### Auth
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/change-password

### Admin
- GET /api/admin/users
- POST /api/admin/users
- PUT /api/admin/users/{id}
- DELETE /api/admin/users/{id}
- POST /api/admin/users/{id}/approve
- POST /api/admin/users/{id}/reject
- GET /api/admin/stats
- GET /api/admin/analytics

### VPS
- GET /api/vps
- POST /api/vps
- DELETE /api/vps/{id}
- POST /api/vps/{id}/test
- GET /api/vps/{id}/available-ports
- GET /api/vps/{id}/security
- POST /api/vps/{id}/security/harden

### Deployments
- GET /api/deployments
- POST /api/deployments
- GET /api/deployments/{id}
- POST /api/deployments/{id}/redeploy
- POST /api/deployments/{id}/stop
- POST /api/deployments/{id}/cancel
- DELETE /api/deployments/{id}
- POST /api/deployments/{id}/domain
- DELETE /api/deployments/{id}/domain
- POST /api/deployments/{id}/ssl
- GET /api/deployments/{id}/logs

### Backups
- GET /api/deployments/{id}/backups
- POST /api/deployments/{id}/backups
- GET /api/deployments/{id}/backups/{backup_id}/download
- POST /api/deployments/{id}/backups/{backup_id}/restore
- DELETE /api/deployments/{id}/backups/{backup_id}
- POST /api/deployments/{id}/backups/import
- PUT /api/deployments/{id}/backups/settings

### Analytics
- POST /api/analytics/track

## Domain Configuration
- **Production Domain**: deployvps.online
- **SEO Languages**: PT (Brazil), EN (US), ES (Spain/LATAM)

## Test Credentials
- **Admin**: admin@admin.com / Admin@123

## Pending/Future Tasks

### P1 - High Priority
- [ ] Open Graph image (og-image.png 1200x630px)
- [ ] Implementar cronjob para backup automático

### P2 - Medium Priority
- [ ] Monitoramento em tempo real de CPU/RAM da VPS
- [ ] Notificações por email (deploy sucesso/falha, baixo espaço)
- [ ] Histórico de deploys
- [ ] Rollback para versão anterior

### P3 - Low Priority
- [ ] Integração com CI/CD (GitHub Actions webhook)
- [ ] Dashboard de métricas de performance
- [ ] Suporte a mais banco de dados (PostgreSQL, MySQL)
- [ ] Multi-tenant (white-label)

## Known Technical Debt
1. **server.py** é muito grande (2700+ linhas) - precisa ser refatorado em módulos (APIRouter)
2. **DeploymentDetails.jsx** e **NewDeployment.jsx** são muito grandes - extrair custom hooks
3. ESLint warnings sobre useEffect dependencies em algumas páginas

## Changelog

### 2025-12-08
- Implementado sistema completo de i18n (PT, EN, ES)
- Detecção automática de idioma por IP
- Atualizado SEO para deployvps.online com suporte multi-idioma
- Criado Admin Analytics dashboard com tracking de page views
- Traduzidas todas as páginas do sistema

### Previous Sessions
- Sistema de backup completo (criar, listar, download, restore, import)
- Seleção inteligente de portas para novos deploys
- Cancelar deploy em andamento
- Limpeza de recursos Docker órfãos
- Correção de bugs de deploy (conflito de portas)
