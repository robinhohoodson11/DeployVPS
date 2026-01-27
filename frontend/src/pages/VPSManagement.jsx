import { useState, useEffect } from "react";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
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
import { Plus, Server, Trash2, CheckCircle, XCircle, Loader2, Wifi, Shield, ShieldCheck, ShieldAlert } from "lucide-react";
import Header from "../components/Header";

export default function VPSManagement() {
  const [vpsList, setVpsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [testingVps, setTestingVps] = useState(null);
  const [checkingSecurity, setCheckingSecurity] = useState(null);
  const [hardeningVps, setHardeningVps] = useState(null);
  const [securityReport, setSecurityReport] = useState(null);
  const [securityDialogOpen, setSecurityDialogOpen] = useState(false);
  
  const [form, setForm] = useState({
    name: "",
    host: "",
    port: 22,
    username: "",
    auth_type: "password",
    password: "",
    ssh_key: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchVPS = async () => {
    try {
      const response = await api.get("/vps");
      setVpsList(response.data);
    } catch (error) {
      toast.error("Erro ao carregar servidores");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVPS();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      await api.post("/vps", form);
      toast.success("Servidor adicionado com sucesso!");
      setDialogOpen(false);
      setForm({
        name: "",
        host: "",
        port: 22,
        username: "",
        auth_type: "password",
        password: "",
        ssh_key: "",
      });
      fetchVPS();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao adicionar servidor");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Tem certeza que deseja remover este servidor?")) return;
    
    try {
      await api.delete(`/vps/${id}`);
      toast.success("Servidor removido");
      fetchVPS();
    } catch (error) {
      toast.error("Erro ao remover servidor");
    }
  };

  const handleTest = async (id) => {
    setTestingVps(id);
    try {
      const response = await api.post(`/vps/${id}/test`);
      if (response.data.status === "success") {
        toast.success("Conexão bem sucedida!", {
          description: response.data.message
        });
      } else {
        toast.error("Falha na conexão", {
          description: response.data.message
        });
      }
    } catch (error) {
      toast.error("Erro ao testar conexão");
    } finally {
      setTestingVps(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b]">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Servidores VPS</h1>
            <p className="text-zinc-500 mt-1">Gerencie seus servidores para deploy</p>
          </div>
          
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button 
                className="bg-green-500 hover:bg-green-600 text-black font-semibold btn-glow"
                data-testid="add-vps-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Adicionar VPS
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg">
              <DialogHeader>
                <DialogTitle>Adicionar Servidor VPS</DialogTitle>
                <DialogDescription className="text-zinc-500">
                  Adicione as credenciais do seu servidor para fazer deploys
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Nome</Label>
                    <Input
                      placeholder="Meu Servidor"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      required
                      data-testid="vps-name-input"
                      className="bg-zinc-800/50 border-zinc-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Porta SSH</Label>
                    <Input
                      type="number"
                      placeholder="22"
                      value={form.port}
                      onChange={(e) => setForm({ ...form, port: parseInt(e.target.value) })}
                      required
                      data-testid="vps-port-input"
                      className="bg-zinc-800/50 border-zinc-700"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-zinc-300">Host / IP</Label>
                  <Input
                    placeholder="192.168.1.1 ou meuserver.com"
                    value={form.host}
                    onChange={(e) => setForm({ ...form, host: e.target.value })}
                    required
                    data-testid="vps-host-input"
                    className="bg-zinc-800/50 border-zinc-700 font-mono"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label className="text-zinc-300">Usuário SSH</Label>
                  <Input
                    placeholder="root"
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    required
                    data-testid="vps-username-input"
                    className="bg-zinc-800/50 border-zinc-700 font-mono"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label className="text-zinc-300">Tipo de Autenticação</Label>
                  <Select
                    value={form.auth_type}
                    onValueChange={(value) => setForm({ ...form, auth_type: value })}
                  >
                    <SelectTrigger className="bg-zinc-800/50 border-zinc-700" data-testid="vps-auth-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      <SelectItem value="password">Senha</SelectItem>
                      <SelectItem value="key">Chave SSH</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                {form.auth_type === "password" ? (
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Senha</Label>
                    <Input
                      type="password"
                      placeholder="••••••••"
                      value={form.password}
                      onChange={(e) => setForm({ ...form, password: e.target.value })}
                      required
                      data-testid="vps-password-input"
                      className="bg-zinc-800/50 border-zinc-700"
                    />
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Label className="text-zinc-300">Chave SSH Privada</Label>
                    <Textarea
                      placeholder="-----BEGIN RSA PRIVATE KEY-----"
                      value={form.ssh_key}
                      onChange={(e) => setForm({ ...form, ssh_key: e.target.value })}
                      required
                      rows={4}
                      data-testid="vps-sshkey-input"
                      className="bg-zinc-800/50 border-zinc-700 font-mono text-xs"
                    />
                  </div>
                )}
                
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
                    data-testid="vps-submit-btn"
                    className="bg-green-500 hover:bg-green-600 text-black font-semibold"
                  >
                    {submitting ? (
                      <span className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Adicionando...
                      </span>
                    ) : "Adicionar"}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : vpsList.length === 0 ? (
          <Card className="bg-zinc-900/50 border-zinc-800 border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center mb-4">
                <Server className="w-8 h-8 text-zinc-500" />
              </div>
              <h3 className="text-lg font-medium mb-2">Nenhum servidor cadastrado</h3>
              <p className="text-zinc-500 text-center mb-6 max-w-md">
                Adicione seu primeiro servidor VPS para começar a fazer deploys dos seus projetos.
              </p>
              <Button
                onClick={() => setDialogOpen(true)}
                className="bg-green-500 hover:bg-green-600 text-black font-semibold"
              >
                <Plus className="w-4 h-4 mr-2" />
                Adicionar VPS
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {vpsList.map((vps) => (
              <Card key={vps.id} className="bg-zinc-900/50 border-zinc-800 card-hover" data-testid={`vps-card-${vps.id}`}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded bg-zinc-800 flex items-center justify-center">
                        <Server className="w-5 h-5 text-zinc-400" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{vps.name}</CardTitle>
                        <p className="text-sm text-zinc-500 font-mono">{vps.host}</p>
                      </div>
                    </div>
                    <Badge variant="outline" className="text-green-500 border-green-500/50">
                      {vps.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Usuário</span>
                      <span className="font-mono">{vps.username}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Porta</span>
                      <span className="font-mono">{vps.port}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-zinc-500">Autenticação</span>
                      <span className="capitalize">{vps.auth_type === "password" ? "Senha" : "Chave SSH"}</span>
                    </div>
                  </div>
                  
                  <div className="flex gap-2 mt-4 pt-4 border-t border-zinc-800">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTest(vps.id)}
                      disabled={testingVps === vps.id}
                      data-testid={`test-vps-${vps.id}`}
                      className="flex-1 border-zinc-700 hover:bg-zinc-800"
                    >
                      {testingVps === vps.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Wifi className="w-4 h-4 mr-2" />
                          Testar
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(vps.id)}
                      data-testid={`delete-vps-${vps.id}`}
                      className="border-zinc-700 hover:bg-red-500/10 hover:text-red-500 hover:border-red-500/50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
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
