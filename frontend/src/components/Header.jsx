import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../App";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Terminal, Server, LogOut, User, ChevronDown, Shield } from "lucide-react";

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
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
                <DropdownMenuItem className="text-zinc-400 focus:bg-zinc-800 focus:text-white">
                  <User className="w-4 h-4 mr-2" />
                  {user?.email}
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-zinc-800" />
                <DropdownMenuItem 
                  onClick={handleLogout}
                  className="text-red-400 focus:bg-red-500/10 focus:text-red-400"
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
  );
}
