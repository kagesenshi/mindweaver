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
const DataSourcesPage = lazy(() => import('./pages/data_sources/Page'))
const PgSqlPage = lazy(() => import('./pages/pgsql/Page'))
const S3StoragePage = lazy(() => import('./pages/s3_storage/Page'))

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
        path: 'data-sources',
        element: <DataSourcesPage />,
      },
      {
        path: 's3-storages',
        element: <S3StoragePage />,
      },

      {
        path: 'platform/pgsql',
        element: <PgSqlPage />,
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

const Loading = () => <div className="flex h-screen w-screen items-center justify-center p-8 text-slate-500">Loading...</div>;

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <Suspense fallback={<Loading />}>
        <RouterProvider router={router} />
      </Suspense>
    </AuthProvider>
  </StrictMode>,
)

