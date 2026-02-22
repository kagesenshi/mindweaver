import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './index.css'
import MainLayout from './layouts/MainLayout'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import CallbackPage from './pages/CallbackPage'
import ProjectsPage from './pages/ProjectsPage'
import DataSourcesPage from './pages/DataSourcesPage'
import PgSqlPage from './pages/pgsql/Page'
import S3StoragePage from './pages/s3_storage/Page'
import { AuthProvider } from './providers/AuthProvider'

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

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </StrictMode>,
)

