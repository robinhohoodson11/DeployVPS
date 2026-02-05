import { useState, useEffect } from "react";
import { api } from "../App";
import { useLanguage } from "../i18n/LanguageContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { toast } from "sonner";
import { 
  Eye, Users, TrendingUp, Globe, FileText, 
  BarChart3, Activity, MapPin, Calendar
} from "lucide-react";
import Header from "../components/Header";

export default function AdminAnalytics() {
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await api.get("/admin/analytics");
      setAnalytics(response.data);
    } catch (error) {
      toast.error(t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-white">
        <Header />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-green-500" />
            {t('admin.analytics')}
          </h1>
          <p className="text-zinc-500 mt-1">{t('admin.recentActivity')}</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {/* Page Views */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <Eye className="w-6 h-6 text-blue-500" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">{t('admin.pageViews')}</p>
                  <p className="text-3xl font-bold font-mono">
                    {formatNumber(analytics?.page_views?.month || 0)}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {t('admin.todayViews')}: {analytics?.page_views?.today || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Unique Visitors */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center">
                  <Users className="w-6 h-6 text-green-500" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">{t('admin.uniqueVisitors')}</p>
                  <p className="text-3xl font-bold font-mono">
                    {formatNumber(analytics?.unique_visitors?.month || 0)}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {t('admin.weekViews')}: {analytics?.unique_visitors?.week || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Conversions */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-purple-500" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">{t('admin.conversions')}</p>
                  <p className="text-3xl font-bold font-mono">
                    {analytics?.conversions?.total || 0}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {t('admin.monthViews')}: {analytics?.conversions?.month || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Conversion Rate */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                  <Activity className="w-6 h-6 text-yellow-500" />
                </div>
                <div>
                  <p className="text-sm text-zinc-500">{t('admin.conversionRate')}</p>
                  <p className="text-3xl font-bold font-mono text-yellow-500">
                    {analytics?.conversions?.rate || 0}%
                  </p>
                  <p className="text-xs text-zinc-500">
                    {t('admin.registrations')}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts and Lists */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Pages */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                {t('admin.topPages')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {analytics?.top_pages?.length > 0 ? (
                <div className="space-y-3">
                  {analytics.top_pages.map((page, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-zinc-500 w-5">{index + 1}.</span>
                        <span className="font-mono text-sm truncate max-w-[200px]">
                          {page.page || '/'}
                        </span>
                      </div>
                      <span className="font-mono text-green-500">{page.views}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-zinc-500">
                  <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>{t('admin.noUsers')}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Top Countries */}
          <Card className="bg-zinc-900/50 border-zinc-800">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                <Globe className="w-4 h-4" />
                {t('admin.topCountries')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {analytics?.top_countries?.length > 0 ? (
                <div className="space-y-3">
                  {analytics.top_countries.map((country, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-zinc-500 w-5">{index + 1}.</span>
                        <span className="flex items-center gap-2">
                          <MapPin className="w-4 h-4 text-zinc-500" />
                          {country.country || 'Unknown'}
                        </span>
                      </div>
                      <span className="font-mono text-blue-500">{country.views}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-zinc-500">
                  <Globe className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>{t('admin.noUsers')}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Daily Views Chart */}
          <Card className="bg-zinc-900/50 border-zinc-800 lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                {t('admin.monthViews')} (30 {t('common.days') || 'dias'})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {analytics?.daily_views?.length > 0 ? (
                <div className="h-40 flex items-end gap-1">
                  {analytics.daily_views.map((day, index) => {
                    const maxViews = Math.max(...analytics.daily_views.map(d => d.views));
                    const height = maxViews > 0 ? (day.views / maxViews) * 100 : 0;
                    return (
                      <div key={index} className="flex-1 flex flex-col items-center group">
                        <div
                          className="w-full bg-green-500/50 hover:bg-green-500 transition-colors rounded-t"
                          style={{ height: `${Math.max(height, 2)}%` }}
                          title={`${day.date}: ${day.views} views`}
                        />
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8 text-zinc-500">
                  <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>{t('admin.noUsers')}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card className="bg-zinc-900/50 border-zinc-800 lg:col-span-2">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-zinc-400 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                {t('admin.recentActivity')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {analytics?.recent_activity?.length > 0 ? (
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {analytics.recent_activity.map((activity, index) => (
                    <div 
                      key={index} 
                      className="flex items-center justify-between text-sm py-2 border-b border-zinc-800 last:border-0"
                    >
                      <div className="flex items-center gap-3">
                        <span className={`w-2 h-2 rounded-full ${
                          activity.type === 'registration' ? 'bg-green-500' :
                          activity.type === 'login' ? 'bg-blue-500' : 'bg-zinc-500'
                        }`} />
                        <span className="text-zinc-300">
                          {activity.type === 'page_view' ? 'View' :
                           activity.type === 'registration' ? 'Register' : 
                           activity.type === 'login' ? 'Login' : activity.type}
                        </span>
                        <span className="text-zinc-500 font-mono text-xs truncate max-w-[150px]">
                          {activity.page}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-zinc-500 text-xs">
                        {activity.country && (
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" />
                            {activity.country}
                          </span>
                        )}
                        <span>
                          {new Date(activity.timestamp).toLocaleString('pt-BR', {
                            day: '2-digit',
                            month: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-zinc-500">
                  <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>{t('admin.noUsers')}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
