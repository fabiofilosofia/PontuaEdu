import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { cores } from '@/constants/estilo';
import { useAuth } from '@/lib/auth';

export type Periodo = 'hoje' | 'semana' | 'mes' | 'ano';

const ROTULOS: Record<Periodo, string> = { hoje: 'Hoje', semana: '7 dias', mes: '30 dias', ano: 'Este ano' };

function isoLocal(data: Date) {
  const mes = String(data.getMonth() + 1).padStart(2, '0');
  const dia = String(data.getDate()).padStart(2, '0');
  return `${data.getFullYear()}-${mes}-${dia}`;
}

/** Datas de início e fim (AAAA-MM-DD) do período escolhido. */
export function intervalo(periodo: Periodo) {
  const hoje = new Date();
  const inicio = new Date(hoje);
  if (periodo === 'semana') inicio.setDate(hoje.getDate() - 6);
  if (periodo === 'mes') inicio.setDate(hoje.getDate() - 29);
  if (periodo === 'ano') inicio.setMonth(0, 1);
  return { inicio: isoLocal(inicio), fim: isoLocal(hoje) };
}

/** "2026-11-03 07:42:10" → "03/11 07:42" */
export function formatarDataHora(texto: string) {
  const [data, hora = ''] = texto.split(' ');
  const [, mes, dia] = data.split('-');
  return `${dia}/${mes} ${hora.slice(0, 5)}`;
}

function Chip({ rotulo, ativo, onPress }: { rotulo: string; ativo: boolean; onPress: () => void }) {
  return (
    <TouchableOpacity style={[styles.chip, ativo && styles.chipAtivo]} onPress={onPress}>
      <Text style={[styles.chipTexto, ativo && styles.chipTextoAtivo]}>{rotulo}</Text>
    </TouchableOpacity>
  );
}

export function Filtros({
  periodo,
  onPeriodo,
  turma,
  onTurma,
}: {
  periodo: Periodo;
  onPeriodo: (p: Periodo) => void;
  turma: string;
  onTurma: (t: string) => void;
}) {
  const { chamar } = useAuth();
  const [turmas, setTurmas] = useState<string[]>([]);

  useEffect(() => {
    chamar<string[]>('/turmas').then(setTurmas).catch(() => {});
  }, [chamar]);

  return (
    <View style={styles.container}>
      <View style={styles.linha}>
        {(Object.keys(ROTULOS) as Periodo[]).map((p) => (
          <Chip key={p} rotulo={ROTULOS[p]} ativo={periodo === p} onPress={() => onPeriodo(p)} />
        ))}
      </View>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.linha}>
        <Chip rotulo="Todas as turmas" ativo={turma === ''} onPress={() => onTurma('')} />
        {turmas.map((t) => (
          <Chip key={t} rotulo={t} ativo={turma === t} onPress={() => onTurma(t)} />
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 8, paddingHorizontal: 16, paddingVertical: 12 },
  linha: { flexDirection: 'row', gap: 8 },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: cores.borda,
    backgroundColor: cores.cartao,
  },
  chipAtivo: { backgroundColor: cores.primaria, borderColor: cores.primaria },
  chipTexto: { fontSize: 13, color: cores.rotulo, fontWeight: '500' },
  chipTextoAtivo: { color: '#FFFFFF' },
});
