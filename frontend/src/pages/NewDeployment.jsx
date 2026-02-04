import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../App";
import { useLanguage } from "../i18n/LanguageContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Checkbox } from "../components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { toast } from "sonner";
import { ArrowLeft, GitBranch, Server, Rocket, Loader2, Key, AlertCircle, Database, RefreshCw } from "lucide-react";
import Header from "../components/Header";

export default function NewDeployment() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [vpsList, setVpsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  
  const [form, setForm] = useState({
    vps_id: "",
    repo_url: "",
    branch: "main",
    project_name: "",
    base_port: 3000,
    port: 3000,
    backend_port: 4000,
    mongodb_port: 27017,
    github_token: "",
    env_vars: "",
    create_mongodb: false,
    create_admin: false,
    admin_email: "admin@admin.com",
    admin_password: "Admin@123",
  });
  
  const [suggestedPorts, setSuggestedPorts] = useState(null);
  const [loadingPorts, setLoadingPorts] = useState(false);

  useEffect(() => {
    const fetchVPS = async () => {
      try {
        const response = await api.get("/vps");
        setVpsList(response.data);
        if (response.data.length > 0) {
          setForm(f => ({ ...f, vps_id: response.data[0].id }));
        }
      } catch (error) {
        toast.error("Erro ao carregar servidores");
      } finally {
        setLoading(false);
      }
    };
    fetchVPS();
  }, []);

  // Fetch available ports when VPS is selected and MongoDB is enabled
  const fetchAvailablePorts = async (vpsId, basePort) => {
    if (!vpsId) return;
    
    setLoadingPorts(true);
    try {
      const response = await api.get(`/vps/${vpsId}/available-ports?base_port=${basePort}`);
      const suggested = response.data.suggested;
      setSuggestedPorts(suggested);
      setForm(f => ({
        ...f,
        port: suggested.frontend_port,
        backend_port: suggested.backend_port,
        mongodb_port: suggested.mongodb_port
      }));
    } catch (error) {
      console.error("Erro ao verificar portas:", error);
      // Use defaults if check fails
      setForm(f => ({
        ...f,
        port: basePort,
        backend_port: basePort + 1000,
        mongodb_port: 27017
      }));
    } finally {
      setLoadingPorts(false);
    }
  };

  const parseEnvVars = (text) => {
    if (!text.trim()) return null;
    const vars = {};
    text.split("\n").forEach(line => {
      const [key, ...valueParts] = line.split("=");
      if (key && valueParts.length > 0) {
        vars[key.trim()] = valueParts.join("=").trim();
      }
    });
    return Object.keys(vars).length > 0 ? vars : null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!form.vps_id) {
      toast.error("Selecione um servidor VPS");
      return;
    }
    
    if (!form.repo_url.includes("github.com")) {
      toast.error("URL do repositório deve ser do GitHub");
      return;
    }
    
    setSubmitting(true);
    
    try {
      const payload = {
        vps_id: form.vps_id,
        repo_url: form.repo_url,
        branch: form.branch,
        project_name: form.project_name.toLowerCase().replace(/[^a-z0-9-]/g, "-"),
        port: form.port,
        backend_port: form.create_mongodb ? form.backend_port : null,
        github_token: form.github_token || null,
        env_vars: parseEnvVars(form.env_vars),
        create_mongodb: form.create_mongodb,
        mongodb_port: form.mongodb_port,
        create_admin: form.create_admin,
        admin_email: form.admin_email,
        admin_password: form.admin_password,
      };
      
      const response = await api.post("/deployments", payload);
      toast.success(t('common.success'));
      navigate(`/deploy/${response.data.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const extractProjectName = (url) => {
    const match = url.match(/github\.com\/[^\/]+\/([^\/\.]+)/);
    return match ? match[1] : "";
  };

  return (
    <div className="min-h-screen bg-[#09090b]">
      <Header />
      
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="mb-6 text-zinc-400 hover:text-white"
          data-testid="back-btn"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          {t('newDeploy.back')}
        </Button>
        
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Rocket className="w-5 h-5 text-green-500" />
              {t('newDeploy.title')}
            </CardTitle>
            <CardDescription className="text-zinc-500">
              {t('newDeploy.subtitle')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : vpsList.length === 0 ? (
              <div className="text-center py-12">
                <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">{t('newDeploy.noVps.title')}</h3>
                <p className="text-zinc-500 mb-6">
                  {t('newDeploy.noVps.subtitle')}
                </p>
                <Button
                  onClick={() => navigate("/vps")}
                  className="bg-green-500 hover:bg-green-600 text-black font-semibold"
                >
                  <Server className="w-4 h-4 mr-2" />
                  {t('newDeploy.noVps.addVps')}
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label className="text-zinc-300 flex items-center gap-2">
                    <Server className="w-4 h-4" />
                    {t('newDeploy.form.vps')}
                  </Label>
                  <Select
                    value={form.vps_id}
                    onValueChange={(value) => setForm({ ...form, vps_id: value })}
                  >
                    <SelectTrigger className="bg-zinc-800/50 border-zinc-700" data-testid="vps-select">
                      <SelectValue placeholder={t('newDeploy.form.selectVps')} />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      {vpsList.map((vps) => (
                        <SelectItem key={vps.id} value={vps.id}>
                          <div className="flex items-center gap-2">
                            <span>{vps.name}</span>
                            <span className="text-zinc-500 font-mono text-xs">({vps.host})</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-zinc-300 flex items-center gap-2">
                    <GitBranch className="w-4 h-4" />
                    {t('newDeploy.form.repoUrl')}
                  </Label>
                  <Input
                    placeholder="https://github.com/usuario/projeto"
                    value={form.repo_url}
                    onChange={(e) => {
                      setForm({ 
                        ...form, 
                        repo_url: e.target.value,
                        project_name: form.project_name || extractProjectName(e.target.value)
                      });
                    }}
                    required
                    data-testid="repo-url-input"
                    className="bg-zinc-800/50 border-zinc-700 font-mono"
                  />
                  <p className="text-xs text-zinc-500">
                    {t('newDeploy.form.githubTokenHelp')}
                  </p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-zinc-300">{t('newDeploy.form.branch')}</Label>
                    <Input
                      placeholder="main"
                      value={form.branch}
                      onChange={(e) => setForm({ ...form, branch: e.target.value })}
                      required
                      data-testid="branch-input"
                      className="bg-zinc-800/50 border-zinc-700 font-mono"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-zinc-300">{t('newDeploy.form.projectName')}</Label>
                    <Input
                      placeholder="meu-projeto"
                      value={form.project_name}
                      onChange={(e) => setForm({ ...form, project_name: e.target.value })}
                      required
                      data-testid="project-name-input"
                      className="bg-zinc-800/50 border-zinc-700 font-mono"
                    />
                  </div>
                </div>
                
                {/* Port - Only show for non-fullstack deploys */}
                {!form.create_mongodb && (
                  <div className="space-y-2">
                    <Label className="text-zinc-300">{t('newDeploy.form.port')}</Label>
                    <Input
                      type="number"
                      placeholder="3000"
                      value={form.port}
                      onChange={(e) => setForm({ ...form, port: parseInt(e.target.value) })}
                      required
                      data-testid="port-input"
                      className="bg-zinc-800/50 border-zinc-700 font-mono w-32"
                    />
                    <p className="text-xs text-zinc-500">
                      {t('newDeploy.form.portHelp')}
                    </p>
                  </div>
                )}
                
                <div className="space-y-2">
                  <Label className="text-zinc-300 flex items-center gap-2">
                    <Key className="w-4 h-4" />
                    {t('newDeploy.form.githubToken')}
                  </Label>
                  <Input
                    type="password"
                    placeholder="ghp_xxxxxxxxxxxx"
                    value={form.github_token}
                    onChange={(e) => setForm({ ...form, github_token: e.target.value })}
                    data-testid="github-token-input"
                    className="bg-zinc-800/50 border-zinc-700 font-mono"
                  />
                  <p className="text-xs text-zinc-500">
                    {t('newDeploy.form.githubTokenHelp')}
                  </p>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-zinc-300">{t('newDeploy.form.envVars')}</Label>
                  <Textarea
                    placeholder={"DATABASE_URL=postgres://...\nAPI_KEY=xxxxx"}
                    value={form.env_vars}
                    onChange={(e) => setForm({ ...form, env_vars: e.target.value })}
                    rows={4}
                    data-testid="env-vars-input"
                    className="bg-zinc-800/50 border-zinc-700 font-mono text-sm"
                  />
                  <p className="text-xs text-zinc-500">
                    {t('newDeploy.form.envVarsHelp')}
                  </p>
                </div>
                
                {/* MongoDB Option */}
                <div className="border border-zinc-800 rounded-lg p-4 space-y-4">
                  <div className="flex items-center space-x-3">
                    <Checkbox
                      id="create_mongodb"
                      checked={form.create_mongodb}
                      onCheckedChange={(checked) => {
                        setForm({ ...form, create_mongodb: checked });
                        if (checked && form.vps_id) {
                          fetchAvailablePorts(form.vps_id, form.base_port);
                        }
                      }}
                      data-testid="create-mongodb-checkbox"
                      className="border-zinc-600 data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500"
                    />
                    <div className="flex items-center gap-2">
                      <Database className="w-4 h-4 text-green-500" />
                      <Label htmlFor="create_mongodb" className="text-zinc-300 cursor-pointer">
                        {t('newDeploy.fullstack.title')}
                      </Label>
                    </div>
                  </div>
                  
                  {form.create_mongodb && (
                    <div className="ml-6 space-y-4 border-l-2 border-green-500/30 pl-4">
                      <div className="space-y-2">
                        <Label className="text-zinc-400 text-sm">{t('newDeploy.form.basePort')}</Label>
                        <div className="flex items-center gap-3">
                          <Input
                            type="number"
                            placeholder="3000"
                            value={form.base_port}
                            onChange={(e) => setForm({ ...form, base_port: parseInt(e.target.value) })}
                            data-testid="base-port-input"
                            className="bg-zinc-800/50 border-zinc-700 font-mono w-28"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => fetchAvailablePorts(form.vps_id, form.base_port)}
                            disabled={loadingPorts || !form.vps_id}
                            className="border-zinc-700"
                          >
                            {loadingPorts ? (
                              <Loader2 className="w-4 h-4 animate-spin mr-2" />
                            ) : (
                              <RefreshCw className="w-4 h-4 mr-2" />
                            )}
                            {t('newDeploy.form.checkPorts')}
                          </Button>
                        </div>
                        <p className="text-xs text-zinc-500">
                          {t('newDeploy.form.basePortHelp')}
                        </p>
                      </div>
                      
                      {/* Suggested Ports Display */}
                      <div className="bg-zinc-800/50 rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-zinc-400 font-medium">{t('newDeploy.form.selectedPorts')}:</span>
                          {loadingPorts && <Loader2 className="w-4 h-4 animate-spin text-green-500" />}
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4">
                          <div className="bg-zinc-900 rounded p-3 text-center">
                            <p className="text-xs text-zinc-500 mb-1">{t('newDeploy.form.frontend')}</p>
                            <p className="text-lg font-mono text-green-500">{form.port}</p>
                          </div>
                          <div className="bg-zinc-900 rounded p-3 text-center">
                            <p className="text-xs text-zinc-500 mb-1">{t('newDeploy.form.backend')}</p>
                            <p className="text-lg font-mono text-blue-500">{form.backend_port}</p>
                          </div>
                          <div className="bg-zinc-900 rounded p-3 text-center">
                            <p className="text-xs text-zinc-500 mb-1">{t('newDeploy.form.mongodb')}</p>
                            <p className="text-lg font-mono text-yellow-500">{form.mongodb_port}</p>
                          </div>
                        </div>
                        
                        {suggestedPorts && (
                          <p className="text-xs text-green-500 text-center">
                            ✓ {t('newDeploy.form.portsVerified')}
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Admin User Option */}
                {form.create_mongodb && (
                  <div className="border border-yellow-500/30 rounded-lg p-4 space-y-4 bg-yellow-500/5">
                    <div className="flex items-center space-x-3">
                      <Checkbox
                        id="create_admin"
                        checked={form.create_admin}
                        onCheckedChange={(checked) => setForm({ ...form, create_admin: checked })}
                        data-testid="create-admin-checkbox"
                        className="border-yellow-500/50 data-[state=checked]:bg-yellow-500 data-[state=checked]:border-yellow-500"
                      />
                      <div className="flex items-center gap-2">
                        <Key className="w-4 h-4 text-yellow-500" />
                        <Label htmlFor="create_admin" className="text-zinc-300 cursor-pointer">
                          {t('newDeploy.fullstack.createAdmin')}
                        </Label>
                      </div>
                    </div>
                    
                    {form.create_admin && (
                      <div className="ml-6 space-y-4">
                        <p className="text-xs text-zinc-500 mb-3">
                          {t('newDeploy.fullstack.adminHelp')}
                        </p>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label className="text-zinc-400 text-sm">{t('newDeploy.fullstack.adminEmail')}</Label>
                            <Input
                              type="email"
                              placeholder="admin@admin.com"
                              value={form.admin_email}
                              onChange={(e) => setForm({ ...form, admin_email: e.target.value })}
                              data-testid="admin-email-input"
                              className="bg-zinc-800/50 border-zinc-700 font-mono"
                            />
                          </div>
                          <div className="space-y-2">
                            <Label className="text-zinc-400 text-sm">Senha do Admin</Label>
                            <Input
                              type="text"
                              placeholder="Admin@123"
                              value={form.admin_password}
                              onChange={(e) => setForm({ ...form, admin_password: e.target.value })}
                              data-testid="admin-password-input"
                              className="bg-zinc-800/50 border-zinc-700 font-mono"
                            />
                          </div>
                        </div>
                        
                        <div className="bg-zinc-800/50 rounded p-3 text-xs">
                          <p className="text-yellow-500 font-medium mb-1">⚠️ Importante:</p>
                          <p className="text-zinc-400">
                            As credenciais serão exibidas nos logs após o deploy. 
                            Recomenda-se alterar a senha no primeiro acesso.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="flex justify-end gap-3 pt-4 border-t border-zinc-800">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => navigate("/")}
                    className="border-zinc-700"
                  >
                    Cancelar
                  </Button>
                  <Button
                    type="submit"
                    disabled={submitting}
                    data-testid="deploy-submit-btn"
                    className="bg-green-500 hover:bg-green-600 text-black font-semibold btn-glow"
                  >
                    {submitting ? (
                      <span className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Iniciando...
                      </span>
                    ) : (
                      <>
                        <Rocket className="w-4 h-4 mr-2" />
                        Iniciar Deploy
                      </>
                    )}
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
