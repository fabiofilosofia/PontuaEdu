import { StyleSheet, Text, View } from 'react-native';

import { ANO, DESENVOLVEDORES } from '@/constants/escola';
import { cores } from '@/constants/estilo';

export function Rodape({ claro = false }: { claro?: boolean }) {
  const cor = claro ? cores.placeholder : cores.textoSuave;
  return (
    <View style={styles.rodape}>
      <Text style={[styles.texto, { color: cor }]}>
        © {ANO} PontuaEdu · Todos os direitos reservados
      </Text>
      <Text style={[styles.texto, { color: cor }]}>Desenvolvido por {DESENVOLVEDORES} {ANO}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  rodape: { alignItems: 'center', paddingVertical: 16, gap: 2 },
  texto: { fontSize: 11, textAlign: 'center' },
});
