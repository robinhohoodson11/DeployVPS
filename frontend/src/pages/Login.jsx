import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { useLanguage } from "../i18n/LanguageContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { toast } from "sonner";
import { Server, GitBranch, Terminal } from "lucide-react";
import LanguageSelector from "../components/LanguageSelector";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success(t('common.success'));
      navigate("/dashboard");
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] grid-pattern flex">
      {/* Language Selector */}
      <div className="absolute top-4 right-4 z-50">
        <LanguageSelector />
      </div>
      
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-center items-center p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 via-transparent to-transparent" />
        <div className="relative z-10 max-w-md">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded bg-green-500/20 flex items-center justify-center">
              <Terminal className="w-6 h-6 text-green-500" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight">DeployVPS</h1>
          </div>
          <p className="text-xl text-zinc-400 mb-8">
            {t('landing.hero.subtitle')}
          </p>
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-zinc-300">
              <GitBranch className="w-5 h-5 text-green-500" />
              <span>{t('landing.features.items.autoDeploy.description')}</span>
            </div>
            <div className="flex items-center gap-3 text-zinc-300">
              <Server className="w-5 h-5 text-green-500" />
              <span>Deploy isolado com Docker</span>
            </div>
            <div className="flex items-center gap-3 text-zinc-300">
              <Terminal className="w-5 h-5 text-green-500" />
              <span>Logs em tempo real</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right side - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <Card className="w-full max-w-md bg-[#09090b] border-zinc-800">
          <CardHeader className="space-y-1">
            <div className="flex items-center gap-2 mb-4 lg:hidden">
              <div className="w-10 h-10 rounded bg-green-500/20 flex items-center justify-center">
                <Terminal className="w-5 h-5 text-green-500" />
              </div>
              <span className="text-xl font-bold">DeployVPS</span>
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight">{t('auth.login.title')}</CardTitle>
            <CardDescription className="text-zinc-500">
              {t('auth.login.subtitle')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-zinc-300">{t('auth.login.email')}</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  data-testid="login-email-input"
                  className="bg-zinc-900/50 border-zinc-800 focus:border-green-500/50 focus:ring-green-500/20"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-zinc-300">{t('auth.login.password')}</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  data-testid="login-password-input"
                  className="bg-zinc-900/50 border-zinc-800 focus:border-green-500/50 focus:ring-green-500/20"
                />
              </div>
              <Button
                type="submit"
                disabled={loading}
                data-testid="login-submit-btn"
                className="w-full bg-green-500 hover:bg-green-600 text-black font-semibold btn-glow"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                    {t('common.loading')}
                  </span>
                ) : t('auth.login.submit')}
              </Button>
            </form>
            <p className="mt-6 text-center text-sm text-zinc-500">
              {t('auth.login.noAccount')}{" "}
              <Link to="/register" className="text-green-500 hover:text-green-400 font-medium" data-testid="register-link">
                {t('auth.login.register')}
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
