import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, 
  Text, 
  View, 
  TextInput, 
  TouchableOpacity, 
  Alert, 
  ActivityIndicator,
  SafeAreaView,
  StatusBar,
  FlatList,
  Keyboard
} from 'react-native';

// Definindo o tipo de dados do Aluno para o TypeScript não reclamar
interface Aluno {
  aluno: str | any;
  turma: str | any;
  responsavel?: str | any;
  telefone?: str | any;
}

export default function App() {
  // ⚠️ CERTIFIQUE-SE DE USAR SEU IP LOCAL ATUAL DO IPCONFIG
const BASE_URL = "http://192.168.0.12:8000";

  const [listaAlunos, setListaAlunos] = useState<Aluno[]>([]);
  const [busca, setBusca] = useState<string>('');
  const [sugestoes, setSugestoes] = useState<Aluno[]>([]);
  const [exibirSugestoes, setExibirSugestoes] = useState<boolean>(false);

  const [responsavel, setResponsavel] = useState<string>('');
  const [telefone, setTelefone] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    carregarAlunos();
  }, []);

  const carregarAlunos = async () => {
    try {
      const response = await fetch(`${BASE_URL}/alunos`);
      const data = await response.json();
      if (response.ok) {
        setListaAlunos(data);
      }
    } catch (error) {
      console.log("Erro ao carregar alunos do Excel", error);
    }
  };

  // Filtra os alunos conforme digita
  const handleBusca = (texto: string) => {
    setBusca(texto);
    if (texto.length > 1) {
      const filtrados = listaAlunos.filter((item: Aluno) => 
        item.aluno && String(item.aluno).toLowerCase().includes(texto.toLowerCase())
      );
      setSugestoes(filtrados);
      setExibirSugestoes(true);
    } else {
      setSugestoes([]);
      setExibirSugestoes(false);
    }
  };

  // Preenche os dados ao clicar no aluno
  const selecionarAluno = (item: Aluno) => {
    setBusca(`${item.aluno} (${item.turma})`);
    setResponsavel(item.responsavel ? String(item.responsavel) : '');
    setTelefone(item.telefone ? String(item.telefone) : '');
    setExibirSugestoes(false);
    Keyboard.dismiss();
  };

  const handleEnviar = async () => {
    if (!busca.trim() || !responsavel.trim() || !telefone.trim()) {
      Alert.alert("Atenção", "Selecione um aluno e confirme o responsável e telefone.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${BASE_URL}/registrar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          aluno: busca,
          nome_responsavel: responsavel,
          telefone_responsavel: telefone,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        Alert.alert("Sucesso 🎉", data.mensagem);
        setBusca('');
        setResponsavel('');
        setTelefone('');
      } else {
        Alert.alert("Erro", data.detail || "Ocorreu um erro no servidor.");
      }
    } catch (error) {
      Alert.alert("Erro de Conexão", "Não foi possível conectar com a API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1E293B" />
      
      <View style={styles.header}>
        <Text style={styles.headerEmoji}>🏫</Text>
        <Text style={styles.titulo}>Controle de Atrasos</Text>
        <Text style={styles.subtitulo}>Pesquisa Integrada ao Excel</Text>
      </View>

      <View style={styles.content}>
        <View style={styles.card}>
          <Text style={styles.cardHeader}>Buscar Aluno</Text>

          {/* CAMPO DE PESQUISA */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Nome do Aluno</Text>
            <TextInput 
              style={styles.input} 
              placeholder="Digite o nome do aluno..." 
              placeholderTextColor="#94A3B8"
              value={busca}
              onChangeText={handleBusca}
            />

            {/* LISTA SUSPENSA DE SUGESTÕES */}
            {exibirSugestoes && sugestoes.length > 0 && (
              <View style={styles.dropdown}>
                <FlatList
                  data={sugestoes}
                  keyExtractor={(_, index) => index.toString()}
                  keyboardShouldPersistTaps="handled"
                  renderItem={({ item }: { item: Aluno }) => (
                    <TouchableOpacity 
                      style={styles.dropdownItem}
                      onPress={() => selecionarAluno(item)}
                    >
                      <Text style={styles.itemNome}>{item.aluno}</Text>
                      <Text style={styles.itemTurma}>Turma: {item.turma}</Text>
                    </TouchableOpacity>
                  )}
                />
              </View>
            )}
          </View>

          {/* DADOS AUTOMÁTICOS / MANUAL */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Responsável</Text>
            <TextInput 
              style={styles.input} 
              placeholder="Nome do responsável" 
              placeholderTextColor="#94A3B8"
              value={responsavel}
              onChangeText={setResponsavel}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>WhatsApp do Responsável</Text>
            <TextInput 
              style={styles.input} 
              placeholder="Telefone com DDD" 
              placeholderTextColor="#94A3B8"
              keyboardType="numeric"
              value={telefone}
              onChangeText={setTelefone}
            />
          </View>

          <TouchableOpacity 
            style={[styles.botao, loading && styles.botaoDesabilitado]} 
            onPress={handleEnviar} 
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.textoBotao}>📲 Registrar e Notificar</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    backgroundColor: '#1E293B',
    paddingVertical: 20,
    alignItems: 'center',
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  headerEmoji: {
    fontSize: 32,
  },
  titulo: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  subtitulo: {
    fontSize: 13,
    color: '#94A3B8',
  },
  content: {
    padding: 20,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    elevation: 3,
  },
  cardHeader: {
    fontSize: 18,
    fontWeight: '600',
    color: '#0F172A',
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    paddingBottom: 8,
  },
  inputGroup: {
    marginBottom: 16,
    position: 'relative',
    zIndex: 1,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 6,
    textTransform: 'uppercase',
  },
  input: {
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    backgroundColor: '#F8FAFC',
    color: '#0F172A',
  },
  dropdown: {
    maxHeight: 180,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    borderRadius: 10,
    marginTop: 4,
    elevation: 5,
  },
  dropdownItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  itemNome: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#1E293B',
  },
  itemTurma: {
    fontSize: 12,
    color: '#64748B',
  },
  botao: {
    backgroundColor: '#2563EB',
    paddingVertical: 16,
    borderRadius: 10,
    alignItems: 'center',
    marginTop: 8,
  },
  botaoDesabilitado: {
    backgroundColor: '#93C5FD',
  },
  textoBotao: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});