import { useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { Rodape } from '@/components/rodape';
import { NOME_ESCOLA } from '@/constants/escola';
import { cores } from '@/constants/estilo';
import { useAuth } from '@/lib/auth';

export default function Login() {
  const { entrar } = useAuth();
  const [usuario, setUsuario] = useState('');
  const [senha, setSenha] = useState('');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  const handleEntrar = async () => {
    if (!usuario.trim() || !senha) {
      setErro('Preencha usuário e senha.');
      return;
    }
    setErro('');
    setEnviando(true);
    try {
      await entrar(usuario.trim(), senha);
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Não foi possível entrar.');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.marca}>
        <Text style={styles.emoji}>🏫</Text>
        <Text style={styles.titulo}>PontuaEdu</Text>
        <Text style={styles.subtitulo}>Controle de atrasos</Text>
        <Text style={styles.escola}>{NOME_ESCOLA}</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.label}>Usuário</Text>
        <TextInput
          style={styles.input}
          value={usuario}
          onChangeText={setUsuario}
          autoCapitalize="none"
          autoCorrect={false}
          placeholder="seu login"
          placeholderTextColor={cores.placeholder}
        />
        <Text style={styles.label}>Senha</Text>
        <TextInput
          style={styles.input}
          value={senha}
          onChangeText={setSenha}
          secureTextEntry
          placeholder="••••••"
          placeholderTextColor={cores.placeholder}
          onSubmitEditing={handleEntrar}
        />
        {erro ? <Text style={styles.erro}>{erro}</Text> : null}
        <TouchableOpacity style={[styles.botao, enviando && styles.botaoDesabilitado]} onPress={handleEntrar} disabled={enviando}>
          {enviando ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.textoBotao}>Entrar</Text>}
        </TouchableOpacity>
      </View>
      <Rodape claro />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: cores.cabecalho, justifyContent: 'center', padding: 24 },
  marca: { alignItems: 'center', marginBottom: 28 },
  emoji: { fontSize: 44 },
  titulo: { fontSize: 28, fontWeight: '800', color: '#FFFFFF', marginTop: 4 },
  subtitulo: { fontSize: 14, color: cores.placeholder },
  escola: { fontSize: 13, color: cores.primariaClara, fontWeight: '600', marginTop: 8, textAlign: 'center' },
  card: { backgroundColor: cores.cartao, borderRadius: 16, padding: 20, width: '100%', maxWidth: 420, alignSelf: 'center' },
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
    marginBottom: 16,
  },
  erro: { color: cores.erro, marginBottom: 12, fontSize: 14 },
  botao: { backgroundColor: cores.primaria, paddingVertical: 16, borderRadius: 10, alignItems: 'center' },
  botaoDesabilitado: { backgroundColor: cores.primariaClara },
  textoBotao: { color: '#FFFFFF', fontSize: 16, fontWeight: '600' },
});
