import { useFocusEffect } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, Alert, FlatList, Linking, RefreshControl, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { Cabecalho } from '@/components/cabecalho';
import { Rodape } from '@/components/rodape';
import { Filtros, formatarDataHora, intervalo, type Periodo } from '@/components/filtros';
import { cores } from '@/constants/estilo';
import { montarUrl, type Atraso, type StatusWhatsapp } from '@/lib/api';
import { useAuth } from '@/lib/auth';

const SELO: Record<StatusWhatsapp, { texto: string; cor: string; fundo: string }> = {
  enviado: { texto: 'WhatsApp enviado', cor: cores.sucesso, fundo: '#DCFCE7' },
  falhou: { texto: 'Falhou — tocar p/ reenviar', cor: cores.erro, fundo: cores.erroFundo },
  nao_configurado: { texto: 'Sem envio', cor: cores.textoSuave, fundo: '#F1F5F9' },
};

export default function Historico() {
  const { chamar } = useAuth();
  const [periodo, setPeriodo] = useState<Periodo>('hoje');
  const [turma, setTurma] = useState('');
  const [atrasos, setAtrasos] = useState<Atraso[]>([]);
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState('');
  const [exportando, setExportando] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro('');
    try {
      setAtrasos(await chamar<Atraso[]>('/atrasos', { params: { ...intervalo(periodo), turma } }));
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao carregar.');
    } finally {
      setCarregando(false);
    }
  }, [chamar, periodo, turma]);

  // Recarrega sempre que a aba é aberta ou o filtro muda
  useFocusEffect(
    useCallback(() => {
      carregar();
    }, [carregar]),
  );

  const reenviar = (atraso: Atraso) => {
    if (atraso.whatsapp_status !== 'falhou') return;
    Alert.alert('Reenviar WhatsApp', `${atraso.whatsapp_detalhe}\n\nTentar enviar de novo para ${atraso.telefone}?`, [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Reenviar',
        onPress: async () => {
          try {
            await chamar(`/atrasos/${atraso.id}/reenviar`, { metodo: 'POST' });
          } catch (e) {
            Alert.alert('Erro', e instanceof Error ? e.message : 'Erro ao reenviar.');
          }
          carregar();
        },
      },
    ]);
  };

  const exportar = async () => {
    setExportando(true);
    try {
      const { token } = await chamar<{ token: string }>('/relatorio/link', { metodo: 'POST' });
      await Linking.openURL(montarUrl('/relatorio.xlsx', { token, ...intervalo(periodo), turma }));
    } catch (e) {
      Alert.alert('Erro', e instanceof Error ? e.message : 'Não foi possível gerar o relatório.');
    } finally {
      setExportando(false);
    }
  };

  return (
    <View style={styles.container}>
      <Cabecalho titulo="Histórico" subtitulo={`${atrasos.length} atraso${atrasos.length === 1 ? '' : 's'} no período`} />
      <Filtros periodo={periodo} onPeriodo={setPeriodo} turma={turma} onTurma={setTurma} />

      <TouchableOpacity style={styles.exportar} onPress={exportar} disabled={exportando}>
        {exportando ? <ActivityIndicator color={cores.primaria} /> : <Text style={styles.exportarTexto}>⬇️ Baixar relatório Excel</Text>}
      </TouchableOpacity>

      {erro ? <Text style={styles.erro}>{erro}</Text> : null}

      <FlatList
        data={atrasos}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.lista}
        refreshControl={<RefreshControl refreshing={carregando} onRefresh={carregar} />}
        ListEmptyComponent={!carregando ? <Text style={styles.vazio}>Nenhum atraso neste período. 🎉</Text> : null}
        ListFooterComponent={<Rodape />}
        renderItem={({ item }) => {
          const selo = SELO[item.whatsapp_status];
          return (
            <TouchableOpacity style={styles.item} onPress={() => reenviar(item)} activeOpacity={item.whatsapp_status === 'falhou' ? 0.6 : 1}>
              <View style={styles.itemTopo}>
                <Text style={styles.nome}>{item.aluno}</Text>
                <Text style={styles.hora}>{formatarDataHora(item.data_hora)}</Text>
              </View>
              <Text style={styles.detalhe}>
                {item.turma} · registrado por {item.registrado_por}
              </Text>
              {item.observacao ? <Text style={styles.detalhe}>“{item.observacao}”</Text> : null}
              <View style={[styles.selo, { backgroundColor: selo.fundo }]}>
                <Text style={[styles.seloTexto, { color: selo.cor }]}>{selo.texto}</Text>
              </View>
            </TouchableOpacity>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: cores.fundo },
  lista: { paddingHorizontal: 16, paddingBottom: 24, gap: 10 },
  exportar: {
    marginHorizontal: 16,
    marginBottom: 8,
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: cores.primaria,
    alignItems: 'center',
  },
  exportarTexto: { color: cores.primaria, fontWeight: '600' },
  erro: { color: cores.erro, marginHorizontal: 16, marginBottom: 8 },
  vazio: { textAlign: 'center', color: cores.textoSuave, marginTop: 40 },
  item: { backgroundColor: cores.cartao, borderRadius: 12, padding: 14, gap: 4, elevation: 1 },
  itemTopo: { flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  nome: { fontSize: 15, fontWeight: '700', color: cores.texto, flex: 1 },
  hora: { fontSize: 13, color: cores.textoSuave },
  detalhe: { fontSize: 13, color: cores.rotulo },
  selo: { alignSelf: 'flex-start', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6, marginTop: 4 },
  seloTexto: { fontSize: 12, fontWeight: '600' },
});
