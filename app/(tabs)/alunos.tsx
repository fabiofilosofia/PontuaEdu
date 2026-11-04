import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';

import { Cabecalho } from '@/components/cabecalho';
import { Filtros, formatarDataHora, intervalo, type Periodo } from '@/components/filtros';
import { cores } from '@/constants/estilo';
import type { ContagemAluno } from '@/lib/api';
import { useAuth } from '@/lib/auth';

export default function PorAluno() {
  const { chamar } = useAuth();
  const [periodo, setPeriodo] = useState<Periodo>('mes');
  const [turma, setTurma] = useState('');
  const [alunos, setAlunos] = useState<ContagemAluno[]>([]);
  const [limite, setLimite] = useState(0);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro('');
    try {
      const r = await chamar<{ limite_alerta: number; alunos: ContagemAluno[] }>('/contagem', {
        params: { ...intervalo(periodo), turma },
      });
      setAlunos(r.alunos);
      setLimite(r.limite_alerta);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao carregar.');
    } finally {
      setCarregando(false);
    }
  }, [chamar, periodo, turma]);

  useFocusEffect(
    useCallback(() => {
      carregar();
    }, [carregar]),
  );

  const emAlerta = alunos.filter((a) => a.alerta).length;

  return (
    <View style={styles.container}>
      <Cabecalho
        titulo="Atrasos por aluno"
        subtitulo={emAlerta ? `🔔 ${emAlerta} aluno${emAlerta === 1 ? '' : 's'} com ${limite}+ atrasos` : 'Quem mais chega atrasado'}
      />
      <Filtros periodo={periodo} onPeriodo={setPeriodo} turma={turma} onTurma={setTurma} />
      {erro ? <Text style={styles.erro}>{erro}</Text> : null}

      <FlatList
        data={alunos}
        keyExtractor={(item) => String(item.aluno_id)}
        contentContainerStyle={styles.lista}
        refreshControl={<RefreshControl refreshing={carregando} onRefresh={carregar} />}
        ListEmptyComponent={!carregando ? <Text style={styles.vazio}>Nenhum atraso neste período. 🎉</Text> : null}
        renderItem={({ item }) => (
          <View style={[styles.item, item.alerta && styles.itemAlerta]}>
            <View style={{ flex: 1 }}>
              <Text style={styles.nome}>{item.aluno}</Text>
              <Text style={styles.detalhe}>
                {item.turma} · último: {formatarDataHora(item.ultimo)}
              </Text>
            </View>
            <View style={[styles.total, item.alerta && styles.totalAlerta]}>
              <Text style={[styles.totalNumero, item.alerta && { color: '#FFFFFF' }]}>{item.total}</Text>
            </View>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: cores.fundo },
  lista: { paddingHorizontal: 16, paddingBottom: 24, gap: 10 },
  erro: { color: cores.erro, marginHorizontal: 16, marginBottom: 8 },
  vazio: { textAlign: 'center', color: cores.textoSuave, marginTop: 40 },
  item: {
    backgroundColor: cores.cartao,
    borderRadius: 12,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    elevation: 1,
  },
  itemAlerta: { backgroundColor: cores.avisoFundo },
  nome: { fontSize: 15, fontWeight: '700', color: cores.texto },
  detalhe: { fontSize: 13, color: cores.rotulo, marginTop: 2 },
  total: {
    minWidth: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E2E8F0',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  totalAlerta: { backgroundColor: cores.aviso },
  totalNumero: { fontSize: 16, fontWeight: '800', color: cores.texto },
});
