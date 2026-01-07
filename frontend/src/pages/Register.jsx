import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, api } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { toast } from "sonner";
import { Terminal, Clock, CheckCircle } from "lucide-react";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingMessage, setPendingMessage] = useState(null);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      toast.error("As senhas não coincidem");
      return;
    }
    
    if (password.length < 6) {
      toast.error("A senha deve ter pelo menos 6 caracteres");
      return;
    }
    
    setLoading(true);
    try {
      const response = await api.post("/auth/register", { name, email, password });
      
      // Check if registration is pending approval
      if (response.data.status === "pending") {
        setPendingMessage(response.data.message);
        toast.success(response.data.message);
      } else {
        // First user (admin) - auto login
        const { access_token, user } = response.data;
        localStorage.setItem("token", access_token);
        localStorage.setItem("user", JSON.stringify(user));
        toast.success("Conta criada com sucesso!");
        window.location.href = "/";
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao criar conta");
    } finally {
      setLoading(false);
    }
  };

  // Show pending message screen
  if (pendingMessage) {
    return (
      <div className="min-h-screen bg-[#09090b] grid-pattern flex items-center justify-center p-8">
        <Card className="w-full max-w-md bg-[#09090b] border-zinc-800">
          <CardHeader className="space-y-1 text-center">
            <div className="w-16 h-16 rounded-full bg-yellow-500/20 flex items-center justify-center mx-auto mb-4">
              <Clock className="w-8 h-8 text-yellow-500" />
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight">Cadastro Recebido!</CardTitle>
            <CardDescription className="text-zinc-400 text-base">
              {pendingMessage}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-zinc-800/50 rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2 text-sm text-zinc-400">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Email cadastrado: <strong className="text-zinc-200">{email}</strong></span>
              </div>
              <p className="text-xs text-zinc-500">
                Você receberá um email quando sua conta for aprovada.
              </p>
            </div>
            <Link to="/login">
              <Button variant="outline" className="w-full border-zinc-700">
                Voltar para Login
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090b] grid-pattern flex items-center justify-center p-8">
      <Card className="w-full max-w-md bg-[#09090b] border-zinc-800">
        <CardHeader className="space-y-1">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-10 h-10 rounded bg-green-500/20 flex items-center justify-center">
              <Terminal className="w-5 h-5 text-green-500" />
            </div>
            <span className="text-xl font-bold">DeployVPS</span>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">Criar conta</CardTitle>
          <CardDescription className="text-zinc-500">
            Crie sua conta para começar a fazer deploys
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-zinc-300">Nome</Label>
              <Input
                id="name"
                type="text"
                placeholder="Seu nome"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                data-testid="register-name-input"
                className="bg-zinc-900/50 border-zinc-800 focus:border-green-500/50 focus:ring-green-500/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-300">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid="register-email-input"
                className="bg-zinc-900/50 border-zinc-800 focus:border-green-500/50 focus:ring-green-500/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-zinc-300">Senha</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                data-testid="register-password-input"
                className="bg-zinc-900/50 border-zinc-800 focus:border-green-500/50 focus:ring-green-500/20"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-zinc-300">Confirmar Senha</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                data-testid="register-confirm-password-input"
                className="bg-zinc-900/50 border-zinc-800 focus:border-green-500/50 focus:ring-green-500/20"
              />
            </div>
            <Button
              type="submit"
              disabled={loading}
              data-testid="register-submit-btn"
              className="w-full bg-green-500 hover:bg-green-600 text-black font-semibold btn-glow"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  Criando...
                </span>
              ) : "Criar conta"}
            </Button>
          </form>
          <div className="mt-4 p-3 bg-zinc-800/30 rounded-lg">
            <p className="text-xs text-zinc-500 text-center">
              ⚠️ Após o cadastro, sua conta precisará ser aprovada pelo administrador.
            </p>
          </div>
          <p className="mt-4 text-center text-sm text-zinc-500">
            Já tem uma conta?{" "}
            <Link to="/login" className="text-green-500 hover:text-green-400 font-medium" data-testid="login-link">
              Entrar
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
