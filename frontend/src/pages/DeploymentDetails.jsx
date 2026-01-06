import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../App";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { ScrollArea } from "../components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import { toast } from "sonner";
import { 
  ArrowLeft, GitBranch, RefreshCw, Square, Play, Trash2, 
  Globe, Terminal, Clock, Server, ExternalLink, Loader2, Copy
} from "lucide-react";
import Header from "../components/Header";

const statusConfig = {
  running: { label: "Rodando", color: "bg-green-500", textColor: "text-green-500" },
  pending: { label: "Pendente", color: "bg-yellow-500", textColor: "text-yellow-500" },
  cloning: { label: "Clonando", color: "bg-purple-500", textColor: "text-purple-500" },
  building: { label: "Construindo", color: "bg-blue-500", textColor: "text-blue-500" },
  deploying: { label: "Deployando", color: "bg-amber-500", textColor: "text-amber-500" },
  failed: { label: "Falhou", color: "bg-red-500", textColor: "text-red-500" },
  stopped: { label: "Parado", color: "bg-zinc-500", textColor: "text-zinc-500" },
};

export default function DeploymentDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [deployment, setDeployment] = useState(null);
  const [vps, setVps] = useState(null);
  const [containerLogs, setContainerLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [domainDialogOpen, setDomainDialogOpen] = useState(false);
  const [domain, setDomain] = useState("");
  const logsEndRef = useRef(null);

  const fetchData = async () => {
    try {
      const [deployRes, logsRes] = await Promise.all([
        api.get(`/deployments/${id}`),
        api.get(`/deployments/${id}/logs`)
      ]);
      setDeployment(deployRes.data);
      setContainerLogs(logsRes.data.container_logs || []);
      
      if (deployRes.data.vps_id) {
        const vpsRes = await api.get(`/vps/${deployRes.data.vps_id}`);
        setVps(vpsRes.data);
      }
    } catch (error) {
      toast.error("Erro ao carregar dados");
      navigate("/");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [id]);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [deployment?.logs, containerLogs]);

  const handleRedeploy = async () => {
    setActionLoading("redeploy");
    try {
      await api.post(`/deployments/${id}/redeploy`);
      toast.success("Redeploy iniciado!");
      fetchData();
    } catch (error) {
      toast.error("Erro ao iniciar redeploy");
    } finally {
      setActionLoading(null);
    }
  };

  const handleStop = async () => {
    setActionLoading("stop");
    try {
      await api.post(`/deployments/${id}/stop`);
      toast.success("Container parado");
      fetchData();
    } catch (error) {
      toast.error("Erro ao parar container");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Tem certeza? Isso irá remover o container e todos os dados.")) return;
    
    try {
      await api.delete(`/deployments/${id}`);
      toast.success("Deployment removido");
      navigate("/");
    } catch (error) {
      toast.error("Erro ao remover deployment");
    }
  };

  const handleConfigureDomain = async () => {
    if (!domain.trim()) {
      toast.error("Digite um domínio");
      return;
    }
    
    setActionLoading("domain");
    try {
      const response = await api.post(`/deployments/${id}/domain`, { domain });
      toast.success("Domínio configurado!", {
        description: response.data.instructions[0]
      });
      setDomainDialogOpen(false);
      setDomain("");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao configurar domínio");
    } finally {
      setActionLoading(null);
    }
  };

  const handleRemoveDomain = async () => {
    setActionLoading("removeDomain");
    try {
      await api.delete(`/deployments/${id}/domain`);
      toast.success("Domínio removido");
      fetchData();
    } catch (error) {
      toast.error("Erro ao remover domínio");
    } finally {
      setActionLoading(null);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copiado!");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!deployment) return null;

  const status = statusConfig[deployment.status] || statusConfig.pending;
  const isDeploying = ["pending", "cloning", "building", "deploying"].includes(deployment.status);
  const appUrl = vps ? `http://${vps.host}:${deployment.port}` : null;

  return (
    <div className="min-h-screen bg-[#09090b]">
      <Header />
      
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="mb-6 text-zinc-400 hover:text-white"
          data-testid="back-btn"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Voltar
        </Button>
        
        {/* Header Card */}
        <Card className="bg-zinc-900/50 border-zinc-800 mb-6">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className={`w-4 h-4 rounded-full ${status.color} glow-dot ${isDeploying ? "animate-pulse-glow" : ""}`} />
                <div>
                  <h1 className="text-2xl font-bold tracking-tight">{deployment.project_name}</h1>
                  <p className="text-sm text-zinc-500 font-mono flex items-center gap-2">
                    <GitBranch className="w-4 h-4" />
                    {deployment.repo_url} ({deployment.branch})
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <Badge variant="outline" className={`${status.textColor} border-current text-sm py-1 px-3`}>
                  {status.label}
                </Badge>
                
                {deployment.status === "running" && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleStop}
                    disabled={actionLoading === "stop"}
                    data-testid="stop-btn"
                    className="border-zinc-700 hover:bg-red-500/10 hover:text-red-500"
                  >
                    {actionLoading === "stop" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />}
                  </Button>
                )}
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRedeploy}
                  disabled={isDeploying || actionLoading === "redeploy"}
                  data-testid="redeploy-btn"
                  className="border-zinc-700 hover:bg-zinc-800"
                >
                  {actionLoading === "redeploy" ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDelete}
                  data-testid="delete-btn"
                  className="border-zinc-700 hover:bg-red-500/10 hover:text-red-500"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-6 md:grid-cols-3">
          {/* Info Cards */}
          <div className="space-y-4">
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-zinc-400">Informações</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-500">Porta</span>
                  <span className="font-mono">{deployment.port}</span>
                </div>
                {deployment.container_id && (
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Container ID</span>
                    <span className="font-mono text-xs">{deployment.container_id}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-500">Criado em</span>
                  <span className="font-mono text-xs">
                    {new Date(deployment.created_at).toLocaleString("pt-BR")}
                  </span>
                </div>
              </CardContent>
            </Card>
            
            {vps && (
              <Card className="bg-zinc-900/50 border-zinc-800">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                    <Server className="w-4 h-4" />
                    Servidor
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Nome</span>
                    <span>{vps.name}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Host</span>
                    <span className="font-mono">{vps.host}</span>
                  </div>
                  {appUrl && deployment.status === "running" && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(appUrl, "_blank")}
                      data-testid="open-app-btn"
                      className="w-full mt-2 border-zinc-700 hover:bg-zinc-800"
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Abrir App
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}
            
            {/* Domain Card */}
            <Card className="bg-zinc-900/50 border-zinc-800">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  Domínio
                </CardTitle>
              </CardHeader>
              <CardContent>
                {deployment.domain ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-green-500">{deployment.domain}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(deployment.domain)}
                        className="h-8 w-8 p-0"
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleRemoveDomain}
                      disabled={actionLoading === "removeDomain"}
                      className="w-full border-zinc-700 hover:bg-red-500/10 hover:text-red-500"
                    >
                      {actionLoading === "removeDomain" ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        "Remover Domínio"
                      )}
                    </Button>
                  </div>
                ) : (
                  <Dialog open={domainDialogOpen} onOpenChange={setDomainDialogOpen}>
                    <DialogTrigger asChild>
                      <Button
                        variant="outline"
                        size="sm"
                        data-testid="configure-domain-btn"
                        className="w-full border-zinc-700 border-dashed hover:bg-zinc-800"
                      >
                        <Globe className="w-4 h-4 mr-2" />
                        Configurar Domínio
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-zinc-900 border-zinc-800">
                      <DialogHeader>
                        <DialogTitle>Configurar Domínio</DialogTitle>
                        <DialogDescription className="text-zinc-500">
                          Configure um domínio personalizado para sua aplicação
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 mt-4">
                        <div className="space-y-2">
                          <Label className="text-zinc-300">Domínio</Label>
                          <Input
                            placeholder="app.meudominio.com"
                            value={domain}
                            onChange={(e) => setDomain(e.target.value)}
                            data-testid="domain-input"
                            className="bg-zinc-800/50 border-zinc-700 font-mono"
                          />
                        </div>
                        <div className="bg-zinc-800/50 rounded p-4 text-sm text-zinc-400 space-y-2">
                          <p className="font-medium text-zinc-300">Após configurar:</p>
                          <ol className="list-decimal list-inside space-y-1">
                            <li>Aponte o DNS A record para: <span className="font-mono text-green-500">{vps?.host}</span></li>
                            <li>Para HTTPS, execute no servidor: <span className="font-mono text-xs">certbot --nginx -d {domain || "seu.dominio.com"}</span></li>
                          </ol>
                        </div>
                        <div className="flex justify-end gap-3">
                          <Button
                            variant="outline"
                            onClick={() => setDomainDialogOpen(false)}
                            className="border-zinc-700"
                          >
                            Cancelar
                          </Button>
                          <Button
                            onClick={handleConfigureDomain}
                            disabled={actionLoading === "domain"}
                            data-testid="domain-submit-btn"
                            className="bg-green-500 hover:bg-green-600 text-black font-semibold"
                          >
                            {actionLoading === "domain" ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              "Configurar"
                            )}
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Logs */}
          <div className="md:col-span-2">
            <Card className="bg-zinc-900/50 border-zinc-800 h-[600px] flex flex-col">
              <CardHeader className="pb-2 flex-shrink-0">
                <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                  <Terminal className="w-4 h-4" />
                  Logs
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden p-0">
                <ScrollArea className="h-full px-6 pb-6">
                  <div className="terminal-log rounded p-4 font-mono text-xs space-y-1">
                    {deployment.logs?.map((log, i) => (
                      <div 
                        key={i} 
                        className={`log-entry flex gap-3 ${
                          log.level === "error" ? "text-red-400" : 
                          log.level === "success" ? "text-green-400" : "text-zinc-400"
                        }`}
                      >
                        <span className="text-zinc-600 flex-shrink-0">
                          {new Date(log.timestamp).toLocaleTimeString("pt-BR")}
                        </span>
                        <span className="whitespace-pre-wrap break-all">{log.message}</span>
                      </div>
                    ))}
                    
                    {containerLogs.length > 0 && (
                      <>
                        <div className="border-t border-zinc-800 my-4 pt-4">
                          <span className="text-zinc-500">--- Container Logs ---</span>
                        </div>
                        {containerLogs.map((line, i) => (
                          <div key={`container-${i}`} className="text-zinc-400 whitespace-pre-wrap break-all">
                            {line}
                          </div>
                        ))}
                      </>
                    )}
                    
                    {(deployment.logs?.length === 0 && containerLogs.length === 0) && (
                      <div className="text-zinc-600 text-center py-8">
                        Aguardando logs...
                      </div>
                    )}
                    
                    <div ref={logsEndRef} />
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
