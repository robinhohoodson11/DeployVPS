import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, useAuth } from "../App";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { toast } from "sonner";
import { 
  Plus, Server, GitBranch, RefreshCw, Terminal, 
  LogOut, ExternalLink, Clock, Globe, Trash2
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

export default function Dashboard() {
  const [deployments, setDeployments] = useState([]);
  const [vpsCount, setVpsCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchData = async () => {
    try {
      const [deploymentsRes, vpsRes] = await Promise.all([
        api.get("/deployments"),
        api.get("/vps")
      ]);
      setDeployments(deploymentsRes.data);
      setVpsCount(vpsRes.data.length);
    } catch (error) {
      toast.error("Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (id, e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm("Tem certeza que deseja deletar este deployment?")) return;
    
    try {
      await api.delete(`/deployments/${id}`);
      toast.success("Deployment deletado");
      fetchData();
    } catch (error) {
      toast.error("Erro ao deletar deployment");
    }
  };

  const runningCount = deployments.filter(d => d.status === "running").length;
  const pendingCount = deployments.filter(d => ["pending", "cloning", "building", "deploying"].includes(d.status)).length;

  return (
    <div className="min-h-screen bg-[#09090b]">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-zinc-900/50 border-zinc-800 card-hover">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500 uppercase tracking-wider">Total Deploys</p>
                  <p className="text-3xl font-bold font-mono mt-1">{deployments.length}</p>
                </div>
                <div className="w-12 h-12 rounded bg-zinc-800 flex items-center justify-center">
                  <GitBranch className="w-6 h-6 text-zinc-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-zinc-900/50 border-zinc-800 card-hover">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500 uppercase tracking-wider">Rodando</p>
                  <p className="text-3xl font-bold font-mono mt-1 text-green-500">{runningCount}</p>
                </div>
                <div className="w-12 h-12 rounded bg-green-500/10 flex items-center justify-center">
                  <div className="w-3 h-3 rounded-full bg-green-500 glow-dot" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-zinc-900/50 border-zinc-800 card-hover">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500 uppercase tracking-wider">Em Progresso</p>
                  <p className="text-3xl font-bold font-mono mt-1 text-yellow-500">{pendingCount}</p>
                </div>
                <div className="w-12 h-12 rounded bg-yellow-500/10 flex items-center justify-center">
                  <RefreshCw className={`w-6 h-6 text-yellow-500 ${pendingCount > 0 ? 'animate-spin' : ''}`} />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-zinc-900/50 border-zinc-800 card-hover">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500 uppercase tracking-wider">Servidores VPS</p>
                  <p className="text-3xl font-bold font-mono mt-1">{vpsCount}</p>
                </div>
                <div className="w-12 h-12 rounded bg-zinc-800 flex items-center justify-center">
                  <Server className="w-6 h-6 text-zinc-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold tracking-tight">Deployments</h2>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={fetchData}
              data-testid="refresh-btn"
              className="border-zinc-800 hover:bg-zinc-800 hover:border-zinc-700"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Atualizar
            </Button>
            <Button
              onClick={() => navigate("/deploy/new")}
              data-testid="new-deploy-btn"
              className="bg-green-500 hover:bg-green-600 text-black font-semibold btn-glow"
            >
              <Plus className="w-4 h-4 mr-2" />
              Novo Deploy
            </Button>
          </div>
        </div>

        {/* Deployments List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : deployments.length === 0 ? (
          <Card className="bg-zinc-900/50 border-zinc-800 border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center mb-4">
                <Terminal className="w-8 h-8 text-zinc-500" />
              </div>
              <h3 className="text-lg font-medium mb-2">Nenhum deployment ainda</h3>
              <p className="text-zinc-500 text-center mb-6 max-w-md">
                Comece criando seu primeiro deployment. Você precisará primeiro adicionar um servidor VPS.
              </p>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => navigate("/vps")}
                  className="border-zinc-800 hover:bg-zinc-800"
                >
                  <Server className="w-4 h-4 mr-2" />
                  Adicionar VPS
                </Button>
                <Button
                  onClick={() => navigate("/deploy/new")}
                  className="bg-green-500 hover:bg-green-600 text-black font-semibold"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Novo Deploy
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {deployments.map((deployment) => {
              const status = statusConfig[deployment.status] || statusConfig.pending;
              return (
                <Link
                  key={deployment.id}
                  to={`/deploy/${deployment.id}`}
                  data-testid={`deployment-card-${deployment.id}`}
                >
                  <Card className="bg-zinc-900/50 border-zinc-800 card-hover cursor-pointer">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`w-3 h-3 rounded-full ${status.color} glow-dot ${
                            ["pending", "cloning", "building", "deploying"].includes(deployment.status) 
                              ? "animate-pulse-glow" : ""
                          }`} />
                          <div>
                            <h3 className="font-semibold text-lg">{deployment.project_name}</h3>
                            <p className="text-sm text-zinc-500 font-mono">{deployment.repo_url}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <Badge variant="outline" className={`${status.textColor} border-current`}>
                              {status.label}
                            </Badge>
                            <p className="text-xs text-zinc-500 mt-1 font-mono">
                              Porta: {deployment.port}
                            </p>
                          </div>
                          {deployment.domain && (
                            <div className="flex items-center gap-1 text-green-500">
                              <Globe className="w-4 h-4" />
                              <span className="text-sm font-mono">{deployment.domain}</span>
                            </div>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => handleDelete(deployment.id, e)}
                            data-testid={`delete-deployment-${deployment.id}`}
                            className="hover:bg-red-500/10 hover:text-red-500"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                          <ExternalLink className="w-4 h-4 text-zinc-500" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
