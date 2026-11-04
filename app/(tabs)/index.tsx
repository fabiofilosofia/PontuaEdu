import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Keyboard,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { Cabecalho } from '@/components/cabecalho';
import { Rodape } from '@/components/rodape';
import { cores } from '@/constants/estilo';
import type { Aluno, ResultadoRegistro } from '@/lib/api';
import { useAuth } from '@/lib/auth';

const MAX_SUGESTOES = 8;

// Compara nomes ignorando acentos e maiúsculas
function normalizar(texto: string) {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}

export default function Registrar() {
  const { chamar } = useAuth();

  const [listaAlunos, setListaAlunos] = useState<Aluno[]>([]);
  const [carregandoLista, setCarregandoLista] = useState(true);
  const [erroLista, setErroLista] = useState('');

  const [busca, setBusca] = useState('');
  const [selecionado, setSelecionado] = useState<Aluno | null>(null);
  const [responsavel, setResponsavel] = useState('');
  const [telefone, setTelefone] = useState('');
  const [observacao, setObservacao] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [resultado, setResultado] = useState<(ResultadoRegistro & { aluno: string }) | null>(null);

  const carregarAlunos = useCallback(
    () =>
      chamar<Aluno[]>('/alunos')
        .then((alunos) => {
          setListaAlunos(alunos);
          setErroLista('');
        })
        .catch((e) => setErroLista(e instanceof Error ? e.message : 'Erro ao carregar alunos.'))
        .finally(() => setCarregandoLista(false)),
    [chamar],
  );

  useEffect(() => {
    carregarAlunos();
  }, [carregarAlunos]);

  const tentarDeNovo = () => {
    setCarregandoLista(true);
    carregarAlunos();
  };

  const termo = normalizar(busca.trim());
  const sugestoes =
    !selecionado && termo.length > 1
      ? listaAlunos.filter((a) => normalizar(a.nome).includes(termo)).slice(0, MAX_SUGESTOES)
      : [];

  const handleBusca = (texto: string) => {
    setBusca(texto);
    setSelecionado(null);
    setResultado(null);
  };

  const selecionarAluno = (aluno: Aluno) => {
    setSelecionado(aluno);
    setBusca(`${aluno.nome} (${aluno.turma})`);
    setResponsavel(aluno.responsavel);
    setTelefone(aluno.telefone);
    Keyboard.dismiss();
  };

  const limpar = () => {
    setBusca('');
    setSelecionado(null);
    setResponsavel('');
    setTelefone('');
    setObservacao('');
  };

  const handleEnviar = async () => {
    if (!selecionado) {
      Alert.alert('Atenção', 'Busque e toque no nome do aluno na lista.');
      return;
    }
    setEnviando(true);
    try {
      const r = await chamar<ResultadoRegistro>('/registrar', {
        metodo: 'POST',
        corpo: {
          aluno_id: selecionado.id,
          nome_responsavel: responsavel,
          telefone_responsavel: telefone,
          observacao,
        },
      });
      setResultado({ ...r, aluno: selecionado.nome });
      limpar();
    } catch (e) {
      Alert.alert('Erro', e instanceof Error ? e.message : 'Ocorreu um erro.');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <View style={styles.container}>
      <Cabecalho titulo="Registrar atraso" subtitulo="Busque o aluno pelo nome" />

      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {resultado ? <Resultado r={resultado} /> : null}

        <View style={styles.card}>
          {erroLista ? (
            <TouchableOpacity onPress={tentarDeNovo} style={styles.avisoErro}>
              <Text style={styles.avisoErroTexto}>{erroLista}</Text>
              <Text style={styles.avisoErroLink}>Tentar novamente</Text>
            </TouchableOpacity>
          ) : null}

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Nome do aluno</Text>
            <TextInput
              style={styles.input}
              placeholder={carregandoLista ? 'Carregando alunos...' : 'Digite o nome do aluno...'}
              placeholderTextColor={cores.placeholder}
              value={busca}
              onChangeText={handleBusca}
              autoCorrect={false}
            />
            {sugestoes.length > 0 && (
              <View style={styles.dropdown}>
                {sugestoes.map((item) => (
                  <TouchableOpacity key={item.id} style={styles.dropdownItem} onPress={() => selecionarAluno(item)}>
                    <Text style={styles.itemNome}>{item.nome}</Text>
                    <Text style={styles.itemTurma}>Turma: {item.turma}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
            {!selecionado && termo.length > 1 && sugestoes.length === 0 && !carregandoLista ? (
              <Text style={styles.semResultado}>Nenhum aluno encontrado.</Text>
            ) : null}
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Responsável</Text>
            <TextInput
              style={styles.input}
              placeholder="Nome do responsável"
              placeholderTextColor={cores.placeholder}
              value={responsavel}
              onChangeText={setResponsavel}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>WhatsApp do responsável</Text>
            <TextInput
              style={styles.input}
              placeholder="Telefone com DDD"
              placeholderTextColor={cores.placeholder}
              keyboardType="phone-pad"
              value={telefone}
              onChangeText={setTelefone}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Observação (opcional)</Text>
            <TextInput
              style={styles.input}
              placeholder="Ex.: chegou com o responsável"
              placeholderTextColor={cores.placeholder}
              value={observacao}
              onChangeText={setObservacao}
            />
          </View>

          <TouchableOpacity
            style={[styles.botao, (enviando || !selecionado) && styles.botaoDesabilitado]}
            onPress={handleEnviar}
            disabled={enviando}>
            {enviando ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.textoBotao}>📲 Registrar e notificar</Text>}
          </TouchableOpacity>
        </View>
        <Rodape />
      </ScrollView>
    </View>
  );
}

function Resultado({ r }: { r: ResultadoRegistro & { aluno: string } }) {
  const ok = r.whatsapp_status === 'enviado';
  return (
    <View style={[styles.resultado, { borderLeftColor: ok ? cores.sucesso : cores.aviso }]}>
      <Text style={styles.resultadoTitulo}>
        {ok ? '✅' : '⚠️'} {r.aluno}
      </Text>
      <Text style={styles.resultadoTexto}>{r.mensagem}</Text>
      {r.whatsapp_status === 'falhou' && r.whatsapp_detalhe ? (
        <Text style={styles.resultadoDetalhe}>{r.whatsapp_detalhe}</Text>
      ) : null}
      <Text style={[styles.resultadoTexto, r.alerta && styles.resultadoAlerta]}>
        {r.alerta ? '🔔 ' : ''}
        {r.total_atrasos} atraso{r.total_atrasos === 1 ? '' : 's'} nos últimos {r.janela_dias} dias
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: cores.fundo },
  content: { padding: 20, gap: 16 },
  card: { backgroundColor: cores.cartao, borderRadius: 16, padding: 20, elevation: 3 },
  inputGroup: { marginBottom: 16 },
  label: { fontSize: 12, fontWeight: '600', color: cores.rotulo, marginBottom: 6, textTransform: 'uppercase' },
  input: {
    borderWidth: 1,
    borderColor: cores.borda,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    backgroundColor: cores.fundo,
    color: cores.texto,
  },
  dropdown: {
    backgroundColor: cores.cartao,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    marginTop: 4,
    overflow: 'hidden',
  },
  dropdownItem: { padding: 12, borderBottomWidth: 1, borderBottomColor: '#F1F5F9' },
  itemNome: { fontSize: 15, fontWeight: 'bold', color: cores.cabecalho },
  itemTurma: { fontSize: 12, color: cores.textoSuave },
  semResultado: { marginTop: 6, color: cores.textoSuave, fontSize: 13 },
  botao: { backgroundColor: cores.primaria, paddingVertical: 16, borderRadius: 10, alignItems: 'center', marginTop: 8 },
  botaoDesabilitado: { backgroundColor: cores.primariaClara },
  textoBotao: { color: '#FFFFFF', fontSize: 16, fontWeight: '600' },
  avisoErro: { backgroundColor: cores.erroFundo, borderRadius: 10, padding: 12, marginBottom: 16 },
  avisoErroTexto: { color: cores.erro, fontSize: 14 },
  avisoErroLink: { color: cores.erro, fontWeight: '700', marginTop: 4 },
  resultado: { backgroundColor: cores.cartao, borderRadius: 12, padding: 16, borderLeftWidth: 5, gap: 4, elevation: 2 },
  resultadoTitulo: { fontSize: 16, fontWeight: '700', color: cores.texto },
  resultadoTexto: { fontSize: 14, color: cores.rotulo },
  resultadoDetalhe: { fontSize: 12, color: cores.erro },
  resultadoAlerta: { color: cores.aviso, fontWeight: '700' },
});
