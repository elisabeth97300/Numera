import { BrowserRouter, Routes, Route } from "react-router-dom";
import type { ReactNode } from "react";
import { AuthProvider } from "./lib/auth";
import { ClientProvider } from "./lib/client";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Assistant } from "./pages/Assistant";
import { Import } from "./pages/Import";
import { Validation } from "./pages/Validation";
import { Ecritures } from "./pages/Ecritures";
import { Rapprochement } from "./pages/Rapprochement";
import { Bilan } from "./pages/Bilan";
import { Analyse } from "./pages/Analyse";

function ProtectedLayout({ children }: { children: ReactNode }) {
  return (
    <ClientProvider>
      <Layout>{children}</Layout>
    </ClientProvider>
  );
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <ProtectedLayout>
                <Import />
              </ProtectedLayout>
            }
          />
          <Route
            path="/assistant"
            element={
              <ProtectedLayout>
                <Assistant />
              </ProtectedLayout>
            }
          />
          <Route
            path="/import"
            element={
              <ProtectedLayout>
                <Import />
              </ProtectedLayout>
            }
          />
          <Route
            path="/validation"
            element={
              <ProtectedLayout>
                <Validation />
              </ProtectedLayout>
            }
          />
          <Route
            path="/ecritures"
            element={
              <ProtectedLayout>
                <Ecritures />
              </ProtectedLayout>
            }
          />
          <Route
            path="/rapprochement"
            element={
              <ProtectedLayout>
                <Rapprochement />
              </ProtectedLayout>
            }
          />
          <Route
            path="/bilan"
            element={
              <ProtectedLayout>
                <Bilan />
              </ProtectedLayout>
            }
          />
          <Route
            path="/analyse"
            element={
              <ProtectedLayout>
                <Analyse />
              </ProtectedLayout>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
