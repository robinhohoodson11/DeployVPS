import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, api } from "../App";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { toast } from "sonner";
import { Terminal, Server, LogOut, User, ChevronDown, Shield, Key, Loader2 } from "lucide-react";

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error("As senhas não coincidem");
      return;
    }
    
    if (passwordForm.new_password.length < 6) {
      toast.error("A nova senha deve ter pelo menos 6 caracteres");
      return;
    }
    
    setSubmitting(true);
    try {
      await api.post("/auth/change-password", {
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      toast.success("Senha alterada com sucesso!");
      setPasswordDialogOpen(false);
      setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao alterar senha");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <header className="glass-header sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-3" data-testid="header-logo">
              <div className="w-9 h-9 rounded bg-green-500/20 flex items-center justify-center">
                <Terminal className="w-5 h-5 text-green-500" />
              </div>
              <span className="text-lg font-bold tracking-tight">DeployVPS</span>
            </Link>

            <nav className="flex items-center gap-6">
              <Link 
                to="/" 
                className="text-sm text-zinc-400 hover:text-white transition-colors"
                data-testid="nav-dashboard"
              >
                Dashboard
              </Link>
              <Link 
                to="/vps" 
                className="text-sm text-zinc-400 hover:text-white transition-colors flex items-center gap-1"
                data-testid="nav-vps"
              >
                <Server className="w-4 h-4" />
                Servidores
              </Link>
              
              {user?.role === "admin" && (
                <Link 
                  to="/admin/users" 
                  className="text-sm text-yellow-500 hover:text-yellow-400 transition-colors flex items-center gap-1"
                  data-testid="nav-admin"
                >
                  <Shield className="w-4 h-4" />
                  Admin
                </Link>
              )}

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="ghost" 
                    className="flex items-center gap-2 hover:bg-zinc-800"
                    data-testid="user-menu-trigger"
                  >
                    <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                      <User className="w-4 h-4 text-green-500" />
                    </div>
                    <span className="text-sm">{user?.name}</span>
                    <ChevronDown className="w-4 h-4 text-zinc-500" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48 bg-zinc-900 border-zinc-800">
                  <DropdownMenuItem className="text-zinc-400 focus:bg-zinc-800 focus:text-white cursor-default">
                    <User className="w-4 h-4 mr-2" />
                    {user?.email}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-zinc-800" />
                  <DropdownMenuItem 
                    onClick={() => setPasswordDialogOpen(true)}
                    className="text-zinc-300 focus:bg-zinc-800 focus:text-white cursor-pointer"
                  >
                    <Key className="w-4 h-4 mr-2" />
                    Alterar Senha
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-zinc-800" />
                  <DropdownMenuItem 
                    onClick={handleLogout}
                    className="text-red-400 focus:bg-red-500/10 focus:text-red-400 cursor-pointer"
                    data-testid="logout-btn"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Sair
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </nav>
          </div>
        </div>
      </header>

      {/* Change Password Dialog */}
      <Dialog open={passwordDialogOpen} onOpenChange={setPasswordDialogOpen}>
        <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="w-5 h-5 text-green-500" />
              Alterar Senha
            </DialogTitle>
            <DialogDescription className="text-zinc-500">
              Digite sua senha atual e a nova senha
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleChangePassword} className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label className="text-zinc-300">Senha Atual</Label>
              <Input
                type="password"
                placeholder="••••••••"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                required
                className="bg-zinc-800/50 border-zinc-700"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-zinc-300">Nova Senha</Label>
              <Input
                type="password"
                placeholder="••••••••"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                required
                className="bg-zinc-800/50 border-zinc-700"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-zinc-300">Confirmar Nova Senha</Label>
              <Input
                type="password"
                placeholder="••••••••"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                required
                className="bg-zinc-800/50 border-zinc-700"
              />
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setPasswordDialogOpen(false);
                  setPasswordForm({ current_password: "", new_password: "", confirm_password: "" });
                }}
                className="border-zinc-700"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={submitting}
                className="bg-green-500 hover:bg-green-600 text-black font-semibold"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Alterar Senha"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
