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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { Switch } from "../components/ui/switch";
import { toast } from "sonner";
import { 
  Plus, Users, Trash2, Shield, User, Loader2, Crown, 
  Clock, CheckCircle, XCircle, Ban, Mail, Settings,
  UserCheck, UserX, Calendar, AlertCircle, Send
} from "lucide-react";
import Header from "../components/Header";

export default function AdminUsers() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [emailDialogOpen, setEmailDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [activeTab, setActiveTab] = useState("all");
  
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "user",
    expires_at: "",
    send_email: false,
  });

  const [editForm, setEditForm] = useState({
    name: "",
    role: "user",
    status: "active",
    expires_at: "",
  });

  const [emailConfig, setEmailConfig] = useState({
    smtp_host: "",
    smtp_port: 587,
    smtp_user: "",
    smtp_password: "",
    smtp_from_name: "DeployVPS",
    smtp_from_email: "",
    smtp_use_tls: true,
    configured: false,
  });

  useEffect(() => {
    if (user?.role !== "admin") {
      toast.error("Acesso negado");
      navigate("/");
      return;
    }
    fetchData();
  }, [user, navigate]);

  const fetchData = async () => {
    try {
      const [usersRes, pendingRes, statsRes, emailRes] = await Promise.all([
        api.get("/admin/users"),
        api.get("/admin/users/pending"),
        api.get("/admin/stats"),
        api.get("/admin/settings/email").catch(() => ({ data: { configured: false } })),
      ]);
      setUsers(usersRes.data);
      setPendingUsers(pendingRes.data);
      setStats(statsRes.data);
      if (emailRes.data.configured) {
        setEmailConfig({ ...emailRes.data, smtp_password: "" });
      }
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error("Acesso negado");
        navigate("/");
      } else {
        toast.error("Erro ao carregar dados");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      const payload = {
        ...form,
        expires_at: form.expires_at || null,
      };
      await api.post("/admin/users", payload);
      toast.success("Usuário criado com sucesso!");
      if (form.send_email) {
        toast.info("Email com credenciais será enviado");
      }
      setDialogOpen(false);
      setForm({ name: "", email: "", password: "", role: "user", expires_at: "", send_email: false });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao criar usuário");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    if (!selectedUser) return;
    setSubmitting(true);
    
    try {
      await api.put(`/admin/users/${selectedUser.id}`, {
        ...editForm,
        expires_at: editForm.expires_at || "",
      });
      toast.success("Usuário atualizado!");
      setEditDialogOpen(false);
      setSelectedUser(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao atualizar usuário");
    } finally {
      setSubmitting(false);
    }
  };

  const openEditDialog = (u) => {
    setSelectedUser(u);
    setEditForm({
      name: u.name,
      role: u.role,
      status: u.status || "active",
      expires_at: u.expires_at ? u.expires_at.split("T")[0] : "",
    });
    setEditDialogOpen(true);
  };

  const handleApprove = async (userId) => {
    try {
      await api.post(`/admin/users/${userId}/approve`);
      toast.success("Usuário aprovado!");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao aprovar usuário");
    }
  };

  const handleReject = async (userId, userName) => {
    if (!window.confirm(`Rejeitar e remover "${userName}"?`)) return;
    try {
      await api.post(`/admin/users/${userId}/reject`);
      toast.success("Usuário rejeitado");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao rejeitar usuário");
    }
  };

  const handleBlock = async (userId) => {
    try {
      await api.post(`/admin/users/${userId}/block`);
      toast.success("Usuário bloqueado");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao bloquear usuário");
    }
  };

  const handleUnblock = async (userId) => {
    try {
      await api.post(`/admin/users/${userId}/unblock`);
      toast.success("Usuário desbloqueado");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao desbloquear usuário");
    }
  };

  const handleDelete = async (userId, userName) => {
    if (!window.confirm(`Deletar "${userName}"? Isso removerá todos os VPS e deploys.`)) return;
    
    try {
      await api.delete(`/admin/users/${userId}`);
      toast.success("Usuário deletado");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao deletar usuário");
    }
  };

  const handleSaveEmailConfig = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      await api.post("/admin/settings/email", emailConfig);
      toast.success("Configuração de email salva!");
      setEmailDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao salvar configuração");
    } finally {
      setSubmitting(false);
    }
  };

  const handleTestEmail = async () => {
    try {
      await api.post("/admin/settings/email/test");
      toast.success("Email de teste enviado!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao enviar email de teste");
    }
  };

  const getStatusBadge = (status) => {
    const configs = {
      pending: { color: "text-yellow-500 border-yellow-500/50", icon: Clock, label: "Pendente" },
      active: { color: "text-green-500 border-green-500/50", icon: CheckCircle, label: "Ativo" },
      expired: { color: "text-orange-500 border-orange-500/50", icon: AlertCircle, label: "Expirado" },
      blocked: { color: "text-red-500 border-red-500/50", icon: Ban, label: "Bloqueado" },
    };
    const config = configs[status] || configs.active;
    const Icon = config.icon;
    return (
      <Badge variant="outline" className={config.color}>
        <Icon className="w-3 h-3 mr-1" />
        {config.label}
      </Badge>
    );
  };

  const filteredUsers = users.filter(u => {
    if (activeTab === "all") return true;
    if (activeTab === "pending") return u.status === "pending";
    if (activeTab === "active") return u.status === "active";
    if (activeTab === "expired") return u.status === "expired";
    if (activeTab === "blocked") return u.status === "blocked";
    return true;
  });

  if (user?.role !== "admin") return null;

  return (
    <div className="min-h-screen bg-[#09090b]">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
              <Shield className="w-6 h-6 text-green-500" />
              Painel Administrativo
            </h1>
            <p className="text-zinc-500 mt-1">Gerencie usuários e configurações do sistema</p>
          </div>
          
          <div className="flex gap-2">
            {/* Email Config Button */}
            <Dialog open={emailDialogOpen} onOpenChange={setEmailDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-zinc-700">
                  <Mail className="w-4 h-4 mr-2" />
                  Email
                  {emailConfig.configured && <CheckCircle className="w-3 h-3 ml-2 text-green-500" />}
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 border-zinc-800 max-w-md">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <Mail className="w-5 h-5" />
                    Configurar Email (SMTP)
                  </DialogTitle>
                  <DialogDescription className="text-zinc-500">
                    Configure o servidor SMTP para enviar emails de acesso
                  </DialogDescription>
                </DialogHeader>
                
                <form onSubmit={handleSaveEmailConfig} className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-zinc-300">Servidor SMTP</Label>
                      <Input
                        placeholder="smtp.gmail.com"
                        value={emailConfig.smtp_host}
                        onChange={(e) => setEmailConfig({ ...emailConfig, smtp_host: e.target.value })}
                        required
                        className="bg-zinc-800/50 border-zinc-700"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-zinc-300">Porta</Label>
                      <Input
                        type="number"
                        placeholder="587"
                        value={emailConfig.smtp_port}
                        onChange={(e) => setEmailConfig({ ...emailConfig, smtp_port: parseInt(e.target.value) })}
                        required
                        className="bg-zinc-800/50 border-zinc-700"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Usuário SMTP</Label>
                    <Input
                      placeholder="seu-email@gmail.com"
                      value={emailConfig.smtp_user}
                      onChange={(e) => setEmailConfig({ ...emailConfig, smtp_user: e.target.value })}
                      required
                      className="bg-zinc-800/50 border-zinc-700"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Senha / App Password</Label>
                    <Input
                      type="password"
                      placeholder="••••••••"
                      value={emailConfig.smtp_password}
                      onChange={(e) => setEmailConfig({ ...emailConfig, smtp_password: e.target.value })}
                      required={!emailConfig.configured}
                      className="bg-zinc-800/50 border-zinc-700"
                    />
                    <p className="text-xs text-zinc-500">Para Gmail, use uma App Password</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Nome do Remetente</Label>
                    <Input
                      placeholder="DeployVPS"
                      value={emailConfig.smtp_from_name}
                      onChange={(e) => setEmailConfig({ ...emailConfig, smtp_from_name: e.target.value })}
                      className="bg-zinc-800/50 border-zinc-700"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label className="text-zinc-300">Usar TLS</Label>
                    <Switch
                      checked={emailConfig.smtp_use_tls}
                      onCheckedChange={(checked) => setEmailConfig({ ...emailConfig, smtp_use_tls: checked })}
                    />
                  </div>
                  
                  <div className="flex justify-between gap-3 pt-4">
                    {emailConfig.configured && (
                      <Button type="button" variant="outline" onClick={handleTestEmail} className="border-zinc-700">
                        <Send className="w-4 h-4 mr-2" />
                        Testar
                      </Button>
                    )}
                    <div className="flex gap-3 ml-auto">
                      <Button type="button" variant="outline" onClick={() => setEmailDialogOpen(false)} className="border-zinc-700">
                        Cancelar
                      </Button>
                      <Button type="submit" disabled={submitting} className="bg-green-500 hover:bg-green-600 text-black font-semibold">
                        {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Salvar"}
                      </Button>
                    </div>
                  </div>
                </form>
              </DialogContent>
            </Dialog>

            {/* New User Button */}
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-green-500 hover:bg-green-600 text-black font-semibold btn-glow">
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Usuário
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 border-zinc-800">
                <DialogHeader>
                  <DialogTitle>Criar Novo Usuário</DialogTitle>
                  <DialogDescription className="text-zinc-500">
                    Crie um novo acesso ao sistema (já aprovado)
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
                      className="bg-zinc-800/50 border-zinc-700"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-zinc-300">Tipo de Acesso</Label>
                      <Select value={form.role} onValueChange={(value) => setForm({ ...form, role: value })}>
                        <SelectTrigger className="bg-zinc-800/50 border-zinc-700">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-900 border-zinc-800">
                          <SelectItem value="user">
                            <div className="flex items-center gap-2">
                              <User className="w-4 h-4" />
                              Usuário
                            </div>
                          </SelectItem>
                          <SelectItem value="admin">
                            <div className="flex items-center gap-2">
                              <Crown className="w-4 h-4 text-yellow-500" />
                              Admin
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label className="text-zinc-300">Expira em</Label>
                      <Input
                        type="date"
                        value={form.expires_at}
                        onChange={(e) => setForm({ ...form, expires_at: e.target.value })}
                        className="bg-zinc-800/50 border-zinc-700"
                        min={new Date().toISOString().split("T")[0]}
                      />
                    </div>
                  </div>
                  
                  {emailConfig.configured && (
                    <div className="flex items-center justify-between p-3 bg-zinc-800/30 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-zinc-400" />
                        <span className="text-sm text-zinc-300">Enviar credenciais por email</span>
                      </div>
                      <Switch
                        checked={form.send_email}
                        onCheckedChange={(checked) => setForm({ ...form, send_email: checked })}
                      />
                    </div>
                  )}
                  
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="border-zinc-700">
                      Cancelar
                    </Button>
                    <Button type="submit" disabled={submitting} className="bg-green-500 hover:bg-green-600 text-black font-semibold">
                      {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Criar Usuário"}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-zinc-800 flex items-center justify-center">
                    <Users className="w-5 h-5 text-zinc-400" />
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 uppercase">Total</p>
                    <p className="text-2xl font-bold font-mono">{stats.total_users}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-yellow-500/10 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-yellow-500" />
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 uppercase">Pendentes</p>
                    <p className="text-2xl font-bold font-mono text-yellow-500">{stats.pending_users}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-green-500/10 flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 uppercase">Ativos</p>
                    <p className="text-2xl font-bold font-mono text-green-500">{stats.active_users}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-orange-500/10 flex items-center justify-center">
                    <AlertCircle className="w-5 h-5 text-orange-500" />
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 uppercase">Expirados</p>
                    <p className="text-2xl font-bold font-mono text-orange-500">{stats.expired_users}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-red-500/10 flex items-center justify-center">
                    <Ban className="w-5 h-5 text-red-500" />
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 uppercase">Bloqueados</p>
                    <p className="text-2xl font-bold font-mono text-red-500">{stats.blocked_users}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-yellow-500/10 flex items-center justify-center">
                    <Crown className="w-5 h-5 text-yellow-500" />
                  </div>
                  <div>
                    <p className="text-xs text-zinc-500 uppercase">Admins</p>
                    <p className="text-2xl font-bold font-mono text-yellow-500">{stats.admin_users}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Pending Users Alert */}
        {pendingUsers.length > 0 && (
          <Card className="bg-yellow-500/10 border-yellow-500/30 mb-6">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-yellow-500" />
                <span className="text-yellow-500 font-medium">
                  {pendingUsers.length} usuário(s) aguardando aprovação
                </span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
          <TabsList className="bg-zinc-800/50 border border-zinc-700">
            <TabsTrigger value="all" className="data-[state=active]:bg-zinc-700">Todos</TabsTrigger>
            <TabsTrigger value="pending" className="data-[state=active]:bg-zinc-700">
              Pendentes {pendingUsers.length > 0 && `(${pendingUsers.length})`}
            </TabsTrigger>
            <TabsTrigger value="active" className="data-[state=active]:bg-zinc-700">Ativos</TabsTrigger>
            <TabsTrigger value="expired" className="data-[state=active]:bg-zinc-700">Expirados</TabsTrigger>
            <TabsTrigger value="blocked" className="data-[state=active]:bg-zinc-700">Bloqueados</TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Users List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="text-center py-20 text-zinc-500">
            Nenhum usuário encontrado
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredUsers.map((u) => (
              <Card key={u.id} className="bg-zinc-900/50 border-zinc-800 card-hover">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                        u.role === "admin" ? "bg-yellow-500/20" : "bg-green-500/20"
                      }`}>
                        {u.role === "admin" ? (
                          <Crown className="w-6 h-6 text-yellow-500" />
                        ) : (
                          <User className="w-6 h-6 text-green-500" />
                        )}
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">{u.name}</h3>
                        <p className="text-sm text-zinc-500">{u.email}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      {getStatusBadge(u.status || "active")}
                      
                      {u.role === "admin" && (
                        <Badge variant="outline" className="text-yellow-500 border-yellow-500/50">
                          <Crown className="w-3 h-3 mr-1" />
                          Admin
                        </Badge>
                      )}
                      
                      {u.expires_at && (
                        <Badge variant="outline" className="text-zinc-400 border-zinc-600">
                          <Calendar className="w-3 h-3 mr-1" />
                          {new Date(u.expires_at).toLocaleDateString("pt-BR")}
                        </Badge>
                      )}
                      
                      {/* Actions */}
                      <div className="flex gap-2 ml-4">
                        {u.status === "pending" && (
                          <>
                            <Button
                              size="sm"
                              onClick={() => handleApprove(u.id)}
                              className="bg-green-500/20 text-green-500 hover:bg-green-500/30"
                            >
                              <UserCheck className="w-4 h-4 mr-1" />
                              Aprovar
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleReject(u.id, u.name)}
                              className="border-red-500/50 text-red-500 hover:bg-red-500/10"
                            >
                              <UserX className="w-4 h-4 mr-1" />
                              Rejeitar
                            </Button>
                          </>
                        )}
                        
                        {u.status !== "pending" && u.id !== user?.id && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openEditDialog(u)}
                              className="border-zinc-700"
                            >
                              <Settings className="w-4 h-4" />
                            </Button>
                            
                            {u.status === "blocked" ? (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleUnblock(u.id)}
                                className="border-green-500/50 text-green-500 hover:bg-green-500/10"
                              >
                                <CheckCircle className="w-4 h-4" />
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleBlock(u.id)}
                                className="border-orange-500/50 text-orange-500 hover:bg-orange-500/10"
                              >
                                <Ban className="w-4 h-4" />
                              </Button>
                            )}
                            
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDelete(u.id, u.name)}
                              className="border-red-500/50 text-red-500 hover:bg-red-500/10"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                      </div>
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

        {/* Edit Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent className="bg-zinc-900 border-zinc-800">
            <DialogHeader>
              <DialogTitle>Editar Usuário</DialogTitle>
              <DialogDescription className="text-zinc-500">
                {selectedUser?.email}
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleEdit} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label className="text-zinc-300">Nome</Label>
                <Input
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="bg-zinc-800/50 border-zinc-700"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-zinc-300">Tipo</Label>
                  <Select value={editForm.role} onValueChange={(value) => setEditForm({ ...editForm, role: value })}>
                    <SelectTrigger className="bg-zinc-800/50 border-zinc-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      <SelectItem value="user">Usuário</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-zinc-300">Status</Label>
                  <Select value={editForm.status} onValueChange={(value) => setEditForm({ ...editForm, status: value })}>
                    <SelectTrigger className="bg-zinc-800/50 border-zinc-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      <SelectItem value="active">Ativo</SelectItem>
                      <SelectItem value="expired">Expirado</SelectItem>
                      <SelectItem value="blocked">Bloqueado</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label className="text-zinc-300">Data de Expiração</Label>
                <Input
                  type="date"
                  value={editForm.expires_at}
                  onChange={(e) => setEditForm({ ...editForm, expires_at: e.target.value })}
                  className="bg-zinc-800/50 border-zinc-700"
                />
                <p className="text-xs text-zinc-500">Deixe vazio para acesso sem expiração</p>
              </div>
              
              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="outline" onClick={() => setEditDialogOpen(false)} className="border-zinc-700">
                  Cancelar
                </Button>
                <Button type="submit" disabled={submitting} className="bg-green-500 hover:bg-green-600 text-black font-semibold">
                  {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Salvar"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}
