import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { ReceiptSummary } from '../types/chat';

interface Props {
  summary: ReceiptSummary;
  onPressDetail: () => void;
}

export const ReceiptSummaryCard: React.FC<Props> = ({ summary, onPressDetail }) => {
  return (
    <View style={styles.card}>
      <Text style={[typography.h3, styles.title]}>Resumen de Comprobantes</Text>

      <View style={styles.row}>
        <Text style={typography.body}>Cantidad:</Text>
        <Text style={[typography.body, styles.value]}>{summary.count}</Text>
      </View>

      <View style={styles.row}>
        <Text style={typography.body}>Monto Total:</Text>
        <Text style={[typography.body, styles.value]}>S/ {summary.totalAmount.toFixed(2)}</Text>
      </View>

      <View style={styles.row}>
        <Text style={typography.body}>Deducible:</Text>
        <Text style={[typography.body, styles.deductibleValue]}>S/ {summary.deductibleAmount.toFixed(2)}</Text>
      </View>

      <TouchableOpacity style={styles.button} onPress={onPressDetail}>
        <Text style={styles.buttonText}>Ver Detalle</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    padding: 16,
    borderRadius: 12,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  title: {
    marginBottom: 12,
    color: colors.text,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  value: {
    fontWeight: '600',
    color: colors.text,
  },
  deductibleValue: {
    fontWeight: 'bold',
    color: colors.secondary,
  },
  button: {
    marginTop: 12,
    backgroundColor: colors.primary,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: colors.surface,
    fontWeight: '600',
    fontSize: 14,
  },
});
