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
  Globe, Terminal, Clock, Server, ExternalLink, Loader2, Copy, Lock, ShieldCheck,
  ChevronDown, ChevronRight, CheckCircle, XCircle, Circle
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

// Define deployment steps for the progress indicator
const deploymentSteps = [
  { id: "pending", label: "Iniciando", keywords: ["Starting", "Iniciando", "Pending"] },
  { id: "cloning", label: "Clonando Repositório", keywords: ["Cloning", "Clonando", "repository", "repositório"] },
  { id: "detecting", label: "Detectando Projeto", keywords: ["Detected", "Detectado", "Fullstack", "frontend", "backend"] },
  { id: "mongodb", label: "Configurando MongoDB", keywords: ["MongoDB", "mongo", "database"] },
  { id: "building_backend", label: "Construindo Backend", keywords: ["Building backend", "backend container", "Backend build"] },
  { id: "building_frontend", label: "Construindo Frontend", keywords: ["Building frontend", "frontend container", "Frontend build"] },
  { id: "starting", label: "Iniciando Containers", keywords: ["Starting container", "Iniciando container", "docker run"] },
  { id: "running", label: "Deploy Concluído", keywords: ["successful", "sucesso", "running", "Rodando"] },
];

// Component for collapsible log step
function LogStep({ step, logs, isActive, isCompleted, isFailed }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const getStepIcon = () => {
    if (isFailed) return <XCircle className="w-5 h-5 text-red-500" />;
    if (isCompleted) return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (isActive) return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    return <Circle className="w-5 h-5 text-zinc-600" />;
  };

  const getStepColor = () => {
    if (isFailed) return "border-red-500/30 bg-red-500/5";
    if (isCompleted) return "border-green-500/30 bg-green-500/5";
    if (isActive) return "border-blue-500/30 bg-blue-500/5";
    return "border-zinc-800 bg-zinc-900/30";
  };

  return (
    <div className={`border rounded-lg overflow-hidden transition-all ${getStepColor()}`}>
      <button
        onClick={() => logs.length > 0 && setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors"
        disabled={logs.length === 0}
      >
        <div className="flex items-center gap-3">
          {getStepIcon()}
          <span className={`font-medium ${isActive ? "text-blue-400" : isCompleted ? "text-green-400" : isFailed ? "text-red-400" : "text-zinc-500"}`}>
            {step.label}
          </span>
          {isActive && (
            <span className="text-xs text-blue-400 animate-pulse">Em andamento...</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {logs.length > 0 && (
            <span className="text-xs text-zinc-500">{logs.length} log(s)</span>
          )}
          {logs.length > 0 && (
            isExpanded ? <ChevronDown className="w-4 h-4 text-zinc-500" /> : <ChevronRight className="w-4 h-4 text-zinc-500" />
          )}
        </div>
      </button>
      
      {isExpanded && logs.length > 0 && (
        <div className="border-t border-zinc-800 bg-zinc-950/50 p-3 max-h-60 overflow-y-auto">
          <div className="font-mono text-xs space-y-1">
            {logs.map((log, i) => (
              <div 
                key={i} 
                className={`flex gap-2 ${
                  log.level === "error" ? "text-red-400" : 
                  log.level === "success" ? "text-green-400" : 
                  log.level === "warning" ? "text-yellow-400" : "text-zinc-400"
                }`}
              >
                <span className="text-zinc-600 flex-shrink-0">
                  {new Date(log.timestamp).toLocaleTimeString("pt-BR")}
                </span>
                <span className="whitespace-pre-wrap break-all">{log.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

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
  const [showAllLogs, setShowAllLogs] = useState(false);
  const logsEndRef = useRef(null);

  const fetchData = async (isInitial = false) => {
    try {
      const [deployRes, logsRes] = await Promise.all([
        api.get(`/deployments/${id}`),
        api.get(`/deployments/${id}/logs`)
      ]);
      setDeployment(deployRes.data);
      setContainerLogs(logsRes.data.container_logs || []);
      
      if (deployRes.data.vps_id && !vps) {
        const vpsRes = await api.get(`/vps/${deployRes.data.vps_id}`);
        setVps(vpsRes.data);
      }
    } catch (error) {
      if (isInitial) {
        toast.error("Erro ao carregar dados");
        navigate("/dashboard");
      }
    } finally {
      if (isInitial) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    fetchData(true);
    const interval = setInterval(() => fetchData(false), 3000);
    return () => clearInterval(interval);
  }, [id]);

  // Warn user before leaving page during active deployment
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (deployment && ["pending", "cloning", "building", "deploying"].includes(deployment.status)) {
        e.preventDefault();
        e.returnValue = "Deploy em andamento! Tem certeza que deseja sair?";
        return e.returnValue;
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [deployment?.status]);

  useEffect(() => {
    if (showAllLogs) {
      logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [deployment?.logs, containerLogs, showAllLogs]);

  // Organize logs into steps
  const organizeLogsIntoSteps = () => {
    const logs = deployment?.logs || [];
    const stepLogs = {};
    let currentStepIndex = 0;

    deploymentSteps.forEach(step => {
      stepLogs[step.id] = [];
    });

    logs.forEach(log => {
      const message = log.message.toLowerCase();
      let assigned = false;

      // Find which step this log belongs to
      for (let i = deploymentSteps.length - 1; i >= 0; i--) {
        const step = deploymentSteps[i];
        if (step.keywords.some(keyword => message.includes(keyword.toLowerCase()))) {
          stepLogs[step.id].push(log);
          if (i > currentStepIndex) currentStepIndex = i;
          assigned = true;
          break;
        }
      }

      // If not matched, add to the current active step
      if (!assigned && currentStepIndex < deploymentSteps.length) {
        stepLogs[deploymentSteps[currentStepIndex].id].push(log);
      }
    });

    return { stepLogs, currentStepIndex };
  };

  const { stepLogs, currentStepIndex } = deployment ? organizeLogsIntoSteps() : { stepLogs: {}, currentStepIndex: 0 };

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

  const handleCancelDeploy = async () => {
    if (!window.confirm("Cancelar o deploy em andamento? O processo será interrompido.")) return;
    
    setActionLoading("cancel");
    try {
      await api.post(`/deployments/${id}/cancel`);
      toast.success("Deploy cancelado");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao cancelar deploy");
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
      navigate("/dashboard");
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
        description: `Aponte o DNS para ${response.data.vps_host}`
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

  const handleConfigureSSL = async () => {
    if (!deployment?.domain) {
      toast.error("Configure um domínio primeiro");
      return;
    }
    
    setActionLoading("ssl");
    try {
      const response = await api.post(`/deployments/${id}/ssl`);
      toast.success("HTTPS configurado!", {
        description: `Acesse: ${response.data.https_url}`
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Erro ao configurar SSL");
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

  const handleNavigateBack = () => {
    if (isDeploying) {
      if (window.confirm("Deploy em andamento! O processo continuará em segundo plano. Deseja sair mesmo assim?")) {
        navigate("/dashboard");
      }
    } else {
      navigate("/dashboard");
    }
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
          onClick={handleNavigateBack}
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
                
                {/* Cancel button during deployment */}
                {isDeploying && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCancelDeploy}
                    disabled={actionLoading === "cancel"}
                    data-testid="cancel-deploy-btn"
                    className="border-red-500/50 text-red-500 hover:bg-red-500/10"
                  >
                    {actionLoading === "cancel" ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    ) : (
                      <XCircle className="w-4 h-4 mr-2" />
                    )}
                    Cancelar
                  </Button>
                )}
                
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
                {deployment.deploy_type && (
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Tipo</span>
                    <span className={`font-mono text-xs px-2 py-0.5 rounded ${
                      deployment.deploy_type === 'fullstack' ? 'bg-purple-500/20 text-purple-400' :
                      deployment.deploy_type === 'backend_only' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {deployment.deploy_type.toUpperCase()}
                    </span>
                  </div>
                )}
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-500">Porta Frontend</span>
                  <span className="font-mono">{deployment.port}</span>
                </div>
                {deployment.backend_port && (
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-500">Porta Backend</span>
                    <span className="font-mono">{deployment.backend_port}</span>
                  </div>
                )}
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
            
            {/* Admin Credentials Card */}
            {deployment.admin_credentials && (
              <Card className="bg-yellow-500/10 border-yellow-500/30">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-yellow-500 flex items-center gap-2">
                    <Lock className="w-4 h-4" />
                    Credenciais Admin
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between text-sm items-center">
                    <span className="text-zinc-500">Email</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-yellow-400">{deployment.admin_credentials.email}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(deployment.admin_credentials.email)}
                        className="h-6 w-6 p-0"
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex justify-between text-sm items-center">
                    <span className="text-zinc-500">Senha</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-yellow-400">{deployment.admin_credentials.password}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyToClipboard(deployment.admin_credentials.password)}
                        className="h-6 w-6 p-0"
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                  <p className="text-xs text-zinc-500 pt-2 border-t border-yellow-500/20">
                    ⚠️ Altere a senha no primeiro acesso
                  </p>
                </CardContent>
              </Card>
            )}
            
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
                      onClick={handleConfigureSSL}
                      disabled={actionLoading === "ssl"}
                      data-testid="configure-ssl-btn"
                      className="w-full border-green-500/50 text-green-500 hover:bg-green-500/10"
                    >
                      {actionLoading === "ssl" ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <ShieldCheck className="w-4 h-4 mr-2" />
                      )}
                      Ativar HTTPS (SSL)
                    </Button>
                    
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
                    <DialogContent className="bg-zinc-900 border-zinc-800 max-w-lg">
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
                        
                        <div className="bg-zinc-800/50 rounded-lg p-4 space-y-4">
                          <p className="font-medium text-zinc-300 flex items-center gap-2">
                            <span className="bg-green-500/20 text-green-500 px-2 py-0.5 rounded text-xs">Passo a Passo</span>
                            Como configurar o DNS
                          </p>
                          
                          <div className="space-y-3 text-sm">
                            <div className="flex gap-3">
                              <span className="bg-zinc-700 text-zinc-300 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">1</span>
                              <div>
                                <p className="text-zinc-300">Acesse o painel DNS do seu provedor de domínio</p>
                                <p className="text-zinc-500 text-xs">(Cloudflare, GoDaddy, Namecheap, Registro.br, etc)</p>
                              </div>
                            </div>
                            
                            <div className="flex gap-3">
                              <span className="bg-zinc-700 text-zinc-300 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">2</span>
                              <div>
                                <p className="text-zinc-300">Crie um registro do tipo <span className="font-mono bg-zinc-700 px-1 rounded">A</span></p>
                                <div className="mt-1 bg-zinc-900 rounded p-2 font-mono text-xs space-y-1">
                                  <p><span className="text-zinc-500">Tipo:</span> <span className="text-green-500">A</span></p>
                                  <p><span className="text-zinc-500">Nome:</span> <span className="text-green-500">{domain || "app"}</span></p>
                                  <p><span className="text-zinc-500">Valor:</span> <span className="text-green-500">{vps?.host}</span></p>
                                  <p><span className="text-zinc-500">TTL:</span> <span className="text-green-500">Auto</span></p>
                                </div>
                              </div>
                            </div>
                            
                            <div className="flex gap-3">
                              <span className="bg-zinc-700 text-zinc-300 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">3</span>
                              <p className="text-zinc-300">Aguarde propagação DNS (até 24h, geralmente minutos)</p>
                            </div>
                          </div>
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

          {/* Logs - New Emergent-style */}
          <div className="md:col-span-2">
            <Card className="bg-zinc-900/50 border-zinc-800 flex flex-col">
              <CardHeader className="pb-2 flex-shrink-0 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                  <Terminal className="w-4 h-4" />
                  Progresso do Deploy
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAllLogs(!showAllLogs)}
                  className="text-xs text-zinc-500 hover:text-zinc-300"
                >
                  {showAllLogs ? "Ver Resumido" : "Ver Todos os Logs"}
                </Button>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden p-4">
                {!showAllLogs ? (
                  // Emergent-style step view
                  <ScrollArea className="h-[500px] pr-4">
                    <div className="space-y-3">
                      {deploymentSteps.map((step, index) => {
                        const logs = stepLogs[step.id] || [];
                        const isActive = isDeploying && index === currentStepIndex;
                        const isCompleted = deployment.status === "running" 
                          ? true 
                          : deployment.status === "failed" 
                            ? index < currentStepIndex
                            : index < currentStepIndex;
                        const isFailed = deployment.status === "failed" && index === currentStepIndex;
                        
                        return (
                          <LogStep
                            key={step.id}
                            step={step}
                            logs={logs}
                            isActive={isActive}
                            isCompleted={isCompleted}
                            isFailed={isFailed}
                          />
                        );
                      })}
                      
                      {/* Container Logs Section */}
                      {containerLogs.length > 0 && (
                        <div className="border border-zinc-800 rounded-lg overflow-hidden mt-4">
                          <button
                            onClick={() => {}}
                            className="w-full flex items-center justify-between p-3 bg-zinc-900/50 hover:bg-white/5"
                          >
                            <div className="flex items-center gap-3">
                              <Terminal className="w-5 h-5 text-zinc-500" />
                              <span className="font-medium text-zinc-400">Logs do Container</span>
                            </div>
                            <span className="text-xs text-zinc-500">{containerLogs.length} linha(s)</span>
                          </button>
                          <div className="border-t border-zinc-800 bg-zinc-950/50 p-3 max-h-40 overflow-y-auto">
                            <div className="font-mono text-xs space-y-1">
                              {containerLogs.slice(-20).map((line, i) => (
                                <div key={i} className="text-zinc-400 whitespace-pre-wrap break-all">
                                  {line}
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                ) : (
                  // Traditional full log view
                  <ScrollArea className="h-[500px]">
                    <div className="terminal-log rounded p-4 font-mono text-xs space-y-1">
                      {deployment.logs?.map((log, i) => (
                        <div 
                          key={i} 
                          className={`log-entry flex gap-3 ${
                            log.level === "error" ? "text-red-400" : 
                            log.level === "success" ? "text-green-400" : 
                            log.level === "warning" ? "text-yellow-400" : "text-zinc-400"
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
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
