import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { 
  Rocket, 
  Server, 
  Shield, 
  Zap, 
  Globe, 
  Database,
  GitBranch,
  Lock,
  CheckCircle,
  ArrowRight,
  Terminal,
  Cloud,
  RefreshCw
} from "lucide-react";

export default function LandingPage() {
  const features = [
    {
      icon: <Rocket className="w-8 h-8" />,
      title: "Deploy em Minutos",
      description: "Conecte seu repositório GitHub e faça deploy automático em sua VPS com apenas alguns cliques."
    },
    {
      icon: <Server className="w-8 h-8" />,
      title: "Múltiplas VPS",
      description: "Gerencie várias VPS em um único painel. Organize seus projetos por servidor."
    },
    {
      icon: <Database className="w-8 h-8" />,
      title: "MongoDB Automático",
      description: "Crie instâncias MongoDB automaticamente para seus projetos fullstack."
    },
    {
      icon: <Globe className="w-8 h-8" />,
      title: "Domínio & SSL",
      description: "Configure domínios personalizados e SSL gratuito com Let's Encrypt."
    },
    {
      icon: <GitBranch className="w-8 h-8" />,
      title: "Integração GitHub",
      description: "Suporte a repositórios públicos e privados. Deploy de qualquer branch."
    },
    {
      icon: <RefreshCw className="w-8 h-8" />,
      title: "Redeploy Inteligente",
      description: "Atualize seu código sem perder dados. O banco de dados é preservado."
    }
  ];

  const benefits = [
    "Deploy de projetos React, Node.js, Python e mais",
    "Suporte a projetos Fullstack (Frontend + Backend)",
    "Criação automática de usuário admin no deploy",
    "Logs em tempo real do processo de deploy",
    "Variáveis de ambiente seguras e criptografadas",
    "Compatível com Nginx e Apache automaticamente"
  ];

  return (
    <div className="min-h-screen bg-[#09090b]">
      {/* Header */}
      <header className="border-b border-zinc-800">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center">
              <Terminal className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">DeployVPS</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" className="text-zinc-400 hover:text-white">
                Entrar
              </Button>
            </Link>
            <Link to="/register">
              <Button className="bg-emerald-600 hover:bg-emerald-700">
                Criar Conta
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-6">
        <div className="container mx-auto text-center max-w-4xl">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm mb-8">
            <Zap className="w-4 h-4" />
            Deploy automatizado para suas VPS
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Faça deploy dos seus projetos
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-emerald-600"> em segundos</span>
          </h1>
          
          <p className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto">
            Conecte seu GitHub, escolha sua VPS e deixe o DeployVPS fazer o resto. 
            Deploy automático com MongoDB, SSL e domínio personalizado.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register">
              <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700 text-lg px-8 py-6">
                Começar Agora
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 text-lg px-8 py-6">
                Já tenho conta
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 border-y border-zinc-800 bg-zinc-900/30">
        <div className="container mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-emerald-500 mb-2">5min</div>
              <div className="text-zinc-400">Tempo médio de deploy</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-emerald-500 mb-2">100%</div>
              <div className="text-zinc-400">Automatizado</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-emerald-500 mb-2">SSL</div>
              <div className="text-zinc-400">Gratuito incluído</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-emerald-500 mb-2">24/7</div>
              <div className="text-zinc-400">Seus apps online</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Tudo que você precisa para deploy
            </h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
              Ferramentas poderosas para automatizar o deploy dos seus projetos em qualquer VPS.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="bg-zinc-900/50 border-zinc-800 hover:border-emerald-500/50 transition-colors">
                <CardContent className="p-6">
                  <div className="w-14 h-14 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-500 mb-4">
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                  <p className="text-zinc-400">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-20 px-6 bg-zinc-900/30">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Como funciona
            </h2>
            <p className="text-zinc-400 text-lg">
              3 passos simples para colocar seu projeto no ar
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-500 text-white text-2xl font-bold flex items-center justify-center mx-auto mb-4">
                1
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Cadastre sua VPS</h3>
              <p className="text-zinc-400">
                Adicione as credenciais SSH da sua VPS (DigitalOcean, AWS, etc)
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-500 text-white text-2xl font-bold flex items-center justify-center mx-auto mb-4">
                2
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Conecte o GitHub</h3>
              <p className="text-zinc-400">
                Informe o repositório e a branch que deseja fazer deploy
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-500 text-white text-2xl font-bold flex items-center justify-center mx-auto mb-4">
                3
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Clique em Deploy</h3>
              <p className="text-zinc-400">
                Acompanhe os logs em tempo real e acesse seu app online
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 px-6">
        <div className="container mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center max-w-5xl mx-auto">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
                Por que escolher o DeployVPS?
              </h2>
              <p className="text-zinc-400 text-lg mb-8">
                Automatize o processo de deploy e foque no que realmente importa: desenvolver seu produto.
              </p>
              <ul className="space-y-4">
                {benefits.map((benefit, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <CheckCircle className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" />
                    <span className="text-zinc-300">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="relative">
              <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-zinc-500 text-sm ml-2">deploy.log</span>
                </div>
                <div className="font-mono text-sm space-y-2">
                  <div className="text-emerald-400">→ Cloning repository...</div>
                  <div className="text-zinc-400">→ Detected: Fullstack (React + FastAPI)</div>
                  <div className="text-zinc-400">→ Building backend container...</div>
                  <div className="text-zinc-400">→ Building frontend container...</div>
                  <div className="text-emerald-400">→ Starting MongoDB on port 27017</div>
                  <div className="text-emerald-400">→ Creating admin user...</div>
                  <div className="text-emerald-400">✓ Deploy successful!</div>
                  <div className="text-blue-400">→ https://meuapp.com</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-b from-zinc-900/50 to-emerald-900/20">
        <div className="container mx-auto text-center max-w-3xl">
          <Cloud className="w-16 h-16 text-emerald-500 mx-auto mb-6" />
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Pronto para automatizar seus deploys?
          </h2>
          <p className="text-zinc-400 text-lg mb-8">
            Crie sua conta gratuitamente e comece a fazer deploy dos seus projetos em minutos.
          </p>
          <Link to="/register">
            <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700 text-lg px-10 py-6">
              Criar Conta Grátis
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 py-8 px-6">
        <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center">
              <Terminal className="w-4 h-4 text-white" />
            </div>
            <span className="text-zinc-400">DeployVPS © 2026</span>
          </div>
          <div className="flex items-center gap-6 text-zinc-500 text-sm">
            <span className="flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Dados criptografados
            </span>
            <span className="flex items-center gap-2">
              <Lock className="w-4 h-4" />
              Conexão segura
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
