import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { NOME_ESCOLA } from '@/constants/escola';
import { cores } from '@/constants/estilo';
import { useAuth } from '@/lib/auth';

export function Cabecalho({ titulo, subtitulo }: { titulo: string; subtitulo?: string }) {
  const { top } = useSafeAreaInsets();
  const { sessao, sair } = useAuth();

  return (
    <View style={[styles.header, { paddingTop: top + 12 }]}>
      <Text style={styles.escola}>🏫 {NOME_ESCOLA}</Text>
      <View style={styles.linha}>
        <View style={{ flex: 1 }}>
          <Text style={styles.titulo}>{titulo}</Text>
          {subtitulo ? <Text style={styles.subtitulo}>{subtitulo}</Text> : null}
        </View>
        {sessao ? (
          <TouchableOpacity onPress={sair} style={styles.sair} accessibilityLabel="Sair">
            <Text style={styles.sairNome} numberOfLines={1}>{sessao.nome}</Text>
            <Text style={styles.sairTexto}>Sair</Text>
          </TouchableOpacity>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    backgroundColor: cores.cabecalho,
    paddingHorizontal: 20,
    paddingBottom: 18,
    gap: 10,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  escola: {
    fontSize: 12,
    fontWeight: '600',
    color: cores.primariaClara,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  linha: { flexDirection: 'row', alignItems: 'center' },
  titulo: { fontSize: 20, fontWeight: '700', color: '#FFFFFF' },
  subtitulo: { fontSize: 13, color: cores.placeholder, marginTop: 2 },
  sair: { alignItems: 'flex-end', maxWidth: 140 },
  sairNome: { color: '#E2E8F0', fontSize: 12 },
  sairTexto: { color: cores.primariaClara, fontSize: 13, fontWeight: '600' },
});
