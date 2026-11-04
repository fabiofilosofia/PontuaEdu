import * as SecureStore from 'expo-secure-store';
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import { Platform } from 'react-native';

import { api, ApiError, type Sessao } from './api';

const CHAVE = 'pontuaedu.sessao';

// SecureStore não existe no navegador; lá usamos o localStorage.
const armazenamento = {
  async ler() {
    return Platform.OS === 'web' ? localStorage.getItem(CHAVE) : SecureStore.getItemAsync(CHAVE);
  },
  async salvar(valor: string) {
    if (Platform.OS === 'web') localStorage.setItem(CHAVE, valor);
    else await SecureStore.setItemAsync(CHAVE, valor);
  },
  async apagar() {
    if (Platform.OS === 'web') localStorage.removeItem(CHAVE);
    else await SecureStore.deleteItemAsync(CHAVE);
  },
};

interface AuthContexto {
  sessao: Sessao | null;
  carregando: boolean;
  entrar: (usuario: string, senha: string) => Promise<void>;
  sair: () => Promise<void>;
  /** Faz a chamada com o token da sessão e desconecta se ele tiver expirado. */
  chamar: <T>(caminho: string, opcoes?: Omit<Parameters<typeof api>[1], 'token'>) => Promise<T>;
}

const Contexto = createContext<AuthContexto | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [sessao, setSessao] = useState<Sessao | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    armazenamento
      .ler()
      .then((salva) => salva && setSessao(JSON.parse(salva)))
      .catch(() => {})
      .finally(() => setCarregando(false));
  }, []);

  const entrar = useCallback(async (usuario: string, senha: string) => {
    const nova = await api<Sessao>('/login', { metodo: 'POST', corpo: { usuario, senha } });
    await armazenamento.salvar(JSON.stringify(nova));
    setSessao(nova);
  }, []);

  const sair = useCallback(async () => {
    if (sessao) api('/logout', { metodo: 'POST', token: sessao.token }).catch(() => {});
    await armazenamento.apagar();
    setSessao(null);
  }, [sessao]);

  const chamar = useCallback(
    async <T,>(caminho: string, opcoes: Omit<Parameters<typeof api>[1], 'token'> = {}) => {
      try {
        return await api<T>(caminho, { ...opcoes, token: sessao?.token });
      } catch (erro) {
        if (erro instanceof ApiError && erro.status === 401) {
          await armazenamento.apagar();
          setSessao(null);
        }
        throw erro;
      }
    },
    [sessao],
  );

  return <Contexto.Provider value={{ sessao, carregando, entrar, sair, chamar }}>{children}</Contexto.Provider>;
}

export function useAuth() {
  const contexto = useContext(Contexto);
  if (!contexto) throw new Error('useAuth precisa estar dentro de <AuthProvider>');
  return contexto;
}
