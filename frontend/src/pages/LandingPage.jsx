import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Card, CardContent } from "../components/ui/card";
import { useLanguage } from "../i18n/LanguageContext";
import LanguageSelector from "../components/LanguageSelector";
import { API } from "../App";
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
  const { t, language } = useLanguage();
  
  // Track page view for analytics
  useEffect(() => {
    const trackPageView = async () => {
      try {
        // Get country from localStorage (set by LanguageContext)
        const country = localStorage.getItem('detected_country') || '';
        
        await fetch(`${API}/analytics/track`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event_type: 'page_view',
            page: '/',
            country: country,
            language: language
          })
        });
      } catch (e) {
        // Silent fail for analytics
      }
    };
    trackPageView();
  }, [language]);
  
  const features = [
    {
      icon: <Rocket className="w-8 h-8" />,
      title: t('landing.features.items.autoDeploy.title'),
      description: t('landing.features.items.autoDeploy.description')
    },
    {
      icon: <Server className="w-8 h-8" />,
      title: t('landing.features.items.multiServer.title'),
      description: t('landing.features.items.multiServer.description')
    },
    {
      icon: <Database className="w-8 h-8" />,
      title: t('landing.features.items.mongodb.title'),
      description: t('landing.features.items.mongodb.description')
    },
    {
      icon: <Globe className="w-8 h-8" />,
      title: t('landing.features.items.ssl.title'),
      description: t('landing.features.items.ssl.description')
    },
    {
      icon: <RefreshCw className="w-8 h-8" />,
      title: t('landing.features.items.backup.title'),
      description: t('landing.features.items.backup.description')
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: t('landing.features.items.security.title'),
      description: t('landing.features.items.security.description')
    }
  ];

  const benefits = [
    t('landing.benefits.items.0') || "Deploy de projetos React, Node.js, Python e mais",
    t('landing.benefits.items.1') || "Suporte a projetos Fullstack (Frontend + Backend)",
    t('landing.benefits.items.2') || "Criação automática de usuário admin no deploy",
    t('landing.benefits.items.3') || "Logs em tempo real do processo de deploy",
    t('landing.benefits.items.4') || "Variáveis de ambiente seguras e criptografadas",
    t('landing.benefits.items.5') || "Compatível com Nginx e Apache automaticamente"
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
            <LanguageSelector />
            <Link to="/login">
              <Button variant="ghost" className="text-zinc-400 hover:text-white">
                {t('landing.hero.login')}
              </Button>
            </Link>
            <Link to="/register">
              <Button className="bg-emerald-600 hover:bg-emerald-700">
                {t('landing.hero.cta')}
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
            {t('landing.hero.title')}
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
            {t('landing.hero.title')}
          </h1>
          
          <p className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto">
            {t('landing.hero.subtitle')}
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register">
              <Button size="lg" className="bg-emerald-600 hover:bg-emerald-700 text-lg px-8 py-6">
                {t('landing.hero.cta')}
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 text-lg px-8 py-6">
                {t('landing.hero.login')}
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Emergent Compatibility Banner */}
      <section className="py-16 px-6 bg-gradient-to-r from-emerald-900/30 via-zinc-900 to-purple-900/30 border-y border-zinc-800">
        <div className="container mx-auto">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-8 max-w-5xl mx-auto">
            <div className="flex-1 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-500/30 text-purple-400 text-sm mb-4">
                <Zap className="w-4 h-4" />
                {t('landing.emergent.title')}
              </div>
              <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">
                {t('landing.emergent.subtitle')}
              </h2>
              <p className="text-zinc-400 text-lg">
                {t('landing.emergent.description')}
              </p>
            </div>
            <div className="flex-shrink-0">
              <div className="bg-zinc-900/80 border border-zinc-700 rounded-xl p-6 backdrop-blur">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                    <Terminal className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <div className="text-white font-semibold">Emergent</div>
                    <div className="text-zinc-500 text-sm">{t('landing.emergent.createWithAI')}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-zinc-400 mb-2">
                  <ArrowRight className="w-4 h-4 text-emerald-500" />
                  <span>{t('landing.emergent.saveToGithub')}</span>
                </div>
                <div className="flex items-center gap-2 text-zinc-400 mb-2">
                  <ArrowRight className="w-4 h-4 text-emerald-500" />
                  <span>{t('landing.emergent.configureVps')}</span>
                </div>
                <div className="flex items-center gap-2 text-emerald-400 font-medium">
                  <CheckCircle className="w-4 h-4" />
                  <span>{t('landing.emergent.autoDeploy')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Compatibility Section */}
      <section className="py-16 px-6">
        <div className="container mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
              {t('landing.compatibility.title')}
            </h2>
            <p className="text-zinc-400 text-lg">
              {t('landing.compatibility.subtitle')}
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 max-w-4xl mx-auto">
            {[
              { name: "Emergent", icon: "⚡", color: "from-purple-500 to-pink-500" },
              { name: "React", icon: "⚛️", color: "from-cyan-500 to-blue-500" },
              { name: "Next.js", icon: "▲", color: "from-zinc-600 to-zinc-800" },
              { name: "Node.js", icon: "🟢", color: "from-green-600 to-green-800" },
              { name: "Python", icon: "🐍", color: "from-yellow-500 to-blue-500" },
              { name: "FastAPI", icon: "🚀", color: "from-teal-500 to-emerald-600" },
              { name: "MongoDB", icon: "🍃", color: "from-green-500 to-green-700" },
              { name: "Express", icon: "📦", color: "from-zinc-500 to-zinc-700" },
              { name: "Vue.js", icon: "💚", color: "from-emerald-500 to-green-600" },
              { name: "Django", icon: "🎸", color: "from-green-700 to-green-900" },
              { name: "Flask", icon: "🧪", color: "from-zinc-600 to-zinc-800" },
              { name: "Static", icon: "📄", color: "from-orange-500 to-red-500" },
            ].map((tech, index) => (
              <div key={index} className="group relative">
                <div className={`absolute inset-0 bg-gradient-to-br ${tech.color} rounded-xl opacity-0 group-hover:opacity-20 transition-opacity`} />
                <div className="relative bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 text-center hover:border-zinc-600 transition-colors">
                  <div className="text-2xl mb-2">{tech.icon}</div>
                  <div className="text-sm text-zinc-400 group-hover:text-zinc-200 transition-colors">{tech.name}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 border-y border-zinc-800 bg-zinc-900/30">
        <div className="container mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-emerald-500 mb-2">5min</div>
              <div className="text-zinc-400">{t('landing.stats.deployTime')}</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-emerald-500 mb-2">100%</div>
              <div className="text-zinc-400">{t('landing.stats.automated')}</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-emerald-500 mb-2">SSL</div>
              <div className="text-zinc-400">{t('landing.stats.freeSSL')}</div>
            </div>
            <div className="text-center">
              <div className="text-3xl md:text-4xl font-bold text-emerald-500 mb-2">24/7</div>
              <div className="text-zinc-400">{t('landing.stats.online')}</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              {t('landing.features.title')}
            </h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
              {t('landing.features.subtitle')}
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
              {t('landing.howItWorks.title')}
            </h2>
            <p className="text-zinc-400 text-lg">
              {t('landing.howItWorks.subtitle')}
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-500 text-white text-2xl font-bold flex items-center justify-center mx-auto mb-4">
                1
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">{t('landing.howItWorks.step1.title')}</h3>
              <p className="text-zinc-400">
                {t('landing.howItWorks.step1.description')}
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-500 text-white text-2xl font-bold flex items-center justify-center mx-auto mb-4">
                2
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">{t('landing.howItWorks.step2.title')}</h3>
              <p className="text-zinc-400">
                {t('landing.howItWorks.step2.description')}
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-500 text-white text-2xl font-bold flex items-center justify-center mx-auto mb-4">
                3
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">{t('landing.howItWorks.step3.title')}</h3>
              <p className="text-zinc-400">
                {t('landing.howItWorks.step3.description')}
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
                {t('landing.benefits.title')}
              </h2>
              <p className="text-zinc-400 text-lg mb-8">
                {t('landing.benefits.subtitle')}
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

      {/* FAQ Section - SEO Optimized */}
      <section className="py-20 px-6 bg-zinc-900/30">
        <div className="container mx-auto max-w-4xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Perguntas Frequentes
            </h2>
            <p className="text-zinc-400 text-lg">
              Tire suas dúvidas sobre como hospedar projetos do Emergent
            </p>
          </div>
          
          <div className="space-y-4">
            {[
              {
                question: "Como hospedar um site criado no Emergent?",
                answer: "Com o DeployVPS você pode hospedar qualquer projeto criado no Emergent.sh em sua própria VPS. Basta salvar o projeto no GitHub usando a função 'Save to GitHub' do Emergent, cadastrar sua VPS no DeployVPS e clicar em Deploy. O sistema detecta automaticamente se é React, Node.js, Python ou FastAPI e configura tudo para você, incluindo MongoDB e SSL."
              },
              {
                question: "O DeployVPS funciona com projetos do Emergent.sh?",
                answer: "Sim! O DeployVPS é 100% compatível com projetos criados no Emergent.sh. Projetos fullstack com React + FastAPI + MongoDB são detectados automaticamente e deployados com as configurações corretas. Você mantém controle total hospedando em sua própria infraestrutura."
              },
              {
                question: "Posso usar minha própria VPS para hospedar apps do Emergent?",
                answer: "Sim! O DeployVPS permite que você use qualquer VPS (DigitalOcean, AWS, Linode, Vultr, etc.) para hospedar seus projetos do Emergent. Você tem controle total sobre sua infraestrutura e seus dados."
              },
              {
                question: "O deploy inclui banco de dados MongoDB?",
                answer: "Sim! O DeployVPS cria automaticamente um container MongoDB para seu projeto, com volume persistente para não perder dados. Também cria automaticamente um usuário admin no primeiro deploy, facilitando o acesso ao sistema."
              },
              {
                question: "Como configurar SSL/HTTPS no meu projeto?",
                answer: "O DeployVPS configura SSL automaticamente usando Let's Encrypt, que é gratuito. Basta configurar um domínio personalizado apontando para sua VPS e clicar em 'Ativar SSL'. O certificado é gratuito e renovado automaticamente."
              },
              {
                question: "O que acontece com meus dados quando faço redeploy?",
                answer: "O DeployVPS preserva seu banco de dados MongoDB durante o redeploy. Apenas os containers de frontend e backend são recriados, garantindo que você não perca nenhum dado dos seus usuários."
              }
            ].map((faq, index) => (
              <div key={index} className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-start gap-3">
                  <span className="text-emerald-500">Q:</span>
                  {faq.question}
                </h3>
                <p className="text-zinc-400 pl-7">
                  <span className="text-emerald-400 font-medium">R:</span> {faq.answer}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800 py-12 px-6">
        <div className="container mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center">
                  <Terminal className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-white">DeployVPS</span>
              </div>
              <p className="text-zinc-400 text-sm max-w-md">
                Plataforma de deploy automático para hospedar projetos criados no Emergent.sh e GitHub em sua própria VPS. 
                Suporte a React, Node.js, Python, FastAPI, MongoDB com SSL grátis.
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Recursos</h4>
              <ul className="space-y-2 text-zinc-400 text-sm">
                <li>Deploy Automático</li>
                <li>MongoDB Integrado</li>
                <li>SSL Gratuito</li>
                <li>Domínio Personalizado</li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">Compatível com</h4>
              <ul className="space-y-2 text-zinc-400 text-sm">
                <li>Emergent.sh</li>
                <li>React / Next.js</li>
                <li>Python / FastAPI</li>
                <li>Node.js / Express</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-zinc-800 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
            <span className="text-zinc-500 text-sm">© 2026 DeployVPS. Hospede seus projetos do Emergent na sua VPS.</span>
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
        </div>
      </footer>
    </div>
  );
}
