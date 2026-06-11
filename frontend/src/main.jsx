import { StrictMode, lazy, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import { AuthProvider } from './providers/AuthProvider'

const MainLayout = lazy(() => import('./layouts/MainLayout'))
const HomePage = lazy(() => import('./pages/HomePage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const CallbackPage = lazy(() => import('./pages/CallbackPage'))
const ProjectsPage = lazy(() => import('./pages/projects/Page'))
const K8sClustersPage = lazy(() => import('./pages/k8s_clusters/Page'))
const DatabaseSourcesPage = lazy(() => import('./pages/data_sources/DatabaseSourcesPage'))
const PgSqlPage = lazy(() => import('./pages/pgsql/Page'))
const S3StoragePage = lazy(() => import('./pages/s3_storage/Page'))
const LdapConfigPage = lazy(() => import('./pages/ldap_config/Page'))
const SSHKeysPage = lazy(() => import('./pages/ssh_keys/Page'))
const GitReposPage = lazy(() => import('./pages/git_repos/Page'))
const HiveMetastorePage = lazy(() => import('./pages/hive_metastore/Page'))
const TrinoPage = lazy(() => import('./pages/trino/Page'))
const SupersetPage = lazy(() => import('./pages/superset/Page'))
const AirflowPage = lazy(() => import('./pages/airflow/Page'))
const RangerPage = lazy(() => import('./pages/ranger/Page'))
const SolrPage = lazy(() => import('./pages/solr/Page'))
const ZookeeperPage = lazy(() => import('./pages/zookeeper/Page'))

import { ProtectedRoute } from './components/ProtectedRoute'

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'projects',
        element: <ProjectsPage />,
      },
      {
        path: 'k8s_clusters',
        element: <K8sClustersPage />,
      },

      {
        path: 'database-sources',
        element: <DatabaseSourcesPage />,
      },
      {
        path: 's3-storages',
        element: <S3StoragePage />,
      },
      {
        path: 'ldap-configs',
        element: <LdapConfigPage />,
      },
      {
        path: 'ssh-keys',
        element: <SSHKeysPage />,
      },
      {
        path: 'git-repos',
        element: <GitReposPage />,
      },

      {
        path: 'platform/pgsql',
        element: <PgSqlPage />,
      },
      {
        path: 'platform/hive-metastore',
        element: <HiveMetastorePage />,
      },
      {
        path: 'platform/trino',
        element: <TrinoPage />,
      },
      {
        path: 'platform/superset',
        element: <SupersetPage />,
      },
      {
        path: 'platform/airflow',
        element: <AirflowPage />,
      },
      {
        path: 'platform/ranger',
        element: <RangerPage />,
      },
      {
        path: 'platform/solr',
        element: <SolrPage />,
      },
      {
        path: 'platform/zookeeper',
        element: <ZookeeperPage />,
      },
      {
        path: 'platform/:service',
        element: <div className="p-8 text-center text-slate-500 text-base italic">This platform service is not yet implemented in React.</div>,
      }
    ]
  },
  {
    path: '/login',
    element: <LoginPage />
  },
  {
    path: '/callback',
    element: <CallbackPage />
  }
])

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <Suspense fallback={<div className="flex h-screen w-screen items-center justify-center p-8 text-slate-500">Loading...</div>}>
        <RouterProvider router={router} />
      </Suspense>
    </AuthProvider>
  </StrictMode>,
)

