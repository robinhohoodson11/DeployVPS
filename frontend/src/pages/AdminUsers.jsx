import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api, useAuth } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { toast } from "sonner";
import { Plus, Users, Trash2, Shield, User, Loader2, Crown } from "lucide-react";
import Header from "../components/Header";

export default function AdminUsers() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "user",
  });

  useEffect(() => {
    if (user?.role !== "admin") {
      toast.error("Acesso negado");
      navigate("/");
      return;
    }
    fetchUsers();
  }, [user, navigate]);

  const fetchUsers = async () => {
    try {
      const response = await api.get("/admin/users");
      setUsers(response.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Acesso negado");
        navigate("/");
      } else {
        toast.error("Erro ao carregar usuários");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      await api.post("/admin/users", form);
      toast.success("Usuário criado com sucesso!");
      setDialogOpen(false);
      setForm({ name: "", email: "", password: "", role: "user" });
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao criar usuário");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (userId, userName) => {
    if (!window.confirm(`Tem certeza que deseja deletar o usuário "${userName}"? Isso também removerá todos os VPS e deploys deste usuário.`)) return;
    
    try {
      await api.delete(`/admin/users/${userId}`);
      toast.success("Usuário deletado");
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao deletar usuário");
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      await api.put(`/admin/users/${userId}/role?role=${newRole}`);
      toast.success(`Role atualizado para ${newRole}`);
      fetchUsers();
    } catch (error) {
      toast.error("Erro ao atualizar role");
    }
  };

  if (user?.role !== "admin") {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#09090b]">
      <Header />
      
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
              <Shield className="w-6 h-6 text-green-500" />
              Gerenciar Usuários
            </h1>
            <p className="text-zinc-500 mt-1">Crie e gerencie acessos ao sistema</p>
          </div>
          
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button 
                className="bg-green-500 hover:bg-green-600 text-black font-semibold btn-glow"
                data-testid="add-user-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Novo Usuário
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-900 border-zinc-800">
              <DialogHeader>
                <DialogTitle>Criar Novo Usuário</DialogTitle>
                <DialogDescription className="text-zinc-500">
                  Crie um novo acesso ao sistema
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label className="text-zinc-300">Nome</Label>
                  <Input
                    placeholder="Nome do usuário"
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    required
                    data-testid="user-name-input"
                    className="bg-zinc-800/50 border-zinc-700"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label className="text-zinc-300">Email</Label>
                  <Input
                    type="email"
                    placeholder="email@exemplo.com"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    required
                    data-testid="user-email-input"
                    className="bg-zinc-800/50 border-zinc-700"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label className="text-zinc-300">Senha</Label>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    required
                    data-testid="user-password-input"
                    className="bg-zinc-800/50 border-zinc-700"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label className="text-zinc-300">Tipo de Acesso</Label>
                  <Select
                    value={form.role}
                    onValueChange={(value) => setForm({ ...form, role: value })}
                  >
                    <SelectTrigger className="bg-zinc-800/50 border-zinc-700" data-testid="user-role-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      <SelectItem value="user">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4" />
                          Usuário Normal
                        </div>
                      </SelectItem>
                      <SelectItem value="admin">
                        <div className="flex items-center gap-2">
                          <Crown className="w-4 h-4 text-yellow-500" />
                          Administrador
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex justify-end gap-3 pt-4">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setDialogOpen(false)}
                    className="border-zinc-700"
                  >
                    Cancelar
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting}
                    data-testid="user-submit-btn"
                    className="bg-green-500 hover:bg-green-600 text-black font-semibold"
                  >
                    {submitting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : "Criar Usuário"}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500 uppercase tracking-wider">Total Usuários</p>
                  <p className="text-3xl font-bold font-mono mt-1">{users.length}</p>
                </div>
                <div className="w-12 h-12 rounded bg-zinc-800 flex items-center justify-center">
                  <Users className="w-6 h-6 text-zinc-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500 uppercase tracking-wider">Admins</p>
                  <p className="text-3xl font-bold font-mono mt-1 text-yellow-500">
                    {users.filter(u => u.role === "admin").length}
                  </p>
                </div>
                <div className="w-12 h-12 rounded bg-yellow-500/10 flex items-center justify-center">
                  <Crown className="w-6 h-6 text-yellow-500" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500 uppercase tracking-wider">Usuários</p>
                  <p className="text-3xl font-bold font-mono mt-1 text-green-500">
                    {users.filter(u => u.role === "user").length}
                  </p>
                </div>
                <div className="w-12 h-12 rounded bg-green-500/10 flex items-center justify-center">
                  <User className="w-6 h-6 text-green-500" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Users List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="grid gap-4">
            {users.map((u) => (
              <Card key={u.id} className="bg-zinc-900/50 border-zinc-800 card-hover" data-testid={`user-card-${u.id}`}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        u.role === "admin" ? "bg-yellow-500/20" : "bg-green-500/20"
                      }`}>
                        {u.role === "admin" ? (
                          <Crown className="w-5 h-5 text-yellow-500" />
                        ) : (
                          <User className="w-5 h-5 text-green-500" />
                        )}
                      </div>
                      <div>
                        <h3 className="font-semibold">{u.name}</h3>
                        <p className="text-sm text-zinc-500">{u.email}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      <Badge 
                        variant="outline" 
                        className={u.role === "admin" ? "text-yellow-500 border-yellow-500/50" : "text-green-500 border-green-500/50"}
                      >
                        {u.role === "admin" ? "Admin" : "Usuário"}
                      </Badge>
                      
                      <Select
                        value={u.role}
                        onValueChange={(value) => handleRoleChange(u.id, value)}
                        disabled={u.id === user?.id}
                      >
                        <SelectTrigger className="w-32 bg-zinc-800/50 border-zinc-700">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-900 border-zinc-800">
                          <SelectItem value="user">Usuário</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(u.id, u.name)}
                        disabled={u.id === user?.id}
                        data-testid={`delete-user-${u.id}`}
                        className="border-zinc-700 hover:bg-red-500/10 hover:text-red-500 hover:border-red-500/50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  
                  <div className="mt-3 pt-3 border-t border-zinc-800 text-xs text-zinc-500">
                    Criado em: {new Date(u.created_at).toLocaleString("pt-BR")}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
