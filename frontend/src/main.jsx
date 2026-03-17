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
const WebSourcesPage = lazy(() => import('./pages/data_sources/WebSourcesPage'))
const ApiSourcesPage = lazy(() => import('./pages/data_sources/ApiSourcesPage'))
const StreamingSourcesPage = lazy(() => import('./pages/data_sources/StreamingSourcesPage'))
const PgSqlPage = lazy(() => import('./pages/pgsql/Page'))
const S3StoragePage = lazy(() => import('./pages/s3_storage/Page'))
const LdapConfigPage = lazy(() => import('./pages/ldap_config/Page'))
const HiveMetastorePage = lazy(() => import('./pages/hive_metastore/Page'))
const TrinoPage = lazy(() => import('./pages/trino/Page'))
const SupersetPage = lazy(() => import('./pages/superset/Page'))

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
        path: 'web-sources',
        element: <WebSourcesPage />,
      },
      {
        path: 'api-sources',
        element: <ApiSourcesPage />,
      },
      {
        path: 'streaming-sources',
        element: <StreamingSourcesPage />,
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

