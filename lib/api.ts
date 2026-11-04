// Endereço do servidor: defina EXPO_PUBLIC_API_URL no arquivo .env (ex.: http://192.168.0.12:8000)
export const BASE_URL = (process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

export interface Aluno {
  id: number;
  matricula: string;
  nome: string;
  turma: string;
  responsavel: string;
  telefone: string;
}

export type StatusWhatsapp = 'enviado' | 'falhou' | 'nao_configurado';

export interface Atraso {
  id: number;
  data_hora: string;
  aluno_id: number;
  aluno: string;
  turma: string;
  responsavel: string;
  telefone: string;
  observacao: string;
  whatsapp_status: StatusWhatsapp;
  whatsapp_detalhe: string;
  registrado_por: string;
}

export interface ResultadoRegistro {
  id: number;
  mensagem: string;
  whatsapp_status: StatusWhatsapp;
  whatsapp_detalhe: string;
  total_atrasos: number;
  janela_dias: number;
  alerta: boolean;
}

export interface ContagemAluno {
  aluno_id: number;
  aluno: string;
  turma: string;
  total: number;
  ultimo: string;
  alerta: boolean;
}

export interface Sessao {
  token: string;
  nome: string;
  admin: boolean;
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

type Params = Record<string, string | number | undefined>;

export function montarUrl(caminho: string, params: Params = {}) {
  const query = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&');
  return `${BASE_URL}${caminho}${query ? `?${query}` : ''}`;
}

export async function api<T>(
  caminho: string,
  { token, metodo = 'GET', corpo, params }: { token?: string | null; metodo?: string; corpo?: unknown; params?: Params } = {},
): Promise<T> {
  let resposta: Response;
  try {
    resposta = await fetch(montarUrl(caminho, params), {
      method: metodo,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    });
  } catch {
    throw new ApiError(`Não foi possível conectar ao servidor (${BASE_URL}). Verifique o Wi-Fi.`, 0);
  }

  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    const detalhe = typeof dados.detail === 'string' ? dados.detail : 'Ocorreu um erro no servidor.';
    throw new ApiError(detalhe, resposta.status);
  }
  return dados as T;
}
